import builtins, json, struct

def reset(path): builtins.PR={"path":path,"pairs":[],"meta":{}}
def _st(): return builtins.PR
def _fr(dbg):
    t=dbg.GetSelectedTarget();p=t.GetProcess();th=p.GetSelectedThread();return p,th.GetSelectedFrame()
def _rd(p,a,n):
    import lldb
    e=lldb.SBError();r=p.ReadMemory(a,n,e);return r if(e.Success() and r and len(r)==n) else None
def _q(p,a):
    r=_rd(p,a,8);return struct.unpack("<Q",r)[0] if r else 0
def _i(p,a):
    r=_rd(p,a,4);return struct.unpack("<i",r)[0] if r else 0
def _desc(p,base):
    return {"W":_i(p,base+0x08),"H":_i(p,base+0x0c),"stride":_i(p,base+0x10),"data":_q(p,base+0x20)}
def _px(p,data,st,x,y):
    r=_rd(p,data+(y*st+x)*16,16)
    return struct.unpack("<4f",r) if r else None

def cap(dbg):
    p,fr=_fr(dbg)
    rbp=fr.FindRegister("rbp").GetValueAsUnsigned()
    r14=fr.FindRegister("r14").GetValueAsUnsigned()
    ind=_desc(p,_q(p,rbp-0xc8))
    out=_desc(p,r14+0x70)
    _st()["meta"]={"in":{k:ind[k] for k in('W','H','stride')},"out":{k:out[k] for k in('W','H','stride')}}
    if not(ind["data"] and out["data"]): return True
    Wo,Ho=out["W"],out["H"]; ost=out["stride"] or Wo
    Wi,Hi=ind["W"],ind["H"]; ist=ind["stride"] or Wi
    sx=Wi//Wo if Wo else 1; sy=Hi//Ho if Ho else 1   # downsample factor (2)
    pr=[]
    for y in range(2,Ho-2,max(1,Ho//150)):
        for x in range(2,Wo-2,max(1,Wo//150)):
            vo=_px(p,out["data"],ost,x,y)
            # average sx*sy input block
            acc=[0.0,0.0,0.0,0.0];n=0
            for dy in range(sy):
                for dx in range(sx):
                    vi=_px(p,ind["data"],ist,x*sx+dx,y*sy+dy)
                    if vi:
                        for c in range(4):acc[c]+=vi[c]
                        n+=1
            if vo and n:
                vi=[a/n for a in acc]
                if all(-1e5<z<1e5 for z in vi[:3]+list(vo[:3])):
                    pr.append([vi[0],vi[1],vi[2],vo[0],vo[1],vo[2]])
    _st()["pairs"]=pr
    return True

def report(dbg):
    s=_st()
    with open(s["path"],"w") as f: json.dump({"meta":s["meta"],"npairs":len(s["pairs"]),"pairs":s["pairs"]},f)
    print("PAIRS_REPORT %s npairs=%d"%(s["path"],len(s["pairs"])))
