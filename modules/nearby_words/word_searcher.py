from typing import List, Dict
import threading
import queue
from PyQt5.QtCore import QThread, pyqtSignal
import nltk
from nltk.corpus import wordnet as wn
from modules.nearby_words.word_types import WordInfo
from modules.nearby_words.word_index import WordIndex

class InitThread(QThread):
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, word_index: WordIndex):
        super().__init__()
        self.word_index = word_index
        self.running = True

    def run(self):
        try:
            try:
                nltk.download('wordnet', quiet=True)
                nltk.download('words', quiet=True)
                self.progress.emit(25)
            except Exception as e:
                self.error.emit(f"Error downloading NLTK data: {e}")
                return

            if not self.running:
                return

            try:
                from nltk.corpus import words
                word_list = set(word.lower() for word in words.words() if word.isalpha())
                total = len(word_list)
                
                for i, word in enumerate(word_list):
                    if not self.running:
                        return
                    
                    synsets = wn.synsets(word)
                    info = WordInfo(
                        word=word,
                        definition=synsets[0].definition() if synsets else None,
                        pos=synsets[0].pos() if synsets else None
                    )
                    
                    self.word_index.add_word(word, info)
                    
                    if i % 1000 == 0:
                        progress = 25 + int(75 * i / total)
                        self.progress.emit(progress)
                
                self.word_index.initialized = True
                self.progress.emit(100)
                
            except Exception as e:
                self.error.emit(f"Error building word index: {e}")
                
        except Exception as e:
            self.error.emit(f"Initialization error: {e}")

    def stop(self):
        self.running = False

class SearchThread(QThread):
    results_ready = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, word_index: WordIndex):
        super().__init__()
        self.word_index = word_index
        self.queue = queue.Queue()
        self.running = True

    def search(self, query: str, options: Dict[str, bool]):
        self.queue.put((query, options))

    def run(self):
        while self.running:
            try:
                query, options = self.queue.get(timeout=0.5)
                
                if not self.queue.empty():
                    continue
                    
                results = self.word_index.search(query, options)
                if self.running:
                    self.results_ready.emit(results)
                    
            except queue.Empty:
                continue
            except Exception as e:
                if self.running:
                    self.error.emit(str(e))

    def stop(self):
        self.running = False
        self.queue.put(("", {}))
        self.wait()