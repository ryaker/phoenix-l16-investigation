import numpy as np, os
D="/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/index5_guidance_pyramid/unit1_28mm"
def load(idx,w,h):
    return np.fromfile(os.path.join(D,"guidance_level%d_%dx%d.rgba8"%(idx,w,h)),dtype=np.uint8).reshape(h,w,4).astype(np.int32)
L5=load(5,2080,1560); L4=load(4,1040,780)
def cmp(name,r):
    d=np.abs(r.astype(np.int32)-L4); print("%-16s MAE=%.4f max=%d exact=%.1f%%"%(name,d.mean(),d.max(),100*(d.sum(2)==0).mean()))
# box trunc
a=L5[0::2,0::2]; b=L5[0::2,1::2]; c=L5[1::2,0::2]; d=L5[1::2,1::2]
cmp("box_trunc",(a+b+c+d)//4)
cmp("box_round",(a+b+c+d+2)//4)
# pavgb 2-stage: ((a+b+1)/2 + (c+d+1)/2 +1)/2
cmp("pavgb",(( (a+b+1)//2 + (c+d+1)//2 +1)//2))
# pavgb other pairing (vertical first)
cmp("pavgb_v",(( (a+c+1)//2 + (b+d+1)//2 +1)//2))
# separable [1,2,1]/4 on 3x3 centered then decimate (approx gaussian)
k=np.array([1,2,1]); 
def sep121(src):
    import numpy as np
    s=src.astype(np.float64)
    # horizontal
    h=(np.pad(s,((0,0),(1,1),(0,0)),mode="edge"))
    hh=h[:, :-2]+2*h[:,1:-1]+h[:,2:]
    v=np.pad(hh,((1,1),(0,0),(0,0)),mode="edge")
    vv=v[:-2]+2*v[1:-1]+v[2:]
    return (vv/16.0)
g=sep121(L5); cmp("gauss121_trunc",(g[0::2,0::2]).astype(np.int32))
cmp("gauss121_round",np.floor(g[0::2,0::2]+0.5).astype(np.int32))
# top-left point
cmp("point_tl",a)
# average of the 4 with numpy round-half-even
cmp("box_npround",np.rint((a+b+c+d)/4.0).astype(np.int32))
