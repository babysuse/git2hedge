from datetime import datetime
import argparse
import logging
import os

from .common.github import *
from .common.hedgedoc import *


def sync_notes(github: GitHub, hedgedoc: HedgeDoc, log_file: str, logger: logging.Logger):
    """Sync notes from GitHub to Hedgedoc.

    Record mappings between node IDs and file paths on the GitHub.
    """
    note_syncs = {}
    all_files = github.list_files()
    for file_path in all_files:

        content = github.get_file_content(file_path)
        metadata = HedgeDoc.get_note_meta(content)
        note_id = hedgedoc.create_note(content, metadata)
        note_syncs[note_id] = file_path

    note_syncs = {note_id: file_path for note_id, file_path in sorted(note_syncs.items(), key=lambda item: item[1])}
    with open(log_file, 'w') as sync_file:
        json.dump(note_syncs, sync_file, indent=4)
    logger.info(f'Synced {len(note_syncs)} notes')


def add_history(hedgedoc: HedgeDoc, notes: list[str]) -> None:
    """Given a list of note IDs, add them to Hedgedoc history."""
    existing_notes = {note['id'] for note in hedgedoc.get_history()}
    for note_id in notes:
        if note_id in existing_notes:
            hedgedoc.logger(f'Note {note_id} already exists.')
            continue
        note = hedgedoc.get_note_info(note_id)
        note_title = note.get('title', '')
        hedgedoc.add_history(note_id, note_title)


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    script_path = os.path.realpath(__file__)
    script_dir = script_path[:script_path.rfind('/')]
    parser.add_argument('--credential-file', default=f'{script_dir}/config.json', help='The abs path to the credential file.')
    parser.add_argument('--hedgedoc-server', default='http://localhost/hedgedoc', help='The URL to the Hedgedoc server.')
    args = parser.parse_args()

    cred = load_credentials(args.credential_file)
    github = GitHub(cred['github_owner'], cred['github_repo'], cred['github_token'], logger)
    hedgedoc = HedgeDoc(args.hedgedoc_server, cred['hedgedoc_email'], cred['hedgedoc_password'], logger)
    log_file = f'{script_dir}/logs/note_sync_{datetime.today().strftime("%Y%m%d")}'
    sync_notes(github, hedgedoc, log_file, logger)

if __name__ == '__main__':
    main()
