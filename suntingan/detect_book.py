import numpy as np, subprocess, sys, json
W,H=480,272; FPS=4
p=subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-vf",f"fps={FPS},scale={W}:{H}","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
fr=np.frombuffer(p,np.uint8).reshape(-1,H,W,3).astype(int)
r,g,b=fr[...,0],fr[...,1],fr[...,2]
yel=(r>110)&(g>85)&(b<0.55*g)&((r-b)>60)&(abs(r-g)<70)
yel[:, :, :int(W*0.25)]=False; yel[:, :, int(W*0.85):]=False   # ignore coat rack/cabinet edges
out=[]
for i,m in enumerate(yel):
    n=int(m.sum()); ys,xs=np.nonzero(m)
    out.append({"t":i/FPS,"n":n,"cx":float(xs.mean()*1920/W) if n else None,"cy":float(ys.mean()*1088/H) if n else None})
json.dump(out,open(sys.argv[2],"w"))
for o in out[::4]:
    print(f"{o['t']:6.1f} {o['n']:4d} " + ("#"*min(60,o['n']//3)))
