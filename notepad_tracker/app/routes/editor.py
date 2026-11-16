
from flask import Blueprint, jsonify, request, render_template
from pathlib import Path
from app.services.instances import file_service, git_service
import subprocess
import tkinter as tk
from tkinter import filedialog


editor_bp = Blueprint("editor", __name__)


# --------------------------------------------------
# LIST FILES
# --------------------------------------------------

@editor_bp.route("/api/files", methods=["GET"])
def list_files():
    result = file_service.list_files()
    return jsonify([{"file": file} for file in result]), 200


# --------------------------------------------------
# READ FILE
# --------------------------------------------------

@editor_bp.route("/api/files/<filename>", methods=["GET"])
def read_file(filename):
    try:
        result = file_service.read_file(filename)

        return jsonify({
            "filename": filename,
            "content": result
        }), 200

    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# --------------------------------------------------
# CREATE FILE
# --------------------------------------------------

@editor_bp.route("/api/files", methods=["POST"])
def create_file():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    filename = data.get("filename")
    content = data.get("content")

    if not filename or not isinstance(filename, str):
        return jsonify({"error": "Filename is required"}), 400

    if content is None or not isinstance(content, str):
        return jsonify({"error": "Content must be a string"}), 400

    try:
        # Resolve relative to the currently selected directory
        file_path = file_service.resolve_path(filename)

        if file_path.exists():
            return jsonify({"error": "File already exists"}), 409

        file_service.create_file(filename, content)

        # Stage and commit the newly created file
        git_service.stage_file(filename)
        git_service.commit_changes(f"Created {filename}")

        return jsonify({
            "message": "File created and committed successfully",
            "filename": filename
        }), 201

    except FileExistsError:
        return jsonify({"error": "File already exists"}), 409

    except FileNotFoundError:
        return jsonify({"error": "Parent directory not found"}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "File created, but Git operation failed",
            "details": e.stderr
        }), 500


# --------------------------------------------------
# UPDATE FILE
# --------------------------------------------------

@editor_bp.route("/api/files/<filename>", methods=["PUT"])
def update_file(filename):
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or "content" not in data:
        return jsonify({"error": "Content is required"}), 400

    if not isinstance(data["content"], str):
        return jsonify({"error": "Content must be a string"}), 400

    try:
        # Resolve relative to the currently selected directory
        file_path = file_service.resolve_path(filename)

        if not file_path.exists() or not file_path.is_file():
            return jsonify({"error": "File not found"}), 404

        file_service.update_file(filename, data["content"])

        # Stage and commit the updated file
        git_service.stage_file(filename)
        git_service.commit_changes(f"Updated {filename}")

        return jsonify({
            "message": "File updated successfully"
        }), 200

    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "File updated, but Git operation failed",
            "details": e.stderr
        }), 500


# --------------------------------------------------
# DELETE FILE
# --------------------------------------------------

@editor_bp.route("/api/files/<filename>", methods=["DELETE"])
def delete_file(filename):
    try:
        # Resolve relative to the currently selected directory
        file_path = file_service.resolve_path(filename)

        if not file_path.exists() or not file_path.is_file():
            return jsonify({"error": "File not found"}), 404

        file_service.delete_file(filename)

        # Stage deletion and commit
        git_service.stage_deleted_file(filename)
        git_service.commit_changes(f"Deleted {filename}")

        return jsonify({
            "message": "File deleted and committed successfully",
            "filename": filename
        }), 200

    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "File deleted, but Git operation failed",
            "details": e.stderr
        }), 500


# --------------------------------------------------
# SELECT WORKSPACE FOLDER
# --------------------------------------------------

@editor_bp.route("/api/select-folder", methods=["POST"])
def select_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        selected_folder = filedialog.askdirectory(
            title="Select a folder for Notepad Tracker"
        )
    finally:
        root.destroy()

    if not selected_folder:
        return jsonify({
            "message": "Folder selection cancelled"
        }), 200

    try:
        selected_path = Path(selected_folder).resolve()

        file_service.set_workspace(selected_path)

        git_initialized = git_service.set_repository(selected_path)

        # Synchronize Git with the selected directory
        git_service.working_directory = file_service.current_directory

        return jsonify({
            "message": "Folder selected successfully",
            "directory": str(selected_path),
            "git_initialized": git_initialized,
            "files": file_service.list_files(),
            "directories": file_service.list_directories()
        }), 200

    except (FileNotFoundError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@editor_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# --------------------------------------------------
# LIST DIRECTORIES
# --------------------------------------------------

@editor_bp.route("/api/directories", methods=["GET"])
def list_directories():
    try:
        result = file_service.list_directories()

        return jsonify(result), 200

    except FileNotFoundError:
        return jsonify({
            "error": "Directory not found"
        }), 404

    except PermissionError:
        return jsonify({
            "error": "Permission denied"
        }), 403


# --------------------------------------------------
# NAVIGATE INTO DIRECTORY
# --------------------------------------------------

@editor_bp.route("/api/navigate-directory", methods=["POST"])
def navigate_directory():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid JSON body"
        }), 400

    directory = data.get("directory")

    if not isinstance(directory, str) or not directory.strip():
        return jsonify({
            "error": "Directory name is required"
        }), 400

    try:
        result = file_service.navigate_directory(directory)

        # Synchronize Git with the current directory
        git_service.working_directory = file_service.current_directory

        return jsonify({
            "message": "Directory opened successfully",
            "directory": result,
            "files": file_service.list_files(),
            "directories": file_service.list_directories()
        }), 200

    except FileNotFoundError:
        return jsonify({
            "error": "Directory not found"
        }), 404

    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400

    except PermissionError:
        return jsonify({
            "error": "Permission denied"
        }), 403


# --------------------------------------------------
# NAVIGATE TO PARENT DIRECTORY
# --------------------------------------------------

@editor_bp.route("/api/navigate-parent", methods=["POST"])
def navigate_parent():
    try:
        result = file_service.navigate_parent()

        # Synchronize Git with the current directory
        git_service.working_directory = file_service.current_directory

        return jsonify({
            "message": "Parent directory opened",
            "directory": result,
            "files": file_service.list_files(),
            "directories": file_service.list_directories()
        }), 200

    except PermissionError:
        return jsonify({
            "error": "Permission denied"
        }), 403
