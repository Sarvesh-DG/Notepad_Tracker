
from pathlib import Path

from app.services.file_service import FileService
from app.services.git_service import GitService

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_PATH = PROJECT_ROOT / "workspace"

file_service = FileService(WORKSPACE_PATH)
git_service = GitService(WORKSPACE_PATH)
