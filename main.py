import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import Qt, QCoreApplication
from omnibar import OmnibarWindow
from settings import load_config
import nltk
import logging
from pathlib import Path
from utils.error_handler import ErrorHandler
from utils.state_persistence import StatePersistence
from utils.history_manager import HistoryManager
import traceback
import multiprocessing
import platform


# Initialize logging
def setup_logging():
    log_dir = Path.home() / '.omnibar' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'omnibar.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('Omnibar')


class OmnibarApplication(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.logger = setup_logging()
        self.error_handler = ErrorHandler("Omnibar")
        self.state_manager = StatePersistence("Omnibar")
        self.history_manager = HistoryManager()
        
        # Set application info
        self.setApplicationName("Omnibar")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Omnibar")
        
        # Initialize subsystems
        self._initialize_system()
        
        # Set up error handling
        self._setup_error_handling()
        
        # Main window
        self.main_window = None

    def _initialize_system(self):
        """Initialize all required subsystems"""
        try:
            # Initialize NLTK data
            self._initialize_nltk()
            
            # Load fonts
            self._initialize_fonts()
            
            # Set default font
            default_font = QFont("Segoe UI", 10)
            self.setFont(default_font)
            
            # Load configuration
            self.config = load_config()
            
            # Apply system-wide settings
            self._apply_system_settings()
            
        except Exception as e:
            self.logger.error(f"Error initializing system: {e}")
            raise

    def _initialize_nltk(self):
        """Initialize NLTK data"""
        try:
            nltk.data.find('corpora/words')
            nltk.data.find('corpora/brown')
        except LookupError:
            self.logger.info("Downloading required NLTK data...")
            nltk.download('words', quiet=True)
            nltk.download('brown', quiet=True)

    def _initialize_fonts(self):
        """Initialize application fonts"""
        try:
            font_dir = Path(__file__).parent / 'resources' / 'fonts'
            if font_dir.exists():
                for font_file in font_dir.glob('*.ttf'):
                    QFontDatabase.addApplicationFont(str(font_file))
        except Exception as e:
            self.logger.warning(f"Error loading custom fonts: {e}")

    def _apply_system_settings(self):
        """Apply system-wide settings"""
        # Set high DPI scaling if enabled
        if self.config.get('enable_high_dpi', True):
            if hasattr(Qt, 'AA_EnableHighDpiScaling'):
                self.setAttribute(Qt.AA_EnableHighDpiScaling)
            if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
                self.setAttribute(Qt.AA_UseHighDpiPixmaps)

        # Set style
        if 'style' in self.config:
            self.setStyle(self.config['style'])

    def _setup_error_handling(self):
        """Set up global error handling"""
        def exception_hook(exc_type, exc_value, exc_traceback):
            # Log the error
            self.logger.critical(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            # Let the error handler handle it
            self.error_handler.handle_error(
                "Uncaught Exception",
                str(exc_value),
                "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            )

        sys.excepthook = exception_hook

    def initialize_main_window(self):
        """Initialize and show the main window"""
        try:
            # Check if another instance is running
            if self.property("omnibar_running"):
                self.logger.warning("Another instance is already running")
                return False
                
            self.setProperty("omnibar_running", True)
            
            # Create main window
            self.main_window = OmnibarWindow()
            
            # Restore previous state if configured
            if self.config.get('restore_state', True):
                window_state = self.state_manager.get_global_state('window_state')
                if window_state:
                    self.main_window.restoreState(window_state)
            
            # Auto-start if configured
            if self.config.get('start_with_windows', False):
                self.main_window.show()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing main window: {e}")
            return False

    def cleanup(self):
        """Perform cleanup before exit"""
        try:
            # Save current state
            if self.main_window:
                self.state_manager.set_global_state(
                    'window_state',
                    self.main_window.saveState()
                )
            
            # Clean up managers
            self.state_manager.cleanup()
            self.history_manager.cleanup()
            
            # Clear property
            self.setProperty("omnibar_running", False)
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def main():
    # Enable Windows DPI awareness
    if platform.system() == 'Windows':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    # Create application
    app = OmnibarApplication(sys.argv)
    
    try:
        # Initialize main window
        if not app.initialize_main_window():
            return 1
            
        # Run event loop
        result = app.exec_()
        
        # Cleanup
        app.cleanup()
        
        return result
        
    except Exception as e:
        app.logger.critical(f"Application crashed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    # Set up multiprocessing for Windows
    if platform.system() == 'Windows':
        multiprocessing.freeze_support()
    
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)