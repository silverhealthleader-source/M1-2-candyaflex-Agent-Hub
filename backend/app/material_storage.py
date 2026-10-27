"""Private PDF, PowerPoint and MP4 storage; never public static assets."""
import hashlib
import math
from functools import lru_cache
from pathlib import Path
from threading import RLock
from uuid import uuid4
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

from .database import get_db

CHUNK_BYTES = 512 * 1024
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_LIBRARY_BYTES = 128 * 1024 * 1024


class MaterialFileUnavailable(RuntimeError):
    pass


def pdf_metadata(path):
    path = Path(path)
    size = path.stat().st_size
    if path.suffix.lower() != '.pdf' or not 5 <= size <= MAX_PDF_BYTES:
        raise ValueError('PDF 파일은 32 MiB 이하로 선택해 주세요.')
    digest = hashlib.sha256()
    with path.open('rb') as source:
        if source.read(5) != b'%PDF-':
            raise ValueError('PDF 파일 형식을 확인해 주세요.')
        source.seek(0)
        for chunk in iter(lambda: source.read(CHUNK_BYTES), b''):
            digest.update(chunk)
    return {'sha256': digest.hexdigest(), 'size_bytes': size,
            'chunk_count': math.ceil(size / CHUNK_BYTES), 'chunk_bytes': CHUNK_BYTES}


def pptx_metadata(path):
    path = Path(path)
    size = path.stat().st_size
    if path.suffix.lower() != '.pptx' or not 5 <= size <= MAX_PDF_BYTES:
        raise ValueError('PowerPoint 원본은 32 MiB 이하의 PPTX 파일로 선택해 주세요.')
    try:
        with ZipFile(path) as archive:
            entries = archive.infolist()
            names = {entry.filename for entry in entries}
            if (len(entries) > 10000 or sum(entry.file_size for entry in entries) > MAX_LIBRARY_BYTES
                    or not {'[Content_Types].xml', 'ppt/presentation.xml'}.issubset(names)
                    or any(name.lower().endswith('vbaproject.bin') for name in names)):
                raise ValueError('일반 PPTX 형식의 교재 파일을 확인해 주세요.')
            types = ElementTree.fromstring(archive.read('[Content_Types].xml'))
            expected = 'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'
            if not any(node.attrib.get('PartName') == '/ppt/presentation.xml'
                       and node.attrib.get('ContentType') == expected for node in types):
                raise ValueError('PowerPoint 프레젠테이션 형식을 확인해 주세요.')
    except (BadZipFile, KeyError, ElementTree.ParseError) as exc:
        raise ValueError('PPTX 파일 형식을 확인해 주세요.') from exc
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'sha256': digest, 'size_bytes': size, 'chunk_count': math.ceil(size / CHUNK_BYTES),
            'chunk_bytes': CHUNK_BYTES, 'file_kind': 'pptx'}


def mp4_metadata(path):
    path = Path(path)
    size = path.stat().st_size
    if path.suffix.lower() != '.mp4' or not 16 <= size <= MAX_PDF_BYTES:
        raise ValueError('웹 재생용 MP4는 32 MiB 이하로 선택해 주세요.')
    digest = hashlib.sha256()
    with path.open('rb') as source:
        header = source.read(12)
        if header[4:8] != b'ftyp' or not 16 <= int.from_bytes(header[:4], 'big') <= min(size, 1024 * 1024):
            raise ValueError('MP4 파일 형식을 확인해 주세요.')
        source.seek(0)
        for chunk in iter(lambda: source.read(CHUNK_BYTES), b''):
            digest.update(chunk)
    return {'sha256': digest.hexdigest(), 'size_bytes': size,
            'chunk_count': math.ceil(size / CHUNK_BYTES), 'chunk_bytes': CHUNK_BYTES, 'file_kind': 'mp4'}


class MaterialFileStore:
    def __init__(self, db, cache_dir):
        self.db = db
        self.cache_dir = Path(cache_dir)
        self._lock = RLock()

    def store_pdf(self, path, stamp):
        metadata = pdf_metadata(path)
        return self._store(path, stamp, metadata)

    def store_pptx(self, path, stamp):
        return self._store(path, stamp, pptx_metadata(path))

    def store_mp4(self, path, stamp):
        return self._store(path, stamp, mp4_metadata(path))

    def _store(self, path, stamp, metadata):
        ref = self.db.collection('material_files').document(metadata['sha256'])
        old = ref.get(timeout=15, retry=None)
        if old.exists and old.to_dict().get('ready'):
            return metadata
        used = sum((row.to_dict() or {}).get('size_bytes', 0)
                   for row in self.db.collection('material_files').stream(timeout=20, retry=None)
                   if (row.to_dict() or {}).get('ready'))
        if used + metadata['size_bytes'] > MAX_LIBRARY_BYTES:
            raise ValueError('개인 교재 보관 한도 128 MiB를 초과합니다. 별도 파일 저장소를 연결해 주세요.')
        with Path(path).open('rb') as source:
            index = 0
            uploaded_hash = hashlib.sha256()
            while index < metadata['chunk_count']:
                batch = self.db.batch()
                for _ in range(8):
                    chunk = source.read(CHUNK_BYTES)
                    if not chunk:
                        break
                    uploaded_hash.update(chunk)
                    batch.set(ref.collection('chunks').document(f'{index:05d}'), {'data': chunk, 'index': index})
                    index += 1
                batch.commit(timeout=45, retry=None)
        if index != metadata['chunk_count'] or uploaded_hash.hexdigest() != metadata['sha256']:
            raise ValueError('보관 중 원본 파일이 변경되었습니다. 원본을 확인한 뒤 다시 실행해 주세요.')
        ref.set({**metadata, 'ready': True, 'created_at': stamp}, timeout=20, retry=None)
        return metadata

    def get_file(self, digest, kind='pdf'):
        if kind not in {'pdf', 'pptx', 'mp4'}:
            raise MaterialFileUnavailable('지원하지 않는 교재 파일 형식입니다.')
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise MaterialFileUnavailable('교재 파일 식별자를 확인해 주세요.')
        with self._lock:
            target = self.cache_dir / (digest + '.' + kind)
            if target.is_file():
                return target
            ref = self.db.collection('material_files').document(digest)
            snapshot = ref.get(timeout=15, retry=None)
            metadata = snapshot.to_dict() if snapshot.exists else {}
            size = metadata.get('size_bytes', 0)
            count = metadata.get('chunk_count', 0)
            if (not metadata.get('ready') or metadata.get('file_kind', 'pdf') != kind or not 5 <= size <= MAX_PDF_BYTES
                    or metadata.get('chunk_bytes') != CHUNK_BYTES or count != math.ceil(size / CHUNK_BYTES)):
                raise MaterialFileUnavailable('보관된 교재 파일을 확인할 수 없습니다.')
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            temporary = self.cache_dir / (uuid4().hex + '.part')
            hasher = hashlib.sha256()
            try:
                with temporary.open('wb') as output:
                    for start in range(0, count, 8):
                        refs = [ref.collection('chunks').document(f'{i:05d}') for i in range(start, min(start + 8, count))]
                        chunks = {s.id: s for s in self.db.get_all(refs, timeout=30, retry=None)}
                        for i in range(start, min(start + 8, count)):
                            snap = chunks.get(f'{i:05d}')
                            chunk = snap.to_dict() if snap and snap.exists else {}
                            data = chunk.get('data')
                            expected = min(CHUNK_BYTES, size - i * CHUNK_BYTES)
                            if not isinstance(data, bytes) or len(data) != expected or chunk.get('index') != i:
                                raise MaterialFileUnavailable('교재 파일 일부를 읽지 못했습니다. 잠시 후 다시 열어 주세요.')
                            output.write(data)
                            hasher.update(data)
                if hasher.hexdigest() != digest:
                    raise MaterialFileUnavailable('교재 파일 검증에 실패했습니다.')
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
            return target


@lru_cache
def get_material_file_store():
    cache = Path(__file__).resolve().parents[2] / '.local/cloud-pdf-cache'
    return MaterialFileStore(get_db(), cache)
