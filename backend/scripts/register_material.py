"""Register an explicitly selected local PDF/PPTX and its subject; no automatic subject guesses."""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import get_repository
from app.routers.materials import LOCAL_LIBRARY
from app.services import now

parser = argparse.ArgumentParser()
parser.add_argument("file", type=Path)
parser.add_argument("--subject", required=True)
parser.add_argument("--title")
parser.add_argument("--page-count", type=int)
args = parser.parse_args()
source = args.file.resolve()
if source.suffix.lower() not in {".pdf", ".pptx"} or not source.is_file():
    raise SystemExit("실제 PDF 또는 PPTX 파일을 선택해 주세요.")
if args.page_count is not None and args.page_count < 1:
    raise SystemExit("쪽수는 1 이상이어야 합니다.")
key = hashlib.sha256((args.subject + ":").encode("utf-8") + source.read_bytes()).hexdigest()[:32]
repo = get_repository()
if repo.db.collection("materials").document(key).get(timeout=15, retry=None).exists:
    print("이미 연결된 교재입니다.")
    raise SystemExit(0)
LOCAL_LIBRARY.mkdir(parents=True, exist_ok=True)
storage_name = key + source.suffix.lower()
shutil.copy2(source, LOCAL_LIBRARY / storage_name)
repo.save("materials", key, {"subject": args.subject.strip(), "title": args.title or source.stem,
          "kind": source.suffix.lower()[1:], "source_type": "local_file", "file_name": source.name,
          "storage_name": storage_name, "page_count": args.page_count,
          "created_at": now(), "updated_at": now(), "deleted": False})
print("과목과 교재 파일을 연결했습니다. 로컬 서버에서 볼 수 있습니다.")
