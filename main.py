import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from omnibar import OmnibarWindow
from settings import load_config
import nltk
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize NLTK data
try:
    nltk.data.find('corpora/words')
    nltk.data.find('corpora/brown')
except LookupError:
    nltk.download('words', quiet=True)
    nltk.download('brown', quiet=True)


def main():
    app = QApplication(sys.argv)

    # Check if another instance is running
    if app.property("omnibar_running"):
        sys.exit(0)
    app.setProperty("omnibar_running", True)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Load configuration
    config = load_config()

    # Create main window
    window = OmnibarWindow()

    # Auto-start if configured
    if config.get('start_with_windows', False):
        window.show()

    return app.exec_()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        sys.exit(1)
