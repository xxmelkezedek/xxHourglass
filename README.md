# xxHourglass

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)
![License](https://img.shields.io/badge/License-MIT-orange.svg)


## 🚀 Funcionalidades

- **Identificação Automática:** Detecta plataforma, região, versão e códigos internos
- **Análise Técnica:** Visualização de headers, offsets de entrada (ARM9/ARM7), mapeamento SNES (LoROM/HiROM)
- **Integridade:** Cálculo automático de CRC32, MD5 e SHA1
- **Exploração:** Árvore de arquivos interna (NDS) e visualização hexadecimal do cabeçalho
- **Engenharia Reversa:** Detecção de compressão LZ77


## 🛠️ Arquitetura do Projeto

O projeto segue uma estrutura organizada e modular:

- `/app`: Aplicação
- `/ui`: interface gráfica (PySide6)
- `/parsers`: classes específicas para leitura de cada plataforma (SNESParser, NDSParser)
- `/core`: processamento e análise.
- `/utils`: criptografia, compressão e configuração
- `/assets`: Ícones e recursos visuais

## 📦 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/usuario/pyromhack.git
cd pyromhack
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
python main.py
```



demoscene 4ever

---

