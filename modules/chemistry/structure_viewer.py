from typing import Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QSvgWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QShortcut
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D

class StructureViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(600, 600)
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with close button
        header = QHBoxLayout()
        title = QLabel("Chemical Structure Viewer")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(title)
        header.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 15px;
                background: #f0f0f0;
                font-size: 20px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        # Structure displays
        self.lewis_svg = QSvgWidget()
        self.structural_svg = QSvgWidget()
        self.skeletal_svg = QSvgWidget()
        self.formula_label = QLabel()
        self.formula_label.setStyleSheet("font-family: monospace; font-size: 14px;")
        
        # Unified view layout
        view_layout = QVBoxLayout()
        view_layout.addWidget(self.lewis_svg)
        view_layout.addWidget(self.structural_svg)
        view_layout.addWidget(self.skeletal_svg)
        view_layout.addWidget(self.formula_label, alignment=Qt.AlignCenter)
        layout.addLayout(view_layout)
        
        self._apply_styles()

    def _setup_shortcuts(self):
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.escape_shortcut.activated.connect(self.hide)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QLabel {
                border: none;
            }
            QSvgWidget {
                border: 1px solid #f0f0f0;
                border-radius: 4px;
                margin: 4px;
                padding: 8px;
            }
        """)

    def update_structure(self, structure):
        if not structure or not structure.mol:
            return
        
        # Generate and update all views
        self.lewis_svg.load(bytearray(self._generate_lewis_structure(structure.mol), 
                                    encoding='utf-8'))
        self.structural_svg.load(bytearray(structure.svg, encoding='utf-8'))
        self.skeletal_svg.load(bytearray(self._generate_skeletal_structure(structure.mol), 
                                       encoding='utf-8'))
        
        formula = rdMolDescriptors.CalcMolFormula(structure.mol)
        self.formula_label.setText(f"Condensed Formula: {formula}")
        
        # Resize SVG widgets
        for svg in [self.lewis_svg, self.structural_svg, self.skeletal_svg]:
            svg.setFixedSize(180, 180)

    def _generate_lewis_structure(self, mol):
        drawer = rdMolDraw2D.MolDraw2DSVG(180, 180)
        drawer.drawOptions().addAtomIndices = True
        drawer.drawOptions().addStereoAnnotation = True
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()

    def _generate_skeletal_structure(self, mol):
        drawer = rdMolDraw2D.MolDraw2DSVG(180, 180)
        drawer.drawOptions().addStereoAnnotation = True
        drawer.drawOptions().addRadicals = True
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.escape_shortcut.setEnabled(True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.escape_shortcut.setEnabled(False)