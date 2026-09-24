"""Personal model receipts contain no keys; ownership and billing claims are atomic."""
import concurrent.futures
import uuid
import psycopg
import pytest
from test_project_database import database,setup,session,identity,query,rpc  # noqa: F401


def test_competition_mode_also_requires_personal_api_for_shared_preparation_phase(setup):
    s=setup;uri=s['uri'];run,participant,_=session(s)
    assert rpc(uri,'observer_model_route',run,participant)=={'personal':False}
    # Project adaptation and preview are assigned a separate shared phase.
    query(uri,"update private.observer_site_mode set mode='competition' where id")
    assert rpc(uri,'observer_model_route',run,participant)['personal']
    assert rpc(uri,'observer_personal_model_routes',role='authenticated',user=s['user'])[0]['run_id']==str(run)
    with pytest.raises(psycopg.Error,match='personal_api_required'):
        rpc(uri,'observer_reserve_model',run,participant,uuid.uuid4(),s['provider'],'test-model','a'*64,1)


def test_personal_model_routes_and_claims_are_private_and_credentials_are_not_stored(setup):
    s=setup;uri=s['uri'];run,participant,_=session(s)
    query(uri,'update public.phases set counts_for_final=true where id=%s',(s['phase'],))
    route=rpc(uri,'observer_model_route',run,participant)
    assert route['personal'] and len(route['topic'])>64
    assert rpc(uri,'observer_personal_model_routes',role='authenticated',user=s['user'])==[{'run_id':str(run),'topic':route['topic']}]
    outsider,_=identity(uri)
    assert rpc(uri,'observer_personal_model_routes',role='authenticated',user=outsider)==[]
    with pytest.raises(psycopg.Error,match='permission denied'):
        rpc(uri,'observer_model_route',run,participant,role='authenticated',user=s['user'])
    with pytest.raises(psycopg.Error,match='personal_api_required'):
        rpc(uri,'observer_reserve_model',run,participant,uuid.uuid4(),s['provider'],'test-model','a'*64,1)
    call=uuid.uuid4()
    assert rpc(uri,'observer_request_personal_model',run,participant,call,'a'*64)
    assert not rpc(uri,'observer_request_personal_model',run,participant,call,'a'*64)
    with pytest.raises(psycopg.Error,match='request_id_conflict'):
        rpc(uri,'observer_request_personal_model',run,participant,call,'b'*64)
    with pytest.raises(psycopg.Error,match='run_not_found'):
        rpc(uri,'observer_claim_personal_model',outsider,run,call,'a'*64)
    with pytest.raises(psycopg.Error,match='request_id_conflict'):
        rpc(uri,'observer_claim_personal_model',s['user'],run,call,'b'*64)
    def claim(_):
        try:return rpc(uri,'observer_claim_personal_model',s['user'],run,call,'a'*64)
        except psycopg.Error as e:
            assert 'model_request_already_received' in str(e)
            return 'duplicate'
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(claim,range(2)))==sorted([route['topic'],'duplicate'])
    rpc(uri,'observer_finish_personal_model',call,'done')
    rpc(uri,'observer_finish_personal_model',call,'timeout')
    assert query(uri,'select status from private.observer_personal_model_calls where id=%s',(call,))==[('done',)]
    stored=query(uri,'select row_to_json(c) from private.observer_personal_model_calls c where id=%s',(call,))[0][0]
    assert set(stored)=={'id','run_id','request_digest','status','created_at','updated_at'}
    second=uuid.uuid4();assert rpc(uri,'observer_request_personal_model',run,participant,second,'a'*64)
    query(uri,"update private.observer_sessions set deadline_at=clock_timestamp()-interval '1 second' where run_id=%s",(run,))
    with pytest.raises(psycopg.Error,match='run_not_found'):
        rpc(uri,'observer_claim_personal_model',s['user'],run,second,'a'*64)
