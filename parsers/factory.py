import os
from parsers.snes_parser import SNESParser
from parsers.nds_parser import NDSParser

def get_parser(file_path):
    """
    Detecta a plataforma baseada na extensão e retorna o parser apropriado.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.smc', '.sfc']:
        return SNESParser(file_path)
    elif ext in ['.nds']:
        return NDSParser(file_path)
    else:
        # Tentar detectar por assinatura se a extensão for genérica (futuro)
        return None
