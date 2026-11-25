import os,ssl,socket,urllib.request,json
OUT=open('ulres4.txt','a',buffering=1)
def P(*a):
    s=' '.join(str(x) for x in a); print('ULW '+s,flush=True); OUT.write(s+'\n')
P('EGRESS',os.popen('curl -s -m 10 https://ipinfo.io/ip').read().strip())
TARGETS=[('t1946107x48','40.113.1.63',8080,'http'),('t1950791eus22','20.97.252.251',443,'https'),('t1946107x54','20.125.42.21',443,'https')]
PATHS=['/','/api','/api/v1','/health','/healthz','/status','/metrics','/login','/api/status','/tree','/lab','/jupyter','/v1/models','/openapi.json','/docs','/actuator/env','/version','/favicon.ico','/system_stats','/queue']
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
for name,ip,port,sch in TARGETS:
    for p in PATHS:
        u=f'{sch}://{ip}:{port}{p}'
        try:
            req=urllib.request.Request(u,headers={'User-Agent':'curl/8'})
            r=urllib.request.urlopen(req,timeout=8,context=ctx) if sch=='https' else urllib.request.urlopen(req,timeout=8)
            b=r.read(700)
            P('HIT',name,ip,port,p,r.status,len(b),repr(b[:300]))
        except urllib.error.HTTPError as e:
            b=e.read(300)
            P('HTTP',name,ip,port,p,e.code,repr(b[:200]))
        except Exception as e:
            pass
P('DONE')
