from construct import Struct, Const, Int32ul, Int16ul, Array, Bytes, Tell
import os

# Estrutura de um arquivo NARC (Nitro Archive)
NARC_HEADER = Struct(
    "magic" / Const(b"NARC"),
    "endian" / Const(b"\xFE\xFF"),
    "version" / Int16ul,
    "file_size" / Int32ul,
    "header_size" / Int16ul,
    "num_sections" / Int16ul,
)

BTAF_SECTION = Struct(
    "magic" / Const(b"BTAF"),
    "section_size" / Int32ul,
    "num_files" / Int32ul,
)

FAT_ENTRY = Struct(
    "start_offset" / Int32ul,
    "end_offset" / Int32ul,
)

class NARCParser:
    """
    Parser para arquivos NARC (.narc), usados para empacotar múltiplos arquivos.
    Comum em jogos como Zelda PH, Pokemon, etc.
    """
    def __init__(self, data):
        self.data = data
        self.files = []

    def parse(self):
        try:
            header = NARC_HEADER.parse(self.data)
            pos = header.header_size
            
            # 1. BTAF (Allocation Table)
            btaf = BTAF_SECTION.parse(self.data[pos:])
            pos += 8 # Pular magic e section_size
            num_files = Int32ul.parse(self.data[pos:pos+4])
            pos += 4
            
            fat_entries = Array(num_files, FAT_ENTRY).parse(self.data[pos:])
            pos = header.header_size + btaf.section_size
            
            # 2. BTNF (Name Table) - Muitas vezes não tem nomes, apenas IDs
            # Vamos pular por enquanto para ir direto aos dados (GMAD)
            btnf_magic = self.data[pos:pos+4]
            btnf_size = Int32ul.parse(self.data[pos+4:pos+8])
            pos += btnf_size
            
            # 3. GMAD (Images/Data)
            gmad_magic = self.data[pos:pos+4]
            if gmad_magic != b"GMAD":
                return []
            
            data_start = pos + 8
            
            for i, entry in enumerate(fat_entries):
                file_data = self.data[data_start + entry.start_offset : data_start + entry.end_offset]
                self.files.append({
                    "id": i,
                    "data": file_data,
                    "size": len(file_data)
                })
                
            return self.files
        except Exception as e:
            print(f"Erro ao parsear NARC: {e}")
            return []
