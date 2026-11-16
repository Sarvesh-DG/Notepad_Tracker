import subprocess
from pathlib import Path

import pytest


def git_output(repo, *args):
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()



def test_initialize_repository(git_service, workspace):
    assert (workspace / ".git").is_dir()

    actual_root = Path(
        git_output(workspace, "rev-parse", "--show-toplevel")
    ).resolve()

    assert actual_root == workspace.resolve()



def test_commit_created_file(git_service, workspace):
    file_path = workspace / "first.txt"
    file_path.write_text("First version", encoding="utf-8")

    git_service.stage_file("first.txt")
    git_service.commit_changes("Created first.txt")

    history = git_service.get_history()
    assert "Created first.txt" in history


def test_commit_updated_file(git_service, workspace):
    file_path = workspace / "notes.txt"
    file_path.write_text("Version one", encoding="utf-8")
    git_service.stage_file("notes.txt")
    git_service.commit_changes("Created notes.txt")

    file_path.write_text("Version two", encoding="utf-8")
    git_service.stage_file("notes.txt")
    git_service.commit_changes("Updated notes.txt")

    history = git_service.get_file_history("notes.txt")
    assert "Updated notes.txt" in history
    assert "Created notes.txt" in history


def test_stage_and_commit_deleted_file(git_service, workspace):
    file_path = workspace / "remove.txt"
    file_path.write_text("Remove me", encoding="utf-8")
    git_service.stage_file("remove.txt")
    git_service.commit_changes("Created remove.txt")

    file_path.unlink()
    git_service.stage_deleted_file("remove.txt")
    git_service.commit_changes("Deleted remove.txt")

    assert "Deleted remove.txt" in git_service.get_history()


def test_restore_previous_file_version(git_service, workspace):
    file_path = workspace / "notes.txt"
    file_path.write_text("Original", encoding="utf-8")
    git_service.stage_file("notes.txt")
    git_service.commit_changes("Original version")

    original_commit = git_output(workspace, "rev-parse", "HEAD")

    file_path.write_text("Changed", encoding="utf-8")
    git_service.stage_file("notes.txt")
    git_service.commit_changes("Changed version")

    git_service.restore_file("notes.txt", original_commit)
    assert file_path.read_text(encoding="utf-8") == "Original"


def test_git_service_rejects_file_outside_repository(git_service, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("Outside", encoding="utf-8")

    with pytest.raises(ValueError):
        git_service.stage_file(str(outside))


def test_set_repository_does_not_reuse_parent_repository(tmp_path):
    parent_repo = tmp_path / "parent"
    selected = parent_repo / "selected"
    selected.mkdir(parents=True)

    subprocess.run(["git", "init"], cwd=parent_repo, check=True, capture_output=True)
    service = __import__(
        "app.services.git_service", fromlist=["GitService"]
    ).GitService(parent_repo)

    initialized = service.set_repository(selected)

    assert initialized is False
    assert service.repository_path == selected.resolve()
    assert service.working_directory == selected.resolve()


def test_set_repository_reuses_selected_folder_repository(tmp_path):
    selected = tmp_path / "selected"
    selected.mkdir()
    subprocess.run(["git", "init"], cwd=selected, check=True, capture_output=True)

    from app.services.git_service import GitService
    service = GitService(selected)

    initialized = service.set_repository(selected)

    assert initialized is True
    assert service.repository_path == selected.resolve()
