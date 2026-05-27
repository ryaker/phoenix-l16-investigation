import builtins
import struct


def reset():
    builtins.l16_36e530_prep_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _f32s(data):
    return list(struct.unpack("<" + "f" * (len(data) // 4), data))


def hit(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()

    rbp = _u(frame, "rbp")
    rax = _u(frame, "rax")
    rdx = _u(frame, "rdx")
    r8 = _u(frame, "r8")
    rsi = _u(frame, "rsi")
    r12 = _u(frame, "r12")
    r13 = _u(frame, "r13")
    scratch_base = rbp - 0x4240
    weights_addr = rbp - 0xA0

    weights_data = _read(process, weights_addr, 16 * 4)
    source_vec4_data = _read(process, rax, 4 * 4)
    dest_vec4_data = _read(process, rdx, 4 * 4)

    if None in (weights_data, source_vec4_data, dest_vec4_data):
        builtins.l16_36e530_prep_first = {
            "error": "failed to read accumulator-prep packet",
            "rip": _u(frame, "rip"),
            "rbp": rbp,
            "rax": rax,
            "rdx": rdx,
            "r8": r8,
            "scratch_base": scratch_base,
            "weights_addr": weights_addr,
        }
        return

    weights = _f32s(weights_data)
    first_weight_product = weights[0] * weights[0]

    builtins.l16_36e530_prep_first = {
        "rip": _u(frame, "rip"),
        "rbp": rbp,
        "scratch_base": scratch_base,
        "source_ptr_rax": rax,
        "source_offset_from_scratch": rax - scratch_base,
        "dest_ptr_rdx": rdx,
        "dest_offset_from_scratch": rdx - scratch_base,
        "dest_row_stride_bytes_r8": r8,
        "loop_row_rsi": rsi,
        "r12": r12,
        "r13": r13,
        "weights_addr": weights_addr,
        "weight16": weights,
        "first_weight_product": first_weight_product,
        "first_source_vec4": _f32s(source_vec4_data),
        "first_dest_vec4_before_add": _f32s(dest_vec4_data),
    }


def report(label):
    if not hasattr(builtins, "l16_36e530_prep_first"):
        reset()
    print("L16_36E530_PREP_PROBE_BEGIN", label)
    print("prep_packet", builtins.l16_36e530_prep_first)
    print("L16_36E530_PREP_PROBE_END", label)
