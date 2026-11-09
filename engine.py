"""Pure, offline supplier capability decision engine. All input data is synthetic.

Preserves the validated assessment and decision-gate calculations.
No external model calls can change gate decisions.
"""
from __future__ import annotations
import copy
import csv
import json
import re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data' if (ROOT/'data'/'cases_seed.json').is_file() else ROOT
CASES=json.loads((DATA/'cases_seed.json').read_text(encoding='utf-8'))
INTERVENTIONS=json.loads((DATA/'interventions.json').read_text(encoding='utf-8'))
CRITERIA=list(csv.DictReader((DATA/'criteria.csv').open(encoding='utf-8')))
SURVEY=json.loads((DATA/'official_questionnaire.json').read_text(encoding='utf-8'))
RESEARCH=json.loads((DATA/'benchmark_research.json').read_text(encoding='utf-8'))
MOCK=json.loads((DATA/'snowflake_mock.json').read_text(encoding='utf-8'))
STAGES = ['Identify trigger & prioritize','Diagnose capability gap','Identify & tailor solutions',
 'Assess feasibility','Agree & commit','Implement capability building','Verify & review','Close, hand over & learn']

def fnum(x,default=0):
    try:
        v=float(x)
        return v if abs(v)<1e15 and v==v else default
    except (ValueError,TypeError,OverflowError): return default

def is_yes(x):return str(x).strip().lower() in {'yes','true','1'} or x is True

def calc(case):
    f=case.get('finance',{})
    ps=[fnum(f.get(k)) for k in ('p_technical','p_on_time','p_sustain')]
    ps=[max(0,min(1,n)) for n in ps]
    p=ps[0]*ps[1]*ps[2]
    gain=max(0,fnum(f.get('gain')))
    costs={k:max(0,fnum(f.get(k))) for k in ('cost_experts','cost_travel','cost_testing','cost_tooling','cost_incentives')}
    total_cost=sum(costs.values())
    net=gain*p-total_cost
    p_low=fnum(f.get('p_low'),None)
    p_high=fnum(f.get('p_high'),None)
    # Optional manually entered scenario range, not a calibrated statistical confidence interval.
    if p_low is not None:p_low=max(0,min(1,p_low))
    if p_high is not None:p_high=max(0,min(1,p_high))
    range_net=[gain*p_low-total_cost,gain*p_high-total_cost] if p_low is not None and p_high is not None and p_low<=p_high else None
    # An illustrative supplier contribution balance, not NPV; explicit non-verified assumptions.
    s_econ={k:fnum(f.get(k)) for k in ('supplier_contribution','retained_savings','productivity_relief','other_customer_upside','supplier_capex','supplier_opex')}
    sup_value=sum(s_econ[k] for k in ('supplier_contribution','retained_savings','productivity_relief','other_customer_upside'))
    sup_cost=s_econ['supplier_capex']+s_econ['supplier_opex']
    supplier_balance=sup_value-sup_cost
    ok_tech=is_yes(f.get('tech_ok'))
    ok_time=is_yes(f.get('timing_ok'))
    gap_valid=bool(case.get('evidence_verified') and case.get('diagnosis_approved') and str(case.get('evidence','')).strip())
    selected=bool(case.get('selected')) and bool(case.get('solution_approved'))
    incentive=str(f.get('supplier_willing','')).lower() in ('yes','yes with conditions')
    reason=[]
    if not gap_valid:reason.append('Stage 2: independent evidence and assessor confirmation required')
    if not selected:reason.append('Stage 3: reviewed intervention shortlist required')
    if not ok_tech:reason.append('Gate 1: technical ability not confirmed')
    if not ok_time:reason.append('Gate 2: timing or resources unresolved')
    if net <= 0:reason.append('Gate 3: illustrative Siemens net value is not positive')
    if not incentive:reason.append('Gate 4: supplier willingness not confirmed')
    if supplier_balance < 0:reason.append('Gate 4: supplier illustrative cash balance is negative; revise incentives or assumptions')
    # approval is separate from model. Example case may show simulated approval but still gate rules apply.
    disposition=('READY FOR HUMAN REVIEW' if not reason else 'REVISE / GATHER EVIDENCE')
    recorded=str(f.get('sponsor_review','Pending'))
    human_go=recorded=='Approved in simulated scenario' and not reason
    return dict(probability=p,probability_factors=ps,scenario_low=p_low,scenario_high=p_high,scenario_net_range=range_net,gain_basis=f.get('gain_basis',''),gross_gain=gain,expected_gain=gain*p,costs=costs,total_cost=total_cost,net=net,supplier_value=sup_value,supplier_cost=sup_cost,supplier_balance=supplier_balance,gates=[
      {'name':'Technical','passed':ok_tech and gap_valid,'reason':'Process & evidence checked'},
      {'name':'Timing / resources','passed':ok_time,'reason':'Need date, engineering time and resources'},
      {'name':'Siemens economics','passed':net>0,'reason':'Illustrative value only; not an approved hurdle'},
      {'name':'Supplier willingness','passed':incentive and supplier_balance>=0,'reason':'CapEx, OpEx, incentives and commitment'}],
      blockers=reason,disposition=disposition,human_go=human_go,recorded_decision=recorded,
      caveat='Illustrative undiscounted model. Probabilities are scenario assumptions, not calibrated confidence intervals. Supplier benefit estimates may overlap; validate before use.')

def recommendations(case,limit=10):
    cset=set(case.get('criteria',[])); out=[]
    for r in INTERVENTIONS:
        match=sorted(cset.intersection(set(r['criteria'].split(';'))))
        if not match:continue
        # evidence-first: case suitability not equivalent to score
        score=len(match)*3 + (2 if r['evidence_status'].upper().startswith('KEEP') else 0)
        out.append({**r,'matched':match,'relevance_score':score})
    return sorted(out,key=lambda r:(-r['relevance_score'],r['id']))[:limit]

def specialist_analysis(case):
    result=[]
    for code,name in [('A','Future Business Readiness'),('B','Production-System Capability'),('C','Resilience & Continuity')]:
        matched=[c for c in case.get('criteria',[]) if c.startswith(code)]
        picks=[r for r in recommendations(case,limit=30) if code in r['domain'] and set(r['matched']).intersection(matched)][:4]
        result.append(dict(code=code,name=name,active=bool(matched),criteria=matched,interventions=picks,
            evidence_state='Validated by demo assessor' if case.get('evidence_verified') and case.get('diagnosis_approved') else 'Requires assessor validation',
            missing=[] if case.get('evidence_verified') else ['Supplier evidence has not been independently verified'],
            note='This agent proposes intervention leads only. Cross-domain choices and feasibility are decided by the coordinating workflow.'))
    return result

def stage_check(case,stage):
    c=calc(case)
    if stage==1:
        return (bool(str(case.get('trigger','')).strip() and str(case.get('objective','')).strip() and str(case.get('need_date','')).strip()),'Enter a business trigger, objective and need date')
    if stage==2:
        ok=bool(case.get('evidence_verified') and case.get('diagnosis_approved') and case.get('criteria') and str(case.get('evidence','')).strip())
        return ok,'Confirm assessment, criteria and cited evidence with an assessor'
    if stage==3:
        valid_ids={r['id'] for r in recommendations(case,50)}
        ok=bool(case.get('selected') and all(x in valid_ids for x in case.get('selected',[])) and case.get('solution_approved'))
        return ok,'Select supported intervention(s) and record a human shortlist review'
    if stage==4:
        return c['human_go'],'Four feasibility gates must pass and a simulated human GO must be recorded'
    if stage==5:
        k=case.get('commitments',{})
        ok=bool(k.get('siemens_owner') and k.get('supplier_owner') and k.get('milestone') and k.get('siemens_approved') and k.get('supplier_approved'))
        return ok,'Named owners, scope/milestone, and both parties’ simulated approvals required'
    if stage==6:
        a=case.get('actions',[])
        return bool(a and all(x.get('status')=='Done' and x.get('evidence') for x in a)),'Every implementation action must be complete with evidence'
    if stage==7:
        v=case.get('verification',{});
        try:meets=fnum(v.get('actual'),-1)>=fnum(v.get('target'),1e9)
        except Exception:meets=False
        return bool(meets and v.get('verifier') and v.get('evidence') and v.get('sustained')),'Actual result at target plus independent evidence, verifier and sustainment'
    if stage==8:
        k=case.get('closure',{})
        return bool(k.get('owner') and k.get('followup') and k.get('lessons') and k.get('approved_by')),'Handover, follow-up trigger, lessons and human closure decision required'
    return False,'Unknown stage'

def stage_status(case):
    completed=int(case.get('completed_stage',0))
    out=[]
    for i,name in enumerate(STAGES,1):
        passed,reason=stage_check(case,i)
        out.append(dict(stage=i,name=name,completed=i<=completed,pass_check=passed,missing=reason if not passed else '',current=i==min(completed+1,8)))
    return out

def search_research(q,domain=None,limit=20):
    q=q.strip(); tokens=[t for t in re.findall(r'[a-z0-9-]{3,}',q.lower()) if t not in {'the','and','for','with','from','case','supplier'}]
    if not tokens:return []
    results=[]
    for doc in RESEARCH:
        for tab in doc.get('tabs',[]):
            if domain and doc['sector']!=domain:continue
            title=tab.get('title','')
            for para in tab.get('paragraphs',[]):
                txt=para.get('text','').strip()
                if len(txt)<32:continue
                lower=(txt+' '+title).lower(); score=sum(min(lower.count(t),4) for t in tokens)
                if not score:continue
                results.append(dict(title=doc['title'],sector=doc['sector'],section=title,quote=txt[:650],index=para.get('index'),url=doc.get('url'),score=score))
    return sorted(results,key=lambda x:-x['score'])[:limit]

def bounded_copilot(case,question):
    """Grounded local answers, not pretend LLM. Optional LLM only with explicit opt-in."""
    q=question.lower(); c=calc(case); picks=recommendations(case,10)
    cites=[{'label':r['name'],'source':r['reference'],'status':r['evidence_status']} for r in picks[:4]]
    if any(k in q for k in ('capex','award','commit','invest','incentiv','supplier side','willing')):
        ans=(f"The supplier’s illustrative balance is {c['supplier_balance']:,.0f} {case['finance'].get('currency','EUR')} before discounting and potential overlapping benefits. "
             f"Recorded willingness: {case['finance'].get('supplier_willing','Unknown')}. Recorded mechanism: {case['finance'].get('mechanism','none')}. "
             "Explore reduced productivity asks, Siemens technical support, other-customer capacity use, and carefully qualified pre-award mechanisms. A forecast is not a purchase award. No contract is approved by the tool.")
    elif any(k in q for k in ('why','recommend','intervention','solution','step 3','benchmark')):
        names=', '.join(r['name'] for r in picks[:4]) or 'None yet'
        ans=f"For {case['name']}, the recorded capability criteria are {', '.join(case.get('criteria',[])) or 'not entered'}. Relevant researched intervention leads: {names}. They are candidates, not Siemens-approved solutions. Compare each method with the actual constraint, review evidence limits, and get the assessor to validate the shortlist."
        if not case.get('evidence_verified'):ans+=' The supplier evidence has not been verified; do not treat these as an approved recommendation.'
    elif any(k in q for k in ('cost','gain','value','business','risk','probab','gate','feasib','step 4','return')):
        ans=(f"The illustrative Siemens expected value is {c['net']:,.0f} {case['finance'].get('currency','EUR')}: gross potential benefit {c['gross_gain']:,.0f} × model success probability {c['probability']:.1%} − intervention cost {c['total_cost']:,.0f}. "
             f"Current gate status: {c['disposition']}. "+('Blockers: '+'; '.join(c['blockers'])+'. ' if c['blockers'] else '')+
             "The individual probabilities are assumptions, not validated statistical predictions. Finance and Siemens stakeholders must approve the conclusion.")
    elif any(k in q for k in ('evidence','diagnos','stage','next','now')):
        n=min(case.get('completed_stage',0)+1,8); ok,why=stage_check(case,n)
        ans=f"The next workflow stage is {n}: {STAGES[n-1]}. It is {'ready to record after human attestation' if ok else 'blocked'}: {why}. The eight-stage workflow is guided by explicit gates. The copilot cannot bypass those gates."
    else:
        ans=(f"I can explain the documented situation for {case['name']}, suggest source-traceable intervention leads, review evidence gaps, and calculate the illustrative two-sided business case. "
             "Ask: ‘Which interventions fit?’, ‘Is the business case positive?’, ‘Why would the supplier invest before award?’, or ‘What blocks the next stage?’")
    return dict(answer=ans,mode='Grounded local rule-based assistant (not an LLM)',citations=cites,case_id=case['id'])

def snowflake_case(cid):
    result=next((s for s in MOCK['suppliers'] if s['supplier_id']==cid),None)
    if not result:return None
    return dict(mode='Mock Snowflake — SYNTHETIC ONLY',sources=MOCK['sources'],record=result)


def new_cases():
    """Each visitor gets an independent in-memory copy; no shared storage."""
    return {c['id']:copy.deepcopy(c) for c in CASES}


def revise_case(case:dict, changes:dict):
    """Apply changes to this session only; invalidate prior stage conclusions.

    Mirrors the original engine's material-change invalidation semantics.
    """
    import json
    from copy import deepcopy
    before=deepcopy(case)
    old_stage=int(case.get('completed_stage',0))
    for k,v in changes.items():
        if k in ('finance','commitments','verification','closure','survey','domain_notes') and isinstance(v,dict):
            case.setdefault(k,{})
            case[k].update(v)
        else:
            case[k]=v
    if before==case:
        return False
    # Changes to records require fresh human checks.
    if any(k in changes for k in ('criteria','evidence','gap','data_snapshot','survey')):
        if ('criteria' in changes and before.get('criteria')!=case.get('criteria')) or ('evidence' in changes and before.get('evidence')!=case.get('evidence')) or ('data_snapshot' in changes and before.get('data_snapshot')!=case.get('data_snapshot')):
            case['diagnosis_approved']=False
            case['solution_approved']=False
            case['evidence_verified']=False
    if 'selected' in changes and before.get('selected')!=case.get('selected'):
        case['solution_approved']=False
    if 'finance' in changes and before.get('finance')!=case.get('finance'):
        if any(k!='sponsor_review' and before.get('finance',{}).get(k)!=case.get('finance',{}).get(k) for k in changes['finance']):
            case['finance']['sponsor_review']='Pending'
    stage=8
    if any(k in changes for k in ('trigger','objective','need_date','owner')):stage=min(stage,0)
    if any(k in changes for k in ('criteria','evidence','evidence_verified','gap','diagnosis_approved','survey','data_snapshot','domain_notes')):stage=min(stage,1)
    if any(k in changes for k in ('selected','solution_approved')):stage=min(stage,2)
    if 'finance' in changes:stage=min(stage,3)
    if 'commitments' in changes:stage=min(stage,4)
    if 'actions' in changes:stage=min(stage,5)
    if 'verification' in changes:stage=min(stage,6)
    if 'closure' in changes:stage=min(stage,7)
    case['completed_stage']=min(old_stage,stage)
    if stage <=3 and old_stage>=4 and 'finance' not in changes:
        case.setdefault('finance',{})['sponsor_review']='Pending'
    return True


def complete_stage_local(case:dict,stage:int):
    cur=int(case.get('completed_stage',0))
    if stage!=cur+1:
        raise ValueError(f'Please complete Stage {cur+1} first.')
    ok,reason=stage_check(case,stage)
    if not ok:raise ValueError(reason)
    case['completed_stage']=stage
    return case


def attach_synthetic_snapshot(case:dict):
    snapshot=snowflake_case(case['id'])
    if snapshot is None:
        raise ValueError('No matching mock supplier record.')
    revise_case(case,{'data_snapshot':snapshot})
    # A snapshot is a data source, NOT validation.
    case['diagnosis_approved']=False
    case['evidence_verified']=False
    case['solution_approved']=False
    case['completed_stage']=min(int(case.get('completed_stage',0)),1)
    case['finance']['sponsor_review']='Pending'
    return snapshot


def clean_imported_case(obj:dict):
    """Validate a downloaded case before adding it to the current demo session."""
    from copy import deepcopy
    if not isinstance(obj,dict) or not obj.get('id') or not obj.get('name'):
        raise ValueError('Expected a JSON object with id and name')
    if len(json.dumps(obj))>1_500_000:
        raise ValueError('Case file is too large')
    expected={r['code'] for r in CRITERIA}
    valid_ids={r['id'] for r in INTERVENTIONS}
    if not isinstance(obj.get('criteria'),list) or any(k not in expected for k in obj['criteria']):
        raise ValueError('Unknown or missing capability criteria')
    if not isinstance(obj.get('finance'),dict):
        raise ValueError('Missing finance object')
    if not isinstance(obj.get('selected'),list) or any(k not in valid_ids for k in obj['selected']):
        raise ValueError('Unknown intervention reference')
    for k in ['survey','commitments','verification','closure']:
        if not isinstance(obj.get(k),dict):raise ValueError('Missing '+k)
    if not isinstance(obj.get('actions'),list):raise ValueError('Missing action list')
    if not 0<=int(obj.get('completed_stage',0))<=8:raise ValueError('Invalid stage')
    allowed=set(CASES[0])
    obj=deepcopy({k:v for k,v in obj.items() if k in allowed})
    # Imported records are unverified until assessor review.
    obj['completed_stage']=0
    obj['evidence_verified']=False
    obj['diagnosis_approved']=False
    obj['solution_approved']=False
    obj['finance']['sponsor_review']='Pending'
    return obj
