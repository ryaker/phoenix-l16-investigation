import builtins, json, struct, os

def reset(d):
    os.makedirs(d, exist_ok=True)
    builtins.P5={"dir":d,"o":{}}
def _st(): return builtins.P5
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

def _dump(p,d,bpp,path):
    W,H,st,data=d["W"],d["H"],d["stride"],d["data"]
    rb=st*bpp
    ok=0
    with open(path,"wb") as f:
        for y in range(H):
            r=_rd(p,data+y*rb,rb)
            if r is None:
                f.write(b"\x00"*rb)
            else:
                f.write(r); ok+=1
    return {"path":path,"W":W,"H":H,"stride":st,"bpp":bpp,"rows_ok":ok}

def cap1(dbg):
    p,th,fr=_fr(dbg)
    rbp=fr.FindRegister("rbp").GetValueAsUnsigned()
    r14=fr.FindRegister("r14").GetValueAsUnsigned()
    s=_st(); o=s["o"]
    ind=_desc(p,_q(p,rbp-0xc8)); out=_desc(p,r14+0x70)
    s["in"]=ind; s["out"]=out; s["r14"]=r14
    o["in_desc"]={k:(hex(v) if k in("base","data") else v) for k,v in ind.items()}
    o["out_desc"]={k:(hex(v) if k in("base","data") else v) for k,v in out.items()}
    # neutral color guard block at r14+0x114
    b=_rd(p,r14+0x110,0x20)
    if b: o["r14_0x110_f32"]=[round(v,6) for v in struct.unpack("<8f",b)]
    o["in_dump"]=_dump(p,ind,2,s["dir"]+"/in_bayer_u16.raw")
    o["pre_out_dump"]=_dump(p,out,8,s["dir"]+"/pre_out_rgba16f.raw")
    return True

def cap2(dbg):
    p,th,fr=_fr(dbg)
    s=_st(); o=s["o"]
    o["post_out_dump"]=_dump(p,s["out"],8,s["dir"]+"/post_out_rgba16f.raw")
    return True

def report(dbg):
    s=_st()
    with open(s["dir"]+"/p5.json","w") as f: json.dump(s["o"],f,indent=1)
    print("P5_REPORT "+s["dir"]+"/p5.json")
