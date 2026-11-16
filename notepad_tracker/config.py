
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = "abcd1234"

    DEBUG = True

    WORKSPACE_PATH = BASE_DIR / "workspace"

    SAVE_DELAY = 1000
