# 캔디A플렉스 에듀 융합에이전트

날짜별 교육시간과 수업 메모를 관리하고, 저장된 통계를 근거로 AI와 대화하는 강사 개인용 서비스입니다. 월별 시간표·과목별 교재·역할별 캐릭터를 함께 제공합니다. 동료평가 대상인 네 가지 핵심 기능은 **강사 워크스페이스**에 있습니다.

| 접속 | URL |
|---|---|
| 평가용 강사 워크스페이스 | https://candyaflex-edu-agent-hub.vercel.app/education |
| 전체 아카데미 허브 | https://candyaflex-edu-agent-hub.vercel.app/ |
| Render 백엔드 | https://candyaflex-edu-api.onrender.com |
| Swagger UI | https://candyaflex-edu-api.onrender.com/docs |

운영 화면은 개인 접속 키로 보호합니다. **실제 교육자료·교재 PDF·운영 캡처·키는 공개 GitHub에 포함하지 않습니다.** 평가 시에는 강사가 연결한 화면을 시연하거나 승인된 비공개 경로의 제출 자료를 사용합니다. 개인 접속 키를 공개 README에 기재하지 않습니다.

## 필수 네 가지 기능

| 기능 | 구현과 화면 |
|---|---|
| 데이터 기반 AI 채팅 | 사용자 질문 → 서버 통계 → 시스템 지시문에 요약 주입 → GPT Responses API → 답변·자동 저장. 채팅 로딩, 기간·개수·평균·최대/최소·교육시간 추세 표시 |
| 데이터 CRUD | `date`, `value`(해당 교육일의 시간), `memo`를 추가·수정·삭제하고 목록·요약 즉시 갱신. 삭제는 원본 보존 후 활성 목록과 집계에서 제외 |
| 대화 기록 | 자동 저장 및 POST 저장 API, 목록, 특정 대화 전체 messages 조회·화면 복원, 삭제 |
| 배포·문서화 | Render FastAPI, Vercel 바닐라 프론트엔드, Swagger, 로컬 실행·환경변수·제출 안내 |

전체 허브의 외부 링크 목록과 별개로 위 네 가지 기능을 하나의 강사 애플리케이션에서 실행합니다. 외부 링크 전체의 최신 동작을 보장하는 것으로 표시하지 않습니다.

## 기술 스택과 구조

- Python 3.10+ / FastAPI / Pydantic / Uvicorn
- Firebase Firestore / firebase-admin / python-dotenv
- OpenAI Python SDK Responses API, 읽기 전용 Function Calling
- HTML / CSS / JavaScript. 프론트엔드 프레임워크 없음
- Render 백엔드, Vercel 프론트엔드

```text
backend/app/
  main.py             앱·CORS·접속 보호·예외 처리
  models.py           Pydantic 요청 검증
  routers/            data / conversations / chat / materials / plans
  services.py         날짜별 통계·GPT 컨텍스트 주입
  database.py         Firestore 접근·조회 캐시·원본 보존 삭제
  planning.py         실적과 구분한 교육계획·대체 일정
  material_storage.py 비공개 PDF 보관·원본 해시 검증
backend/scripts/      데이터 가져오기·가상 자료·배포 점검
backend/tests/        실제 키·DB와 분리한 자동 테스트
frontend/             바닐라 화면·정적 빌드
```

Firestore의 필수 컬렉션은 `data`, `conversations`입니다. `courses`, `plans`, `materials`, `material_files`는 과정별 집계·일정·교재 확장입니다. 라우터는 요청·응답, 서비스는 집계·AI, 저장소는 DB 접근을 담당합니다.

## 필수 API

| 메서드 | 경로 | 동작 |
|---|---|---|
| POST / GET | `/api/data` | 데이터 추가 / 목록 |
| PUT / DELETE | `/api/data/{key}` | 수정 / 원본 보존 삭제 |
| GET | `/api/data/summary` | 프롬프트와 화면에서 쓰는 공통 요약 |
| POST / GET | `/api/conversations` | 대화 저장 / 목록 |
| GET / DELETE | `/api/conversations/{key}` | 전체 메시지 불러오기 / 삭제 |
| POST | `/api/chat` | 실제 GPT 대화와 자동 저장 |

`key`는 과제의 `{id}`와 같은 문서 식별자입니다. 대화 목록은 `messages_included=false`를 명시하고, 상세 조회에서 전체 messages를 제공합니다. 데이터 요약은 같은 Python 집계 함수를 직접 재사용하며 서버가 자기 HTTP API를 다시 호출하지 않습니다.

## 환경변수

서버에서 `backend/.env.example`을 비공개 `backend/.env`로 복사합니다. Vercel에는 공개 가능한 API 서버 주소만 설정합니다.

| 변수 | 용도 |
|---|---|
| `OPENAI_API_KEY` | 서버 전용 GPT 키 |
| `OPENAI_MODEL` | 기본 `gpt-4.1-mini` |
| `OPENAI_MAX_OUTPUT_TOKENS` | 출력 제한, 기본 1000 |
| `FIREBASE_PROJECT_ID` | Firestore 프로젝트 |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | 서버 전용 서비스 계정 JSON 또는 파일 경로 |
| `GOOGLE_APPLICATION_CREDENTIALS` | 서비스 계정 파일 경로를 쓰는 대안 |
| `APP_ACCESS_TOKEN` | 개인 접속 키, production 필수 |
| `APP_ENV` | 로컬 `development`, Render `production` |
| `ALLOWED_ORIGINS` | 허용 Vercel 출처, 쉼표 구분 |
| `API_BASE_URL` | Vercel 빌드·선택 MCP 클라이언트의 API 주소 |
| `FIRESTORE_EMULATOR_HOST` | 로컬 에뮬레이터 전용. Render에서는 비움 |
| `FIRESTORE_CACHE_SECONDS` | 조회 캐시, 기본 900초. 대화 목록 최대 30초 |

CORS는 인증을 대신하지 않습니다. 키는 환경변수로 관리하고 URL·코드·공개 캡처에 넣지 않습니다. Firestore 브라우저 직접 읽기·쓰기는 규칙으로 차단하며 서버 Admin SDK로 접근합니다.

## 로컬 실행 (Windows PowerShell)

Python 3.10+, Node.js가 필요합니다. 에뮬레이터는 Java 21과 공식 Firebase CLI를 사용합니다. 저장소 루트에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
Copy-Item backend/.env.example backend/.env
npm install -g firebase-tools
.\tools\setup-java.ps1
.\tools\start-emulator.ps1
```

위 에뮬레이터 창을 유지하고, 다른 PowerShell 창의 같은 저장소 루트에서 **실제 자료와 무관한 가상 120개 기록**을 생성·가져옵니다.

```powershell
.\.venv\Scripts\python.exe backend/scripts/generate_demo.py
$env:FIREBASE_PROJECT_ID = 'demo-candy-a-academy'
$env:FIRESTORE_EMULATOR_HOST = '127.0.0.1:8088'
.\.venv\Scripts\python.exe backend/scripts/import_data.py --data-dir .local/demo-data
.\.venv\Scripts\python.exe backend/scripts/import_data.py --data-dir .local/demo-data --apply
.\tools\start-local.ps1
```

- 강사 화면: `http://127.0.0.1:8010/education.html`
- 전체 허브: `http://127.0.0.1:8010/`
- Swagger: `http://127.0.0.1:8010/docs`

실제 GPT 대화에는 본인의 서버 전용 OpenAI 키가 필요합니다. 키가 없으면 준비 안내를 표시하며 가짜 AI 답변을 저장하지 않습니다. 가상 자료는 실제 교육 실적이나 운영 검증 결과가 아닙니다.

실제 자료는 저장소 밖이나 Git에서 제외한 `data/`에 준비합니다. `import_data.py --data-dir <비공개 폴더> --apply`는 검증 후 없는 ID만 추가하며 기존 수정·삭제 상태를 덮어쓰지 않습니다.

## 검증과 재현

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
Set-Location ..
node --check frontend/app.js
node --check frontend/workspace.js
node frontend/build.mjs
```

자동 테스트 **45개**는 CRUD·대화·요약·Function Calling·일정 분리·PDF 저장과 손상 검증을 확인합니다. `tests/conftest.py`가 해당 pytest 프로세스의 개인 키·DB 연결 설정을 비워 테스트 전용 저장소와 모의 AI를 사용합니다. `.env` 파일 자체는 수정하지 않습니다.

운영 배포의 읽기 전용 점검은 아래 명령으로 재현합니다. `APP_ACCESS_TOKEN`은 비공개 `.env` 또는 환경변수에만 저장합니다.

```powershell
.\.venv\Scripts\python.exe backend/scripts/check_deployment.py --api-url https://candyaflex-edu-api.onrender.com --origin https://candyaflex-edu-agent-hub.vercel.app
```

Swagger·필수 API 스키마·CORS·접속 보호·100개 이상 데이터·입력 검증·대화 상세·프론트 연결을 확인하고 `.local/verification/deployment-readiness.json`에 비공개 결과를 저장합니다. 이 점검은 실제 GPT 호출이나 데이터 변경을 하지 않습니다. 실제 채팅·CRUD·복원 실행은 별도 화면 증빙으로 확인합니다.

## 배포와 운영

Render는 `render.yaml`의 `backend` 루트와 Python 시작 명령을 사용합니다. 서버 비공개 환경변수와 실제 Vercel 출처를 설정합니다. Vercel Root Directory는 `frontend`, 빌드 환경변수는 `API_BASE_URL`입니다. `frontend/vercel.json`이 빌드와 출력 폴더를 지정합니다.

강사 화면의 **연결 설정**에 개인 접속 키를 입력합니다. 키는 현재 탭 세션에 보관합니다. Swagger는 **Authorize**에서 같은 키를 사용합니다. 무료 Render의 첫 연결은 늦을 수 있으며 화면에서 대기·재시도를 안내합니다.

API를 통한 저장은 캐시에도 즉시 반영합니다. 외부 가져오기 도구의 변경은 기본 15분의 캐시 만료 또는 서버 재시작 후 표시될 수 있습니다. 한도 오류는 별도 503 안내로 처리하며 빈 데이터로 대체하지 않습니다.

## 데이터 기준과 추가 기능

교육 0명이고 수료 인원이 있으면 수료 인원을 분석 인원으로 사용하되 원본 수치를 보존합니다. 축제·에듀버스 만족도 0점은 미입력으로 구분합니다. 교육생 합계는 과정별 연인원입니다. 같은 날짜·교육명이어도 서로 다른 수업은 보존하며, 확인된 동시간대 별개 수업을 자동 병합하지 않습니다. 계획은 실시·승인과 구분해 실적에 합산하지 않습니다.

캔디온(일정)·캔디북(교재)·캔디빛(분석)·캔디봄(보고서)의 3D 전신 PNG와 실행 상태 애니메이션, 월별 블록, 그래프·추가 통계·JSON 내보내기·다크 모드를 제공합니다. 동작 줄이기 설정을 존중합니다. 사용자 제공 로고와 민들레 홈 배경, 투컬러 입체 메뉴를 적용했습니다.

선택한 PDF는 접속 보호된 Firestore 파일 보관 기능으로 온라인 열람·다운로드합니다. 파일당 32 MiB, 전체 128 MiB의 개인용 한도를 적용하며 Render 임시 디스크는 검증된 캐시입니다. Canva 원본의 공유·로그인 조건은 유지합니다. [PDF 안내](docs/pdf-library.md)를 참고하세요.

## 동료평가 제출 자료

[필수 항목·여섯 학습목표 설명](docs/assignment-review.md), [제출 체크리스트](docs/submission-checklist.md), [Function Calling·MCP 호출 흐름](docs/tool-integration.md)을 제공합니다.

실제 자료가 담긴 **채팅+요약, CRUD 동작, 대화 목록+복원** 캡처와 실행환경 README는 비공개 제출 ZIP에 포함합니다. 공개 소스에서 접근 키나 실제 운영자료를 찾을 수 없다는 이유를 문서에 명시했습니다. 평가자는 강사의 연결된 화면을 시연받거나 본인의 로컬 가상 자료로 실행할 수 있습니다.

현재는 강사 개인용입니다. 여러 사용자 계정 분리, 다른 PC에만 있는 미공유 교재 수집은 확장 범위입니다. MCP는 별도 stdio 클라이언트로 호출을 검증하며 Codex·Cowork 영구 설치를 뜻하지 않습니다. GPT Actions는 MCP와 중복 구현하지 않습니다.
