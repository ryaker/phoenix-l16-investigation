import numpy as np, os
D="/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/index5_guidance_pyramid/unit1_28mm"
dims=[(65,49),(130,98),(260,195),(520,390),(1040,780),(2080,1560)]
def load(i):
    w,h=dims[i]; return np.fromfile(os.path.join(D,"guidance_level%d_%dx%d.rgba8"%(i,w,h)),dtype=np.uint8).reshape(h,w,4).astype(np.float64)
lv=[load(i) for i in range(6)]
def stats(name,r,t):
    r=r.astype(np.int64); t=t.astype(np.int64); d=np.abs(r-t)
    print("%-22s MAE=%.4f max=%d exact=%.2f%%"%(name,d.mean(),d.max(),100*(d.sum(2)==0).mean()))

# Hypothesis A: each level = 2x2 reduce of PREVIOUS level, various roundings
def red2(src,tw,th,mode):
    sh,sw=src.shape[:2]
    # gather 2x2 (clamped) blocks
    y0=np.arange(th)*2; x0=np.arange(tw)*2
    y1=np.minimum(y0+1,sh-1); x1=np.minimum(x0+1,sw-1)
    a=src[np.ix_(y0,x0)]; b=src[np.ix_(y0,x1)]; c=src[np.ix_(y1,x0)]; d=src[np.ix_(y1,x1)]
    s=a+b+c+d
    if mode=="trunc": return (s/4.0).astype(np.int64)
    if mode=="round": return np.floor(s/4.0+0.5).astype(np.int64)
    if mode=="ceil": return np.ceil(s/4.0).astype(np.int64)
    if mode=="pavgb": return ((( (a+b+1)//2 + (c+d+1)//2 +1)//2)).astype(np.int64)
    if mode=="pavgb_rd0": # round-down pavgb (a+b)>>1
        return ((( (a+b)//2 + (c+d)//2 )//2)).astype(np.int64)
for i in range(5):
    src=lv[i+1]; t=lv[i]; th,tw=t.shape[:2]
    for m in ["trunc","round","ceil","pavgb","pavgb_rd0"]:
        r=red2(src,tw,th,m); 
        if r.shape==t.shape: stats("L%d->L%d cascade_%s"%(i+1,i,m),r,t)
    print()

# Hypothesis B: each level built from FULL-RES L5 directly (fractional area box)
def area_from_full(full,tw,th):
    sh,sw=full.shape[:2]
    out=np.zeros((th,tw,4))
    ys=(np.arange(th+1)*sh/th).astype(int); xs=(np.arange(tw+1)*sw/tw).astype(int)
    for y in range(th):
        for x in range(tw):
            blk=full[ys[y]:max(ys[y]+1,ys[y+1]), xs[x]:max(xs[x]+1,xs[x+1])].reshape(-1,4)
            out[y,x]=blk.mean(0)
    return out
for i in range(5):
    t=lv[i]; th,tw=t.shape[:2]
    r=np.floor(area_from_full(lv[5],tw,th)+0.5).astype(np.int64)
    stats("L5->L%d area_full_round"%i,r,t)
print()
