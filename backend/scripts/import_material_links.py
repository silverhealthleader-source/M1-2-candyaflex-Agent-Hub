"""Import verified teaching links from a private local JSON catalog, without changing originals."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from pydantic import Field, HttpUrl, field_validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import get_repository
from app.routers.materials import MaterialWrite
from app.services import now


class CatalogMaterial(MaterialWrite):
    source_platform: str = Field(default="Canva", max_length=100)
    design_id: str = Field(min_length=1, max_length=100)
    page_count: int = Field(ge=1)

    @field_validator("url")
    @classmethod
    def canva_original(cls, value: HttpUrl):
        if value.host != "www.canva.com":
            raise ValueError("검증한 Canva 원본 주소를 사용해 주세요.")
        return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows = [CatalogMaterial.model_validate(r).model_dump(mode="json")
            for r in json.loads(args.catalog.read_text(encoding="utf-8"))]
    print(f"검증한 교재 링크: {len(rows)}개")
    if not args.apply:
        print("--apply를 붙이면 데이터베이스에 없는 링크만 추가합니다.")
        return
    repo = get_repository()
    added = 0
    for row in rows:
        key = hashlib.sha256((row["subject"] + ":" + row["design_id"]).encode("utf-8")).hexdigest()[:32]
        if repo.db.collection("materials").document(key).get(timeout=15, retry=None).exists:
            continue
        repo.save("materials", key, {**row, "source_type": "link", "created_at": now(), "updated_at": now(), "deleted": False})
        added += 1
    print(f"교재 링크 {added}개를 추가했습니다. 원본 파일과 공유 권한은 유지됩니다.")


if __name__ == "__main__":
    main()
