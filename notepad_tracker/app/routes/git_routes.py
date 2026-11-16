from flask import Flask,Blueprint,jsonify,request
from pathlib import Path
import subprocess
from app.services.git_service import GitService
git_bp=Blueprint("git_routes",__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_PATH = PROJECT_ROOT / "workspace"
git_service = GitService(WORKSPACE_PATH)



@git_bp.route("/api/git/init", methods=["POST"])
def initialize_git():
    try:
        result = git_service.initialize_repo()
        return jsonify({
            "message": "Git repository initialized successfully",
            "output": result
        }), 200

    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Git initialization failed",
            "details": e.stderr
        }), 500

    except FileNotFoundError:
        return jsonify({
            "error": "Workspace directory not found"
        }), 404
    
@git_bp.route("/api/git/status",methods=["GET"])
def git_status(): 
    try:
        result=git_service.get_status()
        return jsonify({
            "message":"Git status",
            "output":result
        }),200
    except subprocess.CalledProcessError as e:
        return jsonify({
                    "error": "Unable to retrieve Git status",
                    "details": e.stderr
                }), 500

@git_bp.route("/api/git/stage/<filename>",methods=["POST"])
def stage_file(filename):
    try:
        result=git_service.stage_file(filename)
        return jsonify({
            "message":"File successfully staged",
            "output": result
        }),200
    except FileNotFoundError:
        return jsonify({
            "error":"File not found"
        }),404
    except ValueError:
        return jsonify({
            "error":"Invalid path"
        }),400
    except subprocess.CalledProcessError as e:
        return jsonify({
                    "error": "Unable to stage file",
                    "details": e.stderr
                }), 500        





@git_bp.route("/api/git/commit",methods=["POST"])
def commit_change():
    data=request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    message=data.get("message") 
    if message is None or not isinstance(message, str):
            return jsonify({"error": "message must be a string"}), 400
    try:
        result=git_service.commit_changes(message)
        return jsonify({
            "message":"File commited successfully",
            "output":result
        }),200
    except subprocess.CalledProcessError as e:
        return jsonify({
                            "error": "Unable to stage file",
                            "details": e.stderr
                        }), 500        
        


@git_bp.route("/api/git/history",methods=["GET"])
def git_history():
    try:
        result=git_service.get_history()
        return jsonify({
            "message":"History of the repo",
            "output":result
        }),200
    except subprocess.CalledProcessError as e:
        return jsonify({
                    "error": "Unable to stage file",
                    "details": e.stderr
        }), 500  





@git_bp.route("/api/git/history/<filename>",methods=["GET"])
def file_history(filename):
    try:
        result=git_service.get_file_history(filename)
        return jsonify({
            "message":"History of the file",
            "output":result
        }),200
    except FileNotFoundError:
            return jsonify({
                "error":"File not found"
            }),404
    except ValueError:
            return jsonify({
                "error":"Invalid path"
            }),400
    except subprocess.CalledProcessError as e:
            return jsonify({
                        "error": "Unable to get history of file",
                        "details": e.stderr
                    }), 500 


@git_bp.route("/api/git/restore/<path:filename>", methods=["POST"])
def restore_file(filename):
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    commit_id = data.get("commit_id")

    if not isinstance(commit_id, str) or not commit_id.strip():
        return jsonify({"error": "Valid commit ID is required"}), 400

    try:
        
        git_service.restore_file(filename, commit_id)

        git_service.stage_file(filename)

    
        result = git_service.commit_changes(
            f"Restored {filename} to version {commit_id}"
        )

        return jsonify({
            "message": "File restored and committed successfully",
            "filename": filename,
            "output": result
        }), 200

    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Git restore or commit operation failed",
            "details": e.stderr
        }), 500






    












