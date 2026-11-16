
import subprocess
import pytest

from app import create_app
from app.services.file_service import FileService
from app.services.git_service import GitService

import app.routes.editor as editor_routes
import app.routes.git_routes as git_routes


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

    subprocess.run(
        ["git", "config", "user.name", "Notepad Tracker Tests"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True
    )

    subprocess.run(
        ["git", "config", "user.email", "notepad-tests@example.local"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True
    )

    return service


@pytest.fixture
def app_services(tmp_path, monkeypatch):
    workspace = tmp_path / "api_workspace"
    workspace.mkdir()

    fs = FileService(workspace)
    fs.create_workspace()

    gs = GitService(workspace)
    gs.initialize_repo()

    subprocess.run(
        ["git", "config", "user.name", "Notepad Tracker API Tests"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True
    )

    subprocess.run(
        ["git", "config", "user.email", "notepad-api-tests@example.local"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True
    )

    # Replace the shared services with isolated test instances.
    monkeypatch.setattr(editor_routes, "file_service", fs)
    monkeypatch.setattr(editor_routes, "git_service", gs)
    monkeypatch.setattr(git_routes, "git_service", gs)

    app = create_app()
    app.config.update(TESTING=True)

    return app, fs, gs, workspace


@pytest.fixture
def client(app_services):
    app, _, _, _ = app_services
    return app.test_client()
