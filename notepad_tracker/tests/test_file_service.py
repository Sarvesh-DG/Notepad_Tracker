import pytest


def test_create_and_read_file(file_service):
    file_service.create_file("notes.txt", "Hello")
    assert file_service.read_file("notes.txt") == "Hello"


def test_create_file_rejects_duplicate(file_service):
    file_service.create_file("notes.txt", "First")
    with pytest.raises(FileExistsError):
        file_service.create_file("notes.txt", "Second")


def test_update_file(file_service):
    file_service.create_file("notes.txt", "Before")
    file_service.update_file("notes.txt", "After")
    assert file_service.read_file("notes.txt") == "After"


def test_delete_file(file_service):
    file_service.create_file("notes.txt", "Content")
    file_service.delete_file("notes.txt")
    assert "notes.txt" not in file_service.list_files()


def test_read_missing_file_raises(file_service):
    with pytest.raises(FileNotFoundError):
        file_service.read_file("missing.txt")


def test_update_missing_file_raises(file_service):
    with pytest.raises(FileNotFoundError):
        file_service.update_file("missing.txt", "Content")


def test_delete_missing_file_raises(file_service):
    with pytest.raises(FileNotFoundError):
        file_service.delete_file("missing.txt")


def test_list_files_and_directories(file_service):
    file_service.create_file("notes.txt", "Content")
    (file_service.workspace / "documents").mkdir()

    assert "notes.txt" in file_service.list_files()
    assert "documents" in file_service.list_directories()


def test_navigate_into_subdirectory_and_back(file_service):
    folder = file_service.workspace / "documents"
    folder.mkdir()
    (folder / "inside.txt").write_text("Inside", encoding="utf-8")

    file_service.navigate_directory("documents")
    assert file_service.current_directory == folder.resolve()
    assert "inside.txt" in file_service.list_files()

    file_service.navigate_parent()
    assert file_service.current_directory == file_service.workspace.resolve()


def test_navigation_cannot_escape_selected_workspace(file_service, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(ValueError):
        file_service.navigate_directory(str(outside))


def test_create_file_cannot_escape_selected_workspace(file_service):
    with pytest.raises(ValueError):
        file_service.create_file("../outside.txt", "Not allowed")


def test_delete_file_cannot_escape_selected_workspace(file_service):
    outside = file_service.workspace.parent / "outside.txt"
    outside.write_text("Keep me", encoding="utf-8")

    with pytest.raises(ValueError):
        file_service.delete_file("../outside.txt")

    assert outside.read_text(encoding="utf-8") == "Keep me"
