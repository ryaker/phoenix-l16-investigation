import builtins, json, struct

def reset(path,maxhits=6): builtins.P6={"path":path,"hits":[],"max":maxhits}
def _st(): return builtins.P6
def _fr(dbg):
    t=dbg.GetSelectedTarget();p=t.GetProcess();th=p.GetSelectedThread();return p,th.GetSelectedFrame()
def _rd(p,a,n):
    import lldb
    e=lldb.SBError();r=p.ReadMemory(a,n,e);return r if(e.Success() and r and len(r)==n) else None

def _floats(p,a,n):
    b=_rd(p,a,4*n)
    if not b: return None
    return [round(v,8) for v in struct.unpack("<%df"%n,b)]

def cap(dbg):
    p,fr=_fr(dbg)
    s=_st()
    if len(s["hits"])>=s["max"]: return False
    h={}
    regs={}
    for r in ("rdi","rsi","rdx","rcx","r8","r9","rsp","rbp","rbx","r12","r13","r14","r15"):
        v=fr.FindRegister(r)
        regs[r]=v.GetValueAsUnsigned() if v.IsValid() else 0
    h["regs"]={k:hex(v) for k,v in regs.items()}
    for r in ("xmm0","xmm1","xmm2","xmm3"):
        v=fr.FindRegister(r)
        if v.IsValid():
            try: h[r]=[round(struct.unpack("<f",bytes(v.GetData().uint8[i*4:(i+1)*4]))[0],8) for i in range(4)]
            except Exception: pass
    # dump candidate float windows
    for r in ("rdi","rsi","rdx","rcx","r8","r9"):
        a=regs[r]
        if a>0x10000:
            h["f_"+r]=_floats(p,a,24)
    h["f_stack"]=_floats(p,regs["rsp"],48)
    s["hits"].append(h)
    return True

def report(dbg):
    s=_st()
    with open(s["path"],"w") as f: json.dump({"nhits":len(s["hits"]),"hits":s["hits"]},f,indent=1)
    print("P6_REPORT %s nhits=%d"%(s["path"],len(s["hits"])))
