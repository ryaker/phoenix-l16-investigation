import builtins, json, struct

def reset(path): builtins.P4={"path":path,"o":{}}
def _st(): return builtins.P4
def _fr(dbg):
    t=dbg.GetSelectedTarget();p=t.GetProcess();th=p.GetSelectedThread();return p,th,th.GetSelectedFrame()
def _rd(p,a,n):
    import lldb
    e=lldb.SBError();r=p.ReadMemory(a,n,e);return r if(e.Success() and r and len(r)==n) else None
def _q(p,a):
    r=_rd(p,a,8);return struct.unpack("<Q",r)[0] if r else 0
def _i(p,a):
    r=_rd(p,a,4);return struct.unpack("<i",r)[0] if r else 0
def _desc(p,b):
    return {"base":b,"W":_i(p,b+0x08),"H":_i(p,b+0x0c),"stride":_i(p,b+0x10),"data":_q(p,b+0x20)}

def _hexrow(p,d,bpp,x,y,n=64):
    a=d["data"]+(y*d["stride"]+x)*bpp
    r=_rd(p,a,n)
    if not r: return None
    return {"addr":hex(a),"hex":r.hex(),
            "f32":[round(v,7) for v in struct.unpack("<%df"%(n//4),r)],
            "u16":list(struct.unpack("<%dH"%(n//2),r))}

def _mean(p,d,bpp,nch,phase=True):
    W,H,st,data=d["W"],d["H"],d["stride"],d["data"]
    if not data: return None
    acc=[[0.0]*nch for _ in range(4)];cnt=[0]*4
    sy=max(2,(H//150)//2*2); sx=max(2,(W//150)//2*2)
    for y in range(8,H-8,sy):
        for x in range(8,W-8,sx):
            for dy in range(2):
                for dx in range(2):
                    r=_rd(p,data+((y+dy)*st+(x+dx))*bpp,4*nch)
                    if not r: continue
                    v=struct.unpack("<%df"%nch,r)
                    if not all(-1e8<z<1e8 for z in v): continue
                    ph=dy*2+dx
                    for c in range(nch): acc[ph][c]+=v[c]
                    cnt[ph]+=1
    return {"ph%d"%ph:([round(a/cnt[ph],8) for a in acc[ph]] if cnt[ph] else None) for ph in range(4)}

def cap1(dbg):
    p,th,fr=_fr(dbg)
    rbp=fr.FindRegister("rbp").GetValueAsUnsigned()
    r14=fr.FindRegister("r14").GetValueAsUnsigned()
    s=_st()["o"]
    ind=_desc(p,_q(p,rbp-0xc8)); out=_desc(p,r14+0x70)
    builtins.P4["in"]=ind; builtins.P4["out"]=out
    s["in"]={k:(hex(v) if k in("base","data") else v) for k,v in ind.items()}
    s["out"]={k:(hex(v) if k in("base","data") else v) for k,v in out.items()}
    s["pre_in_hex"]=_hexrow(p,ind,4,1000,1000)
    s["pre_out_hex_bpp16"]=_hexrow(p,out,16,500,500)
    s["pre_out_hex_bpp8"]=_hexrow(p,out,8,500,500)
    s["retaddr"]=hex(_q(p,rbp+8))
    return True

def cap2(dbg):
    p,th,fr=_fr(dbg)
    s=_st()["o"]; ind=builtins.P4["in"]; out=builtins.P4["out"]
    s["post_out_hex_bpp16"]=_hexrow(p,out,16,500,500)
    s["post_out_hex_bpp8"]=_hexrow(p,out,8,500,500)
    s["post_in_hex"]=_hexrow(p,ind,4,1000,1000)
    s["in_mean_f32x1"]=_mean(p,ind,4,1)
    s["in_mean_f32x4"]=_mean(p,ind,16,4)
    s["out_mean_f32x4"]=_mean(p,out,16,4)
    s["out_mean_f32x1"]=_mean(p,out,4,1)
    return True

def report(dbg):
    s=_st()
    with open(s["path"],"w") as f: json.dump(s["o"],f,indent=1)
    print("P4_REPORT "+s["path"])
