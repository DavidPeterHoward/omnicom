from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QGroupBox, QLabel, QPushButton, QTreeWidget,
                           QTreeWidgetItem, QKeySequenceEdit, QMessageBox,
                           QDialog, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from typing import Dict, Any, Optional


class ShortcutDialog(QDialog):
    """Dialog for editing a shortcut"""
    def __init__(self, shortcut: str = "", description: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Shortcut")
        self.setModal(True)
        self._setup_ui(shortcut, description)

    def _setup_ui(self, shortcut: str, description: str):
        layout = QVBoxLayout(self)
        
        # Shortcut editor
        shortcut_layout = QHBoxLayout()
        shortcut_layout.addWidget(QLabel("Shortcut:"))
        self.shortcut_edit = QKeySequenceEdit(QKeySequence(shortcut))
        shortcut_layout.addWidget(self.shortcut_edit)
        layout.addLayout(shortcut_layout)
        
        # Description editor
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.description_edit = QLineEdit(description)
        desc_layout.addWidget(self.description_edit)
        layout.addLayout(desc_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

    def get_values(self):
        """Get the entered shortcut and description"""
        return (
            self.shortcut_edit.keySequence().toString(),
            self.description_edit.text()
        )


class ShortcutsPage(QWidget):
    """Settings page for keyboard shortcuts"""
    
    shortcutsChanged = pyqtSignal()
    
    def __init__(self, hotkey_manager, parent=None):
        super().__init__(parent)
        self.hotkey_manager = hotkey_manager
        self._setup_ui()
        self._load_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Global shortcuts
        global_group = QGroupBox("Global Shortcuts")
        global_layout = QVBoxLayout()
        self.global_tree = QTreeWidget()
        self.global_tree.setHeaderLabels(["Action", "Shortcut", "Description"])
        self.global_tree.itemDoubleClicked.connect(
            lambda item: self._edit_shortcut(item, "global")
        )
        global_layout.addWidget(self.global_tree)
        global_group.setLayout(global_layout)
        layout.addWidget(global_group)
        
        # Application shortcuts
        app_group = QGroupBox("Application Shortcuts")
        app_layout = QVBoxLayout()
        self.app_tree = QTreeWidget()
        self.app_tree.setHeaderLabels(["Action", "Shortcut", "Description"])
        self.app_tree.itemDoubleClicked.connect(
            lambda item: self._edit_shortcut(item, "local")
        )
        app_layout.addWidget(self.app_tree)
        app_group.setLayout(app_layout)
        layout.addWidget(app_group)
        
        # Context shortcuts
        context_group = QGroupBox("Context Shortcuts")
        context_layout = QVBoxLayout()
        self.context_tree = QTreeWidget()
        self.context_tree.setHeaderLabels(
            ["Context", "Action", "Shortcut", "Description"]
        )
        self.context_tree.itemDoubleClicked.connect(
            lambda item: self._edit_shortcut(item, "context")
        )
        context_layout.addWidget(self.context_tree)
        context_group.setLayout(context_layout)
        layout.addWidget(context_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        reset_button = QPushButton("Reset to Defaults")
        import_button = QPushButton("Import")
        export_button = QPushButton("Export")
        
        reset_button.clicked.connect(self._reset_shortcuts)
        import_button.clicked.connect(self._import_shortcuts)
        export_button.clicked.connect(self._export_shortcuts)
        
        button_layout.addWidget(reset_button)
        button_layout.addWidget(import_button)
        button_layout.addWidget(export_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }
            QTreeWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
        """)

    def _load_shortcuts(self):
        """Load shortcuts into the trees"""
        # Clear trees
        self.global_tree.clear()
        self.app_tree.clear()
        self.context_tree.clear()
        
        # Get all shortcuts
        shortcuts = self.hotkey_manager.get_all_hotkeys()
        
        # Load global shortcuts
        for shortcut, info in shortcuts['global'].items():
            item = QTreeWidgetItem([
                shortcut,
                shortcut,
                info.get('description', '')
            ])
            self.global_tree.addTopLevelItem(item)
        
        # Load local shortcuts
        for shortcut, info in shortcuts['local'].items():
            item = QTreeWidgetItem([
                shortcut,
                shortcut,
                info.get('description', '')
            ])
            self.app_tree.addTopLevelItem(item)
        
        # Load context shortcuts
        for context, context_shortcuts in shortcuts['contexts'].items():
            for shortcut, info in context_shortcuts.items():
                item = QTreeWidgetItem([
                    context,
                    shortcut,
                    shortcut,
                    info.get('description', '')
                ])
                self.context_tree.addTopLevelItem(item)
        
        # Resize columns
        for tree in [self.global_tree, self.app_tree, self.context_tree]:
            for i in range(tree.columnCount()):
                tree.resizeColumnToContents(i)

    def _edit_shortcut(self, item: QTreeWidgetItem, shortcut_type: str):
        """Edit a shortcut"""
        if shortcut_type == "context":
            context = item.text(0)
            shortcut = item.text(2)
            description = item.text(3)
        else:
            shortcut = item.text(1)
            description = item.text(2)
            context = None
            
        # Show edit dialog
        dialog = ShortcutDialog(shortcut, description, self)
        if dialog.exec_() == QDialog.Accepted:
            new_shortcut, new_description = dialog.get_values()
            
            # Validate shortcut
            if self._validate_shortcut(new_shortcut, shortcut_type, context):
                # Update shortcut
                if shortcut_type == "context":
                    item.setText(2, new_shortcut)
                    item.setText(3, new_description)
                    self.hotkey_manager.unregister_hotkey(shortcut, context)
                    # Re-register with new values
                    info = self.hotkey_manager.get_hotkey_info(shortcut, context)
                    if info and 'action' in info:
                        self.hotkey_manager.register_context_hotkey(
                            context,
                            new_shortcut,
                            info['action'],
                            new_description
                        )
                else:
                    item.setText(1, new_shortcut)
                    item.setText(2, new_description)
                    self.hotkey_manager.unregister_hotkey(shortcut)
                    # Re-register with new values
                    info = self.hotkey_manager.get_hotkey_info(shortcut)
                    if info and 'action' in info:
                        if shortcut_type == "global":
                            self.hotkey_manager.register_global_hotkey(
                                new_shortcut,
                                info['action'],
                                new_description
                            )
                        else:
                            self.hotkey_manager.register_local_hotkey(
                                new_shortcut,
                                info['action'],
                                new_description
                            )
                
                self.shortcutsChanged.emit()

    def _validate_shortcut(self, shortcut: str, 
                          shortcut_type: str,
                          context: Optional[str] = None) -> bool:
        """Validate a shortcut doesn't conflict with existing ones"""
        if not shortcut:
            QMessageBox.warning(
                self,
                "Invalid Shortcut",
                "Shortcut cannot be empty"
            )
            return False

        # Check for conflicts
        all_shortcuts = self.hotkey_manager.get_all_hotkeys()
        
        # Check global shortcuts
        if shortcut in all_shortcuts['global']:
            if shortcut_type != "global":
                QMessageBox.warning(
                    self,
                    "Shortcut Conflict",
                    f"Shortcut {shortcut} is already registered as a global shortcut"
                )
                return False
                
        # Check local shortcuts
        if shortcut in all_shortcuts['local']:
            if shortcut_type != "local":
                QMessageBox.warning(
                    self,
                    "Shortcut Conflict",
                    f"Shortcut {shortcut} is already registered as a local shortcut"
                )
                return False

        # Check context shortcuts
        for ctx, shortcuts in all_shortcuts['contexts'].items():
            if shortcut in shortcuts:
                if shortcut_type != "context" or ctx != context:
                    QMessageBox.warning(
                        self,
                        "Shortcut Conflict",
                        f"Shortcut {shortcut} is already registered in context {ctx}"
                    )
                    return False

        return True

    def _reset_shortcuts(self):
        """Reset shortcuts to default values"""
        reply = QMessageBox.question(
            self,
            "Reset Shortcuts",
            "Are you sure you want to reset all shortcuts to default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.hotkey_manager.cleanup()
            self._load_shortcuts()
            self.shortcutsChanged.emit()

    def _import_shortcuts(self):
        """Import shortcuts from file"""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Shortcuts",
            "",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    import json
                    shortcuts = json.load(f)
                    
                # Validate format
                if not isinstance(shortcuts, dict) or not all(
                    k in shortcuts for k in ['global', 'local', 'contexts']
                ):
                    raise ValueError("Invalid shortcuts file format")
                    
                # Apply shortcuts
                self.hotkey_manager.cleanup()
                for shortcut_type, shortcuts_data in shortcuts.items():
                    if shortcut_type == 'global':
                        for shortcut, info in shortcuts_data.items():
                            if 'action' in info:
                                self.hotkey_manager.register_global_hotkey(
                                    shortcut,
                                    info['action'],
                                    info.get('description', '')
                                )
                    elif shortcut_type == 'local':
                        for shortcut, info in shortcuts_data.items():
                            if 'action' in info:
                                self.hotkey_manager.register_local_hotkey(
                                    shortcut,
                                    info['action'],
                                    info.get('description', '')
                                )
                    elif shortcut_type == 'contexts':
                        for context, context_shortcuts in shortcuts_data.items():
                            for shortcut, info in context_shortcuts.items():
                                if 'action' in info:
                                    self.hotkey_manager.register_context_hotkey(
                                        context,
                                        shortcut,
                                        info['action'],
                                        info.get('description', '')
                                    )
                
                self._load_shortcuts()
                self.shortcutsChanged.emit()
                QMessageBox.information(
                    self,
                    "Success",
                    "Shortcuts imported successfully"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to import shortcuts: {str(e)}"
                )

    def _export_shortcuts(self):
        """Export shortcuts to file"""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Shortcuts",
            "",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                shortcuts = self.hotkey_manager.get_all_hotkeys()
                with open(filename, 'w') as f:
                    import json
                    json.dump(shortcuts, f, indent=2)
                    
                QMessageBox.information(
                    self,
                    "Success",
                    "Shortcuts exported successfully"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to export shortcuts: {str(e)}"
                )