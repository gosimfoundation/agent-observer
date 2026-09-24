"""Only organizers switch the current experience; legacy data stays intact."""
import uuid
import psycopg
import pytest
from test_project_database import database, identity, query, rpc  # noqa: F401
from test_scenario_instance_database import configure


def test_mode_switch_is_admin_only_and_requires_a_ready_competition(database):
    uri=database; admin,team=identity(uri); participant,_=identity(uri)
    practice,competition,scenario=uuid.uuid4(),uuid.uuid4(),uuid.uuid4()
    for phase,slug in ((practice,'practice'),(competition,'online')):
        query(uri,"insert into public.phases(id,slug,name_en,name_zh) values(%s,%s,'Test','测试')",(phase,slug))
    query(uri,'update public.profiles set is_admin=true where id=%s',(admin,))
    before=query(uri,'select row_to_json(p)::text from public.phases p order by id')
    assert rpc(uri,'current_competition',role='anon')=={'mode':'practice','phase_id':str(practice)}
    with pytest.raises(psycopg.Error,match='permission denied'):
        rpc(uri,'set_competition_mode','competition',role='anon')
    with pytest.raises(psycopg.Error,match='admin_required'):
        rpc(uri,'set_competition_mode','competition',role='authenticated',user=participant)
    with pytest.raises(psycopg.Error,match='competition_not_ready'):
        rpc(uri,'set_competition_mode','competition',role='authenticated',user=admin)
    assert rpc(uri,'current_competition',role='anon')['mode']=='practice'
    query(uri,"insert into public.scenarios(id,slug,name) values(%s,%s,'Test')",(scenario,str(scenario)))
    query(uri,'insert into public.phase_scenarios values(%s,%s)',(competition,scenario))
    query(uri,'insert into public.observer_phase_settings(phase_id,projects_enabled,local_sessions_enabled) values(%s,true,true)',(competition,))
    configure({'uri':uri,'phase':competition,'scenario':scenario})
    result=rpc(uri,'set_competition_mode','competition',role='authenticated',user=admin)
    assert result=={'mode':'competition','phase_id':str(competition)}
    assert rpc(uri,'current_competition',role='anon')==result
    rpc(uri,'set_competition_mode','practice',role='authenticated',user=admin)
    assert rpc(uri,'current_competition',role='anon')['mode']=='practice'
    assert query(uri,'select row_to_json(p)::text from public.phases p order by id')==before


def test_formal_competition_rejects_csv_and_local_batches_even_if_config_is_stale(database):
    uri=database;user,team=identity(uri)
    phase,scenario=uuid.uuid4(),uuid.uuid4()
    query(uri,"insert into public.phases(id,slug,name_en,name_zh,counts_for_final) values(%s,%s,'Formal','正式比赛',true)",(phase,str(phase)))
    query(uri,"insert into public.scenarios(id,slug,name) values(%s,%s,'Test')",(scenario,str(scenario)))
    query(uri,'insert into public.phase_scenarios values(%s,%s)',(phase,scenario))
    query(uri,'insert into public.observer_phase_settings(phase_id,projects_enabled,local_sessions_enabled) values(%s,true,true)',(phase,))
    with pytest.raises(psycopg.Error,match='competition_project_required'):
        rpc(uri,'observer_create_batch',phase,None,role='authenticated',user=user)
    with pytest.raises(psycopg.Error,match='competition_project_required'):
        rpc(uri,'create_submission',str(phase),'results',str(scenario),str(team)+'/result.csv',role='authenticated',user=user)
    assert query(uri,'select count(*) from public.observer_batches where phase_id=%s',(phase,))==[(0,)]
    assert query(uri,'select count(*) from public.submissions where phase_id=%s',(phase,))==[(0,)]
