from typing import Dict, List, Set, Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QGraphicsView, QGraphicsScene, QDialog)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
from PyQt5.QtSvg import QSvgGenerator, QSvgWidget
import networkx as nx
import math


class ConceptNode:
    def __init__(self, name: str, concept_type: str, definition: str):
        self.name = name
        self.type = concept_type
        self.definition = definition
        self.x = 0
        self.y = 0
        self.width = 120
        self.height = 80

    def contains(self, point: QPointF) -> bool:
        return (self.x - self.width/2 <= point.x() <= self.x + self.width/2 and
                self.y - self.height/2 <= point.y() <= self.y + self.height/2)


class ConceptMindMapView(QGraphicsView):
    nodeClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setScene(QGraphicsScene(self))
        self.setMouseTracking(True)

        self.nodes: Dict[str, ConceptNode] = {}
        self.edges: List[tuple] = []
        self.graph = nx.Graph()
        self.dragging = False
        self.last_pos = None
        self.scale_factor = 1.0

    def update_graph(self, data: Dict):
        self.nodes.clear()
        self.edges.clear()
        self.graph.clear()
        self.scene().clear()

        # Create nodes
        for node_data in data['nodes']:
            node = ConceptNode(
                name=node_data['id'],
                concept_type=node_data.get('type', 'concept'),
                definition=node_data.get('info', '')
            )
            self.nodes[node.name] = node
            self.graph.add_node(node.name)

        # Create edges
        for edge in data['edges']:
            source = edge['source']
            target = edge['target']
            edge_type = edge.get('type', '')
            self.edges.append((source, target, edge_type))
            self.graph.add_edge(source, target)

        self._layout_graph()
        self.update()

    def _layout_graph(self):
        if not self.nodes:
            return

        # Use networkx spring layout
        pos = nx.spring_layout(self.graph)
        
        # Scale and center the layout
        scene_rect = self.scene().sceneRect()
        scale = min(scene_rect.width(), scene_rect.height()) / 2

        for name, node in self.nodes.items():
            if name in pos:
                node.x = pos[name][0] * scale
                node.y = pos[name][1] * scale

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw edges
        for source, target, edge_type in self.edges:
            if source in self.nodes and target in self.nodes:
                source_node = self.nodes[source]
                target_node = self.nodes[target]
                
                # Draw edge line
                painter.setPen(QPen(QColor("#666666"), 2))
                painter.drawLine(
                    source_node.x, source_node.y,
                    target_node.x, target_node.y
                )
                
                # Draw edge type label
                if edge_type:
                    mid_x = (source_node.x + target_node.x) / 2
                    mid_y = (source_node.y + target_node.y) / 2
                    painter.drawText(
                        int(mid_x - 40), int(mid_y - 10),
                        80, 20,
                        Qt.AlignCenter,
                        edge_type
                    )

        # Draw nodes
        for node in self.nodes.values():
            path = QPainterPath()
            
            if node.type == 'concept':
                # Rounded rectangle for concepts
                path.addRoundedRect(
                    node.x - node.width/2,
                    node.y - node.height/2,
                    node.width,
                    node.height,
                    10, 10
                )
            elif node.type == 'theory':
                # Hexagon for theories
                points = []
                for i in range(6):
                    angle = i * math.pi / 3
                    points.append(QPointF(
                        node.x + node.width/2 * math.cos(angle),
                        node.y + node.height/2 * math.sin(angle)
                    ))
                path.moveTo(points[0])
                for point in points[1:]:
                    path.lineTo(point)
                path.closeSubpath()
            else:
                # Ellipse for other types
                path.addEllipse(
                    node.x - node.width/2,
                    node.y - node.height/2,
                    node.width,
                    node.height
                )

            # Draw node shape
            painter.setPen(QPen(QColor("#2196f3"), 2))
            painter.setBrush(QBrush(QColor("#e3f2fd")))
            painter.drawPath(path)

            # Draw node text
            painter.setPen(QPen(Qt.black))
            painter.drawText(
                int(node.x - node.width/2),
                int(node.y - node.height/2),
                int(node.width),
                int(node.height),
                Qt.AlignCenter,
                node.name
            )

    def mousePressEvent(self, event):
        self.last_pos = event.pos()
        if event.button() == Qt.LeftButton:
            for node in self.nodes.values():
                if node.contains(event.pos()):
                    self.nodeClicked.emit(node.name)
                    break
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.last_pos:
            delta = event.pos() - self.last_pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            self.last_pos = event.pos()
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.scale(factor, factor)
            self.scale_factor *= factor
        else:
            super().wheelEvent(event)

class ConceptMindMapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Concept Mind Map")
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        zoom_in = QPushButton("+")
        zoom_out = QPushButton("-")
        reset = QPushButton("Reset")
        zoom_in.clicked.connect(lambda: self.mind_map.scale(1.1, 1.1))
        zoom_out.clicked.connect(lambda: self.mind_map.scale(0.9, 0.9))
        reset.clicked.connect(self._reset_view)
        
        toolbar.addWidget(zoom_in)
        toolbar.addWidget(zoom_out)
        toolbar.addWidget(reset)
        toolbar.addStretch()
        
        # Mind map view
        self.mind_map = ConceptMindMapView()
        
        layout.addLayout(toolbar)
        layout.addWidget(self.mind_map)

    def _reset_view(self):
        self.mind_map.resetTransform()
        self.mind_map.scale_factor = 1.0
        self.mind_map._layout_graph()
        self.mind_map.update()

    def update_graph(self, data: Dict):
        self.mind_map.update_graph(data)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def showEvent(self, event):
        super().showEvent(event)
        self._reset_view()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

class ConceptDetailsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(self.title_label)
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
        
        # Content
        self.definition_label = QLabel()
        self.definition_label.setWordWrap(True)
        self.definition_label.setStyleSheet("color: #666;")
        
        self.related_label = QLabel()
        self.related_label.setWordWrap(True)
        self.related_label.setStyleSheet("color: #666;")
        
        # Layout
        layout.addLayout(header)
        layout.addWidget(self.definition_label)
        layout.addWidget(self.related_label)
        layout.addStretch()
        
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                padding: 4px;
            }
        """)

    def update_details(self, concept_info: Dict):
        self.title_label.setText(concept_info.get('name', ''))
        self.definition_label.setText(concept_info.get('definition', ''))
        
        related = concept_info.get('related', [])
        if related:
            related_text = "Related concepts:\n" + "\n".join(
                f"• {rel}" for rel in related
            )
            self.related_label.setText(related_text)
        else:
            self.related_label.setText("")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)