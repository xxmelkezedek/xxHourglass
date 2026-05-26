def is_lz77_compressed(data):
    """
    Verifica se o dado começa com o cabeçalho LZ77 (0x10).
    """
    if len(data) < 4:
        return False
    
    # Cabeçalho LZ77 comum em NDS: 0x10 seguido pelo tamanho de 3 bytes (LE)
    if data[0] == 0x10:
        decompressed_size = data[1] | (data[2] << 8) | (data[3] << 16)
        if 0 < decompressed_size < 0x01000000: # Limite razoável de 16MB
            return True
    return False

def decompress_lz77(data):
    """
    Descompressor LZ77 básico para NDS (Tipo 0x10).
    """
    if not is_lz77_compressed(data):
        return None
    
    decompressed_size = data[1] | (data[2] << 8) | (data[3] << 16)
    out = bytearray()
    pos = 4
    
    while len(out) < decompressed_size and pos < len(data):
        flags = data[pos]
        pos += 1
        
        for i in range(7, -1, -1):
            if len(out) >= decompressed_size or pos >= len(data):
                break
                
            if (flags >> i) & 1:
                # Bloco comprimido (2 bytes)
                if pos + 1 >= len(data):
                    break
                b1 = data[pos]
                b2 = data[pos+1]
                pos += 2
                
                # NDS LZ77: [XXXXYYYY YYYYYYYY]
                # XXXX+3 = length, YYYYYYYYYYYY+1 = distance back
                length = (b1 >> 4) + 3
                distance = (((b1 & 0x0F) << 8) | b2) + 1
                
                for _ in range(length):
                    if len(out) >= decompressed_size:
                        break
                    back_pos = len(out) - distance
                    if back_pos >= 0:
                        out.append(out[back_pos])
            else:
                # Byte literal
                out.append(data[pos])
                pos += 1
                
    return bytes(out)
