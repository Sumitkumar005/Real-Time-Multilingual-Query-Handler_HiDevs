"""
Data Processing Pipeline for Real-Time Multilingual Query Handler
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class QueryCache:
    """Simple in-memory cache for translation results"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, datetime] = {}
        
    def _generate_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for query"""
        content = f"{text}|{source_lang}|{target_lang}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired"""
        key = self._generate_key(text, source_lang, target_lang)
        
        if key in self.cache:
            # Check if expired
            access_time = self.access_times.get(key)
            if access_time and datetime.now() - access_time < timedelta(seconds=self.ttl_seconds):
                logger.debug(f"Cache hit for key: {key[:8]}...")
                return self.cache[key]
            else:
                # Remove expired entry
                self._remove(key)
        
        return None
    
    def set(self, text: str, source_lang: str, target_lang: str, result: Dict[str, Any]) -> None:
        """Cache translation result"""
        key = self._generate_key(text, source_lang, target_lang)
        self.cache[key] = result
        self.access_times[key] = datetime.now()
        logger.debug(f"Cached result for key: {key[:8]}...")
    
    def _remove(self, key: str) -> None:
        """Remove expired cache entry"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def clear_expired(self) -> int:
        """Remove all expired entries"""
        now = datetime.now()
        expired_keys = []
        
        for key, access_time in self.access_times.items():
            if now - access_time >= timedelta(seconds=self.ttl_seconds):
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove(key)
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        active_count = 0
        expired_count = 0
        
        for key, access_time in self.access_times.items():
            if now - access_time < timedelta(seconds=self.ttl_seconds):
                active_count += 1
            else:
                expired_count += 1
        
        return {
            "total_entries": len(self.cache),
            "active_entries": active_count,
            "expired_entries": expired_count,
            "ttl_seconds": self.ttl_seconds
        }


class QueryLogger:
    """Logger for tracking query patterns and performance"""
    
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
        self.language_stats: Dict[str, int] = defaultdict(int)
        self.performance_stats: Dict[str, List[float]] = defaultdict(list)
        self.error_stats: Dict[str, int] = defaultdict(int)
        
    def log_query(self, text: str, source_lang: str, target_lang: str, 
                  result: Dict[str, Any]) -> None:
        """Log query details"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "success": result.get("success", False),
            "processing_time": result.get("processing_time", 0),
            "error": result.get("error")
        }
        
        self.queries.append(log_entry)
        
        # Update stats
        self.language_stats[source_lang] += 1
        
        if result.get("success"):
            self.performance_stats[source_lang].append(result.get("processing_time", 0))
        else:
            error_type = result.get("error", "unknown_error")
            self.error_stats[error_type] += 1
        
        # Keep only last 1000 queries to prevent memory issues
        if len(self.queries) > 1000:
            self.queries = self.queries[-1000:]
    
    def get_language_stats(self) -> Dict[str, int]:
        """Get language distribution statistics"""
        return dict(self.language_stats)
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics by language"""
        stats = {}
        for lang, times in self.performance_stats.items():
            if times:
                stats[lang] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        return stats
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return dict(self.error_stats)
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent queries"""
        return self.queries[-limit:]
    
    def clear_stats(self) -> None:
        """Clear all statistics"""
        self.queries.clear()
        self.language_stats.clear()
        self.performance_stats.clear()
        self.error_stats.clear()


class QueryPreprocessor:
    """Preprocess queries before translation"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        
        # Remove excessive punctuation
        import re
        cleaned = re.sub(r'([!?.])\1+', r'\1', cleaned)
        
        # Normalize quotes
        cleaned = re.sub(r'["""]', '"', cleaned)
        cleaned = re.sub(r"[']", "'", cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 1000) -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        
        # Try to truncate at sentence boundary
        sentences = text.split('. ')
        truncated = ""
        
        for sentence in sentences:
            if len(truncated + sentence + '. ') <= max_length:
                truncated += sentence + '. '
            else:
                break
        
        if truncated:
            return truncated.strip()
        else:
            # Fallback to simple truncation
            return text[:max_length-3] + "..."
    
    @staticmethod
    def detect_query_type(text: str) -> str:
        """Detect type of query for better processing"""
        text_lower = text.lower()
        
        # Customer support patterns
        support_patterns = [
            "help", "support", "problem", "issue", "error", "broken", "not working",
            "refund", "return", "cancel", "order", "delivery", "shipping",
            "account", "login", "password", "billing", "payment"
        ]
        
        # Greeting patterns
        greeting_patterns = [
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "how are you", "what's up"
        ]
        
        # Question patterns
        question_patterns = [
            "what", "how", "when", "where", "why", "who", "which", "can you",
            "could you", "would you", "do you", "are you", "is it"
        ]
        
        # Check patterns
        if any(pattern in text_lower for pattern in support_patterns):
            return "customer_support"
        elif any(pattern in text_lower for pattern in greeting_patterns):
            return "greeting"
        elif any(pattern in text_lower for pattern in question_patterns):
            return "question"
        else:
            return "general"
    
    @staticmethod
    def preprocess(text: str, max_length: int = 1000) -> str:
        """Complete preprocessing pipeline"""
        cleaned = QueryPreprocessor.clean_text(text)
        truncated = QueryPreprocessor.truncate_text(cleaned, max_length)
        return truncated


class DataPipeline:
    """Main data processing pipeline"""
    
    def __init__(self, cache_ttl: int = 3600):
        self.cache = QueryCache(ttl_seconds=cache_ttl)
        self.logger = QueryLogger()
        self.preprocessor = QueryPreprocessor()
        
    def process_query(self, text: str, source_lang: str = "auto", 
                     target_lang: str = "English") -> Dict[str, Any]:
        """Process query through complete pipeline"""
        
        # Preprocess
        processed_text = self.preprocessor.preprocess(text)
        query_type = self.preprocessor.detect_query_type(processed_text)
        
        # Check cache first
        cached_result = self.cache.get(processed_text, source_lang, target_lang)
        if cached_result:
            cached_result["from_cache"] = True
            cached_result["query_type"] = query_type
            return cached_result
        
        # If not in cache, would need translation service
        # This is a placeholder - actual translation happens in translation_service
        result = {
            "success": False,
            "error": "Translation service not available in pipeline",
            "text": processed_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "query_type": query_type,
            "from_cache": False,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log the query
        self.logger.log_query(processed_text, source_lang, target_lang, result)
        
        return result
    
    def cache_translation_result(self, original_text: str, source_lang: str, 
                                target_lang: str, result: Dict[str, Any]) -> None:
        """Cache successful translation result"""
        if result.get("success"):
            self.cache.set(original_text, source_lang, target_lang, result)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics"""
        return {
            "cache_stats": self.cache.get_stats(),
            "language_stats": self.logger.get_language_stats(),
            "performance_stats": self.logger.get_performance_stats(),
            "error_stats": self.logger.get_error_stats(),
            "recent_queries": self.logger.get_recent_queries(5)
        }
    
    def clear_cache(self) -> int:
        """Clear expired cache entries"""
        return self.cache.clear_expired()
    
    def reset_stats(self) -> None:
        """Reset all statistics"""
        self.logger.clear_stats()


# Example usage and testing
if __name__ == "__main__":
    # Test the data pipeline
    pipeline = DataPipeline()
    
    # Test preprocessing
    test_texts = [
        "Hello, how can I help you today???",
        "¿Cómo está usted?    This is a longer text that might need truncation...",
        "  Hello   world  ",
        "What is your refund policy?"
    ]
    
    print("=== Data Pipeline Test ===")
    for text in test_texts:
        processed = pipeline.preprocessor.preprocess(text)
        query_type = pipeline.preprocessor.detect_query_type(processed)
        
        print(f"\nOriginal: '{text}'")
        print(f"Processed: '{processed}'")
        print(f"Type: {query_type}")
    
    # Test pipeline
    print("\n=== Pipeline Processing ===")
    for text in test_texts:
        result = pipeline.process_query(text)
        print(f"\nText: '{text[:50]}...'")
        print(f"Success: {result['success']}")
        print(f"Type: {result['query_type']}")
    
    # Get stats
    stats = pipeline.get_pipeline_stats()
    print(f"\n=== Pipeline Statistics ===")
    print(f"Cache entries: {stats['cache_stats']['total_entries']}")
    print(f"Language stats: {stats['language_stats']}")
    print(f"Error stats: {stats['error_stats']}")
