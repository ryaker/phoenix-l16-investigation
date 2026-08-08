#!/usr/bin/env python3
"""Read float/double constants out of libcp.dylib by VM address (x86_64 slice)."""
import struct, sys

PATH = "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"

def slices(data):
    magic = struct.unpack_from(">I", data, 0)[0]
    if magic in (0xcafebabe, 0xbebafeca):
        n = struct.unpack_from(">I", data, 4)[0]
        out = []
        for i in range(n):
            cpu, sub, off, size, align = struct.unpack_from(">5I", data, 8 + 20*i)
            out.append((cpu, off, size))
        return out
    return [(None, 0, len(data))]

def sections(data, base):
    magic = struct.unpack_from("<I", data, base)[0]
    assert magic == 0xfeedfacf, hex(magic)
    ncmds = struct.unpack_from("<I", data, base+16)[0]
    off = base + 32
    secs = []
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from("<II", data, off)
        if cmd == 0x19:  # LC_SEGMENT_64
            segname = data[off+8:off+24].rstrip(b"\0").decode()
            nsects = struct.unpack_from("<I", data, off+64)[0]
            so = off + 72
            for _ in range(nsects):
                sn = data[so:so+16].rstrip(b"\0").decode()
                addr, size = struct.unpack_from("<QQ", data, so+32)
                foff = struct.unpack_from("<I", data, so+48)[0]
                secs.append((segname, sn, addr, size, base+foff))
                so += 80
        off += cmdsize
    return secs

def main():
    data = open(PATH, "rb").read()
    # pick x86_64 slice
    base = 0
    for cpu, off, size in slices(data):
        if cpu is None or cpu == 0x01000007:
            base = off
            break
    secs = sections(data, base)
    addrs = [int(a, 16) for a in sys.argv[1:]]
    for a in addrs:
        hit = None
        for segname, sn, addr, size, foff in secs:
            if addr <= a < addr + size:
                hit = (segname, sn, foff + (a - addr))
                break
        if not hit:
            print(f"{a:#x}: NOT MAPPED")
            continue
        segname, sn, fo = hit
        raw = data[fo:fo+16]
        f = struct.unpack_from("<4f", raw)
        d = struct.unpack_from("<2d", raw)
        i = struct.unpack_from("<4I", raw)
        print(f"{a:#x} [{segname},{sn}] bytes={raw.hex()}")
        print(f"    f32x4 = {f}")
        print(f"    f64x2 = {d}")
        print(f"    u32x4 = {tuple(hex(x) for x in i)}")

main()
