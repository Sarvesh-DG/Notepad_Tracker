import subprocess


def git_log(workspace):
    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_home_page_returns_success(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Notepad Tracker" in response.data


def test_list_files_returns_file_objects(client, app_services):
    _, file_service, _, _ = app_services
    file_service.create_file("alpha.txt", "Alpha")

    response = client.get("/api/files")

    assert response.status_code == 200
    assert response.get_json() == [{"file": "alpha.txt"}]


def test_read_file_returns_content(client, app_services):
    _, file_service, _, _ = app_services
    file_service.create_file("readme.txt", "Hello from API")

    response = client.get("/api/files/readme.txt")

    assert response.status_code == 200
    assert response.get_json() == {
        "filename": "readme.txt",
        "content": "Hello from API",
    }


def test_read_missing_file_returns_404(client):
    response = client.get("/api/files/missing.txt")
    assert response.status_code == 404
    assert response.get_json()["error"] == "File not found"


def test_create_file_returns_201_and_commits(client, app_services):
    _, _, _, workspace = app_services

    response = client.post(
        "/api/files",
        json={"filename": "new.txt", "content": "Created through API"},
    )

    assert response.status_code == 201
    assert (workspace / "new.txt").read_text(encoding="utf-8") == "Created through API"
    assert "Created new.txt" in git_log(workspace)


def test_create_duplicate_file_returns_409(client, app_services):
    _, file_service, _, _ = app_services
    file_service.create_file("duplicate.txt", "First")

    response = client.post(
        "/api/files",
        json={"filename": "duplicate.txt", "content": "Second"},
    )

    assert response.status_code == 409


def test_create_file_validates_missing_filename(client):
    response = client.post("/api/files", json={"content": "No filename"})
    assert response.status_code == 400


def test_create_file_validates_content_type(client):
    response = client.post("/api/files", json={"filename": "bad.txt", "content": 123})
    assert response.status_code == 400


def test_create_file_rejects_path_traversal(client):
    response = client.post(
        "/api/files",
        json={"filename": "../outside.txt", "content": "Should not escape"},
    )
    assert response.status_code == 400


def test_update_file_changes_content_and_commits(client, app_services):
    _, file_service, _, workspace = app_services
    file_service.create_file("edit.txt", "Before")

    # Seed the file in Git so the update is a normal tracked-file update.
    subprocess.run(["git", "add", "edit.txt"], cwd=workspace, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial edit.txt"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )

    response = client.put(
        "/api/files/edit.txt",
        json={"content": "After"},
    )

    assert response.status_code == 200
    assert (workspace / "edit.txt").read_text(encoding="utf-8") == "After"
    assert "Updated edit.txt" in git_log(workspace)


def test_update_missing_file_returns_404(client):
    response = client.put("/api/files/missing.txt", json={"content": "Update"})
    assert response.status_code == 404


def test_update_rejects_invalid_content(client):
    response = client.put("/api/files/notes.txt", json={"content": None})
    assert response.status_code == 400


def test_delete_file_removes_file_and_commits(client, app_services):
    _, file_service, _, workspace = app_services
    file_service.create_file("remove.txt", "Delete me")
    subprocess.run(["git", "add", "remove.txt"], cwd=workspace, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial remove.txt"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )

    response = client.delete("/api/files/remove.txt")

    assert response.status_code == 200
    assert not (workspace / "remove.txt").exists()
    assert "Deleted remove.txt" in git_log(workspace)


def test_delete_missing_file_returns_404(client):
    response = client.delete("/api/files/missing.txt")
    assert response.status_code == 404


def test_list_directories(client, app_services):
    _, file_service, _, _ = app_services
    (file_service.workspace / "docs").mkdir()

    response = client.get("/api/directories")

    assert response.status_code == 200
    assert response.get_json() == ["docs"]


def test_navigate_into_directory_and_back(client, app_services):
    _, file_service, _, _ = app_services
    nested = file_service.workspace / "docs"
    nested.mkdir()
    (nested / "inside.txt").write_text("Nested file", encoding="utf-8")

    response = client.post("/api/navigate-directory", json={"directory": "docs"})
    assert response.status_code == 200
    assert response.get_json()["files"] == ["inside.txt"]

    response = client.post("/api/navigate-parent")
    assert response.status_code == 200
    assert file_service.current_directory == file_service.workspace.resolve()


def test_navigate_directory_validates_body(client):
    response = client.post("/api/navigate-directory", json={})
    assert response.status_code == 400


def test_navigate_directory_rejects_outside_path(client, app_services, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()

    # Absolute paths outside the selected workspace must be rejected.
    response = client.post(
        "/api/navigate-directory",
        json={"directory": str(outside)},
    )
    assert response.status_code == 400


def test_create_update_delete_files_inside_subdirectory(client, app_services):
    _, file_service, _, workspace = app_services
    (workspace / "docs").mkdir()

    navigate = client.post("/api/navigate-directory", json={"directory": "docs"})
    assert navigate.status_code == 200

    created = client.post(
        "/api/files",
        json={"filename": "nested.txt", "content": "Nested original"},
    )
    assert created.status_code == 201

    updated = client.put(
        "/api/files/nested.txt",
        json={"content": "Nested updated"},
    )
    assert updated.status_code == 200

    deleted = client.delete("/api/files/nested.txt")
    assert deleted.status_code == 200
    assert not (workspace / "docs" / "nested.txt").exists()
