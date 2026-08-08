import builtins, json, struct

def reset(path): builtins.SCN={"path":path,"hits":[]}
def _st(): return builtins.SCN
def _fr(dbg):
    t=dbg.GetSelectedTarget();p=t.GetProcess();th=p.GetSelectedThread();return p,th.GetSelectedFrame()
def _rd(p,a,n):
    import lldb
    e=lldb.SBError();r=p.ReadMemory(a,n,e);return r if(e.Success() and r and len(r)==n) else None
def _q(p,a):
    r=_rd(p,a,8);return struct.unpack("<Q",r)[0] if r else 0
def _i(p,a):
    r=_rd(p,a,4);return struct.unpack("<i",r)[0] if r else 0

def _try_img(p,base):
    # image descriptor guess: dims int32 at base+0x08,+0x0c ; stride +0x10 ; data +0x20
    W=_i(p,base+0x08);H=_i(p,base+0x0c);st=_i(p,base+0x10);data=_q(p,base+0x20)
    if not(0<W<20000 and 0<H<20000 and data>0x10000): return None
    # sample center pixel vec4
    r=_rd(p,data+((H//2)*(st or W)+(W//2))*16,16)
    px=struct.unpack("<4f",r) if r else None
    # mean of small central grid
    acc=[0,0,0,0];n=0
    for y in range(H//3,2*H//3,max(1,H//30)):
        for x in range(W//3,2*W//3,max(1,W//30)):
            rr=_rd(p,data+(y*(st or W)+x)*16,16)
            if rr:
                v=struct.unpack("<4f",rr)
                if all(-1e5<z<1e5 for z in v):
                    for c in range(4):acc[c]+=v[c]
                    n+=1
    mean=[a/n for a in acc] if n else None
    rg=mean[0]/mean[1] if(mean and mean[1]) else None
    bg=mean[2]/mean[1] if(mean and mean[1]) else None
    return {"base_off":hex(base),"W":W,"H":H,"stride":st,"data":hex(data),
            "center_px":px,"n":n,"R/G":rg,"B/G":bg}

def cap(dbg):
    p,fr=_fr(dbg)
    r14=fr.FindRegister("r14").GetValueAsUnsigned()
    found=[]
    # scan r14 header for embedded descriptors and pointers-to-descriptors
    for off in range(0,0x180,8):
        d=_try_img(p,r14+off)
        if d: found.append(("inline+%#x"%off,d))
        ptr=_q(p,r14+off)
        if ptr>0x10000:
            d2=_try_img(p,ptr)
            if d2: found.append(("deref+%#x"%off,d2))
    _st()["hits"].append({"r14":hex(r14),"found":found})
    return True

def report(dbg):
    s=_st()
    with open(s["path"],"w") as f: json.dump({"hits":s["hits"]},f,indent=2)
    print("SCAN_REPORT "+s["path"])
