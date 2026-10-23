"""Generate cases-boundaries.json: year change (2025-12-31..2026-01-02), July 2025 change, other frequencies on 2026-07-01 (BC),
and the NL cases for America/Goose_Bay (copied from cases-atlantic.json). Run once; the output is inputs/cases-boundaries.json."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
INPUTS=HERE.parent/'inputs'  # inputs/ of this repository
# basic personal amounts (CAD). 2026: T4127 122nd edition Table 8.2 (federal BPAF 16,452 as used in cases.json). 2025: T4127 122nd edition Table 8.23 (BC 12,932; ON 12,747); federal 2025 16,129 = TD1 2025 basic personal amount
AMOUNTS={2026:{'fed':'16452','ON':'12989','BC':'13216'},2025:{'fed':'16129','ON':'12747','BC':'12932'}}
PROV={'ON':'ONTARIO','BC':'BRITISH_COLUMBIA'}
def base(cid,province,date,freq,gross,periods,mode,td1f,td1p,group,pdf=False):
    return {'id':cid,'group':group,'province':province,'date_paid':date,'freq':freq,'periods':periods,'gross':gross,'pensionable_months':12,
      'pensionable_earnings_ytd':'0','cpp_ytd':'0','cpp2_ytd':'0','ei_ytd':'0','insurable_earnings_ytd':'0','employee_age':35,'single_employer':True,'payment_type':'ordinary_salary',
      'td1_mode':mode,'td1_federal':td1f,'td1_prov':td1p,'pdf':pdf}
cases=[]
# 1. year change
for pk in ('ON','BC'):
    for mode in ('pre','man'):
        for d,s in (('2025-12-31','1231'),('2026-01-01','0101'),('2026-01-02','0102')):
            y=int(d[:4]);a=AMOUNTS[y]
            cases.append(base(f'yr_{pk.lower()}_{mode}_{s}',PROV[pk],d,'MONTHLY_12PP','4000',12,'prefill' if mode=='pre' else 'manual',None if mode=='pre' else a['fed'],None if mode=='pre' else a[pk],'year2026',pdf=(pk=='ON' and mode=='pre' and s in('1231','0101'))))
# 2. July 2025 change (ON)
for mode in ('pre','man'):
    for d,s in (('2025-06-30','0630'),('2025-07-01','0701'),('2025-07-02','0702')):
        a=AMOUNTS[2025]
        cases.append(base(f'jul25_on_{mode}_{s}','ONTARIO',d,'MONTHLY_12PP','4000',12,'prefill' if mode=='pre' else 'manual',None if mode=='pre' else a['fed'],None if mode=='pre' else a['ON'],'july2025'))
# 3. frequencies, BC, 4000-equivalent (annual 48 000)
for code,per,g,tag in (('WEEKLY_52PP',52,'923.08','wk'),('BI_WEEKLY',26,'1846.15','bw'),('SEMI_MONTHLY',24,'2000','sm')):
    for d,s in (('2026-06-30','0630'),('2026-07-01','0701'),('2026-07-02','0702')):
        cases.append(base(f'{tag}_bc_{s}','BRITISH_COLUMBIA',d,code,g,per,'manual','16452','13216','freq2026'))
# 4. NL Goose_Bay (same inputs as nl / nldef in cases-atlantic.json)
for c in json.loads((INPUTS/'cases-atlantic.json').read_text()):
    if c['id'].startswith(('nl_','nldef_')):
        cases.append(base(c['id'],c['province'],c['date_paid'],'MONTHLY_12PP',c['gross'],12,'prefill_prov' if c.get('use_default_td1_prov') else 'manual',c['td1_federal'],None if c.get('use_default_td1_prov') else c['td1_prov'],'nl_goosebay'))
# PDF captures (Halifax BC monthly July 1 and neighbours are added by the driver through --pdf-cases); mark monthly BC cases
cases.append(base('bc_monthly_0630','BRITISH_COLUMBIA','2026-06-30','MONTHLY_12PP','4000',12,'manual','16452','13216','pdf2026',pdf=True))
cases.append(base('bc_monthly_0701','BRITISH_COLUMBIA','2026-07-01','MONTHLY_12PP','4000',12,'manual','16452','13216','pdf2026',pdf=True))
cases.append(base('bc_monthly_0702','BRITISH_COLUMBIA','2026-07-02','MONTHLY_12PP','4000',12,'manual','16452','13216','pdf2026',pdf=True))
(INPUTS/'cases-boundaries.json').write_text(json.dumps(cases,indent=2)+'\n')
print(len(cases),'cases')
