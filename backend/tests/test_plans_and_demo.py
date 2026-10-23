"""Fictitious test inputs, unrelated to real classes."""
import importlib.util
from pathlib import Path

from test_api import setup
from app.routers import chat


def virtual_plans():
    return [
        {'id': 'fictional-held', 'date': '2024-11-01', 'start_time': '09:00', 'end_time': '11:00',
         'planned_hours': 2, 'planned_students': 5, 'region': '[가상] 지역', 'institution': '[가상] 연습기관',
         'title': '[가상] 연습 수업', 'status': 'held', 'approval_status': None,
         'decision_review_after': '2024-11-02', 'replacement_condition': '폐강 확인 시 온라인 대체. 세부 일정 미확정.'},
        {'id': 'fictional-scheduled', 'date': '2024-11-01', 'start_time': '14:00', 'end_time': '16:00',
         'planned_hours': 2, 'planned_students': 6, 'region': '[가상] 지역', 'institution': '[가상] 연습기관',
         'title': '[가상] 연습 수업', 'status': 'scheduled', 'approval_status': None,
         'decision_review_after': None, 'replacement_condition': None},
    ]


def test_plans_do_not_change_actual_totals_and_keep_time_slots(setup):
    client, repo = setup
    for row in virtual_plans():
        repo.save('plans', row['id'], row)
    client.post('/api/data', json={'date': '2024-11-01', 'value': 3, 'memo': '가상 결과'})
    summary = client.get('/api/data/summary').json()
    assert summary['count'] == 1 and summary['metrics']['total'] == 3
    assert summary['planning']['by_status'] == {'scheduled': 1, 'held': 1, 'completed': 0, 'cancelled': 0}
    assert summary['planning']['held_hours'] == 2
    calendar = client.get('/api/data/calendar?year=2024').json()
    assert calendar['hours'] == 3 and len(calendar['months'][10]['plans']) == 2
    assert [p['start_time'] for p in calendar['months'][10]['plans']] == ['09:00', '14:00']
    selected = client.get('/api/plans?month=2024-11&status=held').json()
    assert len(selected['items']) == 1 and selected['summary']['held_hours'] == 2
    assert client.get('/api/plans?month=2024-13').status_code == 422


def test_chat_receives_conditional_plans_separately(setup, monkeypatch):
    client, repo = setup
    for row in virtual_plans():
        repo.save('plans', row['id'], row)
    captured = []
    def fake_answer(summary, messages):
        captured.append(summary)
        return '가상 보류 수업은 온라인 대체 여부를 확인해야 합니다.'
    monkeypatch.setattr(chat, 'generate_answer', fake_answer)
    response = client.post('/api/chat', json={'message': '가상 계획 설명', 'date_from': '2024-11-01', 'date_to': '2024-11-30'})
    assert response.status_code == 200
    assert captured[0]['metrics']['total'] == 0
    assert captured[0]['planning']['conditional_zoom_count'] == 1


def test_demo_generator_produces_consistent_nonpersonal_records(tmp_path):
    scripts = Path(__file__).resolve().parents[1] / 'scripts'
    def load(name):
        spec = importlib.util.spec_from_file_location(name, scripts / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    courses, rows = load('generate_demo').demo_records()
    assert len(rows) == len(courses) == 120
    assert len({r['id'] for r in rows}) == 120 and all(r['is_demo'] for r in rows)
    assert sum(c['hours'] for c in courses) == sum(r['value'] for r in rows)
    import json
    for name, data in [('course_records.json', courses), ('data_records.json', rows)]:
        (tmp_path / name).write_text(json.dumps(data), encoding='utf-8')
    assert len(load('import_data').load_and_validate(tmp_path)[1]) == 120
