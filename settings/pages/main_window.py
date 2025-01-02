from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QTreeWidget, QTreeWidgetItem, QStackedWidget,
                           QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from settings.pages import AppearancePage, BehaviorPage, ModulesPage
from settings.utils import load_config, save_config
from modules import available_modules

class SettingsWindow(QMainWindow):
    settingsChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config = load_config()
        self._setup_ui()
        self.load_settings()
        self._apply_styles()

    def _setup_ui(self):
        self.setWindowTitle("Settings")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(800, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Navigation tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFixedWidth(200)
        
        # Add categories
        categories = {
            "Appearance": ["Fonts & Theme"],
            "Behavior": ["General & Shortcuts"],
            "Modules": ["Available Modules"]
        }

        for category, items in categories.items():
            cat_item = QTreeWidgetItem([category])
            for item in items:
                child = QTreeWidgetItem([item])
                cat_item.addChild(child)
            self.tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True)

        # Settings pages
        self.stacked_widget = QStackedWidget()
        self.pages = {
            "Fonts & Theme": AppearancePage(),
            "General & Shortcuts": BehaviorPage(),
            "Available Modules": ModulesPage()
        }
        
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Apply button
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self._on_apply_clicked)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self._on_save_clicked)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(save_button)

        # Right side layout
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.stacked_widget)
        right_layout.addLayout(button_layout)

        # Main layout
        main_layout.addWidget(self.tree)
        main_layout.addLayout(right_layout, stretch=1)

        # Connect signals
        self.tree.itemSelectionChanged.connect(self._on_category_changed)

    def _apply_styles(self):
        style = """
            QMainWindow {
                background: white;
            }
            QTreeWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: #f8f9fa;
                padding: 5px;
            }
            QTreeWidget::item {
                height: 30px;
                padding: 4px;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background: #e3f2fd;
                color: #1976d2;
            }
            QTreeWidget::item:hover:!selected {
                background: #f5f5f5;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: #ffffff;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #f5f5f5;
            }
            QPushButton[text="Save"] {
                background: #1976d2;
                color: white;
                border: none;
            }
            QPushButton[text="Save"]:hover {
                background: #1565c0;
            }
            QPushButton[text="Apply"] {
                background: #4caf50;
                color: white;
                border: none;
            }
            QPushButton[text="Apply"]:hover {
                background: #43a047;
            }
        """
        self.setStyleSheet(style)

    def _on_category_changed(self):
        selected_items = self.tree.selectedItems()
        if selected_items and selected_items[0].childCount() == 0:
            page_name = selected_items[0].text(0)
            if page_name in self.pages:
                self.stacked_widget.setCurrentWidget(self.pages[page_name])

    def _on_apply_clicked(self):
        try:
            self.save_settings()
            if self.parent_window:
                self.parent_window.apply_settings()
            self.settingsChanged.emit()
            QMessageBox.information(self, "Success", "Settings applied successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")

    def _on_save_clicked(self):
        try:
            self.save_settings()
            save_config(self.config)
            if self.parent_window:
                self.parent_window.apply_settings()
            self.settingsChanged.emit()
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def load_settings(self):
        try:
            for page in self.pages.values():
                page.load_settings(self.config)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Some settings could not be loaded: {str(e)}")

    def save_settings(self):
        for page in self.pages.values():
            page.save_settings(self.config)

    def _check_unsaved_changes(self) -> bool:
        current_settings = {}
        for page in self.pages.values():
            page.save_settings(current_settings)
        
        # Compare with original config
        return current_settings != self.config

    def closeEvent(self, event):
        if self._check_unsaved_changes():
            response = QMessageBox.question(
                self,
                'Save Changes?',
                'You have unsaved changes. Do you want to save them?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if response == QMessageBox.Save:
                try:
                    self.save_settings()
                    save_config(self.config)
                    if self.parent_window:
                        self.parent_window.apply_settings()
                    self.settingsChanged.emit()
                    event.accept()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
                    event.ignore()
            elif response == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        # Select the first item by default
        first_item = self.tree.topLevelItem(0).child(0)
        self.tree.setCurrentItem(first_item)
        self._on_category_changed()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Save window size in settings if needed
        if hasattr(self, 'config'):
            self.config['settings_window_width'] = self.width()
            self.config['settings_window_height'] = self.height()