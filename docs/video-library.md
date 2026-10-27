# 비공개 MP4 연결

허브의 **AI 크리에이터 → 카페 아띠랑 AI 광고 → 아띠랑 로고송 재생**에서 영상 열람 창을 엽니다. 자료실의 동일 항목에서도 재생할 수 있습니다. 재생·일시정지·음량·전체 화면은 브라우저 영상 컨트롤을 사용하며 창을 닫으면 재생을 멈춥니다.

원본은 PC에 보존하고 웹 사본을 H.264/AAC MP4로 준비합니다. 파일은 32 MiB 이하, 기존 비공개 자료 보관 한도는 합계 128 MiB입니다. `backend/scripts/publish_material_video.py`로 명시적으로 선택한 영상만 기존 Firestore `materials`와 `material_files`에 보관합니다. 파일 본문과 인증키는 GitHub에 포함하지 않습니다.

`GET /api/materials/{id}/file`은 기존 개인 접속 키 인증을 적용하며 `video/mp4`, `private, no-store`, 부분 응답(Range)을 제공합니다. 프론트는 인증 헤더로 파일을 받은 뒤 임시 Blob URL로 재생하므로 URL에 키를 넣지 않습니다. `material` 쿼리 값은 자료 식별자이며 인증정보가 아닙니다.

설정된 비공개 환경에서 실행 예:

```powershell
python backend/scripts/publish_material_video.py path/to/web-video.mp4 --id my-video --subject "홍보 영상" --title "브랜드 로고송" --duration-seconds 25.31
# 검증 결과를 확인한 뒤 같은 명령 끝에 --apply를 붙여 비공개 저장
```
