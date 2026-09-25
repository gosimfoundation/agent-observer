"""Guards of the acceptance-phase configuration script, against real SQL semantics."""
import importlib.util
import uuid
import psycopg

from test_project_database import database, query  # noqa: F401

spec=importlib.util.spec_from_file_location('configure_observer_acceptance','scripts/configure-observer-acceptance.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Args:
    daily_batches=10
    runtime_seconds=300
    sort_order=10100


def install(uri,storage_present=True):
    def local_query(sql):
        with psycopg.connect(uri) as conn:
            cur=conn.execute(sql)
            return cur.fetchall() if cur.description else []
    mod.query=local_query
    def one(sql):
        if 'storage.objects' in sql:
            return 1 if storage_present else 0
        rows=local_query(sql)
        assert len(rows)==1 and len(rows[0])==1,sql
        return rows[0][0]
    mod.one=one


def make_hidden_team(uri,name):
    from test_project_database import identity
    leader,team=identity(uri)
    query(uri,'update public.teams set name=%s,slug=%s,is_hidden=true where id=%s',(name,'slug-'+name,team))
    return team


def test_acceptance_plan_is_idempotent_and_projects_only(database):
    uri=database;install(uri)
    team=make_hidden_team(uri,'Acceptance Alpha')
    synthetic=[]
    for index in range(2):
        scenario=uuid.uuid4()
        query(uri,"insert into public.scenarios(id,slug,name,is_active) values(%s,%s,'Synthetic',true)",(scenario,f'synthetic-{index}'))
        synthetic.append({'scenario_id':str(scenario),'slug':f'synthetic-{index}','bundle_path':'bundle.zip','bundle_digest':'a'*64})
    scenarios=synthetic
    plan=mod.plan_phase(mod.check_team(str(team)),scenarios,Args)
    assert plan['is_new_phase']
    assert plan['projects_only']['projects_enabled'] is True
    assert plan['runtime_seconds']==300 and plan['daily_batches']==10
    assert plan['statements'][1].lower().count("'false'")==1 and plan['statements'][1].lower().count("'true'")
    # Applying the plan twice must be idempotent: the second pass reuses the phase.
    for statement in plan['statements']:query(uri,statement)
    replan=mod.plan_phase(mod.check_team(str(team)),scenarios,Args)
    assert not replan['is_new_phase'] and replan['phase_id']==plan['phase_id']
    row=query(uri,'select projects_enabled,local_sessions_enabled,access_team_id from public.observer_phase_settings where phase_id=%s',(plan['phase_id'],))[0]
    assert row==(True,False,team)
    # A second team plans its own independent phase, never shares the first.
    other=make_hidden_team(uri,'Acceptance Beta')
    plan_b=mod.plan_phase(mod.check_team(str(other)),scenarios,Args)
    assert plan_b['phase_id']!=plan['phase_id'] and plan_b['slug'].endswith(str(other)[:8])
    # An unmarked (visible) team is refused outright.
    query(uri,'update public.teams set is_hidden=false where id=%s',(team,))
    try:
        mod.check_team(str(team));raise SystemError('unmarked team accepted')
    except mod.CheckError:pass
    # A phase already restricted to another team is never re-pointed.
    query(uri,'update public.observer_phase_settings set access_team_id=%s where phase_id=%s',(other,plan['phase_id']))
    try:
        mod.plan_phase(mod.check_team(str(team)),scenarios,Args);raise SystemError('foreign phase accepted')
    except mod.CheckError:pass


def test_acceptance_scenario_guard_refuses_formal_and_lab_material(database):
    uri=database;install(uri,storage_present=True)
    formal_phase,formal_scenario=uuid.uuid4(),uuid.uuid4()
    query(uri,"insert into public.phases(id,slug,name_en,name_zh,counts_for_final) values(%s,'online','Online','正式',true)",(formal_phase,))
    query(uri,"insert into public.scenarios(id,slug,name,is_active) values(%s,'formal-secret','Formal',true)",(formal_scenario,))
    query(uri,'insert into public.phase_scenarios values(%s,%s)',(formal_phase,formal_scenario))
    try:
        mod.check_scenario(str(formal_scenario),'x');raise SystemError('formal scenario accepted')
    except mod.CheckError:pass
    # Slug-protected phases (the hidden lab) refuse their scenarios too.
    lab_phase,lab_scenario=uuid.uuid4(),uuid.uuid4()
    query(uri,"insert into public.phases(id,slug,name_en,name_zh) values(%s,'observer-platform-e2e','Lab','实验室')",(lab_phase,))
    query(uri,"insert into public.scenarios(id,slug,name,is_active) values(%s,'synthetic-b','Synthetic',true)",(lab_scenario,))
    query(uri,'insert into public.phase_scenarios values(%s,%s)',(lab_phase,lab_scenario))
    try:
        mod.check_scenario(str(lab_scenario),'x');raise SystemError('lab scenario accepted')
    except mod.CheckError:pass
    # A clean private synthetic scenario plans only with a bundle present.
    private=uuid.uuid4()
    query(uri,"insert into public.scenarios(id,slug,name,is_active) values(%s,'synthetic-a','Synthetic',true)",(private,))
    try:
        mod.check_scenario(str(private),'x');raise SystemError('bundle-less scenario accepted')
    except mod.CheckError:pass
    query(uri,'insert into private.observer_scenario_bundles(scenario_id,storage_path,digest) values(%s,%s,%s)',
          (private,'observer-scenarios/bundle.zip','b'*64))
    checked=mod.check_scenario(str(private),'x')
    assert checked['slug']=='synthetic-a' and checked['bundle_digest']=='b'*64
