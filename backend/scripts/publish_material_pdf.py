"""Publish an explicitly selected PDF to the existing private Firestore library."""
import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import get_repository
from app.material_storage import get_material_file_store, pdf_metadata
from app.services import now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=Path)
    parser.add_argument('--subject', required=True)
    parser.add_argument('--title')
    parser.add_argument('--page-count', type=int, required=True)
    parser.add_argument('--note', default='')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.page_count <= 5000 or not 1 <= len(args.subject.strip()) <= 200:
        parser.error('과목명 또는 PDF 쪽수를 확인해 주세요.')
    metadata = pdf_metadata(args.file)
    print(f"PDF validated: {metadata['size_bytes']} bytes, {metadata['chunk_count']} private chunks")
    if not args.apply:
        print('Dry run only. Add --apply to store the selected PDF privately.')
        return
    repo = get_repository()
    key = hashlib.sha256((args.subject.strip() + ':' + metadata['sha256']).encode()).hexdigest()[:32]
    if repo.get('materials', key):
        print('This PDF is already connected to the subject.')
        return
    stamp = now()
    metadata = get_material_file_store().store_pdf(args.file, stamp)
    repo.save('materials', key, {'subject': args.subject.strip(), 'title': args.title or args.file.stem,
        'kind': 'pdf', 'source_type': 'firestore_file', 'source_platform': '비공개 PDF',
        'storage_sha256': metadata['sha256'], 'file_name': args.file.name, 'size_bytes': metadata['size_bytes'],
        'page_count': args.page_count, 'note': args.note, 'created_at': stamp, 'updated_at': stamp, 'deleted': False})
    print('The private online PDF is connected. Existing teaching results were not changed.')


if __name__ == '__main__':
    main()
