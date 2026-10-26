import hashlib
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED

import pytest

from app.material_storage import CHUNK_BYTES, MaterialFileStore, MaterialFileUnavailable, pdf_metadata, pptx_metadata
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


def make_pptx(path, *, macro=False, presentation=True):
    content_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'
    with ZipFile(path, 'w', ZIP_STORED) as archive:
        archive.writestr('[Content_Types].xml', f'<Types><Override PartName="/ppt/presentation.xml" ContentType="{content_type}"/></Types>')
        if presentation:
            archive.writestr('ppt/presentation.xml', '<presentation/>')
        archive.writestr('ppt/media/image.png', b'x' * (CHUNK_BYTES + 10))
        if macro:
            archive.writestr('ppt/vbaProject.bin', b'macro')


def test_original_pptx_roundtrip_and_pdf_type_separation(tmp_path):
    source = tmp_path / 'editable.pptx'
    make_pptx(source)
    store = MaterialFileStore(FileDatabase(), tmp_path / 'cache')
    metadata = store.store_pptx(source, 'stamp')
    assert metadata['chunk_count'] == 2
    assert store.get_file(metadata['sha256'], kind='pptx').read_bytes() == source.read_bytes()
    with pytest.raises(MaterialFileUnavailable):
        store.get_file(metadata['sha256'])
    with pytest.raises(MaterialFileUnavailable):
        store.get_file(metadata['sha256'], kind='../pptx')


@pytest.mark.parametrize('bad_kind', ['fake', 'macro', 'missing-presentation'])
def test_pptx_validation_rejects_invalid_or_macro_files(tmp_path, bad_kind):
    source = tmp_path / 'invalid.pptx'
    if bad_kind == 'fake':
        source.write_bytes(b'not a presentation')
    else:
        make_pptx(source, macro=bad_kind == 'macro', presentation=bad_kind != 'missing-presentation')
    with pytest.raises(ValueError):
        pptx_metadata(source)


def test_pptx_original_download_preserves_mime_attachment_and_pdf(setup, monkeypatch, tmp_path):
    from app.routers import materials
    client, repo = setup
    pptx = tmp_path / 'original.pptx'
    make_pptx(pptx)
    class Storage:
        def get_file(self, digest, kind='pdf'):
            assert digest == 'pptx-digest' and kind == 'pptx'
            return pptx
    monkeypatch.setattr(materials, 'get_material_file_store', lambda: Storage())
    repo.save('materials', 'lesson', {'kind': 'pdf', 'original_storage_sha256': 'pptx-digest', 'original_file_name': 'lesson.pptx'})
    result = client.get('/api/materials/lesson/original')
    assert result.content == pptx.read_bytes()
    assert result.headers['content-type'] == 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    assert result.headers['content-disposition'].startswith('attachment;')
    assert result.headers['cache-control'] == 'private, no-store'
    partial = client.get('/api/materials/lesson/original', headers={'Range': 'bytes=0-3'})
    assert partial.status_code == 206 and partial.content == b'PK\x03\x04'
    assert client.get('/api/materials/unknown/original').status_code == 404
