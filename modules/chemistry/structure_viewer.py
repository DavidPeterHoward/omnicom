from typing import Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtSvg import QSvgWidget
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D

class StructureViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(400, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(QSvgWidget(), "Lewis")
        self.tabs.addTab(QSvgWidget(), "Structural")
        self.tabs.addTab(QSvgWidget(), "Skeletal")
        self.tabs.addTab(QLabel(), "Condensed")
        
        layout.addWidget(self.tabs)
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin: 2px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #e3f2fd;
                color: #1976d2;
            }
        """)

    def update_structure(self, structure):
        if not structure or not structure.mol:
            return
        
        lewis_svg = self._generate_lewis_structure(structure.mol)
        struct_svg = structure.svg
        skeletal_svg = self._generate_skeletal_structure(structure.mol)
        condensed = self._generate_condensed_formula(structure.mol)
        
        svg_widgets = [self.tabs.widget(i) for i in range(3)]
        svg_contents = [lewis_svg, struct_svg, skeletal_svg]
        
        for widget, svg in zip(svg_widgets, svg_contents):
            if isinstance(widget, QSvgWidget) and isinstance(svg, str):
                widget.load(bytearray(svg, encoding='utf-8'))
        
        condensed_label = self.tabs.widget(3)
        if isinstance(condensed_label, QLabel):
            condensed_label.setText(condensed)

    def _generate_lewis_structure(self, mol):
        drawer = rdMolDraw2D.MolDraw2DSVG(400, 400)
        drawer.drawOptions().addAtomIndices = True
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()

    def _generate_skeletal_structure(self, mol):
        drawer = rdMolDraw2D.MolDraw2DSVG(400, 400)
        drawer.drawOptions().addStereoAnnotation = True
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()

    def _generate_condensed_formula(self, mol):
        return rdMolDescriptors.CalcMolFormula(mol)