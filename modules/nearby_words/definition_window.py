from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QScrollArea, QFrame, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut
import nltk
from nltk.corpus import wordnet as wn
from typing import List, Dict, Any

from utils.tts_manager import TTSManager


class WordMeaningWidget(QFrame):
    def __init__(self, meaning_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.meaning_data = meaning_data
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Part of speech & definition
        pos_def_layout = QHBoxLayout()
        
        pos_label = QLabel(f"[{self.meaning_data['pos']}]")
        pos_label.setStyleSheet("color: #666; font-style: italic;")
        pos_def_layout.addWidget(pos_label)
        
        definition = QLabel(self.meaning_data['definition'])
        definition.setWordWrap(True)
        pos_def_layout.addWidget(definition, stretch=1)
        
        layout.addLayout(pos_def_layout)
        
        # Examples if available
        if self.meaning_data.get('examples'):
            examples_label = QLabel("Examples:")
            examples_label.setStyleSheet("color: #666; margin-top: 8px;")
            layout.addWidget(examples_label)
            
            for example in self.meaning_data['examples']:
                example_label = QLabel(f"• {example}")
                example_label.setWordWrap(True)
                example_label.setStyleSheet("color: #666; margin-left: 16px;")
                layout.addWidget(example_label)

        # Synonyms if available
        if self.meaning_data.get('synonyms'):
            synonyms_label = QLabel("Synonyms:")
            synonyms_label.setStyleSheet("color: #666; margin-top: 8px;")
            layout.addWidget(synonyms_label)
            
            synonyms_text = ", ".join(self.meaning_data['synonyms'])
            synonyms = QLabel(synonyms_text)
            synonyms.setWordWrap(True)
            synonyms.setStyleSheet("color: #666; margin-left: 16px;")
            layout.addWidget(synonyms)

        # Antonyms if available
        if self.meaning_data.get('antonyms'):
            antonyms_label = QLabel("Antonyms:")
            antonyms_label.setStyleSheet("color: #666; margin-top: 8px;")
            layout.addWidget(antonyms_label)
            
            antonyms_text = ", ".join(self.meaning_data['antonyms'])
            antonyms = QLabel(antonyms_text)
            antonyms.setWordWrap(True)
            antonyms.setStyleSheet("color: #666; margin-left: 16px;")
            layout.addWidget(antonyms)

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            WordMeaningWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                margin: 4px;
            }
        """)


class DefinitionWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(500, 400)
        self.tts_manager = TTSManager()
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with word and controls
        header = QHBoxLayout()
        
        self.word_label = QLabel()
        self.word_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1976d2;
        """)
        header.addWidget(self.word_label)
        
        # Pronunciation button
        speak_btn = QPushButton("🔊")
        speak_btn.setToolTip("Pronunciation")
        speak_btn.clicked.connect(self._speak_word)
        speak_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 15px;
                padding: 5px 10px;
                background: #e3f2fd;
            }
            QPushButton:hover {
                background: #bbdefb;
            }
        """)
        header.addWidget(speak_btn)
        
        header.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 15px;
                font-size: 20px;
                background: #f0f0f0;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        header.addWidget(close_btn)
        
        layout.addLayout(header)
        
        # Tabs for different aspects
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_meanings_tab(), "Meanings")
        self.tabs.addTab(self._create_thesaurus_tab(), "Thesaurus")
        self.tabs.addTab(self._create_etymology_tab(), "Etymology")
        
        layout.addWidget(self.tabs)
        
        self._apply_styles()

    def _create_meanings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        self.meanings_container = QWidget()
        self.meanings_layout = QVBoxLayout(self.meanings_container)
        self.meanings_layout.addStretch()
        
        scroll.setWidget(self.meanings_container)
        layout.addWidget(scroll)
        
        return tab

    def _create_thesaurus_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        self.synonyms_label = QLabel("Synonyms")
        self.synonyms_label.setStyleSheet("font-weight: bold;")
        self.synonyms_content = QLabel()
        self.synonyms_content.setWordWrap(True)
        
        self.antonyms_label = QLabel("Antonyms")
        self.antonyms_label.setStyleSheet("font-weight: bold;")
        self.antonyms_content = QLabel()
        self.antonyms_content.setWordWrap(True)
        
        content_layout.addWidget(self.synonyms_label)
        content_layout.addWidget(self.synonyms_content)
        content_layout.addWidget(self.antonyms_label)
        content_layout.addWidget(self.antonyms_content)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return tab

    def _create_etymology_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        self.etymology_content = QLabel()
        self.etymology_content.setWordWrap(True)
        content_layout.addWidget(self.etymology_content)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return tab

    def _setup_shortcuts(self):
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.escape_shortcut.activated.connect(self.hide)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: white;
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
            QScrollArea {
                border: none;
            }
        """)

    def _speak_word(self):
        word = self.word_label.text()
        if word:
            self.tts_manager.speak(word, interrupt=True)

    def update_word(self, word: str):
        self.word_label.setText(word)
        self.setWindowTitle(f"Definition - {word}")
        
        # Clear previous meanings
        while self.meanings_layout.count() > 1:
            item = self.meanings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get word information
        synsets = wn.synsets(word)
        
        # Process meanings
        for synset in synsets:
            meaning_data = {
                'pos': synset.pos(),
                'definition': synset.definition(),
                'examples': synset.examples(),
                'synonyms': [lemma.name() for lemma in synset.lemmas()],
                'antonyms': [ant.name() for lemma in synset.lemmas() 
                            for ant in lemma.antonyms()]
            }
            
            meaning_widget = WordMeaningWidget(meaning_data)
            self.meanings_layout.insertWidget(
                self.meanings_layout.count() - 1, 
                meaning_widget
            )
        
        # Update thesaurus
        all_synonyms = set()
        all_antonyms = set()
        
        for synset in synsets:
            for lemma in synset.lemmas():
                if lemma.name() != word:
                    all_synonyms.add(lemma.name())
                for ant in lemma.antonyms():
                    all_antonyms.add(ant.name())
        
        self.synonyms_content.setText(", ".join(sorted(all_synonyms)))
        self.antonyms_content.setText(", ".join(sorted(all_antonyms)))
        
        # Update etymology (placeholder - would need additional data source)
        self.etymology_content.setText("Etymology information not available.")

    def closeEvent(self, event):
        self.hide()
        event.ignore()
        self.closed.emit()

    def showEvent(self, event):
        super().showEvent(event)
        self.escape_shortcut.setEnabled(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.escape_shortcut.setEnabled(False)