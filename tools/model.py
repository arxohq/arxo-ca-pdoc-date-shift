"""Independent narrow approved T4127 Option1 withholding slice.
Only ordinary monthly BC salary4000, TD1fed16452/prov13216, PM12,
noYTD/other deductions. Cent rounding mode as used by PDOC; T4127ch4Step6 also allows0.05.
This is withholding, never annual tax liability.
"""
from decimal import Decimal as D,ROUND_HALF_UP,ROUND_DOWN

def cents(value):return value.quantize(D('.01'),rounding=ROUND_HALF_UP)
def calculate(case):
    assert case['province']=='BRITISH_COLUMBIA' and case['periods']==12
    assert D(case['gross'])==4000 and D(case['td1_bc'])==13216 and D(case['td1_federal'])==16452
    assert case['pensionable_months']==12
    assert all(D(case[k])==0 for k in ['cpp_ytd','cpp2_ytd','ei_ytd','pensionable_earnings_ytd','insurable_earnings_ytd'])
    p=D(12);gross=D(case['gross'])
    exemption=(D(3500)/p).quantize(D('.01'),rounding=ROUND_DOWN)
    cpp=cents((gross-exemption)*D('.0595'));ei=cents(gross*D('.0163'))
    f5=cpp*D('.0100')/D('.0595')
    cpp_base=cpp*D('.0495')/D('.0595')
    annual=p*(gross-f5)
    assert D(44952)<annual<D(50363) # both first BC bracket and S=0
    rate=D('.0614') if case['date_paid']>='2026-07-01' else D('.0506')
    taxbase=annual-D(case['td1_bc'])-p*cpp_base-p*ei
    provincial=cents(rate*taxbase/p)
    federal=cents(D('.14')*(annual-D(case['td1_federal'])-p*cpp_base-p*ei-D(1501))/p)
    alternative_annual=p*(gross-cents(f5))
    alternative_base=alternative_annual-D(case['td1_bc'])-p*cpp_base-p*ei
    return {'provincial_tax':str(provincial),'federal_tax':str(federal),'cpp':str(cpp),'cpp2':'0.00','ei':str(ei),'net':str(gross-provincial-federal-cpp-ei),'trace':{'periods':'12','basic_exemption':str(exemption),'F5_raw':str(f5),'F5_display':str(cents(f5)),'CPP_base_monthly_raw':str(cpp_base),'CPP_base_display':str(cents(cpp_base)),'A_raw':str(annual),'CPP_base_annual_raw':str(p*cpp_base),'EI_annual':str(p*ei),'BC_first_bracket_base_raw':str(taxbase),'BC_rate':str(rate),'BC_tax_reduction_S':'0','rounding_reference':'Full Decimal ratios retained for income-tax intermediates; final withholding rounded to0.01. CPP/EI first calculated and rounded separately.','sensitivity_F5_display_rounded_base_CPP_unrounded':{'A':str(alternative_annual),'base':str(alternative_base),'provincial_raw':str(rate*alternative_base/p),'provincial_rounded':str(cents(rate*alternative_base/p))}}}

if __name__=='__main__':
    import json
    from pathlib import Path
    print(json.dumps([{'id':c['id'],'expected':calculate(c)} for c in json.loads((Path(__file__).resolve().parent.parent/'inputs'/'cases.json').read_text())],indent=2))
