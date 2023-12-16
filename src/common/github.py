import base64
import logging
import requests


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
