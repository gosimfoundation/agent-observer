#!/usr/bin/env python3
"""Apply only the additive Observer migrations with recorded content hashes.

Reads the already-authorized management credential from process environment.
Never writes credentials. Existing public data is compared inside one repeatable
read transaction; any accidental change rolls back the entire deployment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
# The first Observer migration. Every later migration belongs to Observer too;
# earlier ones are legacy event migrations and are never applied by this script.
FIRST_OBSERVER_MIGRATION = '20260925000100'


def observer_migrations(root):
    return sorted(p for p in (root/'supabase/migrations').glob('*_*.sql') if p.stem>=FIRST_OBSERVER_MIGRATION)


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def query(sql):
    ref = os.environ['SUPABASE_PROJECT_REF']
    request = urllib.request.Request('https://api.supabase.com/v1/projects/'+ref+'/database/query',
        data=json.dumps({'query':sql}).encode(), headers={
            'Authorization':'Bearer '+os.environ['SUPABASE_ACCESS_TOKEN'], 'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        # SQL files contain no secrets; error bodies still stay out of logs.
        raise RuntimeError(f'Migration API returned HTTP {error.code}; no credentials were logged') from None


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true',help='Apply the reviewed, pending additive migrations')
    args=parser.parse_args()
    files=observer_migrations(ROOT)
    exists=query("select to_regclass('private.observer_migrations') is not null as present")[0]['present']
    applied={r['version']:r['digest'] for r in query('select version,digest from private.observer_migrations')} if exists else {}
    pending=[]
    for path in files:
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if path.stem in applied:
            if applied[path.stem]!=digest:
                raise RuntimeError('An applied migration changed: '+path.name+'. Add a new migration instead.')
        else: pending.append((path,digest))
    print(json.dumps({'pending':[p.name for p,_ in pending],'apply':args.apply}),flush=True)
    if not args.apply or not pending: return
    before="""
begin isolation level repeatable read;
select pg_advisory_xact_lock(hashtext('observer-platform-migrations'));
create temp table observer_legacy_snapshot(name text primary key,digest text) on commit drop;
do $$ declare t record;d text;begin
 for t in select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='public' and c.relkind='r' and c.relname not like 'observer_%'
 loop
  execute format('select md5(coalesce(string_agg(row_to_json(x)::text,chr(10) order by row_to_json(x)::text),'''')) from public.%I x',t.relname) into d;
  insert into observer_legacy_snapshot values(t.relname,d);
 end loop;
end $$;
create table if not exists private.observer_migrations(version text primary key,digest text not null,applied_at timestamptz not null default now());
revoke all on private.observer_migrations from public,anon,authenticated;
"""
    after="""
do $$ declare t record;d text;begin
 for t in select * from observer_legacy_snapshot loop
  execute format('select md5(coalesce(string_agg(row_to_json(x)::text,chr(10) order by row_to_json(x)::text),'''')) from public.%I x',t.name) into d;
  if d is distinct from t.digest then raise exception 'Existing data changed in table %; deployment rolled back',t.name; end if;
 end loop;
end $$;
notify pgrst,'reload schema';
commit;
"""
    changes=[]
    for path,digest in pending:
        changes.extend([path.read_text(), '\ninsert into private.observer_migrations(version,digest) values('
                        +quote(path.stem)+','+quote(digest)+');'])
    query(before+'\n'.join(changes)+after)
    print(json.dumps({'applied':[p.name for p,_ in pending],'existing_public_data':'unchanged'}))


if __name__=='__main__': main()
