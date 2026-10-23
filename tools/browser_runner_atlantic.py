"""Replay one synthetic case (Atlantic provinces) through the ordinary public PDOC salary UI in one browser time zone.
Derived from browser_runner.py (BC). Differences: province comes from the case; the provincial TD1 is either entered
or left as pre-filled by PDOC (use_default_td1_prov); the pre-filled values are saved as prefill.json before any entry.
No account, no tax filing, and no direct protected POST endpoint is used.
"""
import argparse,json,hashlib,re,sys
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent
INPUTS=HERE.parent/'inputs'  # inputs/ of this repository
FREQ={12:'MONTHLY_12PP',26:'BI_WEEKLY',27:'BI_WEEKLY_27PP',52:'WEEKLY_52PP',53:'WEEKLY_53PP'}
ENTRY='https://apps.cra-arc.gc.ca/ebci/rhpd/beta/entry/en'
def sha(b): return hashlib.sha256(b).hexdigest()
def write_json(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def read_xssi(txt): return json.loads(txt.split('\n',1)[1] if txt.startswith(")]}'") else txt)
def run(browser,case,tz,out):
    target=out/(case['id']+'--'+tz.replace('/','_'));target.mkdir(parents=True,exist_ok=True)
    context=browser.new_context(timezone_id=tz,locale='en-CA');page=context.new_page();page.set_default_timeout(45000)
    responses=[]
    resources=[]
    errors=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    page.on("response",lambda r:resources.append(r) if r.request.resource_type in ("document","script","stylesheet") else None)
    page.on('response',lambda r:responses.append(r) if '/rhpd/rest/api/' in r.url else None)
    try:
        page.goto(ENTRY,wait_until='domcontentloaded',timeout=60000)
        page.locator('label:has(input[value="SALARY"])').wait_for(timeout=60000)
        page.locator('label:has(input[value="SALARY"])').click();page.locator('button.next').click()
        page.locator('#datePaidYear').wait_for(timeout=60000)
        page.locator('select').nth(0).select_option(case['province']);page.locator('select').nth(1).select_option(FREQ[case['periods']])
        yy,mm,dd=case['date_paid'].split('-');page.locator('#datePaidYear').select_option(yy)
        page.locator('select').nth(3).select_option(mm);page.locator('select').nth(4).select_option(dd)
        page.locator('button.next').click();page.locator('input[name="salaryType"]').first.wait_for(state='attached')
        page.locator('input[type="text"]').nth(0).fill(case['gross']);page.locator('button.next').click()
        page.locator('input[name="cppQppType"]').first.wait_for(state='attached',timeout=60000)
        fields=page.locator('form input[type="text"]')
        page.wait_for_timeout(2000)  # let the client finish its own pre-fill before reading it
        prefill=[fields.nth(i).input_value() for i in range(fields.count())]
        write_json(target/'prefill.json',{'timezone':tz,'province':case['province'],'date_paid':case['date_paid'],'text_fields_before_entry':prefill})
        # Text field order is recorded in UI snapshots; use explicit values, never cached defaults (except use_default_td1_prov).
        values=[case['td1_federal'],'0',case['td1_prov'],str(case['pensionable_months']),case['pensionable_earnings_ytd'],case['cpp_ytd'],case['cpp2_ytd'],case['insurable_earnings_ytd'],case['ei_ytd'],'1.4']
        if fields.count()!=len(values):raise RuntimeError(f'Unexpected PDOC field count {fields.count()}')
        for i,v in enumerate(values):
            if i==2 and case.get('use_default_td1_prov'):continue
            fields.nth(i).fill('' if v=='0' and i not in (0,2,3,9) else v)
        shown_raw=fields.nth(2).input_value();shown=shown_raw.replace(',','')
        if not case.get('use_default_td1_prov') and float(shown)!=float(case['td1_prov']):raise RuntimeError(f'Provincial TD1 field shows {shown}, intended {case["td1_prov"]}')
        write_json(target/'ui-inputs.json',page.locator('form input,form select').evaluate_all('(es)=>es.map(e=>({name:e.name,id:e.id,type:e.type,value:e.value,checked:e.checked,valid:e.checkValidity()}))'))
        with page.expect_response(lambda r:r.url.endswith('/SALARY/calculate'),timeout=60000) as info:
            page.locator('form button.btn-primary').click()
        r=info.value;raw=r.text();reply=read_xssi(raw)
        page.get_by_role('button',name='Modify the Current Calculation',exact=True).wait_for(timeout=60000)
        body=page.locator('body').inner_text();html=page.content()
        (target/'result.html').write_text(html);(target/'result.txt').write_text(body)
        page.screenshot(path=str(target/'result.png'),full_page=True)
        request=json.loads(r.request.post_data)
        (target/'reply.raw.txt').write_text(raw);write_json(target/'request.json',request);write_json(target/'reply.json',reply)
        versions={}
        for response in responses:
            key=response.url.rsplit('/',1)[-1]
            if key in {'getappversion','getdeployidversion','getutmessageinternalversion'}:
                try: versions[key]={'status':response.status,'body':response.text()}
                except Exception:pass
        meta={'prefill_text_fields':prefill,'case_id':case['id'],'inputs':case,'browser_timezone':tz,'browser':browser.version,'accessed_utc':datetime.now(timezone.utc).isoformat(),'accessed_client_date':'2026-10-23','entry_url':ENTRY,'request_url':r.url,'status':r.status,'frontend_script_urls':page.locator('script[src]').evaluate_all('(es)=>es.map(e=>e.src)'),'screen_version':re.findall(r'Version:\s*([^\n]+)',body),'runtime_versions':versions,'request_sha256':sha((target/'request.json').read_bytes()),'reply_raw_sha256':sha(raw.encode()),'reply_json_sha256':sha((target/'reply.json').read_bytes()),'result_html_sha256':sha(html.encode())}
        resource_records=[]
        client=out/'client';client.mkdir(exist_ok=True)
        for resource in resources:
            try:
                payload=resource.body(); name=sha(resource.url.encode())[:16]+'.'+('js' if resource.request.resource_type=='script' else 'html' if resource.request.resource_type=='document' else 'css')
                (client/name).write_bytes(payload)
                resource_records.append({'url':resource.url,'status':resource.status,'type':resource.request.resource_type,'snapshot':str(Path('client')/name),'bytes':len(payload),'sha256':sha(payload)})
            except Exception as err:resource_records.append({'url':resource.url,'error':str(err)})
        meta['fresh_public_runtime']=True;meta['resource_records']=resource_records;meta['page_errors']=errors
        meta['observed_api_responses']=[{'url':x.url,'status':x.status,'method':x.request.method} for x in responses]
        meta['request_method']=r.request.method
        write_json(target/'metadata.json',meta)
        print(json.dumps({'case':case['id'],'province':case['province'],'tz':tz,'td1_prov_shown':shown_raw,'federal':reply.get('federalTaxDeduction'),'cpp':reply.get('cppOrQppDeductions'),'cpp2':reply.get('secondCppOrQppDeductions'),'ei':reply.get('employmentInsuranceDeductions'),'provincial':reply.get('provincialTaxDeduction'),'request_date':request.get('datePaid')}),flush=True)
        return {'case':case['id'],'timezone':tz,'ok':True,'directory':str(target)}
    except Exception as exc:
        try:(target/'failure.html').write_text(page.content());(target/'failure.txt').write_text(page.locator('body').inner_text())
        except Exception:pass
        record={'case':case['id'],'timezone':tz,'ok':False,'error':str(exc)};write_json(target/'failure.json',record);print(json.dumps(record),flush=True);return record
    finally:context.close()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',required=True);parser.add_argument('--timezone',required=True);parser.add_argument('--cases-file',default='cases-atlantic.json');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--chrome',default='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome');args=parser.parse_args()
    cases=json.loads((INPUTS/args.cases_file).read_text());case=[c for c in cases if c['id']==args.case][0]
    args.output.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=args.chrome,headless=True)
        try:result=run(browser,case,args.timezone,args.output)
        finally:browser.close()
    return 0 if result['ok'] else 1
if __name__=='__main__':sys.exit(main())
