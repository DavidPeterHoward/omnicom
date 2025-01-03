import sys
import multiprocessing
import platform
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import Qt, QCoreApplication
from omnibar import OmnibarWindow
from settings import load_config
from utils.error_handler import ErrorHandler
from utils.state_persistence import StatePersistence
from utils.history_manager import HistoryManager
import logging
import nltk
from datetime import datetime
import traceback


class OmnibarApplication(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set up application info
        self.setApplicationName("Omnibar")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Omnibar")
        
        # Initialize logging
        self.logger = self._setup_logging()
        self.logger.info("Starting Omnibar application")
        
        # Initialize core systems
        self.error_handler = ErrorHandler("Omnibar")
        self.state_manager = StatePersistence("Omnibar")
        self.history_manager = HistoryManager()
        
        # Install global event filter for focus handling
        self.installEventFilter(self)
        
        try:
            self._initialize_system()
        except Exception as e:
            self.logger.critical(f"Failed to initialize system: {e}")
            raise

    def _setup_logging(self):
        """Initialize logging system"""
        log_dir = Path.home() / '.omnibar' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f'omnibar_{timestamp}.log'
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger('Omnibar')

    def _initialize_system(self):
        """Initialize all required subsystems"""
        self.logger.info("Initializing subsystems...")
        
        # Initialize NLTK data
        self._initialize_nltk()
        
        # Load fonts
        self._initialize_fonts()
        
        # Load configuration
        self.config = load_config()
        
        # Apply system-wide settings
        self._apply_system_settings()
        
        self.logger.info("System initialization complete")

    def _initialize_nltk(self):
        """Initialize NLTK data"""
        try:
            required_data = [
                "corpora/words",
                "corpora/wordnet",
                "corpora/brown",
                "taggers/averaged_perceptron_tagger",
            ]
            for item in required_data:
                try:
                    nltk.data.find(item)  # Check if the resource is already downloaded
                except LookupError:
                    self.logger.info(f"Downloading NLTK data: {item}")
                    nltk.download(item.split("/")[1], quiet=True)
        except Exception as e:
            self.logger.error(f"Error initializing NLTK: {e}")
            raise

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
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            self.setAttribute(Qt.AA_EnableHighDpiScaling)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            self.setAttribute(Qt.AA_UseHighDpiPixmaps)

        # Set default font
        default_font = QFont(
            self.config.get('font_family', 'Segoe UI'),
            self.config.get('input_font_size', 10)
        )
        self.setFont(default_font)

    def eventFilter(self, obj, event):
        """Global event filter for focus management"""
        try:
            if event.type() == event.WindowActivate:
                if hasattr(obj, 'on_window_activated'):
                    obj.on_window_activated()
            elif event.type() == event.WindowDeactivate:
                if hasattr(obj, 'on_window_deactivated'):
                    obj.on_window_deactivated()
            elif event.type() == event.KeyPress:
                if hasattr(obj, 'handle_global_key'):
                    if obj.handle_global_key(event):
                        return True
        except Exception as e:
            self.logger.error(f"Error in event filter: {e}")
            
        return super().eventFilter(obj, event)

    def initialize_main_window(self) -> bool:
        """Initialize and show the main window"""
        try:
            # Check for existing instance
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
            if self.config.get('startup_behavior', {}).get('show_on_startup', False):
                self.main_window.show()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing main window: {e}")
            return False

    def cleanup(self):
        """Perform cleanup before exit"""
        try:
            self.logger.info("Performing cleanup...")
            
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
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def main():
    """Main application entry point"""
    # Enable Windows DPI awareness
    if platform.system() == 'Windows':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    # Create application
    # Enable DPI scaling attributes
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # Initialize application
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
        print(traceback.format_exc())
        sys.exit(1)