import builtins, json, struct
import lldb
def reset(o): builtins.l16s={"out":o,"ev":[],"err":[]}
def _s(): return builtins.l16s
def rf(proc,addr,n):
    e=lldb.SBError(); d=proc.ReadMemory(addr,n*4,e)
    return list(struct.unpack("<%df"%n,d)) if e.Success() else None
def on_solver(frame,loc,d):
    st=_s()
    try:
        p=frame.GetThread().GetProcess()
        regs={r:frame.FindRegister(r).GetValueAsUnsigned() for r in ("rdi","rsi","rdx","rcx","r8")}
        ev={"regs":{k:hex(v) for k,v in regs.items()}}
        # try reading 3-9 floats at each pointer arg
        for r,a in regs.items():
            for cnt in (3,9):
                v=rf(p,a,cnt)
                if v and all(abs(x)<1e6 for x in v) and any(abs(x)>1e-4 for x in v):
                    ev.setdefault("reads",{})[f"{r}+{cnt}"]=[round(x,6) for x in v]
        # xmm0-2 (args may be in xmm)
        for xr in ("xmm0","xmm1","xmm2"):
            reg=frame.FindRegister(xr)
            if reg and reg.IsValid():
                try: ev.setdefault("xmm",{})[xr]=str(reg.GetValue())
                except: pass
        st["ev"].append(ev)
    except Exception as e: st["err"].append(str(e))
    return True   # stop at first
def report(dbg):
    st=_s(); json.dump(st,open(st["out"],"w"),indent=1)
    print("SOLVER_IN_REPORT",st["out"],"ev",len(st["ev"]),"err",st["err"][:2])
