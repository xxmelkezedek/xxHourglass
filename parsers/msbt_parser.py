from construct import Struct, Const, Int32ul, Int16ul, Array, Bytes, Int8ul
import struct

# Estrutura do MSBT (Message Sequence Binary Text)
MSBT_HEADER = Struct(
    "magic" / Const(b"MsgStdBn"),
    "endian" / Const(b"\xFE\xFF"),
    "unknown1" / Int16ul,
    "encoding" / Int8ul, # 0 = UTF-8, 1 = UTF-16
    "unknown2" / Int8ul,
    "num_sections" / Int16ul,
    "unknown3" / Int16ul,
    "file_size" / Int32ul,
    "padding" / Bytes(10),
)

class MSBTParser:
    """
    Parser para o formato MSBT, usado em Zelda: Phantom Hourglass para textos e diálogos.
    """
    def __init__(self, data):
        self.data = data
        self.messages = []

    def clean_text(self, text):
        """
        Limpa ou interpreta códigos de controle no texto.
        No Zelda PH, códigos começam com 0x0E (ou similar dependendo do jogo).
        """
        cleaned = []
        i = 0
        while i < len(text):
            char = text[i]
            # Em UTF-16, códigos de controle MSBT geralmente seguem um padrão
            # de escape. Aqui fazemos uma limpeza básica.
            if ord(char) < 0x20 and char not in "\n\r\t":
                # Poderíamos expandir aqui para identificar tags específicas [COLOR:RED], etc.
                cleaned.append(f"<{hex(ord(char))}>")
            else:
                cleaned.append(char)
            i += 1
        return "".join(cleaned)

    def parse(self):
        try:
            if self.data[:8] != b"MsgStdBn":
                return []
                
            header = MSBT_HEADER.parse(self.data)
            encoding = 'utf-16-le' if header.encoding == 1 else 'utf-8'
            
            pos = 32 # Tamanho do header
            sections = {}
            
            for _ in range(header.num_sections):
                if pos + 8 > len(self.data): break
                magic = self.data[pos:pos+4].decode('ascii', errors='ignore')
                size = struct.unpack('<I', self.data[pos+4:pos+8])[0]
                sections[magic] = self.data[pos+16 : pos+16+size]
                pos += 16 + ((size + 15) & ~15) # Alinhamento de 16 bytes
            
            # LBL1: Labels (Nomes das mensagens)
            labels = []
            if "LBL1" in sections:
                lbl_data = sections["LBL1"]
                num_groups = struct.unpack('<I', lbl_data[:4])[0]
                # Lógica simplificada para extrair labels se existirem
                # (Zelda PH geralmente usa labels para identificar as mensagens)
                pass

            # TXT2 / STRG: Texto real
            txt_key = "TXT2" if "TXT2" in sections else "STRG"
            
            if txt_key in sections:
                txt_data = sections[txt_key]
                num_msgs = struct.unpack('<I', txt_data[:4])[0]
                
                if num_msgs > 20000: # Segurança
                    return []

                # Alguns MSBTs têm 4 bytes extras de unknown/padding após o num_msgs
                # Verificamos se o primeiro offset faz sentido. 
                # Se o primeiro offset for 4 + num_msgs * 4, é o padrão.
                # Se for 8 + num_msgs * 4, tem o extra.
                header_size = 4
                first_offset = struct.unpack('<I', txt_data[4:8])[0]
                if first_offset == 8 + num_msgs * 4:
                    header_size = 8

                offsets = [struct.unpack('<I', txt_data[header_size + i*4 : header_size + 4 + i*4])[0] for i in range(num_msgs)]
                
                for i in range(num_msgs):
                    start = offsets[i]
                    end = offsets[i+1] if i+1 < num_msgs else len(txt_data)
                    
                    if start >= len(txt_data) or end > len(txt_data) or start > end:
                        continue
                        
                    msg_bytes = txt_data[start:end]
                    
                    try:
                        # MSBT termina cada string com nulo
                        raw_text = msg_bytes.decode(encoding, errors='ignore').split('\0')[0]
                        text = self.clean_text(raw_text)
                        
                        self.messages.append({
                            "id": i,
                            "label": labels[i] if i < len(labels) else f"MSG_{i}",
                            "text": text,
                            "raw": raw_text
                        })
                    except:
                        continue
            
            return self.messages
        except Exception as e:
            print(f"Erro ao parsear MSBT: {e}")
            return []
