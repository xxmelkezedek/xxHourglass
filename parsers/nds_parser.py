import sys
import os
import ndspy.rom
import ndspy.fnt

# Adiciona o diretório raiz ao sys.path para permitir execução direta
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.base_parser import BaseParser
from utils.crypto import format_size

class NDSParser(BaseParser):
    """
    Parser para ROMs de Nintendo DS.
    
    A estrutura do NDS é similar a um sistema de arquivos.
    O header de 512 bytes contém ponteiros para:
    - ARM9/ARM7: Os executáveis principais dos processadores.
    - FNT (File Name Table): Nomes dos arquivos internos.
    - FAT (File Allocation Table): Localização física dos arquivos na ROM.
    """
    def __init__(self, file_path):
        super().__init__(file_path)
        self.platform = "Nintendo DS (NDS)"
        self.files = []
        self.file_tree = {"name": "/", "files": [], "dirs": {}}

    def parse(self):
        """
        Lê a ROM NDS utilizando a biblioteca ndspy para maior compatibilidade.
        """
        try:
            self.rom = ndspy.rom.NintendoDSRom.fromFile(self.file_path)
            
            self.info.update({
                "platform": self.platform,
                "title": self.rom.name.decode('ascii', errors='ignore').strip(),
                "game_code": self.rom.idCode.decode('ascii', errors='ignore'),
                "maker_code": self.rom.developerCode.decode('ascii', errors='ignore'),
                "version": f"1.{self.rom.version}",
                "rom_size": format_size(os.path.getsize(self.file_path)),
                "arm9_size": f"{len(self.rom.arm9)} bytes",
                "arm7_size": f"{len(self.rom.arm7)} bytes",
                "total_files": len(self.rom.files)
            })
            
            # Construir árvore de arquivos usando ndspy.fnt
            if self.rom.filenames:
                self.file_tree = self._build_tree_from_ndspy(self.rom.filenames)
            else:
                # Fallback: Criar lista flat se não houver nomes
                self.file_tree = {"name": "/", "files": [], "dirs": {}}
                for i in range(len(self.rom.files)):
                    self.file_tree["files"].append({
                        "name": f"File_{i:04d}.bin",
                        "offset": 0,
                        "id": i,
                        "size": len(self.rom.files[i])
                    })
            
        except Exception as e:
            self.info["platform"] = self.platform
            self.info["error"] = f"Erro ao ler ROM com ndspy: {str(e)}"
            # Inicializar tree vazia em caso de erro crítico
            self.file_tree = {"name": "/", "files": [], "dirs": {}}
        
        return self.info

    def _build_tree_from_ndspy(self, fnt_node, name="/"):
        """
        Converte a estrutura de nomes do ndspy para o nosso formato de árvore.
        """
        tree = {"name": name, "files": [], "dirs": {}}
        
        try:
            # No ndspy, fnt_node é um objeto Folder
            # Adicionar arquivos
            for i, file_name in enumerate(fnt_node.files):
                file_id = fnt_node.firstID + i
                if file_id < len(self.rom.files):
                    file_data = self.rom.files[file_id]
                    tree["files"].append({
                        "name": file_name,
                        "offset": 0,
                        "id": file_id,
                        "size": len(file_data)
                    })
            
            # Adicionar diretórios
            for dir_name, sub_node in fnt_node.folders:
                tree["dirs"][dir_name] = self._build_tree_from_ndspy(sub_node, dir_name)
        except Exception as e:
            print(f"Erro ao construir árvore: {e}")
        
        return tree

    def get_file_tree(self):
        return self.file_tree

    def get_file_list(self):
        return self.files

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parser = NDSParser(sys.argv[1])
        print(parser.parse())
    else:
        print("Uso: python nds_parser.py <path_to_rom>")
