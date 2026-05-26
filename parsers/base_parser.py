import os
from abc import ABC, abstractmethod
from utils.crypto import calculate_checksums, format_size

class BaseParser(ABC):
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        self.filename = os.path.basename(file_path)
        self.info = {
            "filename": self.filename,
            "path": self.file_path,
            "size": format_size(self.file_size),
            "size_bytes": self.file_size,
        }
        self.checksums = calculate_checksums(file_path)
        self.info.update(self.checksums)

    @abstractmethod
    def parse(self):
        """Implementar lógica de parsing específica da plataforma"""
        pass

    def get_info(self):
        return self.info
