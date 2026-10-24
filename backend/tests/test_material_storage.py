import hashlib
from pathlib import Path

import pytest

from app.material_storage import CHUNK_BYTES, MaterialFileStore, MaterialFileUnavailable, pdf_metadata
from test_api import setup


class Snapshot:
    def __init__(self, key, value):
        self.id, self.value, self.exists = key.split('/')[-1], value, value is not None

    def to_dict(self):
        return self.value


class Reference:
    def __init__(self, db, key):
        self.db, self.key = db, key

    def get(self, **kwargs):
        self.db.reads += 1
        return Snapshot(self.key, self.db.rows.get(self.key))

    def set(self, value, **kwargs):
        self.db.rows[self.key] = value

    def collection(self, name):
        return Collection(self.db, self.key + '/' + name)


class Collection:
    def __init__(self, db, path):
        self.db, self.path = db, path

    def document(self, key):
        return Reference(self.db, self.path + '/' + key)

    def stream(self, **kwargs):
        return [Snapshot(k, v) for k, v in self.db.rows.items() if k.rpartition('/')[0] == self.path]


class Batch:
    def __init__(self):
        self.pending = []

    def set(self, ref, value):
        self.pending.append((ref, value))

    def commit(self, **kwargs):
        for ref, value in self.pending:
            ref.set(value)


class FileDatabase:
    def __init__(self):
        self.rows, self.reads = {}, 0

    def collection(self, name):
        return Collection(self, name)

    def batch(self):
        return Batch()

    def get_all(self, refs, **kwargs):
        # Firestore does not promise request order in its batch result.
        return [ref.get() for ref in reversed(refs)]


def test_private_pdf_roundtrip_handles_unordered_chunks_and_reuses_cache(tmp_path):
    content = b'%PDF-1.7\n' + b'x' * (CHUNK_BYTES * 9 + 7)
    source = tmp_path / 'teaching.pdf'
    source.write_bytes(content)
    db = FileDatabase()
    store = MaterialFileStore(db, tmp_path / 'cache')
    metadata = store.store_pdf(source, 'test-stamp')
    assert metadata['sha256'] == hashlib.sha256(content).hexdigest()
    assert metadata['chunk_count'] == 10
    result = store.get_file(metadata['sha256'])
    assert result.read_bytes() == content
    reads = db.reads
    assert store.get_file(metadata['sha256']) == result and db.reads == reads
    before = dict(db.rows)
    assert store.store_pdf(source, 'later') == metadata and db.rows == before


@pytest.mark.parametrize('damage', ['missing', 'corrupt'])
def test_incomplete_or_corrupt_pdf_is_never_served_or_cached(tmp_path, damage):
    source = tmp_path / 'teaching.pdf'
    source.write_bytes(b'%PDF-1.7\noriginal')
    db = FileDatabase()
    store = MaterialFileStore(db, tmp_path / 'cache')
    metadata = store.store_pdf(source, 'stamp')
    key = 'material_files/' + metadata['sha256'] + '/chunks/00000'
    if damage == 'missing':
        del db.rows[key]
    else:
        db.rows[key]['data'] = b'%PDF-1.7\nmodified'
    with pytest.raises(MaterialFileUnavailable):
        store.get_file(metadata['sha256'])
    assert not list((tmp_path / 'cache').glob('*'))


def test_pdf_import_validates_type_and_library_limit(tmp_path, monkeypatch):
    from app import material_storage
    bad = tmp_path / 'fake.pdf'
    bad.write_bytes(b'not a pdf')
    with pytest.raises(ValueError):
        pdf_metadata(bad)
    source = tmp_path / 'good.pdf'
    source.write_bytes(b'%PDF-1.7\ncontent')
    monkeypatch.setattr(material_storage, 'MAX_LIBRARY_BYTES', 4)
    db = FileDatabase()
    with pytest.raises(ValueError):
        MaterialFileStore(db, tmp_path / 'cache').store_pdf(source, 'stamp')
    assert not db.rows


def test_online_pdf_route_inline_download_range_and_unavailable(setup, monkeypatch, tmp_path):
    from app.routers import materials
    client, repo = setup
    pdf = tmp_path / 'private.pdf'
    pdf.write_bytes(b'%PDF-1.7\nprivate teaching file')
    class Storage:
        def get_file(self, digest):
            if digest != 'valid':
                raise MaterialFileUnavailable('교재 파일을 확인할 수 없습니다.')
            return pdf
    monkeypatch.setattr(materials, 'get_material_file_store', lambda: Storage())
    repo.save('materials', 'online', {'source_type': 'firestore_file', 'storage_sha256': 'valid', 'file_name': 'slides.pdf'})
    result = client.get('/api/materials/online/file')
    assert result.content == pdf.read_bytes()
    assert result.headers['cache-control'] == 'private, no-store'
    assert result.headers['content-disposition'].startswith('inline;')
    assert client.get('/api/materials/online/file?download=true').headers['content-disposition'].startswith('attachment;')
    partial = client.get('/api/materials/online/file', headers={'Range': 'bytes=0-4'})
    assert partial.status_code == 206 and partial.content == b'%PDF-'
    repo.save('materials', 'bad', {'source_type': 'firestore_file', 'storage_sha256': '../private'})
    assert client.get('/api/materials/bad/file').status_code == 503
