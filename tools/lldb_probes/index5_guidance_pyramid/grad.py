import numpy as np, os
D="/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/index5_guidance_pyramid/unit1_28mm"
dims=[(65,49),(130,98),(260,195),(520,390),(1040,780),(2080,1560)]
def load(i):
    w,h=dims[i]; return np.fromfile(os.path.join(D,"guidance_level%d_%dx%d.rgba8"%(i,w,h)),dtype=np.uint8).reshape(h,w,4).astype(np.float64)
L5=load(5)
def box_to(full,tw,th):  # my areaResize: single fractional box
    sh,sw=full.shape[:2]; out=np.zeros((th,tw,4))
    ys=(np.arange(th+1)*sh/th).astype(int); xs=(np.arange(tw+1)*sw/tw).astype(int)
    for y in range(th):
        for x in range(tw):
            out[y,x]=full[ys[y]:max(ys[y]+1,ys[y+1]),xs[x]:max(xs[x]+1,xs[x+1])].reshape(-1,4).mean(0)
    return np.floor(out+0.5)
def gradmag(g):  # mean |Δ| to right+down neighbor, channel0 (luma), the SGM edge term
    c=g[...,0]
    dx=np.abs(np.diff(c,axis=1)); dy=np.abs(np.diff(c,axis=0))
    return dx.mean(), dy.mean(), np.percentile(dx,95), np.percentile(dy,95)
for i in [0,1,2]:
    w,h=dims[i]; lum=load(i); mine=box_to(L5,w,h)
    lg=gradmag(lum); mg=gradmag(mine)
    print("L%d Lumen |dx|=%.2f |dy|=%.2f p95dx=%.1f | MINE(box) |dx|=%.2f |dy|=%.2f p95dx=%.1f  ratio=%.2f"%(
        i, lg[0],lg[1],lg[2], mg[0],mg[1],mg[2], mg[0]/max(lg[0],1e-9)))
