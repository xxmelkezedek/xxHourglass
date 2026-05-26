import sys
import os
#athooooooooooooooooooooooooooooos
# Adiciona o diretório raiz ao sys.path para permitir execução direta
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.strings import extract_strings, detect_likely_encoding
from parsers.narc_parser import NARCParser
from parsers.msbt_parser import MSBTParser
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QDockWidget, QListWidget, QTreeWidget, QTextEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QFileDialog, QMenuBar, QMenu, QStatusBar, QTreeWidgetItem,
                             QLineEdit, QPushButton, QComboBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QFont, QColor, QPalette, QPixmap, QImage
from utils.config import add_recent_file, load_config

from parsers.factory import get_parser

class PyRomHackApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("xxHourglass - by xxmelkezedek ")
        self.resize(1200, 800)
        self.setAcceptDrops(True)
        
        # Setup Theme
        self.apply_dark_theme()
        
        # Central Widget (Technical Info)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        
        self.info_table = QTableWidget(0, 2)
        self.info_table.setHorizontalHeaderLabels(["Propriedade", "Valor"])
        self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.info_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.central_layout.addWidget(QLabel("<b>Informações Técnicas</b>"))
        self.central_layout.addWidget(self.info_table)
        
        # Create Docks
        self.create_docks()
        
        # Menu Bar
        self.create_menu_bar()
        self.update_recent_files_menu()
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Pronto")

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Segoe UI', sans-serif;
            }
            QDockWidget::title {
                background-color: #333333;
                padding: 5px;
            }
            QTableWidget {
                background-color: #252526;
                gridline-color: #3f3f46;
                border: 1px solid #3f3f46;
            }
            QHeaderView::section {
                background-color: #333333;
                color: #00ccff;
                padding: 4px;
                border: 1px solid #3f3f46;
            }
            QTreeWidget, QListWidget, QTextEdit {
                background-color: #252526;
                border: 1px solid #3f3f46;
            }
            QMenuBar {
                background-color: #333333;
            }
            QMenuBar::item:selected {
                background-color: #444444;
            }
            QMenu {
                background-color: #333333;
                border: 1px solid #444444;
            }
            QMenu::item:selected {
                background-color: #007acc;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
        """)

    def create_docks(self):
        # Left Dock: ROM Tree / File System
        self.left_dock = QDockWidget("Explorador de Arquivos", self)
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Nome", "Offset", "Tamanho"])
        self.file_tree.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.left_dock.setWidget(self.file_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
        
        # Bottom Dock: Logs / Console
        self.bottom_dock = QDockWidget("Console de Saída", self)
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setFont(QFont("Consolas", 10))
        self.bottom_dock.setWidget(self.log_console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
        
        # Right Dock: Preview / Hex View
        self.right_dock = QDockWidget("Preview & Análise", self)
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        
        # Sprite Preview Area
        self.preview_label = QLabel("Visualizador de Assets")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 200)
        self.preview_label.setStyleSheet("border: 1px solid #3f3f46; background: #000;")
        self.right_layout.addWidget(self.preview_label)
        
        # Hex Preview
        self.hex_view = QTextEdit()
        self.hex_view.setReadOnly(True)
        self.hex_view.setFont(QFont("Consolas", 9))
        self.right_layout.addWidget(QLabel("Hex View (Header)"))
        self.right_layout.addWidget(self.hex_view)
        
        self.right_dock.setWidget(self.right_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)

        # New Dock: Strings Analysis
        self.create_strings_dock()

    def create_strings_dock(self):
        self.strings_dock = QDockWidget("Análise de Strings", self)
        self.strings_widget = QWidget()
        self.strings_layout = QVBoxLayout(self.strings_widget)

        # Controls
        ctrl_layout = QHBoxLayout()
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["ASCII", "Shift-JIS", "UTF-8"])
        self.encoding_combo.currentTextChanged.connect(self.rescan_strings)
        self.search_strings = QLineEdit()
        self.search_strings.setPlaceholderText("Filtrar strings...")
        self.search_strings.textChanged.connect(self.filter_strings)
        
        ctrl_layout.addWidget(QLabel("Encoding:"))
        ctrl_layout.addWidget(self.encoding_combo)
        ctrl_layout.addWidget(self.search_strings)
        self.strings_layout.addLayout(ctrl_layout)

        # Table
        self.strings_table = QTableWidget(0, 3)
        self.strings_table.setHorizontalHeaderLabels(["Offset", "String", "Len"])
        self.strings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.strings_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.strings_layout.addWidget(self.strings_table)

        self.strings_dock.setWidget(self.strings_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.strings_dock)
        self.tabifyDockWidget(self.bottom_dock, self.strings_dock)

        # New Dock: Zelda PH Script Viewer
        self.create_zelda_dock()

    def create_zelda_dock(self):
        self.zelda_dock = QDockWidget("Zelda PH: Script Viewer", self)
        self.zelda_widget = QWidget()
        self.zelda_layout = QVBoxLayout(self.zelda_widget)

        # Barra de Busca Global
        search_layout = QHBoxLayout()
        self.global_search_input = QLineEdit()
        self.global_search_input.setPlaceholderText("Busca global nos diálogos (Pressione Enter)...")
        self.global_search_input.returnPressed.connect(self.perform_global_dialogue_search)
        
        self.btn_global_search = QPushButton("Buscar na ROM")
        self.btn_global_search.clicked.connect(self.perform_global_dialogue_search)
        
        search_layout.addWidget(self.global_search_input)
        search_layout.addWidget(self.btn_global_search)
        self.zelda_layout.addLayout(search_layout)

        self.zelda_info = QLabel("Abra um arquivo .narc ou .msbt do Zelda PH para visualizar os diálogos.")
        self.zelda_layout.addWidget(self.zelda_info)

        self.script_table = QTableWidget(0, 3)
        self.script_table.setHorizontalHeaderLabels(["ID", "Local", "Diálogo / Texto"])
        self.script_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.script_table.setStyleSheet("font-size: 11pt; color: #00ff00;")
        self.zelda_layout.addWidget(self.script_table)

        # Botão de Exportação
        self.btn_export = QPushButton("Exportar Diálogos Carregados")
        self.btn_export.clicked.connect(self.export_current_dialogues)
        self.zelda_layout.addWidget(self.btn_export)

        self.zelda_dock.setWidget(self.zelda_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.zelda_dock)

    def perform_global_dialogue_search(self):
        query = self.global_search_input.text().strip().lower()
        if not query or not hasattr(self, 'current_parser') or self.current_parser.platform != "Nintendo DS (NDS)":
            return

        self.log(f"Iniciando busca global por: '{query}'...", "#ffa500")
        self.script_table.setRowCount(0)
        
        import ndspy.narc
        import ndspy.lz10
        rom = self.current_parser.rom
        found_count = 0
        total_checked = 0

        # Iterar por todos os arquivos da ROM
        for i, file_data in enumerate(rom.files):
            total_checked += 1
            if total_checked % 500 == 0:
                self.log(f"Processando... {total_checked}/{len(rom.files)} arquivos verificados.", "#888888")
            
            data = file_data
            # Tentar descompressão LZ77 se o dado começar com 0x10
            if len(data) > 4 and data[0] == 0x10:
                try:
                    data = ndspy.lz10.decompress(data)
                except:
                    pass

            # 1. Verificar se é MSBT direto
            if data[:8] == b"MsgStdBn":
                found_count += self._search_in_msbt(data, query, f"ROM File {i}")
            
            # 2. Verificar se é NARC e buscar dentro dele
            elif data[:4] == b"NARC":
                try:
                    narc = ndspy.narc.NARC(data)
                    for j, sub_data in enumerate(narc.files):
                        s_data = sub_data
                        if len(s_data) > 4 and s_data[0] == 0x10:
                            try:
                                s_data = ndspy.lz10.decompress(s_data)
                            except:
                                pass
                        
                        if s_data[:8] == b"MsgStdBn":
                            found_count += self._search_in_msbt(s_data, query, f"NARC {i} Sub {j}")
                except:
                    continue

        self.log(f"Busca concluída. {found_count} ocorrências encontradas.", "#00ff00")
        self.zelda_info.setText(f"Resultados da busca: {found_count} mensagens encontradas.")

    def _search_in_msbt(self, data, query, location):
        msbt = MSBTParser(data)
        messages = msbt.parse()
        found = 0
        for msg in messages:
            if query in msg['text'].lower():
                row = self.script_table.rowCount()
                self.script_table.insertRow(row)
                self.script_table.setItem(row, 0, QTableWidgetItem(str(msg['id'])))
                self.script_table.setItem(row, 1, QTableWidgetItem(location))
                self.script_table.setItem(row, 2, QTableWidgetItem(msg['text']))
                found += 1
        return found

    def export_current_dialogues(self):
        if self.script_table.rowCount() == 0:
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Diálogos", "", "Text Files (*.txt);;JSON Files (*.json)")
        if not path:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                if path.endswith('.json'):
                    import json
                    data = []
                    for row in range(self.script_table.rowCount()):
                        data.append({
                            "id": self.script_table.item(row, 0).text(),
                            "location": self.script_table.item(row, 1).text(),
                            "text": self.script_table.item(row, 2).text()
                        })
                    json.dump(data, f, indent=4, ensure_ascii=False)
                else:
                    for row in range(self.script_table.rowCount()):
                        f.write(f"ID: {self.script_table.item(row, 0).text()} | ")
                        f.write(f"Loc: {self.script_table.item(row, 1).text()}\n")
                        f.write(f"{self.script_table.item(row, 2).text()}\n")
                        f.write("-" * 40 + "\n")
            self.log(f"Diálogos exportados para: {path}", "#00ff00")
        except Exception as e:
            self.log(f"Erro ao exportar: {e}", "#ff3333")

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # Arquivo
        self.file_menu = menubar.addMenu("&Arquivo")
        open_action = QAction("Abrir ROM...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_rom_dialog)
        self.file_menu.addAction(open_action)
        
        self.recent_menu = self.file_menu.addMenu("Arquivos Recentes")
        
        self.file_menu.addSeparator()
        
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)
        
        # Ferramentas
        tools_menu = menubar.addMenu("&Ferramentas")
        tools_menu.addAction("Busca Hexadecimal")
        export_action = QAction("Exportar Relatório", self)
        export_action.triggered.connect(self.export_report)
        tools_menu.addAction(export_action)
        
        # Ajuda
        help_menu = menubar.addMenu("&Ajuda")
        help_menu.addAction("Sobre")

    def update_recent_files_menu(self):
        self.recent_menu.clear()
        config = load_config()
        for f in config.get("recent_files", []):
            action = QAction(os.path.basename(f), self)
            action.setData(f)
            action.triggered.connect(lambda checked, path=f: self.load_rom(path))
            self.recent_menu.addAction(action)

    def log(self, message, color="#d4d4d4"):
        self.log_console.append(f'<span style="color:{color}">{message}</span>')

    def open_rom_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir ROM", "", "ROMs (*.nds *.smc *.sfc);;Todos os arquivos (*.*)"
        )
        if file_path:
            self.load_rom(file_path)

    def load_rom(self, file_path):
        self.current_file_path = file_path
        self.log(f"Carregando: {file_path}", "#00ccff")
        add_recent_file(file_path)
        self.update_recent_files_menu()
        
        self.current_parser = get_parser(file_path)
        
        if not self.current_parser:
            self.log("Erro: Plataforma não suportada!", "#ff3333")
            return
            
        try:
            info = self.current_parser.parse()
            self.display_info(info)
            self.statusBar().showMessage(f"ROM Carregada: {info.get('title', 'Desconhecido')}")
            
            # Atualizar Árvore de Arquivos
            self.file_tree.clear()
            if hasattr(self.current_parser, 'get_file_tree'):
                tree_data = self.current_parser.get_file_tree()
                self.log(f"Populando árvore de arquivos...", "#00ccff")
                self._populate_tree(self.file_tree.invisibleRootItem(), tree_data)
            else:
                files = self.current_parser.get_file_list()
                if files:
                    root = QTreeWidgetItem(self.file_tree, [info.get("platform", "ROM")])
                    for f_info in files:
                        QTreeWidgetItem(root, [f_info["name"], hex(f_info["offset"]), str(f_info["size"])])
                    root.setExpanded(True)
                else:
                    QTreeWidgetItem(self.file_tree, ["Nenhum sistema de arquivos detectado"])

            self.log(f"Total de arquivos mapeados: {info.get('total_files', 0)}", "#00ff00")

            # Atualizar Hex Preview (primeiros 512 bytes)
            with open(file_path, 'rb') as f:
                data = f.read(512)
                self.update_hex_preview(data)
                
                # Check for LZ77
                from utils.compression import is_lz77_compressed
                if is_lz77_compressed(data):
                    self.log("Aviso: Cabeçalho LZ77 detectado no início do arquivo!", "#ffa500")

            # Scan Strings (limitado aos primeiros 1MB para performance inicial)
            with open(file_path, 'rb') as f:
                scan_data = f.read(1024 * 1024)
                encoding = self.encoding_combo.currentText().lower().replace("-", "_")
                self.all_strings = extract_strings(scan_data, encoding=encoding)
                self.update_strings_table(self.all_strings)

            self.log("Parsing concluído com sucesso.", "#00ff00")
        except Exception as e:
            self.log(f"Erro ao processar ROM: {str(e)}", "#ff3333")

    def _populate_tree(self, parent_item, node):
        """
        Popula o QTreeWidget recursivamente com a estrutura de diretórios.
        """
        for dir_name, child_node in node.get("dirs", {}).items():
            dir_item = QTreeWidgetItem(parent_item, [dir_name, "", ""])
            dir_item.setForeground(0, QColor("#ffa500")) # Laranja para pastas
            self._populate_tree(dir_item, child_node)
            
        for f_info in node.get("files", []):
            file_item = QTreeWidgetItem(parent_item, [f_info["name"], hex(f_info["offset"]), str(f_info["size"])])
            if "id" in f_info:
                file_item.setData(0, Qt.UserRole, str(f_info["id"]))
            # Highlight NARC and MSBT
            ext = os.path.splitext(f_info["name"])[1].lower()
            if ext in [".narc", ".msbt"]:
                file_item.setForeground(0, QColor("#00ff00")) # Verde para arquivos chave

    def display_info(self, info):
        self.info_table.setRowCount(0)
        for key, value in info.items():
            row = self.info_table.rowCount()
            self.info_table.insertRow(row)
            item_key = QTableWidgetItem(str(key).upper())
            item_key.setForeground(QColor("#00ccff"))
            self.info_table.setItem(row, 0, item_key)
            self.info_table.setItem(row, 1, QTableWidgetItem(str(value)))

    # Drag and Drop support
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_rom(files[0])

    def on_file_double_clicked(self, item, column):
        # Primeiro, tentar obter o ID do arquivo (se for ndspy)
        file_id_str = item.data(0, Qt.UserRole)
        
        file_data = None
        
        if file_id_str is not None:
            # Carregamento via ndspy (ID do arquivo)
            file_id = int(file_id_str)
            if hasattr(self, 'current_parser') and hasattr(self.current_parser, 'rom'):
                file_data = self.current_parser.rom.files[file_id]
        
        if file_data is None:
            # Fallback para offset/size manual (SNES ou outros)
            offset_str = item.text(1)
            size_str = item.text(2)
            if not offset_str or not offset_str.startswith("0x"):
                return
            offset = int(offset_str, 16)
            size = int(size_str)
            with open(self.current_file_path, 'rb') as f:
                f.seek(offset)
                file_data = f.read(size)

        if file_data:
            import ndspy.lz10
            # Descompressão automática se necessário
            if len(file_data) > 4 and file_data[0] == 0x10:
                try:
                    decomp = ndspy.lz10.decompress(file_data)
                    if decomp:
                        file_data = decomp
                        self.log("Arquivo descomprimido (LZ77) automaticamente.", "#ffa500")
                except:
                    pass

            # Verificar se é NARC ou MSBT
            if file_data[:4] == b"NARC":
                self.log(f"Analisando container NARC...", "#00ccff")
                import ndspy.narc
                try:
                    narc = ndspy.narc.NARC(file_data)
                    self.log(f"NARC contém {len(narc.files)} sub-arquivos.", "#00ff00")
                    # Tentar encontrar MSBT dentro do NARC
                    for i, sub_data in enumerate(narc.files):
                        s_data = sub_data
                        if len(s_data) > 4 and s_data[0] == 0x10:
                            try:
                                s_data = ndspy.lz10.decompress(s_data)
                            except: pass
                        
                        if s_data[:8] == b"MsgStdBn":
                            self.log(f"Arquivo MSBT encontrado no sub-id {i}!", "#ffa500")
                            self.display_zelda_script(s_data)
                            break
                except Exception as e:
                    self.log(f"Erro ao ler NARC: {e}", "#ff3333")
            elif file_data[:8] == b"MsgStdBn":
                self.display_zelda_script(file_data)
            else:
                self.update_hex_preview(file_data[:512])

    def display_zelda_script(self, data):
        msbt = MSBTParser(data)
        messages = msbt.parse()
        self.script_table.setRowCount(0)
        for msg in messages:
            row = self.script_table.rowCount()
            self.script_table.insertRow(row)
            self.script_table.setItem(row, 0, QTableWidgetItem(str(msg['id'])))
            self.script_table.setItem(row, 1, QTableWidgetItem("Manual Load"))
            self.script_table.setItem(row, 2, QTableWidgetItem(msg['text']))
        self.zelda_info.setText(f"Total de mensagens: {len(messages)}")
        self.zelda_dock.raise_()

    def update_strings_table(self, strings):
        self.strings_table.setRowCount(0)
        for s in strings:
            row = self.strings_table.rowCount()
            self.strings_table.insertRow(row)
            self.strings_table.setItem(row, 0, QTableWidgetItem(hex(s['offset'])))
            self.strings_table.setItem(row, 1, QTableWidgetItem(s['string']))
            self.strings_table.setItem(row, 2, QTableWidgetItem(str(s['length'])))

    def filter_strings(self):
        query = self.search_strings.text().lower()
        if not hasattr(self, 'all_strings'):
            return
        
        filtered = [s for s in self.all_strings if query in s['string'].lower()]
        self.update_strings_table(filtered)

    def rescan_strings(self):
        if not hasattr(self, 'current_file_path'):
            return
        
        self.log(f"Re-escaneando strings com {self.encoding_combo.currentText()}...", "#00ccff")
        with open(self.current_file_path, 'rb') as f:
            scan_data = f.read(1024 * 1024)
            encoding = self.encoding_combo.currentText().lower().replace("-", "_")
            self.all_strings = extract_strings(scan_data, encoding=encoding)
            self.filter_strings()

    def update_hex_preview(self, data):
        hex_text = ""
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            hex_text += f"{i:08X}  {hex_part:<48}  {ascii_part}\n"
        self.hex_view.setPlainText(hex_text)

    def export_report(self):
        if self.info_table.rowCount() == 0:
            self.log("Nada para exportar!", "#ff3333")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório", "report.txt", "Texto (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("RELATÓRIO DE ANÁLISE - pyROMHACK\n")
                    f.write("="*40 + "\n\n")
                    for row in range(self.info_table.rowCount()):
                        key = self.info_table.item(row, 0).text()
                        val = self.info_table.item(row, 1).text()
                        f.write(f"{key}: {val}\n")
                self.log(f"Relatório exportado para {file_path}", "#00ff00")
            except Exception as e:
                self.log(f"Erro ao exportar: {str(e)}", "#ff3333")

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = PyRomHackApp()
    window.show()
    sys.exit(app.exec())
