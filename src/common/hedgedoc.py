from . import *
import json
import logging
import time
import yaml


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

    def get_note_info(self, note_id: str) -> dict[str, str]:
        API = f'{self.endpoint}/{note_id}/info'
        response = self.session.get(API)
        return response.json() if response.ok else {}
    
    def get_note(self, note_id: str) -> str:
        API = f'{self.endpoint}/{note_id}/download'
        response = self.session.get(API)
        if not response.ok:
            self.logger.error(f'Failed to read note {note_id}.')
            return ''
        return response.content.decode()

    def get_history(self) -> list[dict]:
        """Get the view history of the current user."""
        API = f'{self.endpoint}/history'
        response = self.session.get(API)
        response.raise_for_status()

        return response.json()['history']
