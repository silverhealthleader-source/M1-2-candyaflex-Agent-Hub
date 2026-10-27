from pathlib import Path

import pytest

from app.material_storage import CHUNK_BYTES, MaterialFileStore, MaterialFileUnavailable, mp4_metadata
from test_api import setup
from test_material_storage import FileDatabase


def make_mp4(path, payload=b"video"):
    content = (24).to_bytes(4, "big") + b"ftypisom" + bytes(4) + b"isomavc1" + payload
    path.write_bytes(content)
    return content


def test_mp4_private_roundtrip_and_type_separation(tmp_path):
    source = tmp_path / "logo.mp4"
    content = make_mp4(source, b"x" * (CHUNK_BYTES + 7))
    store = MaterialFileStore(FileDatabase(), tmp_path / "cache")
    meta = store.store_mp4(source, "stamp")
    assert meta["file_kind"] == "mp4" and meta["chunk_count"] == 2
    assert store.get_file(meta["sha256"], kind="mp4").read_bytes() == content
    with pytest.raises(MaterialFileUnavailable):
        store.get_file(meta["sha256"])
    with pytest.raises(MaterialFileUnavailable):
        store.get_file(meta["sha256"], kind="../mp4")


@pytest.mark.parametrize("damage", ["extension", "signature", "box-size", "too-large"])
def test_mp4_validation_rejects_wrong_type_and_excess_size(tmp_path, monkeypatch, damage):
    from app import material_storage
    source = tmp_path / ("logo.pdf" if damage == "extension" else "logo.mp4")
    make_mp4(source)
    if damage == "signature":
        source.write_bytes(b"not an MP4 file at all")
    if damage == "box-size":
        source.write_bytes((2**32 - 1).to_bytes(4, "big") + b"ftypisom" + bytes(20))
    if damage == "too-large":
        monkeypatch.setattr(material_storage, "MAX_PDF_BYTES", 24)
    with pytest.raises(ValueError):
        mp4_metadata(source)


def test_video_endpoint_requires_key_and_supports_private_range_and_download(setup, monkeypatch, tmp_path):
    from app import main
    from app.config import Settings
    from app.routers import materials
    client, repo = setup
    source = tmp_path / "logo.mp4"
    content = make_mp4(source)
    class Storage:
        def get_file(self, digest, kind="pdf"):
            assert digest == "video-digest" and kind == "mp4"
            return source
    monkeypatch.setattr(materials, "get_material_file_store", lambda: Storage())
    monkeypatch.setattr(main, "get_settings", lambda: Settings(access_token="test-video-key"))
    repo.save("materials", "logo", {"kind": "mp4", "source_type": "firestore_file",
                                  "storage_sha256": "video-digest", "file_name": "logo.mp4"})
    url = "/api/materials/logo/file"
    assert client.get(url).status_code == 401
    headers = {"Authorization": "Bearer test-video-key"}
    full = client.get(url, headers=headers)
    assert full.content == content and full.headers["content-type"] == "video/mp4"
    assert full.headers["cache-control"] == "private, no-store"
    assert full.headers["content-disposition"].startswith("inline;")
    partial = client.get(url, headers={**headers, "Range": "bytes=4-7"})
    assert partial.status_code == 206 and partial.content == b"ftyp"
    assert client.get(url + "?download=true", headers=headers).headers["content-disposition"].startswith("attachment;")
    assert client.get("/api/materials/missing/file", headers=headers).status_code == 404

