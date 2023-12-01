from datetime import datetime
import argparse
import base64
import json
import logging
import requests
import time
import yaml


class GitHub:
    ENDPOINT = 'https://api.github.com'
    def __init__(self, owner: str, repo: str, access_token: str) -> None:
        self.owner = owner
        self.repo = repo
        self.headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def list_files(self, path='') -> list[str]:
        """Recursively list all files in a GitHub repository at a specific path."""
        API = f'{GitHub.ENDPOINT}/repos/{self.owner}/{self.repo}/contents/{path}'
        response = requests.get(API, headers=self.headers)
        response.raise_for_status()

        index = response.json()
        files = []
        for item in index:
            if item['type'] == 'file':
                files.append(item['path'])
            elif item['type'] == 'dir':
                files.extend(self.list_files(item['path']))

        return files

    def get_file_content(self, file_path: str) -> str:
        """Get the content of a file from a GitHub repository."""
        API = f'{GitHub.ENDPOINT}/repos/{self.owner}/{self.repo}/contents/{file_path}'
        response = requests.get(API, headers=self.headers)
        response.raise_for_status()

        metadata = response.json()
        return base64.b64decode(metadata['content']).decode('utf-8')


class HedgeDoc:
    def __init__(self, endpoint: str, email: str, password: str, logger: logging.Logger = logging.getLogger(__name__)) -> None:
        self.endpoint = endpoint
        self.logger = logger
        self.session = requests.Session()
        self.login(email, password)

    @staticmethod
    def get_note_meta(content: str) -> dict:
        """Return note metadata in JSON if there is any."""
        lines = content.split('\n')
        EOYAML = [i for i in range(1, len(lines)) if lines[i] == '---']
        if lines[0] != '---' or len(EOYAML) == 0: return {}

        try:
            note_meta = yaml.safe_load('\n'.join(lines[1:EOYAML[0]]))
        except yaml.YAMLError:
            return {}
        return note_meta

    def login(self, email: str, password: str) -> None:
        """Log in to Hedgedoc."""
        API = f'{self.endpoint}/login'
        response = self.session.post(API, data={
            'email': email,
            'password': password
        })
        response.raise_for_status()

        self.logger.info(f'Logged in as {email}')

    def status(self):
        """Retrieve status of Hedgedoc server."""
        API = f'{self.endpoint}/status'
        response = requests.get(API)
        response.raise_for_status()

        self.logger.info(json.dumps(response.json(), indent=4))

    def create_note(self, content: str = '', metadata: dict = {}) -> str:
        """Create a note with the given content."""
        API = f'{self.endpoint}/new'
        response = self.session.post(API, headers={
            'Content-Type': 'text/markdown'
        }, data=content)
        response.raise_for_status()

        note_id = response.url.split('/')[-1]
        self.logger.info(f'Created note {note_id}')

        title = metadata.get('title', '')
        tags = metadata.get('tags', [])
        tags = [tags] if not isinstance(tags, list) else tags
        self.add_history(note_id, title, tags)
        self.logger.info(f'Synced note for {title}')
        return note_id

    def add_history(self, note_id: str, note_title: str = '', tags: list[str] = []) -> None:
        """Add a note to the view history of the current user.

        This is the only way to display a new created note on the dashboard up to v1.9.9.
        """
        API = f'{self.endpoint}/history'
        history = self.get_history()['history']
        history.append({
            'id': note_id,
            'text': note_title,
            'time': int(time.time() * 1000),
            'tags': tags,
            'pinned': True
        })

        response = self.session.post(API, headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        }, data=f'history={json.dumps(history)}')
        response.raise_for_status()

    def get_history(self) -> list[dict]:
        """Get the view history of the current user."""
        API = f'{self.endpoint}/history'
        response = self.session.get(API)
        response.raise_for_status()

        history = response.json()
        return history


def load_credentials(credential_file: str) -> dict:
    with open(credential_file, 'r') as cred_file:
        return json.load(cred_file)


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--credential-file', default='credentials.json')
    parser.add_argument('--hedgedoc-server', default='http://localhost/hedgedoc')
    args = parser.parse_args()

    credentials = load_credentials(args.credential_file)
    github = GitHub(credentials['github_owner'], credentials['github_repo'], credentials['github_token'])
    hedgedoc = HedgeDoc(args.hedgedoc_server, credentials['hedgedoc_email'], credentials['hedgedoc_password'], logger)

    note_syncs = {}            # records mapping from node_id to file_path for bidirectional sync
    blacklist = {'README.md'}  # blacklists unwanted files
    all_files = github.list_files()
    for file_path in all_files:
        file = file_path.split('/')[-1]
        if file in blacklist: continue

        content = github.get_file_content(file_path)
        metadata = HedgeDoc.get_note_meta(content)
        note_id = hedgedoc.create_note(content, metadata)
        note_syncs[note_id] = file_path

    note_syncs = {note_id: file_path for note_id, file_path in sorted(note_syncs.items(), key=lambda item: item[1])}
    with open(f'logs/note_sync_{datetime.today().strftime("%Y%m%d")}', 'w') as sync_file:
        json.dump(note_syncs, sync_file, indent=4)
    logger.info(f'Synced {len(note_syncs)} notes')

if __name__ == '__main__':
    main()
