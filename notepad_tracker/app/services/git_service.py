from pathlib import Path
import subprocess
class GitService:

    def __init__(self,repository_path):
        self.repository_path=Path(repository_path)

    def initialize_repo(self):
        file_path=Path(self.repository_path)   
        if not file_path.exists():
            raise FileNotFoundError("File not found")
        if not file_path.is_dir():
            raise NotADirectoryError("not a directory")
        result=subprocess.run(["git","init"],cwd=self.repository_path,capture_output=True,text=True,check=True)
        return result.stdout

    def get_status(self):
        result=subprocess.run(["git","status"],cwd=self.repository_path,capture_output=True,text=True,check=True)
        return result.stdout

    def stage_file(self,filename):
        file_path=Path(self.repository_path/filename).resolve()
        if not file_path.is_relative_to(self.repository_path.resolve()):
            raise ValueError("File is outside the repository")
        relative_path=file_path.relative_to(self.repository_path.resolve())
        if not file_path.exists():
            raise FileNotFoundError("File not found")
        if not file_path.is_file():
            raise ValueError("Not a file")
        result=subprocess.run(["git","add","--",str(relative_path)],cwd=self.repository_path,capture_output=True,text=True,check=True)
        return result.stdout

    def commit_changes(self, message):
        result=subprocess.run(["git","commit","-m",str(message)],cwd=self.repository_path,capture_output=True,text=True,check=True)
        return result.stdout

    def get_history(self):
        result=subprocess.run(["git","log","--oneline"],cwd=self.repository_path,capture_output=True,text=True,check=True)
        return result.stdout

    
    def get_file_history(self, filename):
        repository_path = self.repository_path.resolve()
        file_path = (repository_path / filename).resolve()

        if not file_path.is_relative_to(repository_path):
            raise ValueError("File is outside the repository")

        relative_path = file_path.relative_to(repository_path)

        result = subprocess.run(
            ["git", "log", "--oneline", "--", str(relative_path)],
            cwd=repository_path,
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout


    
    def restore_file(self, filename, commit_id):
        repository_path = self.repository_path.resolve()
        file_path = (repository_path / filename).resolve()
    
        if not file_path.is_relative_to(repository_path):
            raise ValueError("File is outside the repository")
    
        if not isinstance(commit_id, str) or not commit_id.strip():
            raise ValueError("Invalid commit ID")
    
        relative_path = file_path.relative_to(repository_path)
    
        result = subprocess.run(
            [
                "git",
                "restore",
                f"--source={commit_id}",
                "--worktree",
                "--",
                str(relative_path)
            ],
            cwd=repository_path,
            capture_output=True,
            text=True,
            check=True
        )
    
        return result.stdout
    

    
    def stage_deleted_file(self, filename):
        repository_path = Path(self.repository_path).resolve()
        file_path = (repository_path / filename).resolve()

        if not file_path.is_relative_to(repository_path):
            raise ValueError("File is outside the repository")

        if file_path.exists():
            raise ValueError("File has not been deleted")

        relative_path = file_path.relative_to(repository_path)

        result = subprocess.run(
            ["git", "add", "-A", "--", str(relative_path)],
            cwd=repository_path,
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout
