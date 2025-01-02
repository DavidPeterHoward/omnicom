import pyttsx3
from typing import Optional, Dict, Any
import threading
import queue
import logging
from functools import lru_cache

class TTSManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TTSManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.engine = None
        self.speaking_queue = queue.Queue()
        self.worker_thread = None
        self.current_voice = None
        self.voices = {}
        self.settings = {
            'rate': 150,
            'volume': 1.0,
            'voice': None
        }
        
        self._initialize_engine()

    def _initialize_engine(self):
        try:
            self.engine = pyttsx3.init()
            self._load_voices()
            self.apply_settings(self.settings)
            
            self.worker_thread = threading.Thread(target=self._speaking_worker, daemon=True)
            self.worker_thread.start()
        except Exception as e:
            logging.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None

    def _load_voices(self):
        if not self.engine:
            return
            
        try:
            for voice in self.engine.getProperty('voices'):
                self.voices[voice.id] = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': voice.languages,
                    'gender': voice.gender
                }
        except Exception as e:
            logging.error(f"Failed to load TTS voices: {e}")

    def get_voices(self) -> Dict[str, Dict[str, Any]]:
        return self.voices

    def apply_settings(self, settings: Dict[str, Any]):
        if not self.engine:
            return
            
        try:
            self.settings.update(settings)
            
            if 'rate' in settings:
                self.engine.setProperty('rate', settings['rate'])
                
            if 'volume' in settings:
                self.engine.setProperty('volume', settings['volume'])
                
            if 'voice' in settings and settings['voice'] in self.voices:
                self.engine.setProperty('voice', settings['voice'])
                self.current_voice = settings['voice']
        except Exception as e:
            logging.error(f"Failed to apply TTS settings: {e}")

    def _speaking_worker(self):
        while True:
            try:
                text = self.speaking_queue.get()
                if text is None:
                    break
                    
                if self.engine:
                    self.engine.say(text)
                    self.engine.runAndWait()
            except Exception as e:
                logging.error(f"TTS speaking error: {e}")
            finally:
                self.speaking_queue.task_done()

    @lru_cache(maxsize=100)
    def get_phonetic(self, word: str) -> str:
        """Get phonetic representation of a word"""
        # This would integrate with a phonetic dictionary
        # For now, return the word itself
        return word

    def speak(self, text: str, interrupt: bool = False):
        if not self.engine:
            return
            
        if interrupt:
            self.stop()
            
        self.speaking_queue.put(text)

    def speak_phonetic(self, word: str, interrupt: bool = True):
        phonetic = self.get_phonetic(word)
        self.speak(phonetic, interrupt)

    def stop(self):
        if not self.engine:
            return
            
        try:
            self.engine.stop()
            with self.speaking_queue.mutex:
                self.speaking_queue.queue.clear()
        except Exception as e:
            logging.error(f"Failed to stop TTS: {e}")

    def shutdown(self):
        self.stop()
        if self.worker_thread and self.worker_thread.is_alive():
            self.speaking_queue.put(None)
            self.worker_thread.join()

    def __del__(self):
        self.shutdown()