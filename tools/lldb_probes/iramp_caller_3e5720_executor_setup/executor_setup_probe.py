import builtins
import struct


def reset():
    builtins.l16_3e5720_executor_setup_first = None


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


def _descriptor(process, addr, first_size):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "error": "failed to read descriptor"}

    base = _u64(data, 0x20)
    first_data = _read(process, base, first_size) if base else None
    first_vec4 = _f32s(first_data) if first_data is not None and first_size == 16 else None
    first_bytes = list(first_data) if first_data is not None else None
    return {
        "addr": addr,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "width_0x10": _i32(data, 0x10),
        "height_0x14": _i32(data, 0x14),
        "stride_0x18": _i32(data, 0x18),
        "data_ptr_0x20": base,
        "qword_28": _u64(data, 0x28),
        "first_bytes": first_bytes,
        "first_vec4": first_vec4,
    }


def hit(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    rdi = _u(frame, "rdi")
    rsi = _u(frame, "rsi")
    rdx = _u(frame, "rdx")
    rcx = _u(frame, "rcx")
    thread = frame.GetThread()
    caller_pc = thread.GetFrameAtIndex(1).GetPC() if thread.GetNumFrames() > 1 else None

    callback_data = _read(process, rcx, 0x20)
    if callback_data is None:
        builtins.l16_3e5720_executor_setup_first = {
            "rip": _u(frame, "rip"),
            "rbp": rbp,
            "callback_object_rcx": rcx,
            "error": "failed to read callback object",
        }
        return

    callback_aux = _u64(callback_data, 0x08)
    dest_desc = _u64(callback_data, 0x10)
    source_desc = _u64(callback_data, 0x18)
    callback_aux_data = _read(process, callback_aux, 8) if callback_aux else None

    builtins.l16_3e5720_executor_setup_first = {
        "rip": _u(frame, "rip"),
        "caller_pc": caller_pc,
        "rbp": rbp,
        "thread_id": thread.GetThreadID(),
        "executor_arg_begin_rdi": rdi,
        "executor_arg_end_rsi": rsi,
        "executor_arg_chunk_rdx": rdx,
        "callback_object_rcx": rcx,
        "callback_vtable": _u64(callback_data, 0x00),
        "callback_aux_ptr_0x08": callback_aux,
        "callback_aux_first_qword": _u64(callback_aux_data) if callback_aux_data else None,
        "dest_descriptor_0x10": dest_desc,
        "source_descriptor_0x18": source_desc,
        "dest_descriptor": _descriptor(process, dest_desc, 12) if dest_desc else None,
        "source_descriptor": _descriptor(process, source_desc, 16) if source_desc else None,
    }


def report(label):
    if not hasattr(builtins, "l16_3e5720_executor_setup_first"):
        reset()
    print("L16_3E5720_EXECUTOR_SETUP_PROBE_BEGIN", label)
    print("setup_packet", builtins.l16_3e5720_executor_setup_first)
    print("L16_3E5720_EXECUTOR_SETUP_PROBE_END", label)
