#!/usr/bin/env python3
"""Offline check of the saved PDOC runs (no network, no browser).

    python3 tools/check_saved.py                 # full check (same as: replay)
    python3 tools/check_saved.py verify          # without the request-pair and PDF comparison
    python3 tools/check_saved.py --output DIR    # also write DIR/comparison.json and DIR/saved-check.json

What it checks:
- SHA256SUMS: every file of the repository is listed and has the listed hash;
- hashes written at capture time (request, raw reply, reply, PDF), HTTP status, the date on the result screen;
- our independent T4127 Option 1 calculation for every 2026 date (tools/model*.py);
- that time zones disagree only on the first day of an edition, and only "east of Eastern" against "Eastern and west";
- every figure quoted in README.md against the saved CRA replies;
- replay: the saved requests differ between zones only in datePaid and the pre-filled TD1 amounts; the PDF dates;
- tools/summarize.py --check: data/*.tsv rebuild from runs/.
Columns marked "our reading" are our interpretation, not fields of the CRA reply.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CAP = ROOT / 'runs'
sys.path.insert(0, str(HERE))
import model as MBC  # noqa: E402
import model_atlantic as MA  # noqa: E402
import model_boundaries as MB  # noqa: E402
import summarize  # noqa: E402

SETS = ['live-20261023', 'live-20261023-atlantic', 'live-20261023-boundaries']
EDITION_DAYS = {'2025-07-01', '2026-01-01', '2026-07-01'}
EAST_OF_EASTERN = {'America/Halifax', 'America/St_Johns', 'America/Goose_Bay', 'America/Moncton', 'UTC', 'Europe/Moscow'}
EASTERN_AND_WEST = {'America/Toronto', 'America/Winnipeg', 'America/Regina', 'America/Edmonton', 'America/Vancouver'}
KEYS = [('federal_tax', 'federalTaxDeduction'), ('provincial_tax', 'provincialTaxDeduction'), ('cpp', 'cppOrQppDeductions'),
        ('ei', 'employmentInsuranceDeductions'), ('total_tax', 'totalTaxDeductions'), ('net', 'netAmount'), ('remit', 'remitAmount')]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def two(x):
    return str(D(str(x)).quantize(D('.01')))


def eastern(ms):
    return datetime.fromtimestamp(ms / 1000, ZoneInfo('America/Toronto')).strftime('%Y-%m-%d %H:%M %Z')


def expected(set_name, case, req):
    """Independent expectation for the screen date (None where not built)."""
    d = case['date_paid']
    if set_name == 'live-20261023':
        return MBC.calculate(case), 'model.py (T4127 122nd/123rd, BC)'
    if case['province'] == 'NEWFOUNDLAND_AND_LABRADOR' and 'td1_mode' in case:
        case = {**case, 'use_default_td1_prov': case['td1_mode'] == 'prefill_prov'}
    if set_name == 'live-20261023-atlantic' or case['province'] == 'NEWFOUNDLAND_AND_LABRADOR':
        return MA.calculate(case), 'model_atlantic.py (T4127 122nd/123rd)'
    if d < '2026-01-01':
        return None, 'no expectation for 2025 (T4127 120th/121st editions not available)'
    return MB.calculate(case, None, td1_fed=str(req['td1ClaimAmountFed']), td1_prov=str(req['td1ClaimAmountProv'])), 'model_boundaries.py, TD1 as sent'


def load_rows():
    rows, problems = [], []
    for set_name in SETS:
        for meta_path in sorted((CAP / set_name).rglob('metadata.json')):
            t = meta_path.parent
            if not (t / 'request.json').exists():
                continue
            m = json.loads(meta_path.read_text(encoding='utf-8'))
            for fname, key in (('request.json', 'request_sha256'), ('reply.raw.txt', 'reply_raw_sha256'), ('reply.json', 'reply_json_sha256'), ('result.html', 'result_html_sha256')):
                if key in m and (t / fname).exists() and sha(t / fname) != m[key]:
                    problems.append(f'hash mismatch {t.name}/{fname}')
            if (t / 'result.pdf').exists() and m.get('pdf', {}).get('sha256') and sha(t / 'result.pdf') != m['pdf']['sha256']:
                problems.append(f'hash mismatch {t.name}/result.pdf')
            if m.get('status') != 200:
                problems.append(f'HTTP status {m.get("status")} in {t.name}')
            case = m['inputs']
            screen = (t / 'result.txt').read_text(encoding='utf-8')
            if case['date_paid'] + ' (YYYY-MM-DD)' not in screen:
                problems.append(f'screen date missing in {t.name}')
            req = json.loads((t / 'request.json').read_text(encoding='utf-8'))
            rep = json.loads((t / 'reply.json').read_text(encoding='utf-8'))
            prefill = m.get('prefill_text_fields')
            if prefill is None and (t / 'prefill.json').exists():
                prefill = json.loads((t / 'prefill.json').read_text())['text_fields_before_entry']
            exp, note = expected(set_name, case, req)
            actual = {k: two(rep[v]) for k, v in KEYS if rep.get(v) is not None}
            pdf_name = (m.get('pdf') or {}).get('suggested_filename')
            pdf_text_date = None
            if (t / 'result-pdf.txt').exists():
                hit = re.search(r'Date the employee is paid:\s*(\d{4}-\d{2}-\d{2})', (t / 'result-pdf.txt').read_text())
                pdf_text_date = hit.group(1) if hit else None
            rows.append({'set': set_name, 'case_id': m['case_id'], 'province': case['province'], 'frequency': case.get('freq', 'MONTHLY_12PP'),
                         'timezone': m['browser_timezone'], 'screen_date': case['date_paid'], 'datePaid_sent': req['datePaid'],
                         'datePaid_read_in_eastern_time (our reading)': eastern(rep['attributes']['datePaid']),
                         'td1_prefilled': [prefill[0], prefill[2]] if prefill else None, 'td1_sent': [req.get('td1ClaimAmountFed'), req.get('td1ClaimAmountProv')],
                         'actual': actual, 'expected_for_screen_date': ({k: exp[k] for k in ('federal_tax', 'provincial_tax', 'cpp', 'ei')} if exp else None), 'expected_note': note,
                         'pdf_file_name': pdf_name, 'pdf_text_date': pdf_text_date, 'dir': t.relative_to(ROOT).as_posix(), 'request': req})
    return rows, problems


def mismatch(r):
    e = r['expected_for_screen_date']
    if not e:
        return None
    fields = ['federal_tax', 'provincial_tax', 'cpp', 'ei']
    diff = {f: (r['actual'][f], e[f]) for f in fields if r['actual'].get(f) != e[f]}
    return diff or None


def classify(r, diff):
    if r['province'] == 'NOVA_SCOTIA' and set(diff) == {'provincial_tax'} and D(diff['provincial_tax'][0]) - D(diff['provincial_tax'][1]) == D('0.01'):
        return 'Nova Scotia one cent above our calculation (all dates and zones; cause not established)'
    if r['province'] == 'PRINCE_EDWARD_ISLAND' and r['screen_date'] == '2026-06-30' and set(diff) == {'provincial_tax'} and D(diff['provincial_tax'][0]) - D(diff['provincial_tax'][1]) == D('0.34'):
        return 'PEI above 142,520 before July 1: 0.34 above the 122nd edition table (fits KP 6,460; not zone dependent)'
    if r['screen_date'] in EDITION_DAYS and r['timezone'] in EAST_OF_EASTERN:
        return 'previous day amounts on the first day of an edition (our reading)'
    return 'UNEXPLAINED'


def find(rows, set_name, case_id, tz):
    hit = [r for r in rows if r['set'] == set_name and r['case_id'] == case_id and r['timezone'] == tz]
    if len(hit) != 1:
        raise RuntimeError(f'{set_name} {case_id} {tz}: {len(hit)} rows')
    return hit[0]


# Figures quoted in README.md: (set, case, zone, field, value)
README_FIGURES = [
    ('live-20261023', 'monthly_july', 'America/Halifax', 'provincial_tax', '132.21'), ('live-20261023', 'monthly_july', 'America/Toronto', 'provincial_tax', '160.43'),
    ('live-20261023', 'monthly_july', 'America/Halifax', 'remit', '1040.52'), ('live-20261023', 'monthly_july', 'America/Toronto', 'remit', '1068.74'),
    ('live-20261023-boundaries', 'wk_bc_0701', 'America/Halifax', 'provincial_tax', '30.51'), ('live-20261023-boundaries', 'wk_bc_0701', 'America/Toronto', 'provincial_tax', '37.02'),
    ('live-20261023-boundaries', 'bw_bc_0701', 'America/Halifax', 'provincial_tax', '61.02'), ('live-20261023-boundaries', 'bw_bc_0701', 'America/Toronto', 'provincial_tax', '74.04'),
    ('live-20261023-boundaries', 'sm_bc_0701', 'America/Halifax', 'provincial_tax', '66.10'), ('live-20261023-boundaries', 'sm_bc_0701', 'America/Toronto', 'provincial_tax', '80.21'),
    ('live-20261023-boundaries', 'yr_on_pre_0101', 'America/Halifax', 'federal_tax', '314.59'), ('live-20261023-boundaries', 'yr_on_pre_0101', 'America/Halifax', 'provincial_tax', '171.40'),
    ('live-20261023-boundaries', 'yr_on_pre_0101', 'America/Halifax', 'ei', '65.60'), ('live-20261023-boundaries', 'yr_on_pre_0101', 'America/St_Johns', 'federal_tax', '314.59'),
    ('live-20261023-boundaries', 'yr_on_pre_0101', 'America/Toronto', 'federal_tax', '310.53'), ('live-20261023-boundaries', 'yr_on_pre_0101', 'America/Toronto', 'provincial_tax', '170.40'),
    ('live-20261023-boundaries', 'yr_on_pre_0101', 'America/Toronto', 'ei', '65.20'), ('live-20261023-boundaries', 'yr_on_pre_0101', 'America/Vancouver', 'federal_tax', '310.53'),
    ('live-20261023-boundaries', 'yr_on_man_0101', 'America/Halifax', 'federal_tax', '310.82'), ('live-20261023-boundaries', 'yr_on_man_0101', 'America/Halifax', 'provincial_tax', '170.38'),
    ('live-20261023-boundaries', 'yr_on_man_0101', 'America/Halifax', 'ei', '65.60'),
    ('live-20261023-boundaries', 'yr_bc_pre_0101', 'America/Halifax', 'provincial_tax', '133.39'), ('live-20261023-boundaries', 'yr_bc_pre_0101', 'America/Toronto', 'provincial_tax', '132.21'),
    ('live-20261023-boundaries', 'jul25_on_pre_0701', 'America/Halifax', 'federal_tax', '337.06'), ('live-20261023-boundaries', 'jul25_on_pre_0701', 'America/St_Johns', 'federal_tax', '337.06'),
    ('live-20261023-boundaries', 'jul25_on_pre_0701', 'UTC', 'federal_tax', '337.06'), ('live-20261023-boundaries', 'jul25_on_pre_0701', 'America/Toronto', 'federal_tax', '314.59'),
    ('live-20261023-boundaries', 'jul25_on_pre_0701', 'America/Vancouver', 'federal_tax', '314.59'),
    ('live-20261023-atlantic', 'nldef_july', 'America/St_Johns', 'provincial_tax', '255.95'), ('live-20261023-atlantic', 'nldef_july', 'America/Toronto', 'provincial_tax', '228.31'),
    ('live-20261023-boundaries', 'nldef_july', 'America/Goose_Bay', 'provincial_tax', '255.95'),
    ('live-20261023-atlantic', 'nl_july', 'America/St_Johns', 'provincial_tax', '228.31'), ('live-20261023-atlantic', 'nl_july', 'America/Toronto', 'provincial_tax', '228.31'),
    ('live-20261023-atlantic', 'peihigh_july', 'America/Halifax', 'provincial_tax', '3068.72'), ('live-20261023-atlantic', 'peihigh_july', 'America/Toronto', 'provincial_tax', '3131.11'),
    ('live-20261023-atlantic', 'peihigh_june', 'America/Halifax', 'provincial_tax', '3068.72'), ('live-20261023-atlantic', 'peihigh_june', 'America/Toronto', 'provincial_tax', '3068.72'),
]
README_FIGURES_PREFILL = [('live-20261023-boundaries', 'yr_on_pre_0101', 'America/Halifax', ['16,129.00', '12,747.00']),
                  ('live-20261023-boundaries', 'yr_on_pre_0101', 'America/Toronto', ['16,452.00', '12,989.00']),
                  ('live-20261023-boundaries', 'yr_bc_pre_0101', 'America/Halifax', ['16,129.00', '12,932.00']),
                  ('live-20261023-atlantic', 'nldef_july', 'America/St_Johns', ['16,452.00', '11,188.00']),
                  ('live-20261023-atlantic', 'nldef_july', 'America/Toronto', ['16,452.00', '15,000.00']),
                  ('live-20261023-boundaries', 'nldef_july', 'America/Goose_Bay', ['16,452.00', '11,188.00'])]
README_FIGURES_DATE_SENT = [('live-20261023', 'monthly_july', 'America/Halifax', '2026-07-01T03:00:00.000Z'), ('live-20261023', 'monthly_july', 'America/Toronto', '2026-07-01T04:00:00.000Z')]
README_FIGURES_PDF = [('bc_monthly_0630', 'America/Halifax', '2026-06-29'), ('bc_monthly_0630', 'America/Toronto', '2026-06-30'),
              ('bc_monthly_0701', 'America/Halifax', '2026-06-30'), ('bc_monthly_0701', 'America/Toronto', '2026-07-01'),
              ('bc_monthly_0702', 'America/Halifax', '2026-07-01'), ('bc_monthly_0702', 'America/Toronto', '2026-07-02'),
              ('yr_on_pre_1231', 'America/Halifax', '2025-12-30'), ('yr_on_pre_1231', 'America/Toronto', '2025-12-31'),
              ('yr_on_pre_0101', 'America/Halifax', '2025-12-31'), ('yr_on_pre_0101', 'America/Toronto', '2026-01-01')]


SKIP = {'SHA256SUMS', '.git', 'new-runs', 'check-output', '__pycache__', '.repro-venv', '.DS_Store'}


def sums():
    """Check SHA256SUMS against the files of the repository."""
    listed, problems = {}, []
    for line in (ROOT / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        listed[name] = digest
    for name, digest in listed.items():
        p = ROOT / name
        if not p.is_file():
            problems.append('SHA256SUMS: missing file ' + name)
        elif sha(p) != digest:
            problems.append('SHA256SUMS: hash differs for ' + name)
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT)
        if p.is_file() and not (set(rel.parts) & SKIP) and rel.as_posix() not in listed:
            problems.append('SHA256SUMS: file not listed ' + rel.as_posix())
    return len(listed), problems


def cross_zone(rows):
    groups = {}
    for r in rows:
        k = (r['actual']['federal_tax'], r['actual']['provincial_tax'], r['actual']['cpp'], r['actual']['ei'], json.dumps(r['td1_prefilled']))
        groups.setdefault((r['set'], r['case_id'], r['screen_date']), {}).setdefault(k, []).append(r['timezone'])
    out = []
    for (s, cid, d), v in sorted(groups.items()):
        zones = sorted(z for zs in v.values() for z in zs)
        if len(zones) < 2:
            continue
        out.append({'set': s, 'case_id': cid, 'screen_date': d, 'zones_agree': len(v) == 1,
                    'results': [{'federal_tax': k[0], 'provincial_tax': k[1], 'cpp': k[2], 'ei': k[3], 'td1_prefilled': json.loads(k[4]), 'zones': sorted(z)} for k, z in sorted(v.items())]})
    return out


def request_pairs(rows):
    by = {}
    for r in rows:
        by.setdefault((r['set'], r['case_id']), []).append(r)
    out = []
    for (s, cid), rs in sorted(by.items()):
        if len(rs) < 2:
            continue
        base = rs[0]['request']
        keys = set()
        for r in rs[1:]:
            for k in set(base) | set(r['request']):
                if base.get(k) != r['request'].get(k):
                    keys.add(k)
        out.append({'set': s, 'case_id': cid, 'zones': sorted(r['timezone'] for r in rs), 'request_fields_that_differ': sorted(keys)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', nargs='?', default='replay', choices=['verify', 'replay'])
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    listed, problems = sums()
    rows, p2 = load_rows()
    problems += p2
    if len(rows) != 183:
        problems.append(f'expected 183 saved runs, found {len(rows)}')
    explained = []
    for r in rows:
        diff = mismatch(r)
        if diff:
            c = classify(r, diff)
            explained.append({'set': r['set'], 'case_id': r['case_id'], 'timezone': r['timezone'], 'screen_date': r['screen_date'], 'differs (reply, our calculation)': diff, 'class (our reading)': c})
            if c == 'UNEXPLAINED':
                problems.append(f'unexplained difference {r["set"]} {r["case_id"]} {r["timezone"]}: {diff}')
    cz = cross_zone(rows)
    for g in cz:
        if g['zones_agree']:
            continue
        if g['screen_date'] not in EDITION_DAYS:
            problems.append(f'zones disagree outside an edition day: {g["case_id"]} {g["screen_date"]}')
        for res in g['results']:
            zs = set(res['zones'])
            if not (zs <= EAST_OF_EASTERN or zs <= EASTERN_AND_WEST):
                problems.append(f'mixed zone group {g["case_id"]}: {sorted(zs)}')
    readme = []
    for s, cid, tz, field, value in README_FIGURES:
        got = find(rows, s, cid, tz)['actual'].get(field)
        readme.append({'set': s, 'case_id': cid, 'timezone': tz, 'field': field, 'readme': value, 'saved_reply': got, 'ok': got == value})
    for s, cid, tz, value in README_FIGURES_PREFILL:
        got = find(rows, s, cid, tz)['td1_prefilled']
        readme.append({'set': s, 'case_id': cid, 'timezone': tz, 'field': 'td1_prefilled (federal, provincial)', 'readme': value, 'saved_reply': got, 'ok': got == value})
    for s, cid, tz, value in README_FIGURES_DATE_SENT:
        got = find(rows, s, cid, tz)['datePaid_sent']
        readme.append({'set': s, 'case_id': cid, 'timezone': tz, 'field': 'datePaid sent', 'readme': value, 'saved_reply': got, 'ok': got == value})
    pdf = []
    if a.mode == 'replay':
        for cid, tz, value in README_FIGURES_PDF:
            r = find(rows, 'live-20261023-boundaries', cid, tz)
            name_date = re.search(r'Date paid-(\d{4}-\d{2}-\d{2})', r['pdf_file_name'] or '')
            pdf.append({'case_id': cid, 'timezone': tz, 'screen_date': r['screen_date'], 'pdf_file_name': r['pdf_file_name'], 'pdf_text_date': r['pdf_text_date'],
                        'readme': value, 'ok': r['pdf_text_date'] == value and name_date is not None and name_date.group(1) == value})
        readme += [{'field': 'pdf date', **p} for p in pdf]
    pairs = request_pairs(rows) if a.mode == 'replay' else []
    for p in pairs:
        extra = set(p['request_fields_that_differ']) - {'datePaid', 'td1ClaimAmountFed', 'td1ClaimAmountProv'}
        if extra:
            problems.append(f'request fields other than the date and pre-filled TD1 differ in {p["case_id"]}: {sorted(extra)}')
    bad_readme = [x for x in readme if not x['ok']]
    if bad_readme:
        problems.append(f'{len(bad_readme)} README figures do not match the saved replies')
    if _summarize_check():
        problems.append('tools/summarize.py --check failed')
    for r in rows:
        r.pop('request')
    result = {'mode': a.mode, 'checked_utc': datetime.now(timezone.utc).isoformat(), 'network_requests': 0, 'status': 'FAIL' if problems else 'PASS',
              'saved_runs': len(rows), 'problems': problems,
              'cross_zone_groups': len(cz), 'cross_zone_groups_that_disagree': sum(not g['zones_agree'] for g in cz),
              'differences_from_our_calculation': explained, 'readme_figures': readme, 'request_pairs': pairs, 'cross_zone': cz,
              'note': 'Our calculation (tools/model.py, tools/model_atlantic.py, tools/model_boundaries.py) is an independent reading of T4127 Option 1; for 2025 dates no expectation is built. Fields marked "our reading" are not CRA fields.'}
    result['files_in_SHA256SUMS'] = listed
    if a.output:
        a.output.mkdir(parents=True, exist_ok=True)
        (a.output / 'comparison.json').write_text(json.dumps({**result, 'rows': rows}, ensure_ascii=False, indent=2) + '\n')
        (a.output / 'saved-check.json').write_text(json.dumps({k: result[k] for k in ('mode', 'status', 'saved_runs', 'problems', 'cross_zone_groups', 'cross_zone_groups_that_disagree', 'files_in_SHA256SUMS')}, indent=2) + '\n')
    print(f"{result['status']} ({a.mode}): {listed} files match SHA256SUMS; {len(rows)} saved runs; "
          f"{result['cross_zone_groups_that_disagree']} of {len(cz)} input sets run in more than one zone depend on the zone; "
          f"{sum(x['ok'] for x in readme)} of {len(readme)} README figures match the saved replies; "
          f"{len(explained)} differences from our T4127 calculation, all explained; {len(problems)} problems")
    for p in problems[:20]:
        print('  ', p)
    return 1 if problems else 0


def _summarize_check():
    saved = sys.argv
    try:
        sys.argv = ['summarize.py', '--check']
        return summarize.main()
    finally:
        sys.argv = saved


if __name__ == '__main__':
    sys.exit(main())
