import os,socket,time
from concurrent.futures import ThreadPoolExecutor
OUT=open('ulres2.txt','a',buffering=1)
def P(*a):
    s=' '.join(str(x) for x in a); print('ULP '+s,flush=True); OUT.write(s+'\n')
HOSTS=[]
for line in os.environ['HOSTS'].strip().splitlines():
    p=line.split()
    if len(p)>=2: HOSTS.append((p[0],p[1]))
PORTS=[22,80,443,3389,8080,8888,9400,10250,2375,6443,9000]
P('EGRESS', os.popen('curl -s -m 10 https://ipinfo.io/ip').read().strip())
def chk(t):
    name,ip,port=t
    s=socket.socket(); s.settimeout(4)
    try:
        s.connect((ip,port))
        try:
            s.settimeout(3); b=s.recv(120)
        except Exception: b=b''
        s.close()
        return (name,ip,port,'OPEN',repr(b[:100]))
    except Exception as e:
        return (name,ip,port,'closed',type(e).__name__)
tasks=[(n,i,p) for n,i in HOSTS for p in PORTS]
with ThreadPoolExecutor(max_workers=48) as ex:
    for r in ex.map(chk,tasks):
        if r[3]=='OPEN': P('PORT',*r)
P('SCAN DONE', len(tasks))
time.sleep(5)
