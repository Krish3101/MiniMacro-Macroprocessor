import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QPlainTextEdit, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pass1 import pass1
from pass2 import pass2

MONO_FONT = "Courier New"


class MiniMacroGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiniMacro Macroprocessor")
        self.resize(1100, 800)
        self.setup_ui()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Header
        header = QHBoxLayout()
        title = QLabel("MiniMacro Macroprocessor")
        title.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()

        btn_sample = QPushButton("Load Sample")
        btn_sample.clicked.connect(self.load_sample)
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.clear_all)
        btn_run = QPushButton("Run Macroprocessor")
        btn_run.clicked.connect(self.run_macroprocessor)
        btn_run.setStyleSheet("font-weight: bold; color: green;")

        header.addWidget(btn_sample)
        header.addWidget(btn_clear)
        header.addWidget(btn_run)
        layout.addLayout(header)

        # Main Splitter (top: editors, bottom: tables)
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Top Pane: Input | Output
        editor_widget = QWidget()
        editor_layout = QHBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        self.input_text = self._make_editor("Input Source Code:", editor_layout, readonly=False)
        self.output_text = self._make_editor("Expanded Output:", editor_layout, readonly=True)
        splitter.addWidget(editor_widget)

        # Bottom Pane: Tabs
        self.tabs = QTabWidget()
        splitter.addWidget(self.tabs)
        splitter.setSizes([450, 300])

        self.mnt_table = self._make_table(["Macro Name", "MDT Index", "#Params"], "MNT (Macro Name Table)")
        self.mdt_table = self._make_table(["Index", "Model Statement"], "MDT (Macro Definition Table)")
        self.ala_table = self._make_table(["Macro Name", "Index Marker", "Formal Param"], "ALA (Argument List Array)")

        self.errors_text = QPlainTextEdit()
        self.errors_text.setFont(QFont(MONO_FONT, 13))
        self.errors_text.setStyleSheet("color: #D32F2F;")
        self.errors_text.setReadOnly(True)
        self.tabs.addTab(self.errors_text, "Errors / Logs")

    def _make_editor(self, label_text, parent_layout, readonly):
        """Helper to create a labelled text editor pane."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 5, 0)
        lbl = QLabel(label_text)
        lbl.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
        text = QPlainTextEdit()
        text.setFont(QFont(MONO_FONT, 13))
        text.setReadOnly(readonly)
        layout.addWidget(lbl)
        layout.addWidget(text)
        parent_layout.addWidget(widget)
        return text

    def _make_table(self, headers, tab_name):
        """Helper to create a table widget and add it to the tab bar."""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(table, tab_name)
        return table

    def load_sample(self):
        self.input_text.setPlainText(
            "MACRO ADD_NUMS &a &b\n"
            "    LOAD &a\n"
            "    ADD &b\n"
            "    STORE &a\n"
            "MEND\n\n"
            "MACRO DISPLAY &x\n"
            "    PRINT &x\n"
            "MEND\n\n"
            "CALL ADD_NUMS 10 20\n"
            "CALL DISPLAY 10\n"
        )

    def clear_all(self):
        self.input_text.clear()
        self.output_text.clear()
        self.mnt_table.setRowCount(0)
        self.mdt_table.setRowCount(0)
        self.ala_table.setRowCount(0)
        self.errors_text.clear()

    def run_macroprocessor(self):
        source = self.input_text.toPlainText().strip()
        if not source:
            QMessageBox.warning(self, "Empty Input", "Please enter some MiniMacro code.")
            return

        lines = source.split('\n')

        # Pass 1 & Pass 2
        intermediate, MNT, MDT, errors1 = pass1(lines)
        expanded, errors2 = pass2(intermediate, MNT, MDT)
        all_errors = errors1 + errors2

        # Output
        self.output_text.setPlainText('\n'.join(expanded) if expanded else "/* No output generated */")

        # Tables
        self._fill_mnt(MNT)
        self._fill_mdt(MDT)
        self._fill_ala(MNT)

        # Errors
        self.errors_text.clear()
        if all_errors:
            self.tabs.setCurrentWidget(self.errors_text)
            self.errors_text.setPlainText("=== ERRORS ===\n\n" + '\n'.join(all_errors) + "\n")
        else:
            self.tabs.setCurrentIndex(0)
            self.errors_text.setPlainText("[+] Processing Successful. No errors found.\n")

    def _fill_mnt(self, MNT):
        self.mnt_table.setRowCount(len(MNT))
        for row, entry in enumerate(MNT):
            self.mnt_table.setItem(row, 0, QTableWidgetItem(entry["name"]))
            self.mnt_table.setItem(row, 1, QTableWidgetItem(str(entry["mdt_index"])))
            self.mnt_table.setItem(row, 2, QTableWidgetItem(str(len(entry["params"]))))

    def _fill_mdt(self, MDT):
        self.mdt_table.setRowCount(len(MDT))
        for row, stmt in enumerate(MDT):
            self.mdt_table.setItem(row, 0, QTableWidgetItem(str(row)))
            self.mdt_table.setItem(row, 1, QTableWidgetItem(stmt))

    def _fill_ala(self, MNT):
        rows = []
        for entry in MNT:
            for idx, param in enumerate(entry["params"]):
                rows.append((entry["name"], f"#{idx+1}", param))
        self.ala_table.setRowCount(len(rows))
        for row, (name, marker, param) in enumerate(rows):
            self.ala_table.setItem(row, 0, QTableWidgetItem(name))
            self.ala_table.setItem(row, 1, QTableWidgetItem(marker))
            self.ala_table.setItem(row, 2, QTableWidgetItem(param))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MiniMacroGUI()
    window.show()
    sys.exit(app.exec())
