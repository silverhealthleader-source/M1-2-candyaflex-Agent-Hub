"""Read-only peer-review readiness check; no GPT calls or production mutations."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
import httpx

ROOT = Path(__file__).resolve().parents[2]


def main():
    load_dotenv(ROOT / 'backend/.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-url', default=os.getenv('API_BASE_URL', ''))
    parser.add_argument('--origin', required=True, help='Vercel frontend origin, without a path')
    parser.add_argument('--output', type=Path, default=ROOT / '.local/verification/deployment-readiness.json')
    args = parser.parse_args()
    for value in [args.api_url, args.origin]:
        url = urlsplit(value)
        if url.scheme != 'https' or not url.netloc or url.username or url.password or url.query or url.fragment or url.path not in ['', '/']:
            parser.error('서비스 주소는 로그인 정보가 없는 https 출처로 입력해 주세요.')
    token = os.getenv('APP_ACCESS_TOKEN', '').strip()
    if not token:
        parser.error('APP_ACCESS_TOKEN을 비공개 환경변수에 설정해 주세요. 키를 명령행 인수에 넣지 않습니다.')
    base, origin = args.api_url.rstrip('/'), args.origin.rstrip('/')
    headers = {'Authorization': 'Bearer ' + token}
    required = {'/api/data': ['get', 'post'], '/api/data/{key}': ['put', 'delete'],
                '/api/data/summary': ['get'], '/api/conversations': ['get', 'post'],
                '/api/conversations/{key}': ['get', 'delete'], '/api/chat': ['post']}
    checks = []
    with httpx.Client(timeout=90) as client:
        def get(path):
            response = client.get(base + path, headers=headers)
            response.raise_for_status()
            return response.json()
        health = get('/health')
        assert health['status'] == 'ok' and health['database_configured'] and health['ai_configured']
        assert health['database_mode'] == 'cloud' and health['access_key_required']
        checks.append('Production health and cloud database / AI configuration')
        assert client.get(base + '/docs').status_code == 200
        schema = get('/openapi.json')
        assert all(method in schema['paths'][path] for path, methods in required.items() for method in methods)
        assert schema['components']['securitySchemes']['HTTPBearer']['scheme'] == 'bearer'
        checks.append('Required API schema and Swagger')
        assert client.get(base + '/api/data/summary').status_code == 401
        preflight = client.options(base + '/api/data', headers={'Origin': origin,
            'Access-Control-Request-Method': 'GET', 'Access-Control-Request-Headers': 'authorization'})
        assert preflight.status_code == 200 and preflight.headers.get('access-control-allow-origin') == origin
        checks.append('Bearer protection and configured CORS origin')
        summary = get('/api/data/summary')
        assert summary['count'] >= 100
        assert all(key in summary['metrics'] for key in ['total', 'average', 'max', 'min'])
        assert summary['period']['start'] and summary['period']['end'] and summary['trend']['label']
        checks.append('At least 100 points and period / statistics / trend summary')
        invalid = client.get(base + '/api/data?limit=0', headers=headers)
        assert invalid.status_code == 422
        history = get('/api/conversations')
        assert history['messages_included'] is False
        restored = False
        if history['items']:
            detail = get('/api/conversations/' + history['items'][0]['id'])
            assert isinstance(detail['messages'], list) and detail['messages']
            restored = True
        checks.append('Input validation and conversation list / detail contract')
        frontend = client.get(origin + '/education')
        gated = frontend.status_code in [302, 303] and frontend.headers.get('location', '').startswith('/_access?')
        content_verified = False
        if gated:
            login = client.get(origin + '/_access')
            assert login.status_code == 200, 'Vercel SITE_ACCESS_CODE 설정과 재배포를 확인해 주세요.'
            assert 'name="code"' in login.text and 'type="password"' in login.text
            assert client.get(origin + '/app.js').status_code == 401
            assert client.get(origin + '/config.js').status_code == 401
            checks.append('Configured server-side site gate; anonymous HTML and source assets blocked')
            site_code = os.getenv('SITE_ACCESS_CODE', '').strip()
            if site_code:
                signed_in = client.post(origin + '/_access/login', data={'code': site_code, 'returnTo': '/education'}, headers={'Origin': origin})
                assert signed_in.status_code == 303, '사이트 인증번호를 비공개 환경변수에서 확인해 주세요.'
                frontend = client.get(origin + '/education')
        if not gated or os.getenv('SITE_ACCESS_CODE', '').strip():
            assert frontend.status_code == 200
            assert all(name in frontend.text for name in ['chat-input', 'send-button', 'data-body', 'history-list', 'context-period'])
            assert base in client.get(origin + '/config.js').text
            content_verified = True
            checks.append('Vanilla frontend and configured backend address')
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
        'api_url': base, 'frontend_origin': origin, 'checks': checks, 'required_api_methods': required,
        'conversation_detail_restored': restored, 'saved_data_count': summary['count'],
        'site_access_gate_detected': gated, 'frontend_content_verified': content_verified,
        'production_mutations': 0, 'gpt_requests': 0,
        'scope': 'No production data mutations or GPT calls. Optional SITE_ACCESS_CODE signs in without recording its value. When absent, a configured gate is checked; authenticated content still needs UI verification.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'PASS: {len(checks)} read-only deployment checks. Private report saved.')


if __name__ == '__main__':
    main()
