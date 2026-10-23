"""Driver: one subprocess per (case, time zone); a run that hangs for more than 300 s is killed and restarted once.
Every event is appended to new-runs/live-boundaries/run-log.txt (a new folder; the saved runs/ are never touched). Usage: run_boundaries.py <python-with-playwright> [workers] [group ...]"""
import json,os,signal,subprocess,sys,time,shutil,threading
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'new-runs'/'live-boundaries'
CASES={c['id']:c for c in json.loads((HERE.parent/'inputs'/'cases-boundaries.json').read_text())}
ZONES5=['America/Halifax','America/St_Johns','UTC','America/Toronto','America/Vancouver']
PLAN={ # group -> (time zones, case-id filter)
 'year2026':(ZONES5,lambda c:c['group']=='year2026'),
 'july2025':(ZONES5,lambda c:c['group']=='july2025'),
 'freq2026':(['America/Halifax','America/Toronto'],lambda c:c['group']=='freq2026'),
 'nl_goosebay':(['America/Goose_Bay'],lambda c:c['group']=='nl_goosebay'),
 'pdf2026':(['America/Halifax','America/Toronto'],lambda c:c['group']=='pdf2026'),
}
PDF_JOBS={('yr_on_pre_1231','America/Halifax'),('yr_on_pre_1231','America/Toronto'),('yr_on_pre_0101','America/Halifax'),('yr_on_pre_0101','America/Toronto')}
LIMIT=300
lock=threading.Lock()
def log(msg):
    line=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+' '+msg
    with lock:
        print(line,flush=True)
        with open(OUT/'run-log.txt','a') as f:f.write(line+'\n')
def one(py,case,tz):
    zdir=OUT/tz.replace('/','_');target=zdir/(case+'--'+tz.replace('/','_'))
    pdf=CASES[case]['group']=='pdf2026' or (case,tz) in PDF_JOBS
    for attempt in (1,2):
        if target.exists():shutil.rmtree(target)
        cmd=[py,str(HERE/'browser_runner_boundaries.py'),'--case',case,'--timezone',tz,'--output',str(zdir)]+(['--pdf'] if pdf else [])
        t0=time.time();p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
        try:
            out,_=p.communicate(timeout=LIMIT)
            log(f'{tz} {case} attempt {attempt} exit {p.returncode} in {time.time()-t0:.0f}s: '+out.strip().replace('\n',' | ')[-700:])
            if p.returncode==0:return True
            if attempt==2:return False
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);out,_=p.communicate()
            log(f'{tz} {case} attempt {attempt} HUNG over {LIMIT}s, process group killed'+(', restarting once' if attempt==1 else ', giving up'))
            if attempt==2:return False
    return False
def main():
    py=sys.argv[1];workers=int(sys.argv[2]) if len(sys.argv)>2 else 3
    groups=sys.argv[3:] or list(PLAN)
    OUT.mkdir(exist_ok=True)
    jobs=[(c['id'],tz) for g in groups for tz,f in [(z,PLAN[g][1]) for z in PLAN[g][0]] for c in CASES.values() if f(c)]
    log(f'start: {len(jobs)} runs, {workers} workers, groups {groups}')
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(workers) as ex:res=list(ex.map(lambda j:one(py,*j),jobs))
    log(f'done: {sum(res)} ok, {len(res)-sum(res)} failed')
if __name__=='__main__':main()
