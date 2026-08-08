import builtins, json, struct

def reset(path):
    builtins.NEU = {"path": path, "hits": [], "errors": []}

def _st(): return builtins.NEU

def _ctx(dbg):
    t=dbg.GetSelectedTarget(); p=t.GetProcess(); th=p.GetSelectedThread()
    return t,p,th,th.GetSelectedFrame()

def _rd(p,a,n):
    import lldb
    e=lldb.SBError(); raw=p.ReadMemory(a,n,e)
    return raw if (e.Success() and raw and len(raw)==n) else None

def _f(p,a,n):
    r=_rd(p,a,4*n)
    return list(struct.unpack("<%df"%n, r)) if r else None

def _u(p,a,n):
    r=_rd(p,a,4*n)
    return list(struct.unpack("<%di"%n, r)) if r else None

def cap(dbg):
    t,p,th,fr=_ctx(dbg)
    rdi=fr.FindRegister("rdi").GetValueAsUnsigned()
    rsi=fr.FindRegister("rsi").GetValueAsUnsigned()
    rdx=fr.FindRegister("rdx").GetValueAsUnsigned()
    h={"rdi":hex(rdi),"rdx":hex(rdx),
       "n_at_rdx_8f": _f(p,rdx,8),
       "img+0x70_12f": _f(p,rdi+0x70,12),
       "img+0x110_16f": _f(p,rdi+0x110,16),
       "img+0x140_int4": _u(p,rdi+0x140,4)}
    _st()["hits"].append(h)
    return len(_st()["hits"])>=3

def report(dbg):
    s=_st()
    with open(s["path"],"w") as f:
        json.dump({k:v for k,v in s.items() if k!="path"}, f, indent=2)
    print("FUSION_NEUTRAL_REPORT "+s["path"]+" hits="+str(len(s["hits"])))
