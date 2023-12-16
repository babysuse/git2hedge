from requests.adapters import HTTPAdapter
from typing import Any
from urllib3.util import Retry
import requests
import json

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
