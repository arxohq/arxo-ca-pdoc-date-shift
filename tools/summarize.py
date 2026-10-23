#!/usr/bin/env python3
"""Build the summary tables in data/ from the saved runs in runs/ (no network, no browser).

    python3 tools/summarize.py            # write data/all-runs.tsv and data/zone-differences.tsv
    python3 tools/summarize.py --check    # rebuild in memory and compare with the files in data/;
                                          # also check every amount in data/*/observations.tsv
                                          # against the saved CRA replies

Columns marked "(our reading)" are our interpretation, not fields of the CRA reply.
"""
import json
import re
import sys
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / 'runs'
DATA = ROOT / 'data'
SETS = ['live-20261023', 'live-20261023-atlantic', 'live-20261023-boundaries']
KEYS = [('federal_tax', 'federalTaxDeduction'), ('provincial_tax', 'provincialTaxDeduction'), ('cpp', 'cppOrQppDeductions'),
        ('ei', 'employmentInsuranceDeductions'), ('total_tax', 'totalTaxDeductions'), ('net', 'netAmount'), ('remit', 'remitAmount')]
COLUMNS = ['set', 'case_id', 'province', 'frequency', 'gross', 'td1_mode', 'timezone', 'screen_date', 'datePaid_sent',
           'datePaid_read_in_eastern_time (our reading)', 'td1_fed_prefilled', 'td1_prov_prefilled', 'td1_fed_sent', 'td1_prov_sent',
           'federal_tax', 'provincial_tax', 'cpp', 'ei', 'total_tax', 'net', 'remit', 'pdf_file_name_date', 'pdf_text_date', 'run']


def two(x):
    return '' if x is None else str(D(str(x)).quantize(D('.01')))


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def td1_mode(case):
    if 'td1_mode' in case:
        return case['td1_mode']
    return 'prefill_prov' if case.get('use_default_td1_prov') else 'manual'


def load():
    rows = []
    for s in SETS:
        for meta_path in sorted((RUNS / s).rglob('metadata.json')):
            d = meta_path.parent
            m = read(meta_path)
            req = read(d / 'request.json')
            rep = read(d / 'reply.json')
            case = m['inputs']
            prefill = m.get('prefill_text_fields')
            if prefill is None and (d / 'prefill.json').exists():
                prefill = read(d / 'prefill.json')['text_fields_before_entry']
            pdf_name = (m.get('pdf') or {}).get('suggested_filename')
            hit = re.search(r'Date paid-(\d{4}-\d{2}-\d{2})', pdf_name or '')
            pdf_text = None
            if (d / 'result-pdf.txt').exists():
                t = re.search(r'Date the employee is paid:\s*(\d{4}-\d{2}-\d{2})', (d / 'result-pdf.txt').read_text(encoding='utf-8'))
                pdf_text = t.group(1) if t else None
            r = {'set': s, 'case_id': m['case_id'], 'province': case['province'], 'frequency': case.get('freq', 'MONTHLY_12PP'),
                 'gross': two(case['gross']), 'td1_mode': td1_mode(case), 'timezone': m['browser_timezone'], 'screen_date': case['date_paid'],
                 'datePaid_sent': req['datePaid'],
                 'datePaid_read_in_eastern_time (our reading)': datetime.fromtimestamp(rep['attributes']['datePaid'] / 1000, ZoneInfo('America/Toronto')).strftime('%Y-%m-%d %H:%M %Z'),
                 'td1_fed_prefilled': prefill[0] if prefill else '', 'td1_prov_prefilled': prefill[2] if prefill else '',
                 'td1_fed_sent': two(req.get('td1ClaimAmountFed')), 'td1_prov_sent': two(req.get('td1ClaimAmountProv')),
                 'pdf_file_name_date': hit.group(1) if hit else '', 'pdf_text_date': pdf_text or '', 'run': d.relative_to(ROOT).as_posix()}
            for k, v in KEYS:
                r[k] = two(rep.get(v))
            rows.append(r)
    rows.sort(key=lambda r: (r['set'], r['province'], r['case_id'], r['screen_date'], r['timezone']))
    return rows


def differences(rows):
    """Input sets run in more than one time zone, and those whose result depends on the zone."""
    groups = {}
    for r in rows:
        key = (r['federal_tax'], r['provincial_tax'], r['cpp'], r['ei'], r['td1_fed_prefilled'], r['td1_prov_prefilled'])
        groups.setdefault((r['set'], r['case_id'], r['screen_date']), {}).setdefault(key, []).append(r['timezone'])
    multi = {k: v for k, v in groups.items() if sum(len(z) for z in v.values()) > 1}
    out = []
    for (s, cid, date), v in sorted(multi.items()):
        if len(v) == 1:
            continue
        r0 = next(r for r in rows if (r['set'], r['case_id'], r['screen_date']) == (s, cid, date))
        for key, zones in sorted(v.items(), key=lambda kv: sorted(kv[1])):
            out.append({'set': s, 'case_id': cid, 'province': r0['province'], 'frequency': r0['frequency'], 'gross': r0['gross'], 'td1_mode': r0['td1_mode'],
                        'screen_date': date, 'zones': ' '.join(sorted(zones)), 'federal_tax': key[0], 'provincial_tax': key[1], 'cpp': key[2], 'ei': key[3],
                        'td1_fed_prefilled': key[4], 'td1_prov_prefilled': key[5]})
    return out, len(multi), sum(len(v) > 1 for v in multi.values())


def tsv(rows, cols):
    return '\t'.join(cols) + '\n' + ''.join('\t'.join(str(r[c]) for c in cols) + '\n' for r in rows)


DIFF_COLUMNS = ['set', 'case_id', 'province', 'frequency', 'gross', 'td1_mode', 'screen_date', 'zones', 'federal_tax', 'provincial_tax', 'cpp', 'ei',
                'td1_fed_prefilled', 'td1_prov_prefilled']
# column of data/<set>/observations.tsv -> column of all-runs.tsv
OBS_MAP = {'datePaid_sent': 'datePaid_sent', 'federal_tax': 'federal_tax', 'federal': 'federal_tax', 'provincial_tax': 'provincial_tax',
           'provincial': 'provincial_tax', 'cpp': 'cpp', 'ei': 'ei', 'total_tax': 'total_tax', 'net': 'net',
           'td1_fed_prefilled': 'td1_fed_prefilled', 'td1_prov_prefilled': 'td1_prov_prefilled', 'pdf_date_in_filename': 'pdf_file_name_date'}
BC_CASE = {'2026-06-30': 'monthly_june', '2026-07-01': 'monthly_july', '2026-07-02': 'monthly_july2'}


def check_observations(rows):
    """Every amount of data/<set>/observations.tsv must equal the saved CRA reply of the same run."""
    index = {(r['set'], r['case_id'], r['timezone']): r for r in rows}
    problems, checked = [], 0
    for s in SETS:
        lines = (DATA / s / 'observations.tsv').read_text(encoding='utf-8').rstrip('\n').split('\n')
        head = lines[0].split('\t')
        for line in lines[1:]:
            row = dict(zip(head, line.split('\t')))
            cid = row.get('case_id') or BC_CASE[row['screen_date']]
            run = index.get((s, cid, row['timezone']))
            if run is None:
                problems.append(f'{s}: no saved run for {cid} {row["timezone"]}')
                continue
            for col, target in OBS_MAP.items():
                if col not in row:
                    continue
                a, b = row[col], run[target]
                if col == 'pdf_date_in_filename' and a == 'None':
                    a = ''
                same = a == b
                if not same and re.fullmatch(r'-?\d+(\.\d+)?', a or '') and re.fullmatch(r'-?\d+(\.\d+)?', b or ''):
                    same = D(a) == D(b)
                checked += 1
                if not same:
                    problems.append(f'{s} {cid} {row["timezone"]} {col}: table {a!r}, reply {b!r}')
    return checked, problems


def main():
    rows = load()
    diff, groups, disagree = differences(rows)
    built = {'all-runs.tsv': tsv(rows, COLUMNS), 'zone-differences.tsv': tsv(diff, DIFF_COLUMNS)}
    if '--check' not in sys.argv:
        for name, text in built.items():
            (DATA / name).write_text(text, encoding='utf-8')
        print(f'{len(rows)} runs; {groups} input sets run in more than one zone; {disagree} of them depend on the zone')
        return 0
    problems = []
    for name, text in built.items():
        if (DATA / name).read_text(encoding='utf-8') != text:
            problems.append(f'data/{name} differs from a rebuild from runs/')
    checked, p2 = check_observations(rows)
    problems += p2
    print(f'summarize --check: {len(rows)} runs; {groups} input sets in more than one zone, {disagree} depend on the zone; '
          f'{checked} values of data/*/observations.tsv compared with the saved replies; {len(problems)} problems')
    for p in problems[:20]:
        print('  ', p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
