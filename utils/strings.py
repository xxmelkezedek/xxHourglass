import re

def extract_strings(data, min_length=4, encoding='ascii'):
    """
    Extrai strings legíveis de um bloco de dados binários.
    
    Args:
        data (bytes): Os dados binários para scan.
        min_length (int): Comprimento mínimo da string para ser considerada.
        encoding (str): Encoding para decodificação ('ascii', 'shift_jis', 'utf-8').
        
    Returns:
        list: Lista de dicionários contendo {'offset': int, 'string': str, 'length': int}
    """
    results = []
    # Regex para encontrar sequências de caracteres imprimíveis
    # ASCII imprimível: 0x20 a 0x7E
    if encoding == 'ascii':
        pattern = rb'[ -~]{' + bytes(str(min_length), 'ascii') + rb',}'
    else:
        # Para outros encodings, o regex é mais complexo. 
        # Simplificando para busca de bytes não-nulos e decodificação posterior.
        pattern = rb'[^\x00]{' + bytes(str(min_length), 'ascii') + rb',}'

    for match in re.finditer(pattern, data):
        start = match.start()
        raw_bytes = match.group()
        
        try:
            # Tentar decodificar com o encoding solicitado
            decoded = raw_bytes.decode(encoding)
            # Limpar caracteres de controle se houver (exceto \n, \r, \t)
            cleaned = "".join(c for c in decoded if c.isprintable() or c in "\n\r\t")
            
            if len(cleaned) >= min_length:
                results.append({
                    "offset": start,
                    "string": cleaned,
                    "length": len(cleaned)
                })
        except (UnicodeDecodeError, LookupError):
            continue
            
    return results

def detect_likely_encoding(data):
    """
    Tenta detectar se o bloco de dados contém mais ASCII ou Shift-JIS.
    Útil para ROMs japonesas.
    """
    # Implementação básica: contar bytes no range Shift-JIS vs ASCII
    ascii_count = 0
    sjis_count = 0
    
    for b in data:
        if 0x20 <= b <= 0x7E:
            ascii_count += 1
        if (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xEF):
            sjis_count += 1
            
    return 'shift_jis' if sjis_count > (ascii_count * 0.5) else 'ascii'
