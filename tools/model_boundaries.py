"""Independent T4127 Option 1 withholding slice for ON and BC, ordinary salary (no bonus, no YTD, no other deductions),
tables transcribed from the T4127 122nd edition (Jan 1, 2026) -- Tables 8.1/8.2 (2026) and Tables 8.22/8.23 (2025, printed in that same edition) --
and the 123rd edition (Jul 1, 2026) Table 8.1.  Editions: 'y2025' (the 2025 tables of the 122nd edition; the federal lowest rate there is the
blended 14.5%), 'y2026jan' (122nd, 2026), 'y2026jul' (123rd).  The 120th (Jan 2025) and 121st (Jul 2025) editions are NOT on canada.ca
(index lists only the 122nd and 123rd), so no expectation is built for pay dates inside 2025 from them; 'y2025' is a reference only.
Withholding only, never annual tax liability."""
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_DOWN
def cents(x): return x.quantize(D('.01'), rounding=ROUND_HALF_UP)
FED={'y2026':{'A':[0,58523,117045,181440,258482],'R':['.14','.205','.26','.29','.33'],'K':[0,3804,10241,15685,26024],'CEA':1501},
     'y2025':{'A':[0,57375,114750,177882,253414],'R':['.145','.205','.26','.29','.33'],'K':[0,3443,9754,15090,25227],'CEA':1471}}
PROV={
 'y2026jan':{'BRITISH_COLUMBIA':{'A':[0,50363,100728,115648,140430,190405,265545],'V':['.0506','.0770','.1050','.1229','.1470','.1680','.2050'],'KP':[0,1330,4150,6220,9604,13603,23428]},
             'ONTARIO':{'A':[0,53891,107785,150000,220000],'V':['.0505','.0915','.1116','.1216','.1316'],'KP':[0,2210,4376,5876,8076]}},
 'y2026jul':{'BRITISH_COLUMBIA':{'A':[0,50363,100728,115648,140430,190405,265545],'V':['.0614','.0770','.1050','.1229','.1470','.1680','.2050'],'KP':[0,786,3606,5676,9061,13059,22884]},
             'ONTARIO':{'A':[0,53891,107785,150000,220000],'V':['.0505','.0915','.1116','.1216','.1316'],'KP':[0,2210,4376,5876,8076]}},
 'y2025':{'BRITISH_COLUMBIA':{'A':[0,49279,98560,113158,137407,186306,259829],'V':['.0506','.0770','.1050','.1229','.1470','.1680','.2050'],'KP':[0,1301,4061,6086,9398,13310,22924]},
          'ONTARIO':{'A':[0,52886,105775,150000,220000],'V':['.0505','.0915','.1116','.1216','.1316'],'KP':[0,2168,4294,5794,7994]}}}
OTHER={'y2026jan':{'cpp_base_max':D('3519.45'),'ei_rate':D('.0163'),'ei_max':D('1123.07'),'on_surtax':(5818,7446),'on_lcp':300,'bc_s':(25570,41722,575)},
       'y2026jul':{'cpp_base_max':D('3519.45'),'ei_rate':D('.0163'),'ei_max':D('1123.07'),'on_surtax':(5818,7446),'on_lcp':300,'bc_s':(25570,41722,575)},
       'y2025':{'cpp_base_max':D('3356.10'),'ei_rate':D('.0164'),'ei_max':D('1077.48'),'on_surtax':(5710,7307),'on_lcp':294,'bc_s':(None,None,562)}}
def bracket(table,A): return max(j for j,a in enumerate(table['A']) if A>a) if A>0 else 0
def edition_for(date_paid):
    return 'y2025' if date_paid<'2026-01-01' else 'y2026jul' if date_paid>='2026-07-01' else 'y2026jan'
def calculate(case,edition=None,td1_fed=None,td1_prov=None):
    """Expected amounts under one edition. td1_* default to the case's entered amounts (manual mode)."""
    edition=edition or edition_for(case['date_paid']);o=OTHER[edition];prov=case['province']
    P=D(case['periods']);g=D(case['gross']);assert case['pensionable_months']==12
    exemption=(D(3500)/P).quantize(D('.01'),rounding=ROUND_DOWN)
    cpp=cents((g-exemption)*D('.0595'));ei=cents(g*o['ei_rate'])
    f5=cpp*D('.0100')/D('.0595');cpp_base=cpp*D('.0495')/D('.0595')
    A=P*(g-f5);cppc=min(P*cpp_base,o['cpp_base_max']);eic=min(P*ei,o['ei_max'])
    fed=FED['y2025' if edition=='y2025' else 'y2026'];i=bracket(fed,A);R=D(fed['R'][i]);K=D(fed['K'][i]);low=D(fed['R'][0])
    tf=D(td1_fed if td1_fed is not None else case['td1_federal']);tp=D(td1_prov if td1_prov is not None else case['td1_prov'])
    K1=low*tf;K2=low*cppc+low*eic;K4=low*min(A,D(fed['CEA']))
    T3=max(R*A-K-K1-K2-K4,D(0));federal=cents(T3/P)
    t=PROV[edition][prov];j=bracket(t,A);V=D(t['V'][j]);KP=D(t['KP'][j]);lowp=D(t['V'][0])
    T4=max(V*A-KP-lowp*tp-(lowp*cppc+lowp*eic),D(0));V1=V2=S=D(0)
    if prov=='ONTARIO':
        a,b=o['on_surtax'];V1=D('.20')*(T4-a) if a<T4<=b else (D('.20')*(T4-a)+D('.36')*(T4-b) if T4>b else D(0))
        V2=(D(0) if A<=20000 else min(D(300),D('.06')*(A-20000)) if A<=36000 else min(D(450),D(300)+D('.06')*(A-36000)) if A<=48000 else min(D(600),D(450)+D('.25')*(A-48000)) if A<=72000 else min(D(750),D(600)+D('.25')*(A-72000)) if A<=200000 else min(D(900),D(750)+D('.25')*(A-200000)))
        S=max(min(T4+V1,2*D(o['on_lcp'])-(T4+V1)),D(0))
    if prov=='BRITISH_COLUMBIA':
        lo,hi,base=o['bc_s']
        if lo is not None: S=min(T4,D(base)) if A<=lo else (min(T4,D(base)-(A-lo)*D('.0356')) if A<=hi else D(0))
    T2=max(T4+V1+V2-S,D(0));provincial=cents(T2/P)
    return {'edition':edition,'federal_tax':str(federal),'provincial_tax':str(provincial),'cpp':str(cpp),'ei':str(ei),'total_tax':str(federal+provincial),'net':str(g-federal-provincial-cpp-ei),
            'trace':{'A':str(A),'F5':str(f5),'fed_bracket':i,'R':str(R),'K':str(K),'T3':str(T3),'T4':str(T4),'V1':str(V1),'V2':str(V2),'S':str(S),'T2':str(T2),'td1_fed':str(tf),'td1_prov':str(tp)}}
if __name__=='__main__':
    import json
    from pathlib import Path
    for c in json.loads((Path(__file__).resolve().parent.parent/'inputs'/'cases-boundaries.json').read_text()):
        if c['td1_mode']=='manual' and c['province'] in('ONTARIO','BRITISH_COLUMBIA'):
            r=calculate(c);print(c['id'],c['date_paid'],r['edition'],'fed',r['federal_tax'],'prov',r['provincial_tax'],'cpp',r['cpp'],'ei',r['ei'])
