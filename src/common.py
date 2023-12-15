
from requests.adapters import HTTPAdapter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Any
from urllib3.util import Retry
import base64
import json
import logging
import requests
import time
import yaml

def get_session(max_retries=3) -> requests.Session:
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=2,
        status_forcelist=[400, 500]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def load_config(config_file: str) -> dict:
    """Load configurations for both Github and Hedgedoc."""
    with open(config_file, 'r') as cred_file:
        return json.load(cred_file)


class GitHub:
    ENDPOINT = 'https://api.github.com'
    def __init__(self, owner: str, repo: str, access_token: str, logger: logging.Logger = logging.getLogger(__name__)) -> None:
        self.owner = owner
        self.repo = repo
        self.headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.logger = logger

    def list_files(self, path='') -> list[str]:
        """Recursively list all files in a GitHub repository at a specific path."""
        API = f'{GitHub.ENDPOINT}/repos/{self.owner}/{self.repo}/contents/{path}'
        response = requests.get(API, headers=self.headers)
        if not response.ok:
            self.logger.error(f'Failed to fetch {path}.')
            return []

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
        if not response.ok:
            self.logger.error(f'Failed to read file {file_path}')

        metadata = response.json()
        return base64.b64decode(metadata['content']).decode('utf-8')


class HedgeDoc:
    def __init__(self, endpoint: str, email: str, password: str, logger: logging.Logger = logging.getLogger(__name__)) -> None:
        self.endpoint = endpoint
        self.logger = logger
        self.session = get_session()
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

    def create_note(self, content: str = '', metadata: dict = {}) -> str:
        """Create a note with the given content."""
        API = f'{self.endpoint}/new'
        response = self.session.post(API, headers={
            'Content-Type': 'text/markdown'
        }, data=content)
        if not response.ok:
            self.logger.error(f'Failed to create note {metadata["title"]}.')

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
        history = self.get_history()
        history.append({
            'id': note_id,
            'text': note_title,
            'time': int(time.time() * 1000),
            'tags': tags,
            'pinned': False
        })

        response = self.session.post(API, headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        }, data=f'history={json.dumps(history)}')
        if not response.ok:
            self.logger.error(f'Failed to add note {note_id} to history.')

    def get_note(self, note_id: str) -> dict[str, str]:
        API = f'{self.endpoint}/{note_id}/info'
        response = self.session.get(API)
        return response.json() if response.ok else {}

    def get_history(self) -> list[dict]:
        """Get the view history of the current user."""
        API = f'{self.endpoint}/history'
        response = self.session.get(API)
        response.raise_for_status()

        return response.json()['history']