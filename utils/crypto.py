import hashlib
import zlib

def calculate_checksums(file_path):
    """
    Calcula CRC32, MD5 e SHA1 de um arquivo.
    """
    crc32 = 0
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            crc32 = zlib.crc32(chunk, crc32)
            md5.update(chunk)
            sha1.update(chunk)
            
    return {
        "crc32": format(crc32 & 0xFFFFFFFF, '08X'),
        "md5": md5.hexdigest().upper(),
        "sha1": sha1.hexdigest().upper()
    }

def format_size(size_bytes):
    """
    Formata o tamanho em bytes para uma string legível.
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"
