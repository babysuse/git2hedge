from datetime import datetime
import argparse
import logging
import os

from common import *

# TODO: optionally remove the notes in GitHub while not in /history API
# TODO: let _sync_notes do the job and sync_notes accepts a pairing record
class Hedge2Git:
    def __init__(self, github: GitHub, hedgedoc: HedgeDoc, logger: logging.Logger = logging.getLogger(__name__)):
        self.github = github
        self.hedgedoc = hedgedoc
        self.logger = logger

    def sync_notes(self):
        """Upload the local notes not yet uploaded."""
        all_notes_github = sorted(self.github.list_files())
        all_notes_hedgedoc = sorted([(note['title'], note['id']) for note in self.hedgedoc.get_history()])
        i = j = 0
        while i < len(all_notes_github) and j < len(all_notes_hedgedoc):
            g_path = all_notes_github[i]
            g_title = g_path.split('/')[-1]
            h_title, h_id = all_notes_hedgedoc[j]

            # if a note in GitHub is not in Hedgedoc
            if g_title < h_title:
                i += 1
                continue

            h_content = self.hedgedoc.get_note(h_id)
            h_tags = HedgeDoc.get_note_meta(h_content).get('tags', [])
            g_content = self.github.get_file_content(g_path)
            g_tags = HedgeDoc.get_note_meta(g_content).get('tags', [])
            # if a note in Hedgedoc is not in GitHub
            if h_title < g_title or h_tags != g_tags:
                self.upload_note(h_title, h_content, h_tags)
                j += 1
                continue

            if h_content != g_content:
                self.upload_note(h_title, h_content, h_tags)

            i += 1
            j += 1

    def upload_note(self, title: str, content: str, tags: list[str]):
        """Upload or update the note."""
        curr_time = datetime.now().strftime('%b %d, %Y %I:%M %p')  # # Dec 17, 2023 11:11 PM
        commit_msg = f'last changed at {curr_time}'
        self.github.upload_file(title, content, commit_msg)


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    script_path = os.path.realpath(__file__)
    script_dir = '/'.join(script_path.split('/')[:-1])
    parser.add_argument('--credential-file', default=f'{script_dir}/config.json', help='The abs path to the credential file.')
    parser.add_argument('--hedgedoc-server', default='http://localhost/hedgedoc', help='The URL to the Hedgedoc server.')
    args = parser.parse_args()

    credentials = load_credentials()
    github = GitHub(credentials['github_owner'], credentials['github_repo'], credentials['github_token'], logger)
    hedgedoc = HedgeDoc(args.hedgedoc_server, credentials['hedgedoc_email'], credentials['hedgedoc_password'], logger)
    hedge2git = Hedge2Git(github, hedgedoc, logger)
    hedge2git.sync_notes()

if __name__ == '__main__':
    main()
