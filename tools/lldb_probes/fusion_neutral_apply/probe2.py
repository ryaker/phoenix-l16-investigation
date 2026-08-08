import builtins, json, struct

def reset(path):
    builtins.NE2 = {"path": path, "hits": []}
def _st(): return builtins.NE2
def _ctx(dbg):
    t=dbg.GetSelectedTarget(); p=t.GetProcess(); th=p.GetSelectedThread()
    return t,p,th,th.GetSelectedFrame()
def _rd(p,a,n):
    import lldb
    e=lldb.SBError(); raw=p.ReadMemory(a,n,e)
    return raw if (e.Success() and raw and len(raw)==n) else None
def _f(p,a,n):
    r=_rd(p,a,4*n); return list(struct.unpack("<%df"%n,r)) if r else None
def _q(p,a):
    r=_rd(p,a,8); return struct.unpack("<Q",r)[0] if r else None

def cap(dbg):
    t,p,th,fr=_ctx(dbg)
    r14=fr.FindRegister("r14").GetValueAsUnsigned()
    h={"r14":hex(r14),
       "img+0x70_as8q":[hex(_q(p,r14+0x70+8*i) or 0) for i in range(8)],
       "img+0x70_16f":_f(p,r14+0x70,16)}
    # follow pointer at +0x70 (vector data ptr) and read floats
    ptr=_q(p,r14+0x70)
    if ptr and ptr>0x1000:
        h["deref70_24f"]=_f(p,ptr,24)
    ptr2=_q(p,r14+0x78)
    h["p70"]=hex(ptr or 0); h["p78"]=hex(ptr2 or 0)
    _st()["hits"].append(h)
    return True

def report(dbg):
    s=_st()
    with open(s["path"],"w") as f: json.dump({"hits":s["hits"]},f,indent=2)
    print("NE2_REPORT "+s["path"]+" hits="+str(len(s["hits"])))
