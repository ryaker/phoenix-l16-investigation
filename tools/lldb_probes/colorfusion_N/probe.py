import lldb, json
Ns = []; desc = {}; DONE = [False]

def on_cfb(frame, bp_loc, internal_dict):
    proc = frame.GetThread().GetProcess()
    err = lldb.SBError()
    rcx = frame.FindRegister("rcx").GetValueAsUnsigned()
    beg = proc.ReadUnsignedFromMemory(rcx, 8, err)
    end = proc.ReadUnsignedFromMemory(rcx + 8, 8, err)
    if not (err.Success() and end >= beg and (end-beg) % 0x30 == 0):
        return False
    n = (end - beg)//0x30
    Ns.append(n)
    if not DONE[0] and n > 0:
        DONE[0] = True
        rows = []
        for k in range(n):
            base = beg + k*0x30
            u32 = [proc.ReadUnsignedFromMemory(base+o, 4, lldb.SBError()) & 0xffffffff for o in range(0,0x30,4)]
            # follow each 8-byte slot that looks like a heap ptr, read a small int (camera key 0..15) at its head
            follow = {}
            for o in range(0,0x30,8):
                p = proc.ReadUnsignedFromMemory(base+o, 8, lldb.SBError())
                if 0x100000000 < p < 0x7fffffffffff:
                    hv = proc.ReadUnsignedFromMemory(p, 4, lldb.SBError()) & 0xffffffff
                    if hv < 64: follow[hex(o)] = hv
            rows.append({"k":k,"u32":u32,"ptr_head_smallints":follow})
        desc["first_tile"] = {"N":n,"rows":rows}
    if len(Ns) >= 400:
        proc.Kill()
    return False

def summarize(path):
    from collections import Counter
    out = {"hits":len(Ns),"N_hist":dict(sorted(Counter(Ns).items())),"desc":desc}
    open(path,"w").write(json.dumps(out,indent=2)); print("SUMMARY", json.dumps(out))
