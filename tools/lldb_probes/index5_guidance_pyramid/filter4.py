import numpy as np, os
D="/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/index5_guidance_pyramid/unit1_28mm"
dims=[(65,49),(130,98),(260,195),(520,390),(1040,780),(2080,1560)]
def load(i):
    w,h=dims[i]; return np.fromfile(os.path.join(D,"guidance_level%d_%dx%d.rgba8"%(i,w,h)),dtype=np.uint8).reshape(h,w,4).astype(np.float64)
L5=load(5); L4=load(4)
def blocks(src):
    sh,sw=src.shape[:2]; th,tw=sh//2,sw//2
    a=src[0:2*th:2,0:2*tw:2]; b=src[0:2*th:2,1:2*tw:2]; c=src[1:2*th:2,0:2*tw:2]; d=src[1:2*th:2,1:2*tw:2]
    return a,b,c,d
def stats(name,r):
    r=np.floor(r+0.5).astype(np.int64); t=L4[:r.shape[0],:r.shape[1]].astype(np.int64); d=np.abs(r-t)
    print("%-26s MAE=%.4f max=%d exact=%.2f%%"%(name,d.mean(),d.max(),100*(d.sum(2)==0).mean()))
a,b,c,d=blocks(L5)
# gamma decode/encode per channel
for g in [1.8,2.0,2.2,2.4,3.0]:
    def dec(x): return (x/255.0)**g
    def enc(x): return (x**(1.0/g))*255.0
    r=enc((dec(a)+dec(b)+dec(c)+dec(d))/4.0)
    stats("linear_gamma_%.1f"%g,r)
# sRGB decode
def srgb_dec(x):
    x=x/255.0; return np.where(x<=0.04045, x/12.92, ((x+0.055)/1.055)**2.4)
def srgb_enc(x):
    return np.where(x<=0.0031308, x*12.92, 1.055*(x**(1/2.4))-0.055)*255.0
r=srgb_enc((srgb_dec(a)+srgb_dec(b)+srgb_dec(c)+srgb_dec(d))/4.0); stats("srgb",r)
# squared (gamma 2 exact, common in fast paths) with round
def dec2(x): return (x)**2
def enc2(x): return np.sqrt(x)
r=enc2((dec2(a)+dec2(b)+dec2(c)+dec2(d))/4.0); stats("square_avg_sqrt",r)
# only luma channel (ch0) gamma, chroma linear
for g in [2.0,2.2]:
    out=np.zeros_like(a)
    out[...,0]=((( (a[...,0]/255.)**g+(b[...,0]/255.)**g+(c[...,0]/255.)**g+(d[...,0]/255.)**g)/4.)**(1/g))*255.
    for ch in [1,2,3]:
        out[...,ch]=(a[...,ch]+b[...,ch]+c[...,ch]+d[...,ch])/4.
    stats("luma_gamma_%.1f_chroma_lin"%g,out)
