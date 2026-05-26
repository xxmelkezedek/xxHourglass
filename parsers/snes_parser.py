import sys
import os

# Adiciona o diretório raiz ao sys.path para permitir execução direta
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from construct import Struct, PaddedString, Int16ul, Int8ul, Const
from parsers.base_parser import BaseParser

# Estrutura do Header do SNES (21 bytes de info relevante + extras)
# Localizado em 0x7FB0 (LoROM) ou 0xFFB0 (HiROM)
SNES_HEADER = Struct(
    "maker_code" / PaddedString(2, "ascii"),
    "game_code" / PaddedString(4, "ascii"),
    "fixed_value" / Const(b"\x00\x00\x00\x00\x00\x00\x00"),
    "title" / PaddedString(21, "ascii"),
    "map_mode" / Int8ul,
    "cart_type" / Int8ul,
    "rom_size" / Int8ul,
    "ram_size" / Int8ul,
    "region" / Int8ul,
    "developer" / Int8ul,
    "version" / Int8ul,
    "checksum_complement" / Int16ul,
    "checksum" / Int16ul,
)

class SNESParser(BaseParser):
    """
    Parser especializado para ROMs de Super Nintendo.
    
    O SNES possui um sistema de mapeamento complexo (LoROM, HiROM, etc).
    O cabeçalho interno da Nintendo geralmente fica no final de um banco de 32KB.
    Para LoROM, o offset é 0x7FB0. Para HiROM, é 0xFFB0.
    """
    def __init__(self, file_path):
        super().__init__(file_path)
        self.header_offset = 0
        self.has_smc_header = False
        self.platform = "Super Nintendo (SNES)"

    def parse(self):
        """
        Realiza a detecção do tipo de mapeamento e extrai os metadados.
        """
        with open(self.file_path, 'rb') as f:
            # ROMs extraídas de cartuchos antigos muitas vezes possuem um cabeçalho
            # de 512 bytes adicionado por dispositivos de cópia (como o Super Magicom).
            # Verificamos isso pelo resto da divisão do tamanho total por 1024.
            if self.file_size % 1024 == 512:
                self.has_smc_header = True
                offset_modifier = 512
            else:
                offset_modifier = 0

            # Tentar LoROM (0x7FB0)
            f.seek(offset_modifier + 0x7FB0 + 0x0) # Maker Code começa em 0x7FB0? Na verdade Maker code é 0x7FB0-0x7FB1
            # O Header real começa em 0x7FB0
            data = f.read(64) # Ler um bloco maior para garantir
            
            # Tentar detectar se é LoROM ou HiROM baseado no Checksum Complement
            # LoROM Header: 0x7FB0
            # HiROM Header: 0xFFB0
            
            # Tentar LoROM primeiro
            f.seek(offset_modifier + 0x7FB0)
            header_data = f.read(64)
            try:
                parsed = SNES_HEADER.parse(header_data)
                # Validar se o checksum + complemento = 0xFFFF
                if (parsed.checksum + parsed.checksum_complement) == 0xFFFF:
                    self.header_offset = offset_modifier + 0x7FB0
                    self._fill_info(parsed, "LoROM")
                    return self.info
            except:
                pass

            # Tentar HiROM
            f.seek(offset_modifier + 0xFFB0)
            header_data = f.read(64)
            try:
                parsed = SNES_HEADER.parse(header_data)
                if (parsed.checksum + parsed.checksum_complement) == 0xFFFF:
                    self.header_offset = offset_modifier + 0xFFB0
                    self._fill_info(parsed, "HiROM")
                    return self.info
            except:
                pass

            # Fallback se falhar a validação estrita
            self.info["platform"] = self.platform
            self.info["status"] = "Header não validado (possível ROM corrompida ou modificada)"
            return self.info

    def _fill_info(self, parsed, map_type):
        self.info.update({
            "platform": self.platform,
            "title": parsed.title.strip(),
            "game_code": parsed.game_code.strip(),
            "maker_code": parsed.maker_code.strip(),
            "mapper": map_type,
            "version": f"1.{parsed.version}",
            "region_code": hex(parsed.region),
            "rom_size_id": hex(parsed.rom_size),
            "header_offset": hex(self.header_offset),
            "smc_header": "Sim" if self.has_smc_header else "Não"
        })

    def get_file_list(self):
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parser = SNESParser(sys.argv[1])
        print(parser.parse())
    else:
        print("Uso: python snes_parser.py <path_to_rom>")
