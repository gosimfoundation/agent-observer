"""A newcomer can discover teams, create one, share a link and join on mobile."""
import hashlib
import os
import uuid

from playwright.sync_api import sync_playwright, expect
from psycopg.types.json import Jsonb
import pytest

from test_project_http import edge_stack  # noqa: F401
from test_project_portal_browser import portal_site  # noqa: F401
from test_project_database import query

pytestmark = pytest.mark.skipif(not all(os.environ.get(key) for key in
    ('OBSERVER_DENO_BIN', 'SAC_POSTGREST_BIN', 'SAC_NODE_BIN')), reason='Local browser toolchain required')


def test_discover_create_invite_login_and_join(portal_site, edge_stack):
    uri = edge_stack['harness'].db_uri
    password = 'local-team-browser-password-23'
    users = [uuid.uuid4(), uuid.uuid4()]
    for index, user in enumerate(users):
        query(uri, 'insert into auth.users(id,email,raw_user_meta_data) values(%s,%s,%s)',
              (user, f'{user}@example.test', Jsonb({'name': f'Team journey {index}',
                'password_hash': hashlib.sha256(password.encode()).hexdigest()})))
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel=os.environ.get('OBSERVER_BROWSER_CHANNEL'))
        leader = browser.new_context(viewport={'width': 1365, 'height': 950})
        guest = browser.new_context(viewport={'width': 390, 'height': 844})
        page, mobile = leader.new_page(), guest.new_page()
        errors = []
        for p in (page, mobile):
            p.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(portal_site + '/teammates?lang=en')
        actions = page.get_by_test_id('team-actions')
        expect(actions.get_by_role('link', name='Create team')).to_be_visible()
        actions.get_by_role('link', name='Create team').click()
        expect(page.get_by_test_id('login-email')).to_be_visible()
        page.get_by_test_id('login-email').fill(f'{users[0]}@example.test')
        page.get_by_test_id('login-password').fill(password)
        page.get_by_test_id('login-submit').click()
        expect(page.get_by_test_id('team-name-input')).to_be_visible(timeout=15000)
        name = 'Team browser ' + str(users[0])[:8]
        page.get_by_test_id('team-name-input').fill(name)
        page.get_by_test_id('team-create').click()
        link = page.get_by_test_id('team-invite-link')
        expect(link).to_be_visible(timeout=15000)
        invite_url = link.input_value()
        code = page.get_by_test_id('team-invite-code').inner_text().strip()
        assert invite_url == portal_site + '/team?invite=' + code
        page.goto(portal_site + '/teammates')
        page.get_by_test_id('team-actions').get_by_role('link', name='Invite teammates').click()
        expect(page.get_by_test_id('team-invite-link')).to_have_value(invite_url)
        mobile.goto(invite_url + '&lang=en')
        expect(mobile.get_by_test_id('login-email')).to_be_visible()
        mobile.get_by_test_id('login-email').fill(f'{users[1]}@example.test')
        mobile.get_by_test_id('login-password').fill(password)
        mobile.get_by_test_id('login-submit').click()
        expect(mobile.get_by_test_id('team-join-code')).to_have_value(code, timeout=15000)
        # Opening an invitation never changes membership without a click.
        assert query(uri, 'select team_id from public.profiles where id=%s', (users[1],)) == [(None,)]
        mobile.get_by_test_id('team-join').click()
        expect(mobile.get_by_role('heading', name=name, exact=True)).to_be_visible(timeout=15000)
        assert query(uri, 'select count(distinct team_id) from public.profiles where id=any(%s)', (users,)) == [(1,)]
        expect(mobile.get_by_test_id('team-invite-link')).to_have_value(invite_url)
        assert not errors, errors
        browser.close()
