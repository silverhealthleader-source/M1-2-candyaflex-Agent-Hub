"""Fictitious same-time classes must retain their confirmed individual identity."""
from test_api import setup


def test_confirmed_distinct_pair_does_not_hide_other_unconfirmed_overlaps(setup):
    client, repo = setup
    template = {'date': '2024-05-08', 'start_time': '09:00', 'end_time': '12:00',
                'planned_hours': 3, 'institution': '[가상] 온라인', 'region': '[가상]',
                'title': '[가상] 독립 수업', 'status': 'scheduled', 'planned_students': None,
                'delivery_mode': '온라인 Zoom', 'schedule_status': 'confirmed'}
    for key, counterpart in [('class-a', 'class-b'), ('class-b', 'class-a'), ('class-c', None)]:
        repo.save('plans', key, {**template, 'id': key, 'distinct_session_confirmed': bool(counterpart),
                                'same_time_separate_session_id': counterpart, 'original_schedule_date': '2024-05-07' if key == 'class-a' else None})
    summary = client.get('/api/data/summary').json()
    plan = summary['planning']
    assert summary['count'] == 0 and summary['metrics']['total'] == 0
    assert plan['confirmed_online_count'] == 3 and plan['confirmed_online_hours'] == 9
    assert plan['schedule_conflict_count'] == 3
    assert plan['confirmed_distinct_overlap_count'] == 1
    assert plan['schedule_conflict_pending_count'] == 2
    sessions = {row['id']: row for row in plan['sessions']}
    assert len(sessions) == 3 and sessions['class-a']['date'] == '2024-05-08'
    assert sessions['class-a']['original_schedule_date'] == '2024-05-07'
    assert sessions['class-a']['same_time_separate_session_id'] == 'class-b'
    conflicts = {row['id']: row for row in sessions['class-a']['schedule_conflicts']}
    assert conflicts['class-b']['distinct_session_confirmed'] is True
    assert conflicts['class-c']['distinct_session_confirmed'] is False
    calendar = client.get('/api/data/calendar?year=2024').json()
    assert len(calendar['months'][4]['plans']) == 3
    assert calendar['months'][4]['planning']['confirmed_distinct_overlap_count'] == 1
