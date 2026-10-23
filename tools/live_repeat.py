#!/usr/bin/env python3
"""Live repeat: six new calculations on the current public PDOC (network; needs Playwright and Chrome or Chromium).

    python3 -m venv .repro-venv
    .repro-venv/bin/python -m pip install -r tools/requirements.txt
    .repro-venv/bin/python -m playwright install chromium      # or set CHROME_PATH to an installed Chrome
    .repro-venv/bin/python tools/live_repeat.py

Cases: British Columbia 1 July 2026 (with the PDF), Ontario 1 January 2026 and Newfoundland and Labrador
1 July 2026, each in America/Halifax or America/St_Johns and in America/Toronto. The script only fills the
normal public form and presses its buttons. It sends no return and no filing. Output: new-runs/live-<UTC time>/.
If CRA has changed PDOC since 23 October 2026, the results may differ from the saved runs.
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CASES = [('bc_monthly_0701', 'America/Halifax', True), ('bc_monthly_0701', 'America/Toronto', True),
         ('yr_on_pre_0101', 'America/Halifax', False), ('yr_on_pre_0101', 'America/Toronto', False),
         ('nldef_july', 'America/St_Johns', False), ('nldef_july', 'America/Toronto', False)]


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def browser_path():
    custom = os.environ.get('CHROME_PATH')
    if custom:
        if not Path(custom).is_file():
            raise SystemExit('Browser not found: ' + custom)
        return custom
    for path in ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', shutil.which('google-chrome'),
                 shutil.which('chromium'), shutil.which('chromium-browser')]:
        if path and Path(path).is_file():
            return path
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        path = pw.chromium.executable_path
    if not Path(path).is_file():
        raise SystemExit('Install a browser: python -m playwright install chromium; or set CHROME_PATH')
    return path


def main():
    chrome = browser_path()
    out = ROOT / 'new-runs' / ('live-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    target = out / 'browser'
    target.mkdir(parents=True)
    rows = []
    for case, tz, pdf in CASES:
        cmd = [sys.executable, '-B', str(HERE / 'browser_runner_boundaries.py'), '--case', case, '--timezone', tz,
               '--output', str(target), '--chrome', chrome] + (['--pdf'] if pdf else [])
        print('+', ' '.join(cmd), flush=True)
        code = subprocess.run(cmd, timeout=600).returncode
        d = target / (case + '--' + tz.replace('/', '_'))
        row = {'case': case, 'timezone': tz, 'exit_code': code}
        if (d / 'reply.json').exists():
            rep, req, meta = read(d / 'reply.json'), read(d / 'request.json'), read(d / 'metadata.json')
            pre = read(d / 'prefill.json')['text_fields_before_entry']
            row.update(datePaid_sent=req['datePaid'], td1_prefilled=[pre[0], pre[2]], federal=rep.get('federalTaxDeduction'),
                       provincial=rep.get('provincialTaxDeduction'), ei=rep.get('employmentInsuranceDeductions'),
                       pdf_file_name=(meta.get('pdf') or {}).get('suggested_filename'))
        rows.append(row)
    pairs = []
    for case in dict.fromkeys(c for c, _, _ in CASES):
        rs = [r for r in rows if r['case'] == case and 'provincial' in r]
        if len(rs) == 2:
            keys = ('federal', 'provincial', 'ei', 'td1_prefilled')
            pairs.append({'case': case, 'zones': [r['timezone'] for r in rs], 'same_result_in_both_zones': all(rs[0][k] == rs[1][k] for k in keys)})
    (out / 'comparison.json').write_text(json.dumps({'mode': 'live', 'checked_utc': datetime.now(timezone.utc).isoformat(), 'browser': chrome,
                                                     'rows': rows, 'pairs': pairs}, ensure_ascii=False, indent=2) + '\n')
    for p in pairs:
        print(p['case'], p['zones'], 'same result' if p['same_result_in_both_zones'] else 'DIFFERENT results', flush=True)
    print('written', out.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
