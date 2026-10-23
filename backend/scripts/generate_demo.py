"""Generate fictitious time-series JSON locally; never connects to a database."""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path


def demo_records(count=120):
    if not 100 <= count <= 1000:
        raise ValueError('연습용 기록 수는 100~1000개로 지정해 주세요.')
    courses, rows = [], []
    for index in range(count):
        key = f'demo-{index + 1:04d}'
        day = (date(2024, 1, 1) + timedelta(days=index)).isoformat()
        hours = 1 + index % 3
        title = f'[가상 연습자료] 디지털 실습 {index % 4 + 1}'
        educated = 0 if index % 5 == 0 else 5 + index % 10
        completed = 5 + index % 10
        mode = ['집합', '온라인', '에듀버스'][index % 3]
        courses.append({'course_id': key, 'title': title, 'hours': hours,
                        'educated': educated, 'completed': completed,
                        'students_for_analysis': educated or completed,
                        'student_count_basis': 'completed_when_educated_zero' if educated == 0 else 'educated',
                        'satisfaction_for_analysis': None if mode == '에듀버스' else 90 + index % 10,
                        'approval_status': None, 'is_demo': True})
        rows.append({'id': key + '-day', 'course_id': key, 'date': day, 'value': hours,
                     'memo': '실제 강사·교육생·기관과 무관한 가상 연습자료', 'course_title': title,
                     'mode': mode, 'venue': '[가상] 연습 공간', 'is_demo': True,
                     'schedule_units': [{'start_time': '09:00', 'end_time': f'{9 + hours:02d}:00',
                                         'hours': hours, 'topic': '가상 디지털 실습'}]})
    return courses, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=120)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[2] / '.local/demo-data')
    args = parser.parse_args()
    courses, rows = demo_records(args.count)
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ['course_records.json', 'data_records.json']:
        if (args.output / name).exists():
            raise SystemExit('이미 생성된 파일이 있습니다. 다른 --output 폴더를 지정해 주세요.')
    for name, data in [('course_records.json', courses), ('data_records.json', rows)]:
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'가상 연습자료 {len(rows)}개를 로컬에 생성했습니다. 실제 교육 실적이 아닙니다. DB에는 저장하지 않았습니다.')


if __name__ == '__main__':
    main()
