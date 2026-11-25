import os,ssl,socket,urllib.request,json
OUT=open('ulres8.txt','a',buffering=1)
def P(*a):
    s=' '.join(str(x) for x in a); print('ULY '+s,flush=True); OUT.write(s+'\n')
P('EGRESS',os.popen('curl -s -m 10 https://ipinfo.io/ip').read().strip())
TG=[('70.153.87.133',80),('134.149.59.33',80),('40.113.1.63',8080)]
PATHS=['/','/api','/api/v1','/health','/healthz','/status','/metrics','/login','/tree','/lab','/v1/models','/openapi.json','/docs','/actuator','/actuator/env','/version','/system_stats','/queue','/hostname','/whoami','/env','/debug','/metrics/','/admin','/console']
for ip,port in TG:
    for p in PATHS:
        u=f'http://{ip}:{port}{p}'
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'curl/8'}),timeout=8)
            b=r.read(600); P('HIT',ip,port,p,r.status,len(b),dict(r.headers).get('Server',''),repr(b[:250]))
        except urllib.error.HTTPError as e:
            try: b=e.read(200)
            except Exception: b=b''
            P('HTTP',ip,port,p,e.code,dict(e.headers or {}).get('Server',''),repr(b[:150]))
        except Exception as ex:
            P('ERR',ip,port,p,type(ex).__name__)
P('DONE')
