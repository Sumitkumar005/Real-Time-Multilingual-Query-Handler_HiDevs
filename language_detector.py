"""
Language Detection Service for Real-Time Multilingual Query Handler
"""

import logging
from typing import Optional, Dict, Any
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Service for detecting language of input text"""
    
    def __init__(self):
        self.min_length = 8  # Reduced for better UX
        self.confidence_threshold = 0.3  # Lower threshold, we'll handle low confidence gracefully
        
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the language of input text
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Optional[str]: Language code (e.g., 'en', 'es') or None if detection fails
        """
        if not text or len(text.strip()) < self.min_length:
            logger.warning(f"Text too short for language detection: {len(text)} chars")
            return None
            
        try:
            # Clean text for detection
            clean_text = self._clean_text(text)
            
            # Detect language
            detected_lang = detect(clean_text)
            logger.info(f"Detected language: {detected_lang} for text: {text[:50]}...")
            
            return detected_lang
            
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in language detection: {str(e)}")
            return None
    
    def detect_with_confidence(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detect language with confidence scores
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Optional[Dict]: Contains language code and confidence score
        """
        if not text or len(text.strip()) < self.min_length:
            return None
            
        try:
            clean_text = self._clean_text(text)
            
            # Get multiple language possibilities
            detections = detect_langs(clean_text)
            
            if not detections:
                return None
                
            # Get the most confident detection
            best_detection = max(detections, key=lambda x: x.prob)
            
            # Special handling for common false positives with better logic
            if best_detection.lang in ['cy', 'ga', 'mt', 'is', 'eu', 'ca'] and best_detection.prob < 0.85:
                # Enhanced English detection
                english_indicators = [
                    'the', 'and', 'or', 'is', 'are', 'was', 'were', 'have', 'has', 'had',
                    'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must',
                    'this', 'that', 'these', 'those', 'with', 'from', 'they', 'them',
                    'what', 'when', 'where', 'why', 'how', 'who', 'which', 'hello', 'hi',
                    'please', 'thank', 'help', 'need', 'want', 'like', 'know', 'think'
                ]
                
                text_lower = clean_text.lower()
                # Better word boundary checking
                english_count = 0
                for word in english_indicators:
                    if f' {word} ' in f' {text_lower} ' or text_lower.startswith(f'{word} ') or text_lower.endswith(f' {word}') or text_lower == word:
                        english_count += 1
                
                if english_count >= 1:  # If contains English indicators
                    return {
                        "language": "en",
                        "confidence": min(0.8, best_detection.prob + 0.3),  # Boost confidence
                        "all_possibilities": [("en", 0.8)] + [(d.lang, d.prob) for d in detections[:2]],
                        "corrected": True
                    }
            
            # Return result even with low confidence, let the UI handle it
            return {
                "language": best_detection.lang,
                "confidence": best_detection.prob,
                "all_possibilities": [(d.lang, d.prob) for d in detections[:3]],
                "corrected": False
            }
            
        except LangDetectException as e:
            logger.warning(f"Language detection with confidence failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in language detection with confidence: {str(e)}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for better language detection
        
        Args:
            text (str): Raw text to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        
        # Remove URLs
        import re
        cleaned = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', cleaned)
        
        # Remove excessive punctuation
        cleaned = re.sub(r'[^\w\s.,!?-]', '', cleaned)
        
        return cleaned.strip()
    
    def is_english(self, text: str) -> bool:
        """
        Quick check if text is likely in English
        
        Args:
            text (str): Input text to check
            
        Returns:
            bool: True if text appears to be in English
        """
        if not text:
            return False
            
        detection = self.detect_language(text)
        return detection == 'en' if detection else False
    
    def get_language_name(self, lang_code: str) -> str:
        """
        Get full language name from language code
        
        Args:
            lang_code (str): ISO language code
            
        Returns:
            str: Full language name
        """
        from config import SUPPORTED_LANGUAGES
        return SUPPORTED_LANGUAGES.get(lang_code, f"Unknown ({lang_code})")
    
    def get_common_languages(self) -> Dict[str, str]:
        """
        Get list of most common languages for UI display
        
        Returns:
            Dict[str, str]: Language codes and names
        """
        common_codes = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar', 'hi']
        from config import SUPPORTED_LANGUAGES
        
        return {code: SUPPORTED_LANGUAGES[code] for code in common_codes if code in SUPPORTED_LANGUAGES}


# Example usage and testing
if __name__ == "__main__":
    # Test language detection
    detector = LanguageDetector()
    
    test_texts = [
        "Hello, how are you today?",
        "Hola, ¿cómo estás hoy?",
        "Bonjour, comment allez-vous aujourd'hui?",
        "Guten Tag, wie geht es Ihnen heute?",
        "こんにちは元気ですか？"
    ]
    
    for text in test_texts:
        result = detector.detect_with_confidence(text)
        if result:
            print(f"Text: '{text}' -> Language: {result['language']} ({result['confidence']:.2f})")
        else:
            print(f"Text: '{text}' -> Could not detect language")
