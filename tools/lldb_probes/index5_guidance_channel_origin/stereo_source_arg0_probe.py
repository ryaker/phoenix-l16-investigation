# Dump arg0 Image<vec4x8ui> (real stereo source/guidance) of CreateStereoImage
# at each call's RETURN (buffer filled). Entry bp set in .lldb; every hit is entry.
import builtins, json, struct
_OUT={"prefix":None,"max":8}
def reset(prefix,max_planes=8):
    _OUT["prefix"]=prefix; _OUT["max"]=int(max_planes)
    builtins.l16_ssrc={"planes":[],"errors":[],"pending":{}}
def _st():
    if not hasattr(builtins,"l16_ssrc"): reset(_OUT["prefix"] or "/tmp/ss")
    return builtins.l16_ssrc
def _u(frame,n): return frame.FindRegister(n).GetValueAsUnsigned()
def _read(process,addr,size):
    import lldb
    if not addr or size<=0: return None
    e=lldb.SBError(); d=process.ReadMemory(addr,size,e)
    return d if e.Success() and len(d)==size else None
def _dump(process,desc_addr,key):
    st=_st()
    hdr=_read(process,desc_addr,0x30)
    if hdr is None: st["errors"].append("no hdr"); return
    w=struct.unpack("<8iQQ",hdr)
    width,height,stride,data=w[2],w[3],w[6],w[8]
    if not (0<width<=8192 and 0<height<=8192 and data):
        st["errors"].append(f"bad {width}x{height} st{stride}"); return
    nbytes=height*stride*4
    buf=_read(process,data,nbytes)
    if buf is None: st["errors"].append(f"readfail {nbytes}"); return
    idx=len(st["planes"]); fn=f"{_OUT['prefix']}_call{idx}_k{key}.rgba8"
    open(fn,"wb").write(buf)
    st["planes"].append({"call":idx,"camera_key":key,"width":width,"height":height,"stride":stride,"bytes":nbytes,"file":fn})
def hit(frame,bp_loc,internal_dict):
    st=_st()
    if len(st["planes"])>=_OUT["max"]: return False
    process=frame.GetThread().GetProcess(); target=process.GetTarget()
    desc=_u(frame,"rdi"); key=_u(frame,"rsi")&0xFFFFFFFF
    sp=_u(frame,"rsp"); raw=_read(process,sp,8)
    if raw is None: st["errors"].append("no ret"); return False
    ret=struct.unpack("<Q",raw)[0]
    rb=target.BreakpointCreateByAddress(ret); rb.SetOneShot(True)
    st["pending"][rb.GetID()]=(desc,key)
    rb.SetScriptCallbackFunction("stereo_source_arg0_probe.ret_hit")
    return False
def ret_hit(frame,bp_loc,internal_dict):
    st=_st(); process=frame.GetThread().GetProcess()
    bid=bp_loc.GetBreakpoint().GetID()
    if bid in st["pending"]:
        desc,key=st["pending"].pop(bid); _dump(process,desc,key)
    return False
def attach(debugger):
    t=debugger.GetSelectedTarget()
    for i in range(t.GetNumBreakpoints()):
        bp=t.GetBreakpointAtIndex(i)
        if bp and bp.IsValid() and bp.GetNumLocations()>=1:
            bp.SetScriptCallbackFunction("stereo_source_arg0_probe.hit")
    print("STEREO_SRC_ATTACHED", t.GetNumBreakpoints())
def write_report(debugger,path):
    st=_st(); json.dump(st,open(path,"w"),indent=1)
    print("STEREO_SRC_REPORT",path,len(st["planes"]),st["errors"][:3])
