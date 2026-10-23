"""Independent T4127 Option 1 withholding slice for NS, NB, PE, NL.

Source tables: T4127 122nd edition (Jan 1, 2026) Table 8.1 / 8.2 and 123rd edition
(Jul 1, 2026) Table 8.1 / 8.2, transcribed below. Ordinary monthly salary, no bonus,
no YTD amounts, no other deductions, 12 pensionable months, single employer, CPP/EI as
in model.py. Provincial tax and federal tax are computed by the 122nd and by the 123rd
edition for every case, so the result does not depend on which date is on the screen.
Withholding only, never annual tax liability.
"""
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_DOWN

def cents(x): return x.quantize(D('.01'), rounding=ROUND_HALF_UP)

FED = {'A': [0, 58523, 117045, 181440, 258482], 'R': ['.14', '.205', '.26', '.29', '.33'], 'K': [0, 3804, 10241, 15685, 26024]}
# province tables: (A thresholds, V rates, KP constants)
PROV = {
 'NEW_BRUNSWICK': {'A': [0, 52333, 104666, 193861], 'V': ['.0940', '.1400', '.1600', '.1950'], 'KP': [0, 2407, 4501, 11286]},
 'NOVA_SCOTIA': {'A': [0, 30995, 61991, 97417, 157124], 'V': ['.0879', '.1495', '.1667', '.1750', '.2100'], 'KP': [0, 1909, 2976, 3784, 9283]},
 'NEWFOUNDLAND_AND_LABRADOR': {'A': [0, 44678, 89354, 159528, 223340, 285319, 570638, 1141275],
                               'V': ['.0870', '.1450', '.1580', '.1780', '.1980', '.2080', '.2130', '.2180'],
                               'KP': [0, 2591, 3753, 6943, 11410, 14263, 17117, 22823]},
}
# jan = 122nd edition, jul = 123rd edition
TABLES = {
 'jan': {**PROV, 'PRINCE_EDWARD_ISLAND': {'A': [0, 33928, 65820, 106890, 142520], 'V': ['.0950', '.1347', '.1660', '.1762', '.1900'], 'KP': [0, 1347, 3407, 4497, 6464]}},
 'jul': {**PROV, 'PRINCE_EDWARD_ISLAND': {'A': [0, 33928, 65820, 106890, 142520, 200000], 'V': ['.0950', '.1347', '.1660', '.1762', '.1900', '.2100'], 'KP': [0, 1347, 3407, 4497, 6464, 10464]}},
}
# Table 8.2 basic personal amounts by edition
BPA = {'jan': {'NEW_BRUNSWICK': 13664, 'NOVA_SCOTIA': 11932, 'NEWFOUNDLAND_AND_LABRADOR': 11188, 'PRINCE_EDWARD_ISLAND': 15000},
       'jul': {'NEW_BRUNSWICK': 13664, 'NOVA_SCOTIA': 11932, 'NEWFOUNDLAND_AND_LABRADOR': 15000, 'PRINCE_EDWARD_ISLAND': 15000}}
CPP_BASE_MAX = D('3519.45'); EI_MAX = D('1123.07')

def bracket(table, A):
    i = max(j for j, a in enumerate(table['A']) if A > a) if A > 0 else 0
    return i

def edition_for(date_paid): return 'jul' if date_paid >= '2026-07-01' else 'jan'

def calculate(case, edition=None):
    """Expected amounts for one case under one edition ('jan'|'jul'); default: edition of the screen date."""
    edition = edition or edition_for(case['date_paid'])
    prov = case['province']; assert case['periods'] == 12 and case['pensionable_months'] == 12
    assert all(D(case[k]) == 0 for k in ['cpp_ytd', 'cpp2_ytd', 'ei_ytd', 'pensionable_earnings_ytd', 'insurable_earnings_ytd'])
    P = D(12); gross = D(case['gross'])
    exemption = (D(3500) / P).quantize(D('.01'), rounding=ROUND_DOWN)
    cpp = cents((gross - exemption) * D('.0595')); ei = cents(gross * D('.0163'))
    f5 = cpp * D('.0100') / D('.0595')
    cpp_base = cpp * D('.0495') / D('.0595')
    A = P * (gross - f5)
    # credits for CPP base and EI, capped as in T4127 Step 5 / Step 3
    cpp_credit_base = min(P * cpp_base, CPP_BASE_MAX)
    ei_credit_base = min(P * ei, EI_MAX)
    # provincial
    t = TABLES[edition][prov]; i = bracket(t, A); V = D(t['V'][i]); KP = D(t['KP'][i]); low = D(t['V'][0])
    # use_default_td1_prov: the entry keeps the provincial TD1 pre-filled by PDOC; the edition's own basic personal amount applies (Table 8.2)
    tcp = D(BPA[edition][prov]) if case.get('use_default_td1_prov') else D(case['td1_prov'])
    K1P = low * tcp; K2P = low * cpp_credit_base + low * ei_credit_base
    T4 = V * A - KP - K1P - K2P
    T2 = max(T4, D(0))
    provincial = cents(T2 / P)
    # federal
    fi = max(j for j, a in enumerate(FED['A']) if A > a); R = D(FED['R'][fi]); K = D(FED['K'][fi])
    K1 = D('.14') * D(case['td1_federal']); K2 = D('.14') * cpp_credit_base + D('.14') * ei_credit_base
    K4 = D('.14') * min(A, D(1501))
    T3 = max(R * A - K - K1 - K2 - K4, D(0))
    federal = cents(T3 / P)
    net = gross - provincial - federal - cpp - ei
    return {'edition': edition, 'provincial_tax': str(provincial), 'federal_tax': str(federal), 'cpp': str(cpp), 'cpp2': '0.00', 'ei': str(ei),
            'total_tax': str(provincial + federal), 'net': str(net),
            'trace': {'A_raw': str(A), 'F5_raw': str(f5), 'bracket_index': i, 'V': str(V), 'KP': str(KP), 'K1P': str(K1P), 'K2P': str(K2P), 'T4': str(T4), 'TCP': str(tcp),
                      'cpp_credit_base_annual': str(cpp_credit_base), 'ei_credit_annual': str(ei_credit_base), 'fed_bracket_index': fi, 'R': str(R), 'K': str(K)}}

def both(case):
    return {'jan': calculate(case, 'jan'), 'jul': calculate(case, 'jul')}

if __name__ == '__main__':
    import json, sys
    from pathlib import Path
    cases = json.loads((Path(__file__).resolve().parent.parent / 'inputs' / 'cases-atlantic.json').read_text())
    for c in cases:
        b = both(c)
        print(c['id'], c['date_paid'], 'prov jan', b['jan']['provincial_tax'], 'jul', b['jul']['provincial_tax'], 'fed jan', b['jan']['federal_tax'], 'jul', b['jul']['federal_tax'])
