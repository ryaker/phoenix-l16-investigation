import numpy as np, os
D="/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/index5_guidance_pyramid/unit1_28mm"
def load(idx,w,h):
    a=np.fromfile(os.path.join(D,"guidance_level%d_%dx%d.rgba8"%(idx,w,h)),dtype=np.uint8)
    return a.reshape(h,w,4).astype(np.int32)
dims=[(65,49),(130,98),(260,195),(520,390),(1040,780),(2080,1560)]
lv=[load(i,w,h) for i,(w,h) in enumerate(dims)]

def reduce_box(src,tw,th):
    sh,sw=src.shape[:2]; out=np.zeros((th,tw,4),np.int32)
    for y in range(th):
        y0=(y*sh)//th; y1=max(y0+1,((y+1)*sh)//th)
        for x in range(tw):
            x0=(x*sw)//tw; x1=max(x0+1,((x+1)*sw)//tw)
            out[y,x]=src[y0:y1,x0:x1].reshape(-1,4).mean(0)
    return out
def reduce_box2(src,tw,th):
    # simple 2x2 average (pairs), clamp
    out=np.zeros((th,tw,4),np.int32)
    for y in range(th):
        for x in range(tw):
            ys=slice(2*y,2*y+2); xs=slice(2*x,2*x+2)
            out[y,x]=src[ys,xs].reshape(-1,4).mean(0)
    return out
def reduce_point(src,tw,th):
    sh,sw=src.shape[:2]
    ys=((np.arange(th)*sh)//th); xs=((np.arange(tw)*sw)//tw)
    return src[np.ix_(ys,xs)]
def reduce_pavg(src,tw,th):
    # pavgb-style 2x2: (a+b+1)>>1 pairwise
    out=np.zeros((th,tw,4),np.int32)
    for y in range(th):
        for x in range(tw):
            a=src[2*y,2*x]; b=src[2*y,min(2*x+1,src.shape[1]-1)]
            c=src[min(2*y+1,src.shape[0]-1),2*x]; d=src[min(2*y+1,src.shape[0]-1),min(2*x+1,src.shape[1]-1)]
            top=(a+b+1)//2; bot=(c+d+1)//2; out[y,x]=(top+bot+1)//2
    return out

for i in range(5):
    src=lv[i+1]; tgt=lv[i]; th,tw=tgt.shape[:2]
    for name,fn in [("box_frac",reduce_box),("box_2x2",reduce_box2),("point",reduce_point),("pavgb",reduce_pavg)]:
        try:
            r=fn(src,tw,th)
            if r.shape!=tgt.shape: print("L%d->L%d %s SHAPE %s vs %s"%(i+1,i,name,r.shape,tgt.shape)); continue
            d=np.abs(r-tgt)
            print("L%d(%dx%d)->L%d %-9s MAE=%.3f max=%d exact=%.1f%%"%(i+1,src.shape[1],src.shape[0],i,name,d.mean(),d.max(),100*(d.sum(2)==0).mean()))
        except Exception as e:
            print("L%d %s ERR %s"%(i,name,e))
    print()
