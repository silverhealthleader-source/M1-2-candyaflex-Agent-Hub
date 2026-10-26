# 사이트 접속 인증번호 설정

사이트 입장 번호는 교육운영 API의 APP_ACCESS_TOKEN과 별도입니다. 실제 값은 Vercel의 비공개 환경변수에만 입력합니다. GitHub·README·HTML·config.js·제출 ZIP에 넣지 않습니다.

## 직접 설정·변경하기

1. Vercel의 `candyaflex-edu-agent-hub` 프로젝트에서 **Environment Variables → Add Environment Variable**를 엽니다.
2. 이름은 **SITE_ACCESS_CODE**, 값은 본인이 정한 인증번호를 직접 입력합니다. 8~128자이며 생일·전화번호 대신 12자리 이상의 무작위 숫자나 영문·숫자 조합을 권장합니다. 채팅에는 보내지 않습니다.
3. **Production과 Preview**에 적용하고 **Secret** 유형으로 저장합니다.
4. 최신 배포를 **Redeploy**합니다. 환경변수 변경은 기존 배포에 소급 적용되지 않습니다.
5. 사이트에서 틀린 번호는 거절되고 올바른 번호로 입장되는지 확인합니다.

변경할 때도 같은 변수의 값을 수정·저장하고 Redeploy합니다. 새 배포에서는 이전 번호의 쿠키도 무효가 됩니다. 번호가 없거나 8자 미만이면 사이트는 열리지 않습니다. 기본 번호나 임시 공용 번호는 없습니다.

## 동작과 적용 범위

- [Vercel Routing Middleware](https://vercel.com/docs/routing-middleware)의 `proxy.entrypoint`로 캐시보다 먼저 모든 경로를 확인합니다. JS·CSS·이미지 직접 요청도 보호합니다. 기존 바닐라 HTML/CSS/JavaScript는 유지합니다.
- 인증번호는 서버에서 비교합니다. 브라우저에는 번호 대신 서명된 세션 토큰을 HttpOnly·Secure·SameSite=Strict·호스트 전용 쿠키로 전달합니다. 최대 8시간 뒤 재인증합니다. 메뉴의 **접속 인증 · 종료 → 접속 종료**로 현재 브라우저 인증을 끝냅니다.
- 같은 출처의 POST만 로그인·종료를 허용하며 위조·만료·다른 호스트의 쿠키, 외부 주소로의 리다이렉트를 거절합니다. 실행 인스턴스별로 10분간 실패 15회 후 요청을 제한합니다. 이 제한은 분산 환경 전체의 강제 제한을 보장하지 않습니다.
- Render 운영 배포는 프론트 파일을 제공하지 않습니다. `/health`, `/docs`, `/openapi.json`은 평가용이며 교육 데이터 API는 기존 Bearer 키로 보호합니다. 로컬 개발 화면 실행은 유지합니다.
- 현재 배포에 적용하는 보호이며 공개 GitHub 코드나 과거 공개 커밋·배포를 비공개로 바꾸는 기능은 아닙니다. 과거 배포 보호는 Vercel 설정 또는 오래된 배포 정리가 별도로 필요합니다.

## 검증·동료평가

`cd frontend` 후 `npm ci`, `npm test`로 인증 회귀 검사 10개를 실행합니다. 가상 테스트 값은 운영 번호가 아닙니다. 백엔드 테스트는 66개입니다. 동료평가 때는 승인된 비공개 경로로 번호를 공유하거나 본인이 직접 입력한 뒤, 교육 화면의 기존 개인 키로 연결해 시연합니다. 인증 추가 전의 제출 ZIP·캡처 시각과 이후 결과를 구분합니다.

로그인 페이지는 Referrer-Policy: same-origin을 사용해 브라우저의 정상 폼 POST가 Origin을 유지하도록 합니다. no-referrer는 폼 제출의 Origin을 null로 만들 수 있어 사용하지 않습니다. 서버는 외부 출처와 null Origin을 계속 거절합니다. HTTP 도구로 Origin을 수동 지정한 검사와 실제 브라우저 폼 제출 검사를 구분합니다. [브라우저 동작 근거](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referrer-Policy#effect_on_the_origin_header)
