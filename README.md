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
- 교육 실적 CRUD, 기간별 합계·평균·최댓값·최솟값·추세, JSON 내보내기, 대화 자동 저장·조회·삭제.

외부 링크 상태는 사용자 제공 원본의 분류입니다. 모든 외부 앱의 현재 동작을 검증했다는 뜻은 아닙니다.

## 구현 및 배포 상태

FastAPI·Pydantic, Firestore 접근, GPT Responses API 연결 코드, 바닐라 HTML/CSS/JS 화면과 Render·Vercel 설정을 준비했습니다. API 테스트는 격리된 가상 기록과 모의 AI 응답으로 검증합니다.

Render 무료 백엔드와 Vercel 프론트엔드를 배포했습니다. 인터넷 Firestore 연결, 접속 키 없는 조회 차단, 교육기록 추가·수정·삭제, 대화 저장·전체 메시지 복원을 검증했습니다. Vercel 화면에서 실제 GPT 답변과 후속 질문, 자동 저장을 확인했고 실제 프론트엔드 출처의 CORS 요청도 통과했습니다. 검증용 교육기록은 활성 목록에서 제외하고 원래 합계가 복원됐는지 확인했습니다. 실제 운영자료와 검증 화면은 비공개로 보관합니다.

선택 보너스로 GPT의 교육 요약 Function Calling, 같은 요약을 조회하는 로컬 stdio MCP 서버와 별도 클라이언트, 월별 그래프·추가 통계·JSON 내보내기·강사 화면 다크 모드 토글을 구현했습니다. GPT Actions는 MCP와의 중복 구현을 하지 않습니다. 교재는 연결된 항목부터 사용할 수 있으며 전체 교재 수집은 진행 중입니다.

배포된 [전체 허브](https://candyaflex-edu-agent-hub.vercel.app/)에서 ‘강사 에이전트 실행’을 누릅니다. [강사 화면](https://candyaflex-edu-agent-hub.vercel.app/education)의 ‘연결 설정’에 본인의 개인 접속 키를 입력하면 운영자료를 조회할 수 있습니다. 키는 현재 탭의 세션에만 저장합니다. 이 저장소는 강사 개인용이며 공개 체험 계정이나 다중 사용자 계정 분리는 제공하지 않습니다.

## 기술 스택

| 영역 | 구성 |
|---|---|
| Backend | Python 3.10+, FastAPI, Pydantic, Uvicorn |
| Database | Firebase Firestore, firebase-admin |
| AI | OpenAI Python SDK · Responses API · 읽기 전용 Function Calling |
| Frontend | HTML/CSS/JavaScript, 프레임워크 없음 |
| 배포 | Render 백엔드 · Vercel 정적 프론트엔드 |
| 선택 외부 채널 | 공식 MCP Python SDK 2.3.0 · 로컬 stdio 서버/별도 클라이언트 |

구조 설계와 여섯 학습목표 설명은 [과제 요구사항 점검](docs/assignment-review.md), 함수 스키마·호출 흐름과 MCP 실행은 [도구 연동](docs/tool-integration.md)에 정리했습니다.

## 환경변수

서버의 `backend/.env.example`을 복사해 비공개 `.env`를 만듭니다. Vercel에는 공개 가능한 `API_BASE_URL`만 설정합니다.

| 변수 | 위치·용도 |
|---|---|
| OPENAI_API_KEY | 서버 전용 실제 GPT 키 |
| OPENAI_MODEL | 서버 모델, 기본 `gpt-4.1-mini` |
| OPENAI_MAX_OUTPUT_TOKENS | 요청당 출력 제한, 기본 1000 |
| FIREBASE_PROJECT_ID | 서버 Firestore 프로젝트 ID |
| FIREBASE_SERVICE_ACCOUNT_JSON | 서버 서비스 계정 JSON 또는 파일 경로 |
| GOOGLE_APPLICATION_CREDENTIALS | 서비스 계정 파일 경로를 사용하는 대안 |
| FIRESTORE_EMULATOR_HOST | 로컬 에뮬레이터 전용. 인터넷 DB에서는 비움 |
| APP_ACCESS_TOKEN | 서버의 개인 접속 키, production 필수 |
| APP_ENV | 로컬 `development`, Render `production` |
| FIRESTORE_CACHE_SECONDS | 컬렉션 조회 재사용 시간, 기본 900초(0~3600). 대화 목록은 최대 30초 |
| ALLOWED_ORIGINS | Render에서 허용할 Vercel 출처, 쉼표 구분 |
| API_BASE_URL | Vercel 빌드의 Render 주소. 선택 MCP 클라이언트도 조회 대상 주소로 사용 |

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

격리된 자동 테스트 37개는 CRUD·요약·시간대 보존, 교재 경로 보호, 대화 저장·실패 처리, 계획과 실적 분리, 가상 자료 생성과 클라우드/에뮬레이터 연결 선택을 검증합니다. 도구 호출 결과 전달, 허용하지 않은 함수·인수 차단, 호출 횟수 제한도 검사합니다. 자동 테스트에는 실제 운영 데이터나 GPT 과금 호출을 사용하지 않습니다. 빈 `FIRESTORE_EMULATOR_HOST` 값은 클라우드 연결 전에 제거하여 SDK가 빈 에뮬레이터 주소에 연결하지 않도록 합니다.

## 배포

| 서비스 | 주소·상태 |
|---|---|
| Render 백엔드 | https://candyaflex-edu-api.onrender.com |
| Swagger | https://candyaflex-edu-api.onrender.com/docs |
| Vercel 프론트엔드 | https://candyaflex-edu-agent-hub.vercel.app/ |
| 강사 워크스페이스 | https://candyaflex-edu-agent-hub.vercel.app/education |
| 실제 GPT 답변 | 서버 전용 키 연결 및 배포 화면 검증 완료 |

Render 운영 API는 개인 접속 키 없이는 교육자료를 반환하지 않습니다. 운영자료와 검증 캡처는 이 공개 저장소에 포함하지 않습니다. 교재를 열면 메모와 버전 설명을 표시하며 원본 서비스의 로그인 조건을 유지합니다.

1. Render에서 `render.yaml` 기준으로 백엔드를 구성합니다. `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `OPENAI_API_KEY`, `APP_ACCESS_TOKEN`, `ALLOWED_ORIGINS`를 비공개 환경변수로 설정합니다. 운영 환경에서 에뮬레이터 주소는 비웁니다.
2. Vercel의 Root Directory는 `frontend`입니다. `API_BASE_URL`에 Render HTTPS 주소를 입력합니다. `frontend/vercel.json`이 빌드와 출력 폴더를 설정합니다.
3. Render의 `ALLOWED_ORIGINS`에 실제 Vercel 주소를 넣습니다. 강사 화면의 ‘연결 설정’에서 개인 접속 키를 입력합니다. 접속 키는 배포 소스나 `API_BASE_URL`에 넣지 않습니다.
4. 실제 Firestore 데이터·대화 저장을 확인하고 제출용 캡처를 별도로 준비합니다. 공개 캡처에는 실제 교육 운영자료를 노출하지 않습니다.

로컬 교재는 `.local/library`에 보관합니다. 현재 인터넷 배포는 링크형 교재를 사용하며 원본 서비스의 로그인·공유 조건을 따릅니다. 로컬 PDF 원본은 Render에 배포하지 않았습니다. PDF 원본도 인터넷에서 제공하려면 인증된 영구 저장소를 추가로 연결해야 합니다.

## 제출 스크린샷과 시연

실제 운영자료의 공개를 제외해 달라는 사용자 요청에 따라 캡처는 공개 GitHub에 올리지 않습니다. 비공개 제출 폴더의 `README.md`에 아래 세 종류의 실제 실행 화면을 삽입합니다.

| 필수 증빙 | 확인할 내용 |
|---|---|
| 채팅 + 요약 | 질문·실제 GPT 답변과 DATA CONTEXT의 기간·개수·통계·추세 |
| 데이터 관리 | 검증용 기록 추가/수정 결과가 목록에 표시되고 제거 후 원래 집계로 복원됨 |
| 대화 기록 | 이전 대화 목록과 ‘대화 이어가기’ 후 전체 메시지 재표시 |

평가자가 실제 앱을 조회하려면 개인 접속 키가 필요합니다. 공개 체험 계정을 만들지 않았으며 실제 키를 README에 기재하지 않습니다. 키 전달과 운영자료가 포함된 캡처 제출은 승인된 비공개 경로 또는 직접 시연으로 진행합니다.

Firestore 전체 컬렉션을 화면 이동마다 다시 읽지 않도록 서버 프로세스에서 기본 15분 동안 조회 결과를 재사용합니다. 이 API를 통한 추가·수정·삭제는 DB 저장이 성공한 뒤 캐시에도 즉시 반영합니다. 외부 콘솔이나 가져오기 도구로 바꾼 자료는 캐시 만료 또는 서버 재시작 후 반영될 수 있습니다. 대화 목록은 최대 30초만 재사용합니다. 사용량 제한 오류가 발생하면 안내와 60초 재조회 대기를 적용하며, 오류를 빈 데이터로 저장하지 않습니다. 캐시는 서버 재시작 후 새로 읽으며 DB를 대신하는 별도 원본이 아닙니다.

Firestore 무료 일일 한도와 초기화 기준은 [공식 사용량 안내](https://firebase.google.com/docs/firestore/quotas)를 참고합니다. 검증·시연 중 전체 기록을 반복해서 직접 조회하면 무료 한도를 소진할 수 있습니다.

Firestore 직접 읽기·쓰기는 규칙으로 차단하고 서버의 Admin SDK로 접근합니다. 배포 환경에서는 개인 접속 키 설정이 필수입니다. 현재는 강사 개인용이며 여러 사용자의 계정별 데이터 분리는 구현하지 않았습니다.
