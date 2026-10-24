# 과목별 비공개 온라인 PDF

과목별 교재에서 **PDF 보기**를 누르면 전체 문서를 열람하고 원본을 내려받을 수 있습니다. 기존 개인 접속 키가 필요합니다. Canva·Drive 원본 링크의 공유 설정은 그대로 유지합니다. 쪽수가 다른 교재는 별도 버전으로 안내합니다.

## 선택한 PDF 추가

저장소 루트에서 본인의 비공개 환경변수를 설정한 뒤 실행합니다. 기본 실행은 형식·크기만 검사합니다.

```powershell
.\.venv\Scripts\python.exe backend/scripts/publish_material_pdf.py '선택한 교재.pdf' --subject '자료실의 과목명' --page-count 10
.\.venv\Scripts\python.exe backend/scripts/publish_material_pdf.py '선택한 교재.pdf' --subject '자료실의 과목명' --page-count 10 --apply
```

과목·교재 이름과 쪽수는 원본을 확인해 입력합니다. `--title`, `--note`로 대상·수업시간·버전 설명을 남길 수 있습니다. 파일을 공개 GitHub나 정적 프론트엔드에 넣지 않습니다. 현재 목록 캐시는 최대 15분이므로 외부 등록 도구의 변경은 캐시 만료 또는 서버 재시작 뒤 표시될 수 있습니다.

## 저장과 열람

- `materials`: 과목·이름·쪽수·버전 설명·파일 SHA-256 식별자. `source_type=firestore_file`.
- `material_files/{sha256}`: 크기·조각 개수·완료 상태.
- `material_files/{sha256}/chunks/{index}`: 각 512 KiB 이하의 비공개 파일 조각. 8개씩 저장하며 모든 조각이 준비된 뒤 완료로 표시합니다.
- `GET /api/materials/{id}/file`: 기존 인증을 통과한 요청만 파일을 받습니다. 조각의 길이·순서·최종 SHA-256을 확인하고 손상·누락 시 503을 반환합니다. `download=true`는 내려받기입니다.
- 서버의 `.local/cloud-pdf-cache`는 검증한 임시 사본입니다. 서버 교체 시 Firestore에서 복원합니다. 브라우저에는 Bearer 인증으로 받아 만든 Blob URL만 연결합니다. 접속 키를 파일 URL에 넣지 않습니다.

파일당 **32 MiB**, 전체 파일 보관량 **128 MiB**의 개인용 한도입니다. 더 큰 자료실은 별도 비공개 객체 저장소를 연결하는 확장 범위입니다. 파일을 여러 조각으로 보관하므로 새 서버의 최초 열람에는 여러 문서 읽기가 발생하며, 같은 서버에서는 검증한 파일 캐시를 재사용합니다. Firestore의 무료 사용량은 다른 교육기록·대화와 공유합니다.

[Firestore 공식 한도](https://firebase.google.com/docs/firestore/quotas)의 문서당 1 MiB 제한을 고려해 조각 크기를 정했습니다. [Firebase Storage 공식 변경 안내](https://firebase.google.com/docs/storage/faqs-storage-changes-announced-sept-2024)에 따라 Cloud Storage 사용은 Blaze 요금제가 필요하므로, 이 개인용 구현은 기존 Firestore와 접속 보호를 사용합니다. 이 기능이 요금제나 공유 권한을 자동 변경하지 않습니다.

## 검증

가상 PDF로 순서가 다른 조각·누락·손상·형식·보관 한도와 API의 inline/다운로드/Range 응답을 테스트합니다. 실제 교재는 비공개 경로에서 원본 SHA-256과 배포 응답 SHA-256을 대조합니다. 실제 수업·계획·대화 데이터와 파일 보관 컬렉션은 구분합니다.
