"""New board aggregates one complete evaluation without exposing private evidence."""
import uuid
from psycopg.types.json import Jsonb
from test_project_database import database,setup,query,rpc  # noqa: F401


def test_board_uses_one_complete_batch_and_respects_private_phase(setup):
    s=setup;uri=s['uri'];scenario=uuid.uuid4()
    query(uri,"insert into public.scenarios(id,slug,name) values(%s,%s,'Second')",(scenario,str(scenario)))
    query(uri,'insert into public.phase_scenarios values(%s,%s)',(s['phase'],scenario))
    batches=[]
    for scores in ((100,0),(60,60),(0,100)):
        batch=rpc(uri,'observer_create_batch',s['phase'],None,role='authenticated',user=s['user']);batches.append(batch)
        runs=query(uri,'select id from public.observer_runs where batch_id=%s order by scenario_id',(batch,))
        for (run,),value in zip(runs,scores):
            summary={'score':{'total':value,'base_science':value+5,'program_bonus':2,'report_reward':3,'penalties':{'bad_action':10}},
              'completed_tiles':4,'required_missing':2}
            query(uri,"update public.observer_runs set status='scored',score=%s,score_summary=%s,result_path='github:private-evidence',finished_at=now() where id=%s",(value,Jsonb(summary),run))
        query(uri,'select private.observer_finalize_batch(%s)',(batch,))
    rows=rpc(uri,'observer_board',s['phase'],100,role='anon')
    assert len(rows)==1
    row=rows[0]
    assert row['observer_batch_id']==str(batches[1]) and row['total_score']==60
    assert row['submission_count']==3 and row['base_science']==65 and row['penalty_total']==10
    assert row['report_reward']==3 and row['completed_tiles']==4
    assert 'private-evidence' not in str(rows) and 'run_id' not in str(rows)
    query(uri,'update public.observer_phase_settings set access_team_id=%s where phase_id=%s',(s['team'],s['phase']))
    assert rpc(uri,'observer_board',s['phase'],100,role='anon')==[]
    assert query(uri,'select * from public.observer_leaderboard(%s)',(s['phase'],),role='anon')==[]
    assert rpc(uri,'observer_board',s['phase'],100,role='authenticated',user=s['user'])[0]['total_score']==60
