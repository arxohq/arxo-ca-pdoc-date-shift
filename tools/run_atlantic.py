"""Driver: one subprocess per (case, time zone); a run that hangs for more than 300 s is killed and restarted once.
Every event is appended to new-runs/live-atlantic/run-log.txt (a new folder; the saved runs/ are never touched). Usage: run_atlantic.py <python-with-playwright> [workers]"""
import json,os,signal,subprocess,sys,time,shutil,threading
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'new-runs'/'live-atlantic'
PLAN=[('America/Halifax',['ns','pei','peihigh']),('America/Moncton',['nb']),('America/St_Johns',['nl','nldef']),('America/Toronto',['ns','nb','pei','peihigh','nl','nldef'])]
SUFFIX=['june','july','july2']
LIMIT=300
lock=threading.Lock()
def log(msg):
    line=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+' '+msg
    with lock:
        print(line,flush=True)
        with open(OUT/'run-log.txt','a') as f:f.write(line+'\n')
def one(py,case,tz):
    zdir=OUT/tz.replace('/','_');target=zdir/(case+'--'+tz.replace('/','_'))
    for attempt in (1,2):
        if target.exists():shutil.rmtree(target)
        cmd=[py,str(HERE/'browser_runner_atlantic.py'),'--case',case,'--timezone',tz,'--output',str(zdir)]
        t0=time.time();p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
        try:
            out,_=p.communicate(timeout=LIMIT)
            log(f'{tz} {case} attempt {attempt} exit {p.returncode} in {time.time()-t0:.0f}s: '+out.strip().replace('\n',' | ')[-600:])
            if p.returncode==0:return True
            if attempt==2:return False
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);out,_=p.communicate()
            log(f'{tz} {case} attempt {attempt} HUNG over {LIMIT}s, process group killed'+(', restarting once' if attempt==1 else ', giving up'))
            if attempt==2:return False
    return False
def main():
    py=sys.argv[1];workers=int(sys.argv[2]) if len(sys.argv)>2 else 3
    OUT.mkdir(exist_ok=True)
    jobs=[(f'{prefix}_{s}',tz) for tz,prefixes in PLAN for prefix in prefixes for s in SUFFIX]
    log(f'start: {len(jobs)} runs, {workers} workers')
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(workers) as ex:res=list(ex.map(lambda j:one(py,*j),jobs))
    log(f'done: {sum(res)} ok, {len(res)-sum(res)} failed')
if __name__=='__main__':main()
