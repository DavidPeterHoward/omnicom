from typing import Optional, Callable, Dict, Any
import sys
import traceback
import logging
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QObject, pyqtSignal
import json
from datetime import datetime

class ErrorLevel:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorHandler(QObject):
    errorOccurred = pyqtSignal(str, str, str)  # level, message, details
    
    def __init__(self, app_name: str = "Omnibar"):
        super().__init__()
        self.app_name = app_name
        self.log_dir = Path.home() / '.omnibar' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.error_log = self.log_dir / 'errors.log'
        self.crash_reports = self.log_dir / 'crash_reports'
        self.crash_reports.mkdir(exist_ok=True)
        
        self.handlers: Dict[str, Callable] = {}
        self._setup_logging()
        self._install_exception_hook()

    def _setup_logging(self):
        logging.basicConfig(
            filename=str(self.error_log),
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.app_name)

    def _install_exception_hook(self):
        self._original_hook = sys.excepthook
        sys.excepthook = self._handle_uncaught_exception

    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions globally"""
        try:
            # Create crash report
            crash_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.crash_reports / f"crash_{crash_time}.json"
            
            # Get traceback info
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            
            # Create crash report
            report = {
                "timestamp": crash_time,
                "type": str(exc_type.__name__),
                "message": str(exc_value),
                "traceback": "".join(tb_lines),
                "system_info": self._get_system_info()
            }
            
            # Save crash report
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Log the error
            self.logger.critical(
                f"Uncaught exception: {exc_value}",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            # Show error dialog
            self.show_error_dialog(
                "Critical Error",
                f"An unexpected error occurred: {exc_value}\n\n"
                f"A crash report has been saved to:\n{report_file}"
            )
            
        finally:
            # Call original exception hook
            self._original_hook(exc_type, exc_value, exc_traceback)

    def _get_system_info(self) -> dict:
        """Get system information for error reports"""
        import platform
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "qt_version": QApplication.instance().applicationVersion(),
            "app_name": self.app_name
        }

    def register_handler(self, error_type: str, handler: Callable):
        """Register a custom error handler for specific error types"""
        self.handlers[error_type] = handler

    def handle_error(self, error_type: str, message: str, 
                    details: Optional[str] = None, 
                    level: str = ErrorLevel.ERROR):
        """Handle an error with registered handler or default behavior"""
        try:
            # Log the error
            if level == ErrorLevel.CRITICAL:
                self.logger.critical(f"{error_type}: {message}")
            elif level == ErrorLevel.ERROR:
                self.logger.error(f"{error_type}: {message}")
            elif level == ErrorLevel.WARNING:
                self.logger.warning(f"{error_type}: {message}")
            else:
                self.logger.info(f"{error_type}: {message}")
            
            # Emit signal
            self.errorOccurred.emit(level, message, details or "")
            
            # Call custom handler if registered
            if error_type in self.handlers:
                self.handlers[error_type](message, details)
            else:
                # Default handling
                if level in [ErrorLevel.ERROR, ErrorLevel.CRITICAL]:
                    self.show_error_dialog(error_type, message, details)
                elif level == ErrorLevel.WARNING:
                    self.show_warning_dialog(error_type, message, details)
                
        except Exception as e:
            # If error handling fails, log it and show basic error message
            self.logger.critical(f"Error handler failed: {e}")
            self.show_error_dialog(
                "Error Handler Failed",
                "An error occurred while handling another error."
            )

    def show_error_dialog(self, title: str, message: str, 
                         details: Optional[str] = None):
        """Show error message dialog"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setDetailedText(details)
        msg.exec_()

    def show_warning_dialog(self, title: str, message: str,
                          details: Optional[str] = None):
        """Show warning message dialog"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setDetailedText(details)
        msg.exec_()

    def get_recent_errors(self, count: int = 10) -> list:
        """Get recent errors from log file"""
        try:
            if not self.error_log.exists():
                return []
                
            errors = []
            with open(self.error_log, 'r') as f:
                for line in f.readlines()[-count:]:
                    errors.append(line.strip())
            return errors
        except Exception as e:
            self.logger.error(f"Failed to read error log: {e}")
            return []

    def get_crash_reports(self) -> list:
        """Get list of crash reports"""
        try:
            return sorted(
                [f for f in self.crash_reports.glob("crash_*.json")],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
        except Exception as e:
            self.logger.error(f"Failed to get crash reports: {e}")
            return []

    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log files"""
        try:
            import time
            now = time.time()
            
            # Clean up old crash reports
            for report in self.crash_reports.glob("crash_*.json"):
                if (now - report.stat().st_mtime) > (days * 86400):
                    report.unlink()
                    
            # Rotate error log if too large
            if self.error_log.exists():
                if self.error_log.stat().st_size > 10 * 1024 * 1024:  # 10MB
                    backup = self.error_log.with_suffix('.log.old')
                    if backup.exists():
                        backup.unlink()
                    self.error_log.rename(backup)
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup logs: {e}")