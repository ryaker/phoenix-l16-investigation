import builtins
import struct


def reset():
    builtins.l16_iramp_square_copy_handoff_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _f32s(data):
    return list(struct.unpack("<" + "f" * (len(data) // 4), data))


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "error": "failed to read descriptor"}

    width = _i32(data, 0x10)
    height = _i32(data, 0x14)
    stride = _i32(data, 0x18)
    base = _u64(data, 0x20)
    first_vec_data = _read(process, base, 16) if base else None
    first_vec4 = _f32s(first_vec_data) if first_vec_data is not None else None
    return {
        "addr": addr,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "width_0x10": width,
        "height_0x14": height,
        "stride_0x18": stride,
        "data_ptr_0x20": base,
        "qword_28": _u64(data, 0x28),
        "first_vec4": first_vec4,
        "first_vec4_squared": [v * v for v in first_vec4] if first_vec4 is not None else None,
    }


def hit(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()

    rbp = _u(frame, "rbp")
    rbx = _u(frame, "rbx")
    rdi = _u(frame, "rdi")
    rsi = _u(frame, "rsi")
    r15 = _u(frame, "r15")

    wrapper_data = _read(process, rsi, 8)
    roi_data = _read(process, rbx, 16)
    source_desc = _u64(wrapper_data) if wrapper_data is not None else 0

    if roi_data is not None:
        roi = [_i32(roi_data, off) for off in (0, 4, 8, 12)]
        roi_width = roi[2] - roi[0]
        roi_height = roi[3] - roi[1]
    else:
        roi = None
        roi_width = None
        roi_height = None

    source = _descriptor(process, source_desc) if source_desc else None
    dest_before = _descriptor(process, rdi) if rdi else None
    source_matches_roi = None
    if source is not None and "error" not in source and roi_width is not None:
        source_matches_roi = (
            source["width_0x10"] == roi_width
            and source["height_0x14"] == roi_height
        )

    builtins.l16_iramp_square_copy_handoff_first = {
        "rip": _u(frame, "rip"),
        "rbp": rbp,
        "rbx_roi_ptr": rbx,
        "rdi_destination_descriptor": rdi,
        "r15_saved_destination_descriptor": r15,
        "rsi_source_wrapper_ptr": rsi,
        "source_wrapper_expected_rbp_minus_0x88": rbp - 0x88,
        "source_desc_from_wrapper": source_desc,
        "source_desc_expected_rbp_minus_0x60": rbp - 0x60,
        "source_wrapper_is_stack_minus_0x88": rsi == rbp - 0x88,
        "source_desc_is_stack_minus_0x60": source_desc == rbp - 0x60,
        "destination_register_matches_saved_r15": rdi == r15,
        "roi_rect_i32": roi,
        "roi_width": roi_width,
        "roi_height": roi_height,
        "source_descriptor": source,
        "destination_descriptor_before_helper": dest_before,
        "source_dimensions_match_roi": source_matches_roi,
    }


def report(label):
    if not hasattr(builtins, "l16_iramp_square_copy_handoff_first"):
        reset()
    print("L16_IRAMP_SQUARE_COPY_HANDOFF_PROBE_BEGIN", label)
    print("handoff_packet", builtins.l16_iramp_square_copy_handoff_first)
    print("L16_IRAMP_SQUARE_COPY_HANDOFF_PROBE_END", label)
