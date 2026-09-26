"""Formal generator inputs stay private before, during and after competition."""
import uuid

import pytest
import psycopg

from test_project_database import database, identity, query  # noqa: F401


def test_formal_sources_never_reopen_at_start_or_with_public_weather(database):
    uri = database
    participant, _ = identity(uri)
    admin, _ = identity(uri)
    query(uri, 'update public.profiles set is_admin=true where id=%s', (admin,))
    phase, formal, practice = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    prefix = str(formal)
    query(uri, "insert into public.phases(id,slug,name_en,name_zh,counts_for_final) values(%s,%s,'F','F',true)", (phase,str(phase)))
    for sid in (formal, practice):
        query(uri, "insert into public.scenarios(id,slug,name,weather_public,forecasts_public,events_public) values(%s,%s,'S',true,true,true)", (sid,str(sid)))
    query(uri, 'insert into public.phase_scenarios values(%s,%s)', (phase,formal))
    paths = ['config/scenario_config.json', 'config/weather_config.json',
             'config/tile_config.json', 'config/request_config.json',
             'outputs/reference/scenario_manifest.json', 'outputs/reference/catalog_metadata.json',
             'outputs/reference/observation_request_metadata.json', 'outputs/reference/weather.csv',
             'outputs/reference/weather_forecasts.csv', 'outputs/reference/weather_events.csv',
             'outputs/reference/tiles.csv']
    for sid in (formal, practice):
        for path in paths:
            query(uri, "insert into storage.objects(bucket_id,name) values('scenarios',%s)", (str(sid)+'/'+path,))
    def visible(role, user=None):
        return {r[0] for r in query(uri, "select name from storage.objects where bucket_id='scenarios'", role=role,user=user)}
    for start, end in (("now()+interval '1 day'", 'null'),
                       ("now()-interval '1 day'", "now()+interval '1 day'"),
                       ("now()-interval '2 days'", "now()-interval '1 day'")):
        query(uri, f'update public.phases set starts_at={start},ends_at={end} where id=%s', (phase,))
        for role,user in (('anon',None),('authenticated',participant)):
            names = visible(role,user)
            assert not any(n.startswith(prefix+'/') for n in names)
            assert all(str(practice)+'/'+p in names for p in paths)
        for role,user in (('authenticated',admin),('service_role',None)):
            assert all(prefix+'/'+p in visible(role,user) for p in paths)
    # SQL columns are a separate disclosure channel; the previous seed-column
    # protections must remain effective as well.
    for column in ('seed', 'checksum', 'manifest'):
        with pytest.raises(psycopg.Error, match='permission denied'):
            query(uri, f'select {column} from public.scenarios', role='anon')
