"""The deployment transaction must roll back an accidental legacy data edit."""
import importlib.util
from pathlib import Path
import sys

import psycopg
from psycopg.rows import dict_row
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests/supabase'))
from pg import start  # noqa: E402


def test_deployment_records_hashes_is_repeatable_and_rolls_back_legacy_changes(tmp_path,monkeypatch):
    spec=importlib.util.spec_from_file_location('observer_deploy',ROOT/'scripts/deploy-observer-backend.py')
    deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)
    server,uri=start(apply_migrations=False)
    def query(statement):
        with psycopg.connect(uri,autocommit=True,row_factory=dict_row) as connection:
            cursor=connection.execute(statement)
            # The management API returns only the last command's result.
            while cursor.nextset(): pass
            return cursor.fetchall() if cursor.description else []
    try:
        query((ROOT/'tests/supabase/auth_stub.sql').read_text())
        for path in sorted((ROOT/'supabase/migrations').glob('*.sql')):
            if path.name<'20260925000100':query(path.read_text())
        query("insert into public.phases(slug,name_en,name_zh) values('protected','Original','原有赛程')")
        monkeypatch.setattr(deploy,'query',query)
        monkeypatch.setattr(sys,'argv',['deploy-observer-backend.py','--apply'])
        deploy.main();deploy.main()
        count=len(list((ROOT/'supabase/migrations').glob('20260925*_*.sql')))
        assert query('select count(*) as n from private.observer_migrations')[0]['n']==count
        assert query("select name_en from public.phases where slug='protected'")==[{'name_en':'Original'}]
        path=tmp_path/'supabase/migrations';path.mkdir(parents=True)
        (path/'20260925009999_accidental.sql').write_text("update public.phases set name_en='Oops' where slug='protected';")
        monkeypatch.setattr(deploy,'ROOT',tmp_path)
        with pytest.raises(psycopg.Error,match='Existing data changed'):
            deploy.main()
        assert query("select name_en from public.phases where slug='protected'")==[{'name_en':'Original'}]
        assert query('select count(*) as n from private.observer_migrations')[0]['n']==count
    finally:server.cleanup()
