import pytest
from fastapi import HTTPException
from services.api import accounts, main
from fastapi.testclient import TestClient


def test_register_does_not_fallback_when_database_fails(monkeypatch):
    class BrokenDB:
        def account_by_email(self, email):
            raise RuntimeError('database unavailable')

    monkeypatch.setattr(accounts, '_db', lambda: BrokenDB())
    with pytest.raises(RuntimeError, match='database unavailable'):
        accounts.register('failure@example.com', 'password123')
    assert 'failure@example.com' not in accounts.BY_EMAIL


def test_game_save_does_not_report_success_on_database_failure(monkeypatch):
    monkeypatch.setattr(main, '_DB_OK', True)
    def fail(*args):
        raise RuntimeError('database unavailable')
    monkeypatch.setattr(main, 'save_game', fail)
    with pytest.raises(HTTPException) as error:
        main._persist('failure-test', {'ephemeral': True, 'seed': 1, 'state': main._new_state()})
    assert error.value.status_code == 503


def test_production_password_recovery_is_unavailable_without_email_provider(monkeypatch):
    monkeypatch.setenv('TECRURAL_PROD', '1')
    response = TestClient(main.app).post('/accounts/recover', json={'email': 'test@example.com'})
    assert response.status_code == 503
    assert 'reset_debug' not in response.json()


def test_database_game_read_failure_is_not_reported_as_missing(monkeypatch):
    monkeypatch.setattr(main, '_DB_OK', True)
    monkeypatch.setattr(main, 'load_game', lambda gid: (_ for _ in ()).throw(RuntimeError('database unavailable')))
    with pytest.raises(HTTPException) as error:
        main._get('unknown-game')
    assert error.value.status_code == 503


@pytest.mark.parametrize('operation', ['logout', 'save_version', 'delete_account'])
def test_account_operations_do_not_hide_database_failure(monkeypatch, operation):
    class BrokenDB:
        def __getattr__(self, name):
            def fail(*args):
                raise RuntimeError('database unavailable')
            return fail
    monkeypatch.setattr(accounts, '_db', lambda: BrokenDB())
    args = {'logout': ('token',), 'save_version': ('game', {'day': '2026-01-01'}),
            'delete_account': ('account',)}
    with pytest.raises(RuntimeError, match='database unavailable'):
        getattr(accounts, operation)(*args[operation])


def test_game_database_read_is_not_masked_by_stale_memory(monkeypatch):
    monkeypatch.setattr(main, '_DB_OK', True)
    monkeypatch.setitem(main.GAMES, 'stale-test', {'state': main._new_state(), 'account': None})
    monkeypatch.setattr(main, 'load_game', lambda gid: None)
    with pytest.raises(HTTPException) as error:
        main._get('stale-test')
    assert error.value.status_code == 404


def test_authenticated_owner_can_edit_and_restart_game():
    client = TestClient(main.app)
    email = 'owner-edit-test@example.com'
    client.post('/accounts/register', json={'email': email, 'password': 'password123'})
    token = client.post('/accounts/login', json={'email': email, 'password': 'password123'}).json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    gid = client.post('/games', json={}, headers=headers).json()['game_id']
    assert client.put(f'/games/{gid}', json={'parcels': {}}, headers=headers).status_code == 200
    assert client.post(f'/games/{gid}/restart', headers=headers).status_code == 200
