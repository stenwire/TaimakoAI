import os
import shutil
from abc import ABC, abstractmethod
from typing import BinaryIO

class BaseFileStorage(ABC):
    @abstractmethod
    def save(self, file_obj: BinaryIO, filename: str, user_id: str) -> str:
        """Saves file and returns the relative path or ID."""
        pass

    @abstractmethod
    def get_full_path(self, file_path: str) -> str:
        """Returns full filesystem path (for local processing)."""
        pass
    
    @abstractmethod
    def list_files(self, user_id: str) -> list[str]:
        """Lists files for a user."""
        pass

    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """Deletes a file."""
        pass

class LocalFileStorage(BaseFileStorage):
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save(self, file_obj: BinaryIO, filename: str, user_id: str) -> str:
        user_dir = os.path.join(self.base_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        file_path = os.path.join(user_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        # Return relative path from base_dir, or just the path itself
        # Storing relative to project root or absolute? 
        # Let's return path relative to project root for consistency.
        return file_path

    def get_full_path(self, file_path: str) -> str:
        return os.path.abspath(file_path)

    def list_files(self, user_id: str) -> list[str]:
        user_dir = os.path.join(self.base_dir, user_id)
        if not os.path.exists(user_dir):
            return []
        return os.listdir(user_dir)

    def delete(self, file_path: str) -> bool:
        full_path = self.get_full_path(file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

file_storage = LocalFileStorage()
