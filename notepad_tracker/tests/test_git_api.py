import subprocess


def test_git_status_endpoint(client):
    response = client.get("/api/git/status")
    assert response.status_code == 200
    assert "output" in response.get_json()


def test_git_history_endpoint(client, app_services):
    _, _, _, workspace = app_services
    (workspace / "history.txt").write_text("History", encoding="utf-8")
    subprocess.run(["git", "add", "history.txt"], cwd=workspace, check=True)
    subprocess.run(
        ["git", "commit", "-m", "History test commit"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )

    response = client.get("/api/git/history")
    assert response.status_code == 200
    assert "History test commit" in response.get_json()["output"]


def test_git_stage_endpoint(client, app_services):
    _, _, _, workspace = app_services
    (workspace / "stage.txt").write_text("Stage me", encoding="utf-8")

    response = client.post("/api/git/stage/stage.txt")

    assert response.status_code == 200
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "stage.txt" in status


def test_git_stage_missing_file_returns_404(client):
    response = client.post("/api/git/stage/missing.txt")
    assert response.status_code == 404


def test_git_commit_endpoint(client, app_services):
    _, _, git_service, workspace = app_services
    (workspace / "commit.txt").write_text("Commit me", encoding="utf-8")
    git_service.stage_file("commit.txt")

    response = client.post(
        "/api/git/commit",
        json={"message": "Commit through API"},
    )

    assert response.status_code == 200
    log = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert log == "Commit through API"


def test_git_commit_validates_message(client):
    response = client.post("/api/git/commit", json={"message": 123})
    assert response.status_code == 400


def test_file_history_endpoint(client, app_services):
    _, _, git_service, workspace = app_services
    (workspace / "tracked.txt").write_text("Tracked", encoding="utf-8")
    git_service.stage_file("tracked.txt")
    git_service.commit_changes("Tracked file commit")

    response = client.get("/api/git/history/tracked.txt")

    assert response.status_code == 200
    assert "Tracked file commit" in response.get_json()["output"]


def test_restore_endpoint_restores_and_commits(client, app_services):
    _, _, git_service, workspace = app_services
    path = workspace / "restore.txt"
    path.write_text("Original", encoding="utf-8")
    git_service.stage_file("restore.txt")
    git_service.commit_changes("Original version")

    original_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    path.write_text("Changed", encoding="utf-8")
    git_service.stage_file("restore.txt")
    git_service.commit_changes("Changed version")

    response = client.post(
        "/api/git/restore/restore.txt",
        json={"commit_id": original_commit},
    )

    assert response.status_code == 200
    assert path.read_text(encoding="utf-8") == "Original"

    latest_message = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert latest_message.startswith("Restored restore.txt to version")


def test_restore_validates_commit_id(client):
    response = client.post("/api/git/restore/file.txt", json={"commit_id": ""})
    assert response.status_code == 400
