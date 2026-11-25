import os,ssl,socket,urllib.request,json
OUT=open('ulres5.txt','a',buffering=1)
def P(*a):
    s=' '.join(str(x) for x in a); print('ULX '+s,flush=True); OUT.write(s+'\n')
P('EGRESS',os.popen('curl -s -m 10 https://ipinfo.io/ip').read().strip())
def certinfo(ip,port=443,sni=None):
    ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    try:
        s=ctx.wrap_socket(socket.create_connection((ip,port),timeout=10),server_hostname=sni or ip)
        c=s.getpeercert(); s.close()
        return {'subj':c.get('subject'),'issuer':d if False else c.get('issuer'),'san':c.get('subjectAltName'),'notAfter':c.get('notAfter')}
    except Exception as e:
        return {'err':type(e).__name__+':'+str(e)[:80]}
TC=[('t1946107x54','20.125.42.21',443),('t1950791eus22','20.97.252.251',443),('t1946107x48','40.113.1.63',8080),('t1946107x184','70.153.87.133',22)]
for n,ip,port in TC:
    if port!=443: 
        P('SKIP-CERT',n,ip,port); continue
    for sni in [None]:
        ci=certinfo(ip,port,sni)
        P('CERT',n,ip,sni,json.dumps(ci)[:600])
        sans=[]
        for t,v in (ci.get('san') or []): 
            if t=='DNS': sans.append(v)
        P('SANS',n,sans)
        for host in sans[:6]:
            for path in ['/','/health','/api','/v1/models','/lab','/orca-api/api/v1/version','/openapi.json','/.well-known/openid-configuration']:
                for sch in ['https']:
                    u=f'{sch}://{ip}:{port}{path}'
                    try:
                        req=urllib.request.Request(u,headers={'Host':host,'User-Agent':'curl/8'})
                        ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
                        r=urllib.request.urlopen(req,timeout=8,context=ctx); b=r.read(500)
                        P('VHIT',n,host,path,r.status,len(b),repr(b[:250]))
                    except urllib.error.HTTPError as e:
                        b=e.read(200); P('VHTTP',n,host,path,e.code,repr(b[:150]))
                    except Exception: pass
# 8080 service deep probe
for path in ['/health','/ping','/ready','/live','/api/v1/health','/v1/chat/completions','/v1/models','/generate','/status/','/metrics']:
    try:
        r=urllib.request.urlopen(urllib.request.Request(f'http://40.113.1.63:8080{path}',headers={'User-Agent':'curl/8'}),timeout=8)
        b=r.read(400); P('H8080',path,r.status,len(b),repr(b[:200]))
    except urllib.error.HTTPError as e:
        P('H8080',path,e.code,repr(e.read(120)[:100]))
    except Exception: pass
P('DONE')
