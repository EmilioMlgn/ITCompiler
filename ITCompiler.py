import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget,
                             QMenuBar, QAction, QFileDialog, QLabel, QPushButton, QHBoxLayout,
                             QSplitter)
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from PyQt5.QtCore import Qt, QRegularExpression

class CustomLanguage:
    KEYWORDS = ["if", "else", "while", "for", "function", "return",
                "int", "float", "string", "bool", "true", "false",
                "print", "input", "and", "or", "not"]

    COLORS = {
        "keyword": QColor(88, 129, 87),
        "number": QColor(174, 177, 120),
        "string": QColor(208, 135, 112),
        "comment": QColor(128, 128, 128),
        "identifier": QColor(163, 190, 140)
    }

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(CustomLanguage.COLORS["keyword"])
        keyword_format.setFontWeight(QFont.Bold)

        for word in CustomLanguage.KEYWORDS:
            pattern = QRegularExpression(r"\b" + word + r"\b")
            self.highlighting_rules.append((pattern, keyword_format))

        number_format = QTextCharFormat()
        number_format.setForeground(CustomLanguage.COLORS["number"])
        pattern = QRegularExpression(r"\b\d+(\.\d+)?\b")
        self.highlighting_rules.append((pattern, number_format))

        string_format = QTextCharFormat()
        string_format.setForeground(CustomLanguage.COLORS["string"])
        pattern = QRegularExpression(r'\".*?\"')
        self.highlighting_rules.append((pattern, string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(CustomLanguage.COLORS["comment"])
        pattern = QRegularExpression(r"//[^\n]*")
        self.highlighting_rules.append((pattern, comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class SymbolTable:
    def __init__(self, filename="tabla_simbolos.dat"):
        self.filename = filename
        self.symbols = []
        self._create_file()
        self.load()

    def _create_file(self):
        """Crea el archivo con el encabezado descriptivo si no existe"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                f.write("=== TABLA DE SIMBOLOS ===\n")
                f.write("Formato: Tipo | Valor | Linea\n")
                f.write("---------------------------\n")
                f.write("TIPOS POSIBLES:\n")
                f.write("- PALABRA_RESERVADA\n")
                f.write("- IDENTIFICADOR\n")
                f.write("- NUMERO_ENTERO\n")
                f.write("- NUMERO_DECIMAL\n")
                f.write("- STRING\n")
                f.write("- OPERADOR\n")
                f.write("---------------------------\n")

    def add_symbol(self, token_type, token_value, line_number):
        symbol = {
            "type": token_type,
            "value": token_value,
            "line": line_number
        }
        self.symbols.append(symbol)
        self.save()

    def save(self):
        with open(self.filename, 'w') as f:
            f.write("=== TABLA DE SIMBOLOS ===\n")
            f.write("Formato: Tipo | Valor | Linea\n")
            f.write("---------------------------\n")

            for symbol in self.symbols:
                f.write(f"{symbol['type']}\t{symbol['value']}\t{symbol['line']}\n")

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                lines = f.readlines()
                for line in lines[8:]:
                    parts = line.strip().split("\t")
                    if len(parts) == 3:
                        self.symbols.append({
                            "type": parts[0],
                            "value": parts[1],
                            "line": int(parts[2])
                        })

    def clear(self):
        self.symbols = []
        self.save()

    def __str__(self):
        header = "=== TABLA DE SIMBOLOS ===\n"
        header += "Tipo             Valor               Linea\n"
        header += "-----------------------------------------\n"
        symbols_str = "\n".join([f"{s['type']:15} {s['value']:20} Linea: {s['line']}"
                                 for s in self.symbols])
        return header + symbols_str

class LexicalAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []

    def analyze(self, code):
        self.symbol_table.clear()
        self.errors = []
        lines = code.split("\n")

        for line_num, line in enumerate(lines, 1):
            self.tokenize_line(line, line_num)

    def tokenize_line(self, line, line_num):
        i = 0
        n = len(line)

        while i < n:
            char = line[i]

            if char.isspace():
                i += 1
                continue

            if char.isalpha() or char == '_':
                start = i
                while i < n and (line[i].isalnum() or line[i] == '_'):
                    i += 1
                identifier = line[start:i]

                if identifier in CustomLanguage.KEYWORDS:
                    self.symbol_table.add_symbol("PALABRA_RESERVADA", identifier, line_num)
                else:
                    self.symbol_table.add_symbol("IDENTIFICADOR", identifier, line_num)
                continue

            if char.isdigit():
                start = i
                has_decimal = False
                while i < n and (line[i].isdigit() or line[i] == '.'):
                    if line[i] == '.':
                        if has_decimal:
                            self.errors.append(
                                f"Error léxico en línea {line_num}: Número con múltiples puntos decimales")
                            break
                        has_decimal = True
                    i += 1

                number = line[start:i]
                if has_decimal:
                    self.symbol_table.add_symbol("NUMERO_DECIMAL", number, line_num)
                else:
                    self.symbol_table.add_symbol("NUMERO_ENTERO", number, line_num)
                continue

            if char == '"':
                start = i
                i += 1
                while i < n and line[i] != '"':
                    i += 1

                if i >= n:
                    self.errors.append(f"Error léxico en línea {line_num}: String no cerrado")
                    break

                i += 1
                string_literal = line[start:i]
                self.symbol_table.add_symbol("STRING", string_literal, line_num)
                continue

            if i + 1 < n and line[i] == '/' and line[i + 1] == '/':
                break

            operators = ['+', '-', '*', '/', '=', '!', '<', '>', '&', '|', '(', ')', '{', '}', '[', ']', ';', ',']
            if char in operators:
                if i + 1 < n:
                    two_char_op = char + line[i + 1]
                    if two_char_op in ['==', '!=', '<=', '>=', '&&', '||']:
                        self.symbol_table.add_symbol("OPERADOR", two_char_op, line_num)
                        i += 2
                        continue

                self.symbol_table.add_symbol("OPERADOR", char, line_num)
                i += 1
                continue

            self.errors.append(f"Error léxico en línea {line_num}: Carácter no reconocido '{char}'")
            i += 1

class CodeEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ITCompiler")
        self.setGeometry(100, 100, 1600, 800)

        self.symbol_table = SymbolTable()
        self.lexer = LexicalAnalyzer()

        self.init_ui()

    def init_ui(self):
        self.editor = QTextEdit()
        self.highlighter = SyntaxHighlighter(self.editor.document())

        self.error_display = QTextEdit()
        self.error_display.setReadOnly(True)
        self.error_display.setStyleSheet("background-color: #f8d7da; color: #721c24;")

        self.symbol_table_display = QTextEdit()
        self.symbol_table_display.setReadOnly(True)

        self.compile_btn = QPushButton("Compilar")
        self.compile_btn.clicked.connect(self.compile_code)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Tabla de Símbolos:"))
        right_panel.addWidget(self.symbol_table_display)
        right_panel.addWidget(QLabel("Errores:"))
        right_panel.addWidget(self.error_display)
        right_panel.addWidget(self.compile_btn)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 300])

        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.create_menu()

        font = QFont("Consolas", 12)
        self.editor.setFont(font)
        self.error_display.setFont(font)
        self.symbol_table_display.setFont(QFont("Consolas", 10))

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Archivo")

        open_action = QAction("Abrir archivo", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Guardar como...", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "",
                                                  "Archivos de texto (*.txt);;Todos los archivos (*)")
        if filename:
            with open(filename, "r") as f:
                content = f.read()
                self.editor.setPlainText(content)

    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", "",
                                                  "Archivos de texto (*.txt);;Todos los archivos (*)")
        if filename:
            with open(filename, "w") as f:
                f.write(self.editor.toPlainText())

    def compile_code(self):
        code = self.editor.toPlainText()
        self.lexer.analyze(code)

        self.symbol_table_display.setPlainText(str(self.lexer.symbol_table))

        if self.lexer.errors:
            self.error_display.setPlainText("\n".join(self.lexer.errors))
        else:
            self.error_display.setPlainText("Compilación exitosa. No se encontraron errores léxicos.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = CodeEditor()
    editor.show()
    sys.exit(app.exec_())