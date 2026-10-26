# 캔디A플렉스 에듀 융합에이전트

날짜별 교육시간과 수업 메모를 관리하고, 저장된 통계를 근거로 AI와 대화하는 강사 개인용 서비스입니다. 월별 시간표·과목별 교재·역할별 캐릭터를 함께 제공합니다. 동료평가 대상인 네 가지 핵심 기능은 **강사 워크스페이스**에 있습니다.

| 접속 | URL |
|---|---|
| 평가용 강사 워크스페이스 | https://candyaflex-edu-agent-hub.vercel.app/education |
| 전체 아카데미 허브 | https://candyaflex-edu-agent-hub.vercel.app/ |
| Render 백엔드 | https://candyaflex-edu-api.onrender.com |
| Swagger UI | https://candyaflex-edu-api.onrender.com/docs |

운영 화면은 개인 접속 키로 보호합니다. **실제 교육자료·교재 PDF·운영 캡처·키는 공개 GitHub에 포함하지 않습니다.** 평가 시에는 강사가 연결한 화면을 시연하거나 승인된 비공개 경로의 제출 자료를 사용합니다. 개인 접속 키를 공개 README에 기재하지 않습니다.

사전평가 보완 설명은 [18개 평가 항목과 검증 방법](docs/evaluation-evidence.md)에 정리했습니다. **코드 구현, 자동 테스트, 실제 배포 실행 기록은 서로 다른 근거**입니다. 비공개 제출 ZIP의 `실행검증.md`에는 실제 HTTP 요청·응답, Firestore 직접 재조회, 대화 전체 메시지 복원 결과를 Markdown으로 수록하고 `screenshots/`의 실제 화면을 연결합니다. 이미지가 분석되지 않는 평가에서도 실행 결과의 본문을 읽을 수 있게 구성했습니다. 이 설명은 점수나 통과를 보장하는 선언이 아닙니다.

## 사이트 입장 인증

Vercel의 서버 전용 비공개 환경변수 `SITE_ACCESS_CODE`로 사이트 입장 번호를 직접 설정합니다. 실제 값은 코드·GitHub·브라우저 설정 파일에 포함하지 않습니다. 번호가 없으면 사이트를 열지 않으며 교육운영 API의 기존 개인 접속 키 보호도 유지합니다. [설정·변경·접속 종료 안내](docs/site-access.md)를 참고하세요. Render 운영 배포는 API·Swagger를 제공하고 프론트 화면은 인증된 Vercel에서만 제공합니다.

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

`data/{id}`는 **교육일별 실적 문서**로 `date`(ISO 날짜), `value`(시간), `memo`, 과목·방식·장소, 생성/수정 시각, `deleted`를 저장합니다. `conversations/{id}`는 **한 대화 문서**로 `title`, `messages:[{role,content}]`, `agent_id`, 생성/수정 시각, `deleted`를 저장하며 `/api/chat` 자동 저장은 `tool_calls`와 `save_mode=auto`도 기록합니다. 수동 저장은 `save_mode=manual`로 구분합니다. 임의 UUID 문서 ID를 사용하고 원본 가져오기는 재실행 가능한 결정적 ID를 사용합니다.

두 컬렉션을 분리한 이유는 데이터 수정 때 메시지 배열을 다시 쓰지 않고, 대화 목록을 볼 때 전체 교육 원문을 반환하지 않기 위해서입니다. 현재 개인 규모에서는 컬렉션을 서버 캐시에 읽고 Python에서 날짜·방식·검색어로 필터링합니다. **Firestore의 `where(date)` 조회·DB 수준 페이지네이션을 구현했다고 주장하지 않습니다.** 데이터가 커지면 날짜 범위 쿼리·정렬·인덱스로 확장할 수 있습니다. 대화는 전체 복원이 빈번하여 메시지 배열을 한 문서에 보관하며 저장은 최대 100메시지, GPT 입력은 최근 12메시지로 제한합니다. 상세 설계와 조회 경로는 [평가 설명](docs/evaluation-evidence.md#8-firestore-컬렉션-설계)에 있습니다.

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

### 데이터 요약 응답 스키마와 컨텍스트 주입

| 필드 | 형식·의미 |
|---|---|
| `period.start/end` | ISO 날짜 또는 null. 선택한 기록의 최소/최대 날짜 |
| `count` / `teaching_days` / `course_count` | 기록 건수 / 서로 다른 교육일 / 과정 수. 서로 다른 지표 |
| `metrics.total/average/max/min` | 시간 합계 / 기록 1건당 평균 / 최대 / 최소 |
| `monthly:[{month,hours}]` | 기록이 있는 월의 시간 합계 |
| `trend` | 최근 두 기록 월의 시간 변화율. 비교 자료가 부족하면 percent=null |
| `students` | 과정별 연인원. 고유 인원 아님 |
| `planning` | 별도 계획 요약. 실제 시간과 합산하지 않음 |

아래는 **가상 기록 2건의 대표 필드 예시**이며 운영 실행 증거가 아닙니다.

```json
{"period":{"start":"2026-10-01","end":"2026-10-02"},"count":2,"teaching_days":2,"course_count":2,"metrics":{"total":3,"average":1.5,"max":2,"min":1,"unit":"hours"},"monthly":[{"month":"2026-10","hours":3}],"trend":{"label":"비교할 기록이 부족합니다","percent":null,"metric":"education_hours"}}
```

서버는 기간으로 선택한 기록을 `build_summary()`로 계산한 뒤 `generate_answer()`의 `instructions`에 JSON을 붙입니다. 모델 학습을 바꾸는 과정이 아니라 **요청 시 참고 맥락을 제공하는 과정**입니다. 통계가 일관되고 최신 조회값을 쓰기 쉬운 장점이 있지만, 긴 요약은 입력 토큰·지연을 늘리며 원본 누락·잘못된 입력까지 교정하지 못합니다. 모델 답변의 수치도 검산해야 합니다. `planning.sessions`는 최대 80개이며 `sessions_truncated`로 생략을 알립니다. 원본 메모 전체를 일괄 전송하지는 않지만, 개인정보가 담긴 과목명이나 사용자 질문은 외부 AI 요청에 포함될 수 있으므로 사람 이름·연락처를 입력하지 않는 운영 기준을 둡니다. 연락처·이메일·주민번호 형식·API 키·비공개 키 블록은 AI 전송 경계에서 형식에 따라 가립니다. 이름·주소 등 모든 개인정보를 자동 탐지하는 기능은 아닙니다.

컨텍스트는 데이터 구역과 규칙을 구분하고 그 안의 문구를 명령으로 실행하지 않도록 지시합니다. 읽기 전용 도구 이름과 빈 인수 스키마도 검증합니다. 이는 모든 프롬프트 공격을 차단한다는 보장은 아닙니다. [OpenAI 공식 텍스트 생성 문서](https://developers.openai.com/api/docs/guides/text)의 `instructions` 사용 방식과 [Function Calling 흐름](https://developers.openai.com/api/docs/guides/function-calling)을 참고했습니다.

### 요청 검증과 재현 예시

`DataCreate`는 `date`를 날짜로 파싱하고 `value`를 0~24의 유한수로 제한합니다. `memo`는 공백 제거 후 1~2000자, 과목은 1~200자, 장소는 최대 300자, 인원은 0~100000의 정수입니다. 미정의 필드는 거부합니다. `PUT`는 부분 변경만 받으며 원본 과정의 인원 중복 수정은 422입니다. 예를 들어 `value=-1` 요청은 **저장 전에 422**가 됩니다. 정상 POST 응답은 입력 필드와 `id`, `unit`, 생성/수정 시각, `source`, `approval_status`, `deleted`를 포함합니다. 상세 요청·응답 예시는 [평가 설명](docs/evaluation-evidence.md#9-요청-검증과-응답-예시)에 있습니다.

다음 명령은 **자신의 로컬 가상 데이터**에서 사용합니다. 접속 키는 기존 비공개 환경변수를 참조하며 출력하지 않습니다.

```powershell
$taskHeaders = @{Authorization = "Bearer $env:APP_ACCESS_TOKEN"}
Invoke-RestMethod -Uri 'http://127.0.0.1:8010/api/data/summary?date_from=2026-01-01&date_to=2026-12-31' -Headers $taskHeaders
$taskBody = @{date='2026-10-01';value=1;memo='가상 CRUD 실습';course_title='가상 수업';mode='기타';students=0} | ConvertTo-Json
$taskRecord = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8010/api/data' -Headers $taskHeaders -ContentType 'application/json; charset=utf-8' -Body $taskBody
Invoke-RestMethod -Method Put -Uri "http://127.0.0.1:8010/api/data/$($taskRecord.id)" -Headers $taskHeaders -ContentType 'application/json' -Body '{"value":2}'
Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8010/api/data/$($taskRecord.id)" -Headers $taskHeaders
```

대화 자동 저장은 `/api/chat` 응답 생성 후 수행합니다. 수동 저장은 별도 `POST /api/conversations`이고 현재 웹 화면은 자동 저장과 ‘대화 저장’ 버튼의 수동 재저장을 제공합니다. 수동 저장은 `title/messages`를 받으며 실제 GPT를 호출하지 않습니다. 기존 대화의 서버 생성 `tool_calls`·생성 시각·담당 에이전트를 유지하고, 메시지 변경 여부를 `messages_edited_manually`로 표시합니다. `id`를 주면 기존 대화를 갱신하고 생략하면 새 문서를 만듭니다. 자동 저장의 `tool_calls`는 이름·인수·호출 근거·분석 기간을 기록하며 도구의 전체 결과 JSON이나 OpenAI 내부 응답 ID 전체를 저장하는 방식은 아닙니다. [자동·수동 저장 타이밍과 형식](docs/evaluation-evidence.md#13-대화-저장-타이밍과-형식)을 참고하세요.

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

자동 테스트 **66개**는 CRUD·대화·요약·Function Calling·일정 분리·PDF 저장과 손상 검증을 확인합니다. `tests/conftest.py`가 해당 pytest 프로세스의 개인 키·DB 연결 설정을 비워 테스트 전용 저장소와 모의 AI를 사용합니다. `.env` 파일 자체는 수정하지 않습니다.

운영 배포의 읽기 전용 점검은 아래 명령으로 재현합니다. `APP_ACCESS_TOKEN`은 비공개 `.env` 또는 환경변수에만 저장합니다.

```powershell
.\.venv\Scripts\python.exe backend/scripts/check_deployment.py --api-url https://candyaflex-edu-api.onrender.com --origin https://candyaflex-edu-agent-hub.vercel.app
```

Swagger·필수 API 스키마·CORS·접속 보호·100개 이상 데이터·입력 검증·대화 상세·프론트 연결을 확인하고 `.local/verification/deployment-readiness.json`에 비공개 결과를 저장합니다. 이 읽기 전용 점검 자체는 실제 GPT 호출이나 데이터 변경을 하지 않습니다. 최종 비공개 ZIP에는 별도의 실제 채팅·390px 화면 CRUD·수동 저장·복원 증빙과 18개 항목별 검증표를 함께 제공합니다.

## 배포와 운영

Render는 `render.yaml`의 `backend` 루트와 Python 시작 명령을 사용합니다. 서버 비공개 환경변수와 실제 Vercel 출처를 설정합니다. Vercel Root Directory는 `frontend`, 빌드 환경변수는 `API_BASE_URL`입니다. `frontend/vercel.json`이 빌드와 출력 폴더를 지정합니다.

강사 화면의 **연결 설정**에 개인 접속 키를 입력합니다. 키는 현재 탭 세션에 보관합니다. Swagger는 **Authorize**에서 같은 키를 사용합니다. 무료 Render의 첫 연결은 늦을 수 있으며 화면에서 대기·재시도를 안내합니다.

API를 통한 저장은 캐시에도 즉시 반영합니다. 외부 가져오기 도구의 변경은 기본 15분의 캐시 만료 또는 서버 재시작 후 표시될 수 있습니다. 한도 오류는 별도 503 안내로 처리하며 빈 데이터로 대체하지 않습니다.

운영 CORS 예시는 `ALLOWED_ORIGINS=https://candyaflex-edu-agent-hub.vercel.app`이며, 로컬은 `http://127.0.0.1:8010,http://localhost:8010,http://127.0.0.1:4173`입니다. staging 출처는 실제 생성한 주소만 추가합니다. 허용 출처 OPTIONS와 미허용 출처의 응답 헤더를 각각 검증합니다.

비밀값 교체는 새 키 준비 → Render 비공개 Environment 갱신·재배포 → 보호 API·Firestore·작은 AI 호출 확인 → 이전 키 폐기 순서입니다. 긴급 유출 때는 이전 키 폐기를 우선합니다. Firebase JSON도 새 연결을 확인하고 이전 키를 폐기합니다. `APP_ACCESS_TOKEN`을 바꾸면 브라우저도 새 접속 키로 다시 연결합니다. 이번 문서 보완에서 실제 키를 교체한 것은 아닙니다.

콜드스타트 대비로 발표 5분 전 `/health`와 강사 화면 요약을 열어 연결을 확인합니다. 연결 8초 경과 안내와 65초 타임아웃 안내가 구현되어 있습니다. 자동 주기적 워밍업은 미구현이고 이번 일반 접속 성공을 강제 슬립 후 첫 요청 지연 검증으로 표현하지 않습니다. [운영 절차와 한계](docs/evaluation-evidence.md#15-콜드스타트-대응)를 참고하세요.

## 데이터 기준과 추가 기능

교육 0명이고 수료 인원이 있으면 수료 인원을 분석 인원으로 사용하되 원본 수치를 보존합니다. 축제·에듀버스 만족도 0점은 미입력으로 구분합니다. 교육생 합계는 과정별 연인원입니다. 같은 날짜·교육명이어도 서로 다른 수업은 보존하며, 확인된 동시간대 별개 수업을 자동 병합하지 않습니다. 계획은 실시·승인과 구분해 실적에 합산하지 않습니다.

캔디온(일정)·캔디북(교재)·캔디빛(분석)·캔디봄(보고서)의 3D 전신 PNG와 실행 상태 애니메이션, 월별 블록, 그래프·추가 통계·JSON 내보내기·다크 모드를 제공합니다. 동작 줄이기 설정을 존중합니다. 사용자 제공 로고와 민들레 홈 배경, 투컬러 입체 메뉴를 적용했습니다.

선택한 PDF는 접속 보호된 Firestore 파일 보관 기능으로 온라인 열람·다운로드합니다. 파일당 32 MiB, 전체 128 MiB의 개인용 한도를 적용하며 Render 임시 디스크는 검증된 캐시입니다. Canva 원본의 공유·로그인 조건은 유지합니다. [PDF 안내](docs/pdf-library.md)를 참고하세요.

## 동료평가 제출 자료

발표 슬라이드·발표자 대본·메모는 개인 연습 및 비공개 동료평가 제출자료로 별도 보관합니다. 공개 저장소와 서비스 배포에는 포함하지 않습니다. 공개 저장소는 과제 코드·필수 실행 설명·서비스 및 Swagger 주소를 제공합니다.

[필수 항목·여섯 학습목표 설명](docs/assignment-review.md), [제출 체크리스트](docs/submission-checklist.md), [Function Calling·MCP 호출 흐름](docs/tool-integration.md)을 제공합니다.

실제 자료가 담긴 **채팅+요약, CRUD 동작, 대화 목록+복원** 캡처와 실행환경 README는 비공개 제출 ZIP에 포함합니다. 공개 소스에서 접근 키나 실제 운영자료를 찾을 수 없다는 이유를 문서에 명시했습니다. 평가자는 강사의 연결된 화면을 시연받거나 본인의 로컬 가상 자료로 실행할 수 있습니다.

현재는 강사 개인용입니다. 여러 사용자 계정 분리, 다른 PC에만 있는 미공유 교재 수집은 확장 범위입니다. MCP는 별도 stdio 클라이언트로 호출을 검증하며 Codex·Cowork 영구 설치를 뜻하지 않습니다. GPT Actions는 MCP와 중복 구현하지 않습니다.

## 최종 시연에서 확인할 추가 보완

‘대화 저장’ 버튼은 현재 자동 저장된 대화를 다시 저장하며 새 GPT 요청을 만들지 않습니다. 도구 이력이 유지되는지 서버·Firestore 재조회로 확인합니다. 연락처·이메일 형식을 질문에 넣으면 `[연락처 가림]`·`[이메일 가림]`으로 바꿔 AI 입력과 대화 저장에 사용하고, 응답의 `user_message`와 `privacy_notice`로 화면에도 알립니다. 한국어 조사와 붙은 이메일도 회귀 테스트에 포함합니다. 개인정보 전체를 탐지하거나 모든 공격을 막는다는 의미는 아닙니다.

좁은 화면은 390px CSS 뷰포트의 실제 배포 페이지에서 메뉴 이동·16px 입력·44px 이상 주요 버튼·추가/수정/삭제를 검증합니다. 이는 브라우저 반응형 검증이며 휴대폰 하드웨어 터치 검증과 구분합니다. 통과 여부는 제출 ZIP의 최신 `18개항목-검증결과.md`와 `실행검증.md`에서 실행 시각·방법·화면을 대조합니다. 
