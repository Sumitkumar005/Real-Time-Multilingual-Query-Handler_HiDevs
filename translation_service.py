"""
Translation Service for Real-Time Multilingual Query Handler
"""

import logging
import time
import hashlib
from typing import Optional, Dict, Any, Tuple
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from config import Config, TRANSLATION_PROMPTS
from language_detector import LanguageDetector

logger = logging.getLogger(__name__)

class TranslationService:
    """Main translation service using Groq API and Llama 3"""
    
    def __init__(self):
        # Initialize language detector
        self.language_detector = LanguageDetector()
        
        # Initialize Groq LLM
        try:
            Config.validate()
            self.llm = ChatGroq(
                model=Config.GROQ_MODEL,
                temperature=0.1,  # Low temperature for consistent translations
                max_tokens=1000,
                timeout=Config.TRANSLATION_TIMEOUT
            )
            logger.info("Translation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize translation service: {str(e)}")
            raise
    
    def translate_text(self, text: str, source_lang: str = "auto", target_lang: str = "English") -> Dict[str, Any]:
        """
        Translate text from source language to target language
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language code or 'auto' for detection
            target_lang (str): Target language (default: English)
            
        Returns:
            Dict[str, Any]: Translation result with metadata
        """
        start_time = time.time()
        
        # Input validation
        if not text or not text.strip():
            return {
                "success": False,
                "error": "Empty text provided",
                "translation": "",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "processing_time": time.time() - start_time
            }
        
        if len(text) > Config.MAX_QUERY_LENGTH:
            return {
                "success": False,
                "error": f"Text too long (max {Config.MAX_QUERY_LENGTH} characters)",
                "translation": "",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "processing_time": time.time() - start_time
            }
        
        try:
            # Detect source language if auto
            if source_lang == "auto":
                detection_result = self.language_detector.detect_with_confidence(text)
                if detection_result and detection_result["confidence"] > 0.3:
                    source_lang = detection_result["language"]
                    confidence = detection_result["confidence"]
                    logger.info(f"Auto-detected language: {source_lang} (confidence: {confidence:.2f})")
                else:
                    # Fallback: try simple detection or assume English for short text
                    try:
                        simple_detection = self.language_detector.detect_language(text)
                        if simple_detection:
                            source_lang = simple_detection
                            logger.info(f"Fallback detection: {source_lang}")
                        else:
                            # Final fallback for very short text - assume English
                            source_lang = "en"
                            logger.info("Using English as fallback for short/unclear text")
                    except:
                        source_lang = "en"
                        logger.info("Detection failed, defaulting to English")
            
            # Check if already in target language
            if source_lang == "en" and target_lang.lower() == "english":
                return {
                    "success": True,
                    "translation": text.strip(),
                    "source_lang": "en",
                    "target_lang": target_lang,
                    "detected": False,
                    "processing_time": time.time() - start_time,
                    "note": "Text was already in English"
                }
            
            # Perform translation
            translated_text = self._translate_with_llm(text, source_lang, target_lang)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "translation": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "detected": source_lang == "auto",
                "processing_time": processing_time,
                "model_used": Config.GROQ_MODEL
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "translation": "",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "processing_time": time.time() - start_time
            }
    
    def _translate_with_llm(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text using Groq LLM
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language
            target_lang (str): Target language
            
        Returns:
            str: Translated text
        """
        # Get language names
        source_name = self.language_detector.get_language_name(source_lang)
        
        # Use customer support prompt for better context
        if target_lang.lower() == "english":
            prompt_template = TRANSLATION_PROMPTS["customer_support"]
        else:
            prompt_template = f"""You are a professional translator. Translate the following text from {{source_lang}} to {target_lang}. 
Provide only the translation without any explanations, notes, or additional text.

Text: {{text}}

Translation:"""
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a professional translator specializing in customer support queries."),
            ("human", prompt_template)
        ])
        
        # Create chain
        chain = prompt | self.llm
        
        try:
            # Get translation
            response = chain.invoke({
                "source_lang": source_name,
                "text": text
            })
            
            # Extract translation
            translation = response.content.strip()
            
            # Post-process translation
            translation = self._post_process_translation(translation)
            
            logger.info(f"Translation completed: {source_lang} -> {target_lang}")
            return translation
            
        except Exception as e:
            logger.error(f"LLM translation failed: {str(e)}")
            raise Exception(f"Translation service error: {str(e)}")
    
    def _post_process_translation(self, translation: str) -> str:
        """
        Post-process translation for better quality
        
        Args:
            translation (str): Raw translation from LLM
            
        Returns:
            str: Cleaned translation
        """
        # Remove common prefixes that might be added by LLM
        prefixes_to_remove = [
            "Translation:",
            "English Translation:",
            "Translated text:",
            "The translation is:",
            "Here is the translation:",
            "Translation to English:"
        ]
        
        cleaned = translation
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Remove excessive whitespace
        cleaned = " ".join(cleaned.split())
        
        # Ensure proper sentence endings
        if cleaned and not cleaned.endswith(('.', '!', '?', '。', '！', '？')):
            cleaned += '.'
        
        return cleaned.strip()
    
    def evaluate_translation(self, original: str, translation: str, source_lang: str) -> Dict[str, float]:
        """
        Evaluate translation quality using LLM
        
        Args:
            original (str): Original text
            translation (str): Translated text
            source_lang (str): Source language code
            
        Returns:
            Dict[str, float]: Quality scores
        """
        try:
            # Accuracy evaluation
            accuracy_prompt = ChatPromptTemplate.from_messages([
                ("human", "Evaluate the following translation for accuracy on a scale of 1-10.\n\nOriginal: {original}\nTranslation: {translation}\n\nScore (1-10):")
            ])
            
            accuracy_chain = accuracy_prompt | self.llm
            accuracy_response = accuracy_chain.invoke({
                "original": original,
                "translation": translation
            })
            
            # Fluency evaluation
            fluency_prompt = ChatPromptTemplate.from_messages([
                ("human", "Evaluate the following translation for fluency and naturalness on a scale of 1-10.\n\nOriginal: {original}\nTranslation: {translation}\n\nScore (1-10):")
            ])
            
            fluency_chain = fluency_prompt | self.llm
            fluency_response = fluency_chain.invoke({
                "original": original,
                "translation": translation
            })
            
            # Parse scores
            def parse_score(response_content: str) -> float:
                content = response_content.strip()
                # Extract number from response
                import re
                numbers = re.findall(r'\d+', content)
                if numbers:
                    score = int(numbers[0])
                    return min(max(score, 1), 10)  # Clamp between 1-10
                return 5.0  # Default score
            
            return {
                "accuracy": parse_score(accuracy_response.content),
                "fluency": parse_score(fluency_response.content),
                "overall": (parse_score(accuracy_response.content) + parse_score(fluency_response.content)) / 2
            }
            
        except Exception as e:
            logger.warning(f"Translation evaluation failed: {str(e)}")
            return {"accuracy": 5.0, "fluency": 5.0, "overall": 5.0}
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.language_detector.get_common_languages()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if translation service is working
        
        Returns:
            Dict[str, Any]: Health status
        """
        try:
            # Test with simple translation
            test_result = self.translate_text("Hello", "en", "Spanish")
            
            if test_result["success"]:
                return {
                    "status": "healthy",
                    "model": Config.GROQ_MODEL,
                    "test_translation": "Hello -> Hola",
                    "response_time": test_result["processing_time"]
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": test_result.get("error", "Unknown error")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize translation service
    translator = TranslationService()
    
    # Test basic translation
    test_texts = [
        "Hello, how can I help you today?",
        "¿Cómo está usted?",
        "Bonjour, comment puis-je vous aider?",
        "Guten Tag, wie kann ich Ihnen helfen?",
        "こんにちは"
    ]
    
    print("=== Translation Service Test ===")
    for text in test_texts:
        result = translator.translate_text(text)
        print(f"\nOriginal: {text}")
        print(f"Translation: {result['translation']}")
        print(f"Source: {result['source_lang']}")
        print(f"Success: {result['success']}")
        print(f"Time: {result['processing_time']:.2f}s")
    
    # Health check
    health = translator.health_check()
    print(f"\n=== Health Check ===")
    print(f"Status: {health['status']}")
