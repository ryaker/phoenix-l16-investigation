import builtins, json, struct

def reset(path): builtins.FM={"path":path,"o":{}}
def _st(): return builtins.FM
def _fr(dbg):
    t=dbg.GetSelectedTarget();p=t.GetProcess();th=p.GetSelectedThread();return p,th.GetSelectedFrame()
def _rd(p,a,n):
    import lldb
    e=lldb.SBError();r=p.ReadMemory(a,n,e);return r if(e.Success() and r and len(r)==n) else None
def _q(p,a):
    r=_rd(p,a,8);return struct.unpack("<Q",r)[0] if r else 0
def _i(p,a):
    r=_rd(p,a,4);return struct.unpack("<i",r)[0] if r else 0

def _hdr(p,base):
    b=_rd(p,base,0x48)
    if not b: return {"base":hex(base),"bad":1}
    return {"base":hex(base),
            "i32":list(struct.unpack("<18i",b)),
            "q64":[hex(v) for v in struct.unpack("<9Q",b)]}

def _stats(p,base,bpp,nch):
    """sample assuming bpp bytes/pixel, nch leading float channels, stride in PIXELS"""
    W=_i(p,base+0x08);H=_i(p,base+0x0c);st=_i(p,base+0x10) or W;data=_q(p,base+0x20)
    if not(16<W<40000 and 16<H<40000 and data>0x10000): return {"bad":1,"W":W,"H":H}
    # phase-resolved means (2x2 CFA phases)
    acc=[[0.0]*nch for _ in range(4)];cnt=[0]*4
    for y in range(4,H-4,max(2,(H//120)//2*2)):
        for x in range(4,W-4,max(2,(W//120)//2*2)):
            for dy in range(2):
                for dx in range(2):
                    r=_rd(p,data+((y+dy)*st+(x+dx))*bpp,4*nch)
                    if not r: continue
                    v=struct.unpack("<%df"%nch,r)
                    if not all(-1e6<z<1e6 for z in v): continue
                    ph=dy*2+dx
                    for c in range(nch): acc[ph][c]+=v[c]
                    cnt[ph]+=1
    out={"W":W,"H":H,"stride":st,"bpp":bpp,"nch":nch}
    for ph in range(4):
        out["ph%d"%ph]=([a/cnt[ph] for a in acc[ph]] if cnt[ph] else None)
        out["n%d"%ph]=cnt[ph]
    return out

def cap(dbg):
    p,fr=_fr(dbg)
    rbp=fr.FindRegister("rbp").GetValueAsUnsigned()
    r14=fr.FindRegister("r14").GetValueAsUnsigned()
    inb=_q(p,rbp-0xc8)
    outb=r14+0x70
    s=_st()["o"]
    s["in_hdr"]=_hdr(p,inb)
    s["out_hdr"]=_hdr(p,outb)
    s["in_bpp4_c1"]=_stats(p,inb,4,1)
    s["in_bpp8_c2"]=_stats(p,inb,8,2)
    s["in_bpp16_c4"]=_stats(p,inb,16,4)
    s["out_bpp16_c4"]=_stats(p,outb,16,4)
    # scan the frame for other descriptor-looking pointers
    cands=[]
    for off in range(-0x200,0x40,8):
        pv=_q(p,rbp+off)
        if pv<0x10000: continue
        W=_i(p,pv+0x08);H=_i(p,pv+0x0c);dp=_q(p,pv+0x20)
        if 16<W<40000 and 16<H<40000 and dp>0x10000:
            cands.append({"off":hex(off),"ptr":hex(pv),"W":W,"H":H,"stride":_i(p,pv+0x10),"data":hex(dp)})
    s["frame_desc_candidates"]=cands
    return True

def report(dbg):
    s=_st()
    with open(s["path"],"w") as f: json.dump(s["o"],f,indent=1)
    print("FMT_REPORT "+s["path"])
