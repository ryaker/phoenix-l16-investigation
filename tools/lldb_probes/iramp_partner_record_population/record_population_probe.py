import builtins
import struct


DESCRIPTOR_OFFSETS = [
    0x10,
    0x40,
    0x70,
    0xA0,
    0xD0,
    0x100,
    0x130,
    0x160,
    0x190,
    0x1C0,
    0x1F0,
    0x220,
    0x250,
]


def reset():
    builtins.l16_record_population_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _i32(data, off):
    return struct.unpack_from("<i", data, off)[0]


def _u64(data, off):
    return struct.unpack_from("<Q", data, off)[0]


def _descriptor(data, record_addr, offset):
    base = offset
    return {
        "offset": hex(offset),
        "addr": record_addr + offset,
        "i32_00": _i32(data, base + 0x00),
        "i32_04": _i32(data, base + 0x04),
        "i32_08": _i32(data, base + 0x08),
        "i32_0c": _i32(data, base + 0x0C),
        "i32_10": _i32(data, base + 0x10),
        "i32_14": _i32(data, base + 0x14),
        "i32_18": _i32(data, base + 0x18),
        "i32_1c": _i32(data, base + 0x1C),
        "ptr_20": _u64(data, base + 0x20),
        "ptr_28": _u64(data, base + 0x28),
    }


def hit(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    end_ptr_data = _read(process, rbp - 0x17F8, 8)
    begin_ptr_data = _read(process, rbp - 0x1800, 8)
    if end_ptr_data is None or begin_ptr_data is None:
        builtins.l16_record_population_first = {"error": "failed to read vector begin/end"}
        return

    end = struct.unpack("<Q", end_ptr_data)[0]
    begin = struct.unpack("<Q", begin_ptr_data)[0]
    record = end - 0x280
    record_data = _read(process, record, 0x280)
    if record_data is None:
        builtins.l16_record_population_first = {
            "rbp": rbp,
            "begin": begin,
            "end": end,
            "record": record,
            "error": "failed to read record",
        }
        return

    diff = end - begin if end >= begin else None
    builtins.l16_record_population_first = {
        "rbp": rbp,
        "begin": begin,
        "end": end,
        "diff": diff,
        "npartners": diff // 0x280 if diff is not None else None,
        "record": record,
        "scalar_i32_00": _i32(record_data, 0x00),
        "scalar_i32_04": _i32(record_data, 0x04),
        "scalar_i32_08": _i32(record_data, 0x08),
        "scalar_i32_0c": _i32(record_data, 0x0C),
        "descriptor_offsets": [hex(x) for x in DESCRIPTOR_OFFSETS],
        "descriptors": [_descriptor(record_data, record, x) for x in DESCRIPTOR_OFFSETS],
    }


def report(label):
    if not hasattr(builtins, "l16_record_population_first"):
        reset()
    print("L16_RECORD_POPULATION_PROBE_BEGIN", label)
    print("record_population", builtins.l16_record_population_first)
    print("L16_RECORD_POPULATION_PROBE_END", label)
