"""Offline acceptance against real SQLite and HTTP routes; no paid model needed."""
import uuid
import datetime
import json
from types import SimpleNamespace
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.services import tools


def slot(capacity=1):
    key = 'acceptance-' + uuid.uuid4().hex
    with tools.db() as c:
        c.execute('INSERT INTO clinic_slots(id,dept,slot_date,slot_time,capacity) VALUES (?,?,?,?,?)',
                  (key, '全科', '2099-01-01', '09:00', capacity))
    return key


def book(s, key, user='acceptance'):
    return tools.create_appointment(s, '演示', '全科', None, key, user_id=user)


def test_retry_when_slot_full():
    s=slot(); key=uuid.uuid4().hex
    first=book(s,key); second=book(s,key)
    assert first['ok'] and second['ok']
    assert first['data']['appointment_id']==second['data']['appointment_id']
    assert second['data']['duplicated']
    with tools.db() as c:
        assert c.execute('SELECT booked FROM clinic_slots WHERE id=?', (s,)).fetchone()[0] == 1


def test_idempotency_key_cannot_reveal_other_users_booking():
    s=slot(2); key=uuid.uuid4().hex
    assert book(s,key,'alice')['ok']
    assert book(s,key,'bob')['code']==6007
    assert book(slot(), key, 'alice')['code'] == 6007


def test_concurrent_bookings_never_exceed_capacity():
    s=slot(3)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda i:book(s,uuid.uuid4().hex,str(i)),range(12)))
    assert sum(r['ok'] for r in results)==3
    with tools.db() as c:
        assert c.execute('SELECT booked FROM clinic_slots WHERE id=?',(s,)).fetchone()[0]==3


def test_invalid_confirmation_action_rejected():
    from app.main import app
    with TestClient(app) as api:
        assert api.post('/chat/confirm',json={'token':'test','action':'anything'}).status_code==422


def test_confirm_response_saved_to_original_conversation(monkeypatch):
    from app import main
    original,newer=uuid.uuid4().hex,uuid.uuid4().hex
    with main.db() as c:
        c.executemany('INSERT INTO conversations(id) VALUES (?)',[(original,),(newer,)])
    def resume(*a,**kw):
        yield {'type':'delta','text':'确认结果'}
        yield {'type':'done','conv_id':original,'committed':True}
    monkeypatch.setattr(main.harness,'resume',resume)
    with TestClient(main.app) as api:
        assert 'event: done' in api.post('/chat/confirm',json={'token':'test'}).text
    with main.db() as c:
        assert c.execute('SELECT conversation_id FROM messages WHERE content=?',('确认结果',)).fetchone()[0]==original


@pytest.mark.parametrize('amount', [float('nan'), float('inf'), -10])
def test_invalid_amount_never_issues_eligibility_token(amount):
    result = tools.check_reimbursement_eligibility(
        '门诊', amount, '电子发票', tools.COMPANY_TITLE, datetime.date.today().isoformat(), user_id='bad-amount')
    assert result['code'] == 6002
    assert 'eligibility_token' not in result.get('data', {})


def pending_draft():
    from app.repositories import agent_trace
    from app import main
    conv = uuid.uuid4().hex
    with main.db() as c:
        c.execute('INSERT INTO conversations(id) VALUES (?)', (conv,))
    date = datetime.date.today().isoformat()
    checked = tools.check_reimbursement_eligibility(
        '门诊', 300, '电子发票', tools.COMPANY_TITLE, date, user_id='demo_user')
    args = dict(visit_type='门诊', amount=300, invoice_type='电子发票',
                invoice_no=uuid.uuid4().hex, visit_date=date,
                eligibility_token=checked['data']['eligibility_token'], idempotency_key=uuid.uuid4().hex)
    token = agent_trace.create_pending(uuid.uuid4().hex, 'create_reimbursement_draft', args, {},
                                       conv_id=conv, user_id='demo_user')
    return token, conv, args['invoice_no']


def test_http_confirmation_creates_exactly_one_draft_and_audit(monkeypatch):
    from app import main
    token, conv, invoice = pending_draft()
    # Only replace the external model response. HTTP, confirmation, tools and SQLite stay real.
    reply = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='草稿已生成'))])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: reply)))
    monkeypatch.setattr(main.harness, '_client', lambda: client)
    with tools.db() as c:
        assert c.execute('SELECT COUNT(*) FROM reimbursement_drafts WHERE invoice_no=?', (invoice,)).fetchone()[0] == 0
    with TestClient(main.app) as api:
        first = api.post('/chat/confirm', json={'token': token}).text
        second = api.post('/chat/confirm', json={'token': token}).text
    assert 'event: done' in first
    assert 'event: error' in second
    with main.db() as c:
        assert c.execute('SELECT COUNT(*) FROM reimbursement_drafts WHERE invoice_no=?', (invoice,)).fetchone()[0] == 1
        assert c.execute('SELECT COUNT(*) FROM messages WHERE conversation_id=?', (conv,)).fetchone()[0] == 1
        assert c.execute("SELECT COUNT(*) FROM agent_steps WHERE conv_id=? AND tool_name='create_reimbursement_draft'", (conv,)).fetchone()[0] == 1


def test_http_reject_prevents_later_execution():
    from app import main
    token, _, invoice = pending_draft()
    with TestClient(main.app) as api:
        assert api.post('/chat/confirm', json={'token': token, 'action': 'reject'}).json()['code'] == 0
        assert 'event: error' in api.post('/chat/confirm', json={'token': token}).text
    with tools.db() as c:
        assert c.execute('SELECT COUNT(*) FROM reimbursement_drafts WHERE invoice_no=?', (invoice,)).fetchone()[0] == 0


def test_expired_and_wrong_user_confirmation_cannot_execute():
    from app.repositories import agent_trace
    token, _, _ = pending_draft()
    assert agent_trace.take_pending(token, 'another-user')[0] is None
    with agent_trace.db() as c:
        c.execute('UPDATE pending_actions SET created_at=0 WHERE token=?', (token,))
    row, error = agent_trace.take_pending(token, 'demo_user')
    assert row is None and '超时' in error


def test_signing_uses_configured_secret():
    import hashlib
    import hmac
    from app.core.config import TOKEN_SECRET
    payload = {'amount': 300}
    expected = hmac.new(TOKEN_SECRET.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    assert tools._sign(payload) == expected
