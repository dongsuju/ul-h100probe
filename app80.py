import urllib.request,urllib.error,re,json,os
OUT=open('ulres9.txt','a',buffering=1)
def P(*a):
    s=' '.join(str(x) for x in a); print('ULA '+s,flush=True); OUT.write(s+'\n')
P('EGRESS',os.popen('curl -s -m 10 https://ipinfo.io/ip').read().strip())
def get(ip,path,host=None,body=None,ct=None,method=None,t=10):
    u=f'http://{ip}{path}'
    h={'User-Agent':'Mozilla/5.0'}
    if host: h['Host']=host
    if ct: h['Content-Type']=ct
    try:
        req=urllib.request.Request(u,headers=h,data=body,method=method or ('POST' if body is not None else 'GET'))
        r=urllib.request.urlopen(req,timeout=t)
        return r.status,dict(r.headers),r.read(200000)
    except urllib.error.HTTPError as e:
        return e.code,dict(e.headers or {}),e.read(20000)
    except Exception as ex:
        return -1,{},str(ex).encode()
HOSTS=[('70.153.87.133','t1946107x184'),('134.149.59.33','t1946107x')]
for ip,vm in HOSTS:
    for path in ['/brand','/index.html','/favicon.ico']:
        s,h,b=get(ip,path)
        P('GET',ip,path,s,len(b),h.get('Server',''),h.get('Content-Type',''))
        if path=='/brand' and s==200:
            txt=b.decode('utf-8','replace')
            js=set(re.findall(r'(?:src|href)="([^"]+\.(?:js|css))"',txt))
            P('ASSETS',ip,sorted(js)[:10])
            for a in list(js)[:6]:
                if not a.startswith('http'): a='/'+a.lstrip('/')
                s2,h2,b2=get(ip,a)
                P('ASSET',ip,a,s2,len(b2))
                if b2 and len(b2)>200:
                    t2=b2.decode('utf-8','replace')
                    eps=sorted(set(re.findall(r'["\'`](/[a-zA-Z0-9_\-/]{2,60})["\'`]',t2)))[:60]
                    P('EPS',ip,a,eps[:40])
                    keys=re.findall(r'(api[_-]?key|token|secret|Bearer\s+[A-Za-z0-9._\-]{10,})',t2,re.I)
                    P('KEYS',ip,list(set(keys))[:10])
    for path in ['/actuator','/actuator/health','/actuator/env','/actuator/info','/api/login','/login','/dex/token','/oauth2/token','/api','/api/','/api/v1','/api/v1/','/api/user','/api/auth/login','/service/','/lab','/files','/jupyter/api/status','/jupyter/lab','/jupyter/tree','/gateway/routes']:
        s,h,b=get(ip,path)
        P('P',ip,path,s,len(b),h.get('Content-Type',''),repr(b[:160]))
    for host in [vm,'localhost','t1946107x184','jupyter','lab']:
        s,h,b=get(ip,'/',host=host)
        P('VH',ip,host,s,len(b),repr(b[:100]))
    # POST probes on the JSON API envelope
    for path,body in [('/api/login',b'{"username":"t19","password":"A100h100!"}'),('/api/auth/login',b'{"username":"t19","password":"t19"}'),('/jupyter',b'{}')]:
        s,h,b=get(ip,path,body=body,ct='application/json')
        P('POST',ip,path,s,len(b),repr(b[:200]))
P('DONE')
