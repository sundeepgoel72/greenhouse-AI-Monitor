from datetime import datetime
from pathlib import Path
import os
import requests


class FrigateClient:
    def __init__(self):
        self.base_url = os.getenv('FRIGATE_BASE_URL', '').rstrip('/')
        self.camera = os.getenv('FRIGATE_CAMERA', 'rooftop_growhouse')
        if not self.base_url:
            raise ValueError('FRIGATE_BASE_URL is required')

    @property
    def latest_url(self):
        return f'{self.base_url}/api/{self.camera}/latest.jpg'

    def fetch_latest(self, timeout=20):
        response = requests.get(self.latest_url, timeout=timeout)
        response.raise_for_status()
        return response.content

    def save_latest(self, storage_dir: str | Path):
        now = datetime.now()
        day = now.strftime('%Y-%m-%d')
        out_dir = Path(storage_dir) / 'snapshots' / self.camera / day
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f'{now.strftime("%H%M%S")}.jpg'
        path.write_bytes(self.fetch_latest())
        return path
