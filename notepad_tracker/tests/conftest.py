import subprocess
import pytest

from app.services.file_service import FileService
from app.services.git_service import GitService


@pytest.fixture
def workspace(tmp_path):
    path = tmp_path / "workspace"
    path.mkdir()
    return path


@pytest.fixture
def file_service(workspace):
    service = FileService(workspace)
    service.create_workspace()
    return service


@pytest.fixture
def git_service(workspace):
    service = GitService(workspace)
    service.initialize_repo()

    # Configure an identity locally so tests do not depend on global Git config.
    subprocess.run(
        ["git", "config", "user.name", "Notepad Tracker Tests"],
        cwd=workspace,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "notepad-tests@example.local"],
        cwd=workspace,
        check=True,
    )
    return service
