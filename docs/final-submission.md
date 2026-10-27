# 캔디A플렉스 에듀 융합에이전트 — 최종 제출 내용

날짜별 교육시간과 메모를 Firestore에 저장하고, 같은 기간의 통계 요약을 GPT 요청에 주입하여 데이터에 근거한 대화를 제공하는 강사 개인용 웹 애플리케이션입니다.

| 제출 항목 | 링크 |
|---|---|
| GitHub | https://github.com/silverhealthleader-source/M1-2-candyaflex-Agent-Hub |
| 프론트엔드 | https://candyaflex-edu-agent-hub.vercel.app/education |
| 백엔드 API | https://candyaflex-edu-api.onrender.com |
| Swagger | https://candyaflex-edu-api.onrender.com/docs |
| 공개용 최종 ZIP | [다운로드](../submission/M1-2-candyaflex-final-public-2026-10-27.zip) |

구현: 데이터 기반 AI 채팅·로딩 표시, date/value/memo CRUD와 목록·통계 갱신, 대화 자동/수동 저장·목록·전체 메시지 복원, Render/Vercel 배포 및 Swagger·환경변수 문서화.

백엔드는 FastAPI·Pydantic·Firestore·OpenAI SDK, 프론트는 HTML/CSS/JavaScript로 구성했습니다. 라우터·서비스·저장소를 분리하고 입력 검증·CORS·서버 비밀값 관리·입장 인증을 적용했습니다. 선택 기능으로 Function Calling·stdio MCP, 월별 그래프·JSON 내보내기·다크 모드·일정·교재 연결을 제공합니다.

2026-10-27 점검에서 백엔드 자동 테스트 74개, 사이트 인증 테스트 10개, 프론트 구문 검사·빌드를 통과했습니다. 별도로 실제 운영 API의 목록·통계 대조, 임시 CRUD와 통계 복원, 실제 GPT 답변 생성·통계 일치, Firestore 자동 저장·새 연결 재조회, Chrome 새로고침 후 대화 복원을 확인했습니다. 실제 운영 수치·문서 ID·기관·일정·화면 캡처는 이 공개 문서에 싣지 않습니다. 자동 테스트와 실제 실행은 서로 다른 근거입니다.

공개 ZIP은 코드·로고 등 공개 자산·일반 문서·실제 운영자료와 무관한 가상 데이터 120건을 담습니다. 가상 120건이 운영 DB 저장 건수의 증거는 아닙니다. [시연 절차](peer-review-walkthrough.md), [18개 항목의 설계·검증 방법](evaluation-evidence.md), [로컬 실행](../README.md#로컬-실행-windows-powershell)을 참고하세요. 공식 재평가 점수나 100점 확정을 뜻하지 않습니다.

운영 화면은 강사가 연결한 브라우저로 시연합니다. 공개 공용 인증키나 인증 우회 주소를 제공하지 않습니다. 인증번호·API 키·서비스 계정·실제 운영 원본·운영 캡처·발표 슬라이드와 대본은 공개 ZIP에 포함하지 않습니다.

## 제출 설명란에 복사할 내용

```text
캔디A플렉스 에듀 융합에이전트 — 최종 개인과제

GitHub: https://github.com/silverhealthleader-source/M1-2-candyaflex-Agent-Hub
프론트: https://candyaflex-edu-agent-hub.vercel.app/education
백엔드: https://candyaflex-edu-api.onrender.com
Swagger: https://candyaflex-edu-api.onrender.com/docs
최종 공개 ZIP: 저장소의 submission/M1-2-candyaflex-final-public-2026-10-27.zip

Firestore 시계열 데이터 요약을 활용한 실제 GPT 채팅, date/value/memo CRUD, 대화 저장·목록·복원, Render/Vercel 배포를 구현했습니다.
백엔드 74개·사이트 인증 10개 자동 테스트와 별도의 실제 API·Firestore·GPT·브라우저 대화 복원 검증을 수행했습니다.
공개 ZIP에는 코드·일반 문서·가상 데이터 120건을 포함합니다. 운영 증빙은 강사가 연결한 화면으로 시연하며 비밀값·운영 원본·발표자료는 공개하지 않습니다.
실행환경·검증 범위·시연 절차는 README와 docs 문서를 참고하세요. 공식 재평가 점수는 아직 확인하지 않았습니다.
```
