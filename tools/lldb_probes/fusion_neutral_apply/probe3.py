import builtins, json, struct

def reset(path): builtins.NE3={"path":path,"hits":[]}
def _st(): return builtins.NE3
def _fr(dbg):
    t=dbg.GetSelectedTarget();p=t.GetProcess();th=p.GetSelectedThread();return p,th.GetSelectedFrame()
def _rd(p,a,n):
    import lldb
    e=lldb.SBError();r=p.ReadMemory(a,n,e);return r if(e.Success() and r and len(r)==n) else None
def _q(p,a):
    r=_rd(p,a,8);return struct.unpack("<Q",r)[0] if r else 0
def _i(p,a):
    r=_rd(p,a,4);return struct.unpack("<i",r)[0] if r else 0

def _imgmean(p,base):
    W=_i(p,base+0x08);H=_i(p,base+0x0c);data=_q(p,base+0x20);st=_i(p,base+0x10) or W
    if not(16<W<20000 and 16<H<20000 and data>0x10000): return {"W":W,"H":H,"bad":1}
    acc=[0.0,0.0,0.0];n=0
    for y in range(2,H-2,max(1,H//200)):
        for x in range(2,W-2,max(1,W//200)):
            r=_rd(p,data+(y*st+x)*16,16)
            if r:
                v=struct.unpack("<4f",r)
                if v[1]>1e-3 and all(-1e5<z<1e5 for z in v):
                    acc[0]+=v[0];acc[1]+=v[1];acc[2]+=v[2];n+=1
    if not n: return {"W":W,"H":H,"n":0}
    return {"W":W,"H":H,"n":n,"R/G":acc[0]/acc[1],"B/G":acc[2]/acc[1]}

def cap(dbg):
    p,fr=_fr(dbg)
    r14=fr.FindRegister("r14").GetValueAsUnsigned()
    _st()["hits"].append({"out(img+0x70)":_imgmean(p,r14+0x70)})
    return True

def report(dbg):
    s=_st()
    with open(s["path"],"w") as f: json.dump({"hits":s["hits"]},f,indent=2)
    print("NE3_REPORT "+s["path"])
