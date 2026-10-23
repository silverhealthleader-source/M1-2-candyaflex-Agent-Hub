# 캔디A플렉스 에듀 융합에이전트

코디세이 M1-2 개인과제 · 캔디A플렉스 에듀 융합에이전트

교육 영역별 웹앱·교재를 연결하는 전체 허브와 강사 전용 교육운영 AI 비서의 소스 코드입니다. Cowork에서 제작한 8개 영역·47개 항목을 유지하고 교육운영 진입 카드를 추가했습니다. 사용자 제공 CandyAflex PNG 로고를 데스크톱·모바일에 적용했습니다.

**실제 교육 실적·계획 JSON, 교재 원본, 운영 화면 캡처, 계정 키는 이 공개 저장소에 포함하지 않습니다.** 개인 자료는 별도로 보관하고 인증된 데이터베이스에만 가져옵니다. 코드를 실행하면 개인 교육자료가 자동 표시되지 않습니다.

## 화면과 기능

- `frontend/index.html`: 전체 아카데미 허브. 기존 외부 링크와 교육 영역을 유지합니다.
- `frontend/education.html`: 강사 워크스페이스. 전체 허브로 돌아가는 메뉴를 제공합니다.
- 모모: 12개월 블록, 날짜·시간대별 수업 및 별도 교육계획.
- 루미: 과목별 슬라이드·Canva 링크 연결, 등록한 로컬 PDF 열람·다운로드.
- 코코·보리: 교육 분석과 활동 보고서 역할의 AI 대화. 실행 상태에 따라 캐릭터가 움직입니다.
- 교육 실적 CRUD, 기간별 합계·평균·최댓값·최솟값·추세, CSV/JSON 내보내기, 대화 자동 저장·조회·삭제.

외부 링크 상태는 사용자 제공 원본의 분류입니다. 모든 외부 앱의 현재 동작을 검증했다는 뜻은 아닙니다.

## 구현 상태와 남은 과제

FastAPI·Pydantic, Firestore 접근, GPT Responses API 연결 코드, 바닐라 HTML/CSS/JS 화면과 Render·Vercel 설정을 준비했습니다. API 테스트는 격리된 가상 기록과 모의 AI 응답으로 검증합니다.

**실제 GPT 응답, 인터넷 Firestore 연결, Render·Vercel 배포는 아직 완료하지 않았습니다.** 제출 시 실제 실행 화면, 배포 URL, 데이터 저장·복원 확인을 추가해야 합니다. Function Calling과 MCP Server/GPT Actions는 선택 보너스로 아직 구현하지 않았습니다. 전체 허브는 시스템의 밝은/어두운 테마를 따르며 강사 화면의 수동 다크 모드 토글은 없습니다.

## 실행 순서 (Windows PowerShell)

Python 3.10 이상, Node.js가 필요합니다. 로컬 Firestore 테스트에는 Java 21과 Firebase CLI도 필요합니다. 아래 명령은 저장소 루트에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
Copy-Item backend/.env.example backend/.env
```

Java 21을 설치하거나 제공된 도구를 실행합니다. Firebase CLI는 공식 npm 패키지를 사용합니다.

```powershell
npm install -g firebase-tools
.\tools\setup-java.ps1
.\tools\start-emulator.ps1
```

다른 PowerShell 창에서 다음을 실행합니다.

```powershell
.\tools\start-local.ps1
```

- 전체 허브: `http://127.0.0.1:8010/`
- 강사 화면: `http://127.0.0.1:8010/education.html`
- Swagger: `http://127.0.0.1:8010/docs`

실제 GPT 답변을 사용하려면 `backend/.env`에 본인의 `OPENAI_API_KEY`를 설정합니다. 키는 브라우저 코드나 GitHub에 넣지 않습니다. 키가 없으면 AI 준비 안내를 표시하며 가짜 답변을 저장하지 않습니다.

## 데이터 가져오기

실제 자료는 저장소 밖이나 Git에서 제외된 `data/`에 보관합니다. 과정 JSON은 `course_records.json`, 교육일별 JSON은 `data_records.json` 형식입니다. 가져오기 도구는 ID·과정 연결·교육시간 합계를 검증하고 `--apply`를 지정했을 때만 Firestore에 없는 ID를 추가합니다. 기존 수정·삭제 기록을 덮어쓰지 않습니다.

실제 자료 없이 연습하려면 **가상의 120개 시계열 기록**을 로컬에서 생성할 수 있습니다. 결과는 `.local/`에만 저장하며 Git에 포함하지 않습니다.

```powershell
.\.venv\Scripts\python.exe backend/scripts/generate_demo.py
$env:FIREBASE_PROJECT_ID = 'demo-candy-a-academy'
$env:FIRESTORE_EMULATOR_HOST = '127.0.0.1:8088'
.\.venv\Scripts\python.exe backend/scripts/import_data.py --data-dir .local/demo-data
.\.venv\Scripts\python.exe backend/scripts/import_data.py --data-dir .local/demo-data --apply
```

가상 자료는 실제 교육 실적이나 실제 운영 검증 결과가 아닙니다. 생성기는 Firestore에 직접 쓰지 않습니다.

교육계획은 `backend/scripts/import_plans.py --file <비공개 JSON 경로> --apply`로 별도 `plans` 컬렉션에 저장합니다. 계획시간·예정인원은 실적에 합산하지 않고 보류·폐강·조건부 온라인 대체를 구분합니다. 개별 수업 상태나 재확인 날짜를 공개 코드에 고정하지 않습니다.

## 집계 기준

교육 0명·수료 인원 있음은 분석 인원을 수료 인원으로 기록하되 원본 수치를 보존합니다. 축제·에듀버스 만족도 0점은 미입력으로 구분해 평균에서 제외합니다. 승인 교육은 정상 교육이며 승인 근거가 없는 항목을 자동 승인으로 바꾸지 않습니다. 같은 날짜·교육명이라도 시간대가 다르면 각각 보존합니다. 인원 합계는 과정별 연인원이며 고유 인원이나 회차별 출석이 아닙니다.

## 검증

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
Set-Location ..
node --check frontend/app.js
node --check frontend/workspace.js
node frontend/build.mjs
```

테스트는 CRUD·요약·시간대 보존, 교재 경로 보호, 대화 저장·실패 처리, 계획과 실적 분리, 가상 자료 생성을 검증합니다. 실제 운영 데이터나 GPT 과금 호출을 사용하지 않습니다.

## 배포

1. Render에서 `render.yaml` 기준으로 백엔드를 구성합니다. `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `OPENAI_API_KEY`, `APP_ACCESS_TOKEN`, `ALLOWED_ORIGINS`를 비공개 환경변수로 설정합니다. 운영 환경에서 에뮬레이터 주소는 비웁니다.
2. Vercel의 Root Directory는 `frontend`입니다. `API_BASE_URL`에 Render HTTPS 주소를 입력합니다. `frontend/vercel.json`이 빌드와 출력 폴더를 설정합니다.
3. Render의 `ALLOWED_ORIGINS`에 실제 Vercel 주소를 넣습니다. 강사 화면의 ‘연결 설정’에서 개인 접속 키를 입력합니다. 접속 키는 배포 소스나 `API_BASE_URL`에 넣지 않습니다.
4. 실제 Firestore 데이터·대화 저장을 확인하고 제출용 캡처를 별도로 준비합니다. 공개 캡처에는 실제 교육 운영자료를 노출하지 않습니다.

로컬 교재는 `.local/library`에 보관합니다. Render 임시 파일 시스템에서는 영구 보관되지 않으므로 배포 전에 인증된 영구 저장소를 연결해야 합니다. 링크형 교재는 원본 서비스의 로그인·공유 조건을 따릅니다.

Firestore 직접 읽기·쓰기는 규칙으로 차단하고 서버의 Admin SDK로 접근합니다. 배포 환경에서는 개인 접속 키 설정이 필수입니다. 현재는 강사 개인용이며 여러 사용자의 계정별 데이터 분리는 구현하지 않았습니다.
