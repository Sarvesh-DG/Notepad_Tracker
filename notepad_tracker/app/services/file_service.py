from pathlib import Path
class FileService:
    def __init__(self,workspace):
        self.workspace=Path(workspace)

    def create_workspace(self):
        directory=Path(self.workspace)
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

    def create_file(self, filename, content):
        workspace_path = Path(self.workspace).resolve()
        file_path = (Path(self.workspace) / filename).resolve()

        if not file_path.is_relative_to(workspace_path):
            raise ValueError("Invalid file path")

        if file_path.exists():
            raise FileExistsError("File already exists")

        if not file_path.parent.exists():
            raise FileNotFoundError("Parent directory does not exist")

        if not file_path.parent.is_dir():
            raise ValueError("Invalid parent directory")

        with file_path.open("x", encoding="utf-8") as file:
            file.write(content)

        return "File created successfully"

    def read_file(self,filename):
        file_path=Path(self.workspace)/filename
        return file_path.read_text()

    def update_file(self,filename, content):
        file_path = Path(self.workspace)/filename
        if file_path.exists():
            file_path.write_text(content)
            return "File successfully updated"
        return "File not found"

    def delete_file(self, filename):
        file_path = (Path(self.workspace) / filename).resolve()
        workspace_path = Path(self.workspace).resolve()
    
        if not file_path.is_relative_to(workspace_path):
            raise ValueError("Invalid file path")
    
        if not file_path.exists():
            raise FileNotFoundError("File not found")
    
        if not file_path.is_file():
            raise ValueError("Path is not a file")
    
        file_path.unlink()
    
        return "File deleted successfully"

    def list_files(self):
        file_path=Path(self.workspace)
        result=[]
        for file in file_path.iterdir():
            if file.is_file():
                result.append(file.name)
        return result