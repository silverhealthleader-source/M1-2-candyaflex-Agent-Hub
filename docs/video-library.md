# MP4 영상 재생

허브의 **AI 크리에이터 → 카페 아띠랑 AI 광고**에는 브랜드 필름·10초 광고·로고송 버튼이 있습니다. 사용자의 PC 보관 선택에 따라 처음에는 해당 PC의 MP4를 직접 선택해 재생합니다. 선택한 영상은 서버나 Firebase에 전송하지 않으며 GitHub에도 포함하지 않습니다.

같은 탭에서는 각 버튼에 선택한 파일을 기억합니다. 새로고침하거나 다른 기기에서 열면 다시 선택합니다. 재생·일시정지·음량·전체 화면은 브라우저 영상 컨트롤을 사용하며 창을 닫으면 재생을 멈춥니다. 이 기능은 File과 임시 Blob URL만 사용하며 영상 본문을 브라우저 영구 저장소에 복사하지 않습니다.

## 선택적 서버 보관 기능

아래 기능은 별도로 온라인 저장을 명시적으로 승인한 파일에만 적용합니다. 현재 카페 아띠랑 영상은 해당하지 않습니다.

원본은 PC에 보존하고 웹 사본을 H.264/AAC MP4로 준비합니다. 파일은 32 MiB 이하, 기존 비공개 자료 보관 한도는 합계 128 MiB입니다. `backend/scripts/publish_material_video.py`로 명시적으로 선택한 영상만 기존 Firestore `materials`와 `material_files`에 보관합니다. 파일 본문과 인증키는 GitHub에 포함하지 않습니다.

`GET /api/materials/{id}/file`은 기존 개인 접속 키 인증을 적용하며 `video/mp4`, `private, no-store`, 부분 응답(Range)을 제공합니다. 프론트는 인증 헤더로 파일을 받은 뒤 임시 Blob URL로 재생하므로 URL에 키를 넣지 않습니다. `material` 쿼리 값은 자료 식별자이며 인증정보가 아닙니다.

설정된 비공개 환경에서 실행 예:

```powershell
python backend/scripts/publish_material_video.py path/to/web-video.mp4 --id my-video --subject "홍보 영상" --title "브랜드 로고송" --duration-seconds 25.31
# 검증 결과를 확인한 뒤 같은 명령 끝에 --apply를 붙여 비공개 저장
```
