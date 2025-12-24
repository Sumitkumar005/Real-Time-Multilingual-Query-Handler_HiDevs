"""
Configuration and Environment Settings for Real-Time Multilingual Query Handler
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import streamlit for secrets (when deployed on Streamlit Cloud)
try:
    import streamlit as st
    _streamlit_available = True
except ImportError:
    _streamlit_available = False

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get secret from Streamlit secrets or environment variables"""
    if _streamlit_available:
        try:
            return st.secrets.get(key, os.getenv(key, default))
        except:
            return os.getenv(key, default)
    return os.getenv(key, default)

class Config:
    """Application configuration class"""
    
    # API Keys
    GROQ_API_KEY: Optional[str] = get_secret("GROQ_API_KEY")
    
    # Model Settings
    GROQ_MODEL = "llama-3.1-8b-instant"  # Confirmed working model
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Application Settings
    APP_TITLE = get_secret("APP_TITLE", "Real-Time Multilingual Query Handler")
    APP_DESCRIPTION = "AI-powered translation for global customer support"
    
    # Translation Settings
    MAX_QUERY_LENGTH = int(get_secret("MAX_QUERY_LENGTH", "1000"))
    TRANSLATION_TIMEOUT = int(get_secret("TRANSLATION_TIMEOUT", "30"))
    CACHE_TTL = int(get_secret("CACHE_TTL", "3600"))  # 1 hour
    
    # Vector Database Settings
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    RETRIEVAL_K = 3
    
    # UI Settings
    MAX_HISTORY_ITEMS = 10
    DEFAULT_TARGET_LANGUAGE = "English"
    
    # Logging
    LOG_LEVEL = get_secret("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required. Please set it in Streamlit secrets or environment variables.")
        return True

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    "auto": "Auto Detect",
    "en": "English",
    "es": "Spanish", 
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "nl": "Dutch",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "pl": "Polish",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "et": "Estonian",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "el": "Greek",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "tl": "Filipino",
    "fa": "Persian",
    "ur": "Urdu",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "kn": "Kannada",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ne": "Nepali",
    "si": "Sinhala",
    "my": "Myanmar",
    "km": "Khmer",
    "lo": "Lao",
    "ka": "Georgian",
    "am": "Amharic",
    "sw": "Swahili",
    "zu": "Zulu",
    "af": "Afrikaans",
    "sq": "Albanian",
    "eu": "Basque",
    "ca": "Catalan",
    "gl": "Galician",
    "he": "Hebrew",
    "is": "Icelandic",
    "mk": "Macedonian",
    "mt": "Maltese",
    "sr": "Serbian",
    "uk": "Ukrainian",
    "cy": "Welsh"
}

# Translation prompt templates
TRANSLATION_PROMPTS = {
    "default": """You are a professional translator. Translate the following text from {source_lang} to English. 
Provide only the translation without any explanations, notes, or additional text.

Text: {text}

Translation:""",
    
    "customer_support": """You are a customer support translator. Translate the following customer query from {source_lang} to English. 
Focus on maintaining the meaning and tone, especially for customer service contexts. 
Provide only the translation.

Customer Query: {text}

English Translation:""",
    
    "formal": """Translate the following text from {source_lang} to English using formal language. 
Maintain professionalism and accuracy. Provide only the translation.

Text: {text}

Formal English Translation:""",
    
    "casual": """Translate the following text from {source_lang} to English using a natural, conversational tone. 
Keep the informal style but ensure accuracy. Provide only the translation.

Text: {text}

Conversational English Translation:"""
}

# Quality evaluation prompts
EVALUATION_PROMPTS = {
    "accuracy": """Evaluate the following translation for accuracy on a scale of 1-10.

Original: {original}
Translation: {translation}

Consider:
- Meaning preservation
- Grammatical correctness
- Cultural appropriateness
- Clarity

Score (1-10):""",
    
    "fluency": """Evaluate the following translation for fluency and naturalness on a scale of 1-10.

Original: {original}
Translation: {translation}

Consider:
- Natural English flow
- Idiomatic expressions
- Readability
- Style consistency

Score (1-10):"""
}
