import urllib.request,urllib.error,re,os,time,json,socket
OUT=open('ulres10.txt','a',buffering=1)
def P(*a):
    s=' '.join(str(x) for x in a); print('ULZ '+s,flush=True); OUT.write(s+'\n')
P('EGRESS',os.popen('curl -s -m 10 https://ipinfo.io/ip').read().strip())
def get(ip,port,path,host=None,t=6):
    u=f'http://{ip}:{port}{path}'
    h={'User-Agent':'Mozilla/5.0'}
    if host: h['Host']=host
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=t)
        return r.status,dict(r.headers),r.read(120000)
    except urllib.error.HTTPError as e:
        return e.code,dict(e.headers or {}),e.read(20000)
    except Exception as ex:
        return -1,{},str(ex).encode()[:120]
TG=[('70.153.87.133',80),('134.149.59.33',80),('40.113.1.63',8080),('20.97.252.251',80),('20.125.42.21',443)]
END=time.time()+int(os.environ.get('LOOPMIN','38'))*60
done=set(); rnd=0
while time.time()<END:
    rnd+=1
    for ip,port in TG:
        s,h,b=get(ip,port,'/',t=5)
        if s>0:
            P('OPEN',ip,port,s,len(b),h.get('Server',''),time.strftime('%H:%M:%SZ',time.gmtime()),'rnd',rnd)
            if (ip,port) in done: continue
            done.add((ip,port))
            for path in ['/brand','/jupyter','/metrics','/actuator/health','/actuator/env','/api/login','/api/v1/version','/system_stats','/openapi.json','/favicon.ico','/robots.txt']:
                s2,h2,b2=get(ip,port,path)
                P('P',ip,port,path,s2,len(b2),h2.get('Content-Type',''),repr(b2[:300]))
            s3,h3,b3=get(ip,port,'/brand')
            if s3==200:
                t3=b3.decode('utf-8','replace')
                P('BRANDTITLE',ip,re.findall(r'<title>(.*?)</title>',t3)[:1])
                js=sorted(set(re.findall(r'(?:src|href)="([^"]+\.(?:js|css))"',t3)))
                P('ASSETS',ip,js[:10])
                for a in js[:8]:
                    ap=a if a.startswith('/') else '/'+a.lstrip('/')
                    s4,h4,b4=get(ip,port,ap)
                    P('ASSET',ip,ap,s4,len(b4))
                    if len(b4)>100:
                        t4=b4.decode('utf-8','replace')
                        P('EPS',ip,ap,sorted(set(re.findall(r'["\'`](/[a-zA-Z0-9_\-/]{2,60})["\'`]',t4)))[:50])
                        P('TOK',ip,ap,re.findall(r'(?:token|apiKey|secret|Authorization)["\']?\s*[:=]\s*["\']([A-Za-z0-9._\-]{8,60})',t4)[:5])
            for host in ['t1946107x184','localhost']:
                s5,h5,b5=get(ip,port,'/',host=host)
                P('VH',ip,port,host,s5,len(b5),repr(b5[:120]))
    time.sleep(25)
P('DONE rnds',rnd,'opened',sorted(done))
