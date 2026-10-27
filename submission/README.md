# GitHub 최종 제출 ZIP

[공개용 최종 ZIP 다운로드](M1-2-candyaflex-final-public-2026-10-27.zip) · [제출 설명](../docs/final-submission.md)

이 ZIP은 공개 GitHub에 등록할 수 있도록 구성한 제출본입니다. 별도로 PC에 보관한 운영 증빙 ZIP과는 다른 파일입니다.

- 앱 기능 기준 소스: `4c7027e91bd35b5a42e9c4b6f2ad51b421447f23`. 이 커밋 이후의 제출 안내 문서·README와 가상 120건을 함께 담았습니다. 실행 코드는 동일합니다.
- 포함: FastAPI·바닐라 프론트 소스, 공개 이미지 자산, 일반 문서, `demo-data/`의 가상 기록 120건, 파일별 SHA-256을 담은 `PUBLIC-MANIFEST.json`.
- 제외: `.env`, 서비스 계정·인증번호·API 키, `.git`, `.local`, 실제 교육 원본·운영 데이터·운영 캡처, 교재 원본, 발표 슬라이드·발표 대본.
- ZIP 자체를 다시 ZIP 안에 넣지 않습니다. 압축 CRC와 매니페스트의 파일 해시를 검사했습니다.

압축을 푼 폴더에서 README의 Python venv·Firebase 에뮬레이터 설정을 진행합니다. ZIP에는 가상 데이터가 있으므로 생성 대신 다음 명령으로 가져옵니다. **실제 운영 Firestore에 가상 자료를 넣지 않습니다.**

```powershell
$env:FIREBASE_PROJECT_ID = 'demo-candy-a-academy'
$env:FIRESTORE_EMULATOR_HOST = '127.0.0.1:8088'
.\.venv\Scripts\python.exe backend/scripts/import_data.py --data-dir demo-data
.\.venv\Scripts\python.exe backend/scripts/import_data.py --data-dir demo-data --apply
.\tools\start-local.ps1
```

실제 GPT 시연은 본인의 비공개 OpenAI 키가 필요합니다. 가상 기록 수와 실제 운영 DB 건수·현재 데이터는 서로 다른 근거입니다. 운영 서비스의 비공개 키는 ZIP이나 공개 설명에 넣지 않습니다.
