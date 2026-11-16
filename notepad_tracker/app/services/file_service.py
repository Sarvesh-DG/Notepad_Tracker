
from pathlib import Path


class FileService:

    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
        self.current_directory = self.workspace

    def create_workspace(self):
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.current_directory = self.workspace

    def set_workspace(self, directory):
        directory = Path(directory).resolve()

        if not directory.exists():
            raise FileNotFoundError("Directory not found")

        if not directory.is_dir():
            raise ValueError("Path is not a directory")

        self.workspace = directory
        self.current_directory = directory

   
    def resolve_path(self, filename):
        file_path = (self.current_directory / filename).resolve()

        if not file_path.is_relative_to(self.workspace):
            raise ValueError("Invalid file path")

        return file_path

    def navigate_directory(self, directory):
        new_directory = self.resolve_path(directory)

        if not new_directory.exists():
            raise FileNotFoundError("Directory not found")

        if not new_directory.is_dir():
            raise ValueError("Not a directory")

        self.current_directory = new_directory

        return str(self.current_directory)

    def navigate_parent(self):
        if self.current_directory != self.workspace:
            self.current_directory = self.current_directory.parent

        return str(self.current_directory)


    def list_directories(self):
        return sorted(
        item.name
        for item in self.current_directory.iterdir()
        if item.is_dir() and item.name != ".git"
    )

    
    def create_file(self, filename, content):
        file_path = self.resolve_path(filename)

        if file_path.exists():
            raise FileExistsError("File already exists")

        if not file_path.parent.exists():
            raise FileNotFoundError("Parent directory does not exist")

        if not file_path.parent.is_dir():
            raise ValueError("Invalid parent directory")

        with file_path.open("x", encoding="utf-8") as file:
            file.write(content)

        return "File created successfully"


    def read_file(self, filename):
        file_path = self.resolve_path(filename)

        if not file_path.exists():
            raise FileNotFoundError("File not found")

        if not file_path.is_file():
            raise ValueError("Not a file")

        return file_path.read_text(encoding="utf-8")


    def update_file(self, filename, content):
        file_path = self.resolve_path(filename)

        if not file_path.exists():
            raise FileNotFoundError("File not found")

        if not file_path.is_file():
            raise ValueError("Not a file")

        file_path.write_text(content, encoding="utf-8")

        return "File successfully updated"

  
    def delete_file(self, filename):
        file_path = self.resolve_path(filename)

        if not file_path.exists():
            raise FileNotFoundError("File not found")

        if not file_path.is_file():
            raise ValueError("Path is not a file")

        file_path.unlink()

        return "File deleted successfully"

 
    def list_files(self):
        result = []

        for item in self.current_directory.iterdir():
            if item.is_file():
                result.append(item.name)

        return result
