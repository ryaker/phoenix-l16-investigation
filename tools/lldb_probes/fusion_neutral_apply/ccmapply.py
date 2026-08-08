import builtins, json, struct
def reset(path): builtins.CA={"path":path,"hits":[]}
def _st(): return builtins.CA
def _fr(dbg):
    t=dbg.GetSelectedTarget();p=t.GetProcess();th=p.GetSelectedThread();return p,th.GetSelectedFrame()
def _rd(p,a,n):
    import lldb
    e=lldb.SBError();r=p.ReadMemory(a,n,e);return r if(e.Success() and r and len(r)==n) else None
def cap(dbg):
    p,fr=_fr(dbg)
    rbp=fr.FindRegister("rbp").GetValueAsUnsigned()
    offs=[0x7c,0x80,0x84,0x88,0x8c,0x90,0x94,0x98,0x9c]
    vals=[]
    for o in offs:
        r=_rd(p,rbp-o,4); vals.append(struct.unpack("<f",r)[0] if r else None)
    _st()["hits"].append({"nine_floats_order[-7c..-9c]":vals})
    return len(_st()["hits"])>=2
def report(dbg):
    s=_st()
    with open(s["path"],"w") as f: json.dump({"hits":s["hits"]},f,indent=2)
    print("CCMAPPLY_REPORT %s hits=%d"%(s["path"],len(s["hits"])))
