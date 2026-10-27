"""Store an explicitly selected web MP4 in the existing private material library."""
import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import get_repository
from app.material_storage import get_material_file_store, mp4_metadata
from app.services import now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--id", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--duration-seconds", type=float)
    parser.add_argument("--note", default="")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", args.id):
        parser.error("파일 ID는 영문·숫자·밑줄·하이픈으로 지정해 주세요.")
    if not all(1 <= len(value.strip()) <= 200 for value in [args.subject, args.title]) or len(args.note) > 1000:
        parser.error("과목·제목은 1~200자, 메모는 1000자 이하로 입력해 주세요.")
    if args.duration_seconds is not None and not (math.isfinite(args.duration_seconds) and 0 < args.duration_seconds <= 36000):
        parser.error("영상 길이를 확인해 주세요.")
    meta = mp4_metadata(args.file)
    print(f"MP4 validated: {meta['size_bytes']} bytes, {meta['chunk_count']} private chunks")
    if not args.apply:
        print("Dry run only. Add --apply to store this video privately.")
        return
    repo = get_repository()
    old = repo.get("materials", args.id)
    if old and old.get("storage_sha256") == meta["sha256"]:
        print("This video is already connected.")
        return
    stamp = now()
    get_material_file_store().store_mp4(args.file, stamp)
    row = {"subject": args.subject.strip(), "title": args.title.strip(), "kind": "mp4",
           "source_type": "firestore_file", "source_platform": "비공개 MP4",
           "storage_sha256": meta["sha256"], "size_bytes": meta["size_bytes"],
           "file_name": args.title.strip() + ".mp4", "note": args.note,
           "created_at": old.get("created_at", stamp) if old else stamp,
           "updated_at": stamp, "deleted": False}
    if args.duration_seconds is not None:
        row["duration_seconds"] = args.duration_seconds
    repo.save("materials", args.id, row)
    print("Private video connected. Teaching records were not changed.")


if __name__ == "__main__":
    main()

