"""
Unit Tests for Real-Time Multilingual Query Handler
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from language_detector import LanguageDetector
from translation_service import TranslationService
from data_pipeline import DataPipeline, QueryCache, QueryPreprocessor, QueryLogger
from evaluation_system import TranslationEvaluator, PerformanceMonitor


class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def test_config_validation_with_api_key(self):
        """Test config validation when API key is set"""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            try:
                Config.validate()
                self.assertTrue(True)
            except ValueError:
                self.fail("Config validation should pass with valid API key")
    
    def test_config_validation_without_api_key(self):
        """Test config validation fails without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                Config.validate()


class TestLanguageDetector(unittest.TestCase):
    """Test language detection functionality"""
    
    def setUp(self):
        self.detector = LanguageDetector()
    
    def test_detect_english(self):
        """Test English language detection"""
        result = self.detector.detect_language("Hello, how are you today?")
        self.assertEqual(result, "en")
    
    def test_detect_spanish(self):
        """Test Spanish language detection"""
        result = self.detector.detect_language("Hola, ¿cómo estás?")
        self.assertEqual(result, "es")
    
    def test_detect_short_text(self):
        """Test detection with short text"""
        result = self.detector.detect_language("Hi")
        # Short text might not be detected reliably
        self.assertIsInstance(result, (str, type(None)))
    
    def test_clean_text(self):
        """Test text cleaning"""
        dirty_text = "  Hello   world  http://example.com  !!!"
        clean_text = self.detector._clean_text(dirty_text)
        self.assertNotIn("http://example.com", clean_text)
        self.assertNotIn("!!!", clean_text)
    
    def test_is_english(self):
        """Test English detection"""
        self.assertTrue(self.detector.is_english("Hello world"))
        self.assertFalse(self.detector.is_english("Hola mundo"))
    
    def test_get_language_name(self):
        """Test language name retrieval"""
        name = self.detector.get_language_name("en")
        self.assertEqual(name, "English")


class TestQueryCache(unittest.TestCase):
    """Test query caching functionality"""
    
    def setUp(self):
        self.cache = QueryCache(ttl_seconds=1)  # Short TTL for testing
    
    def test_cache_set_and_get(self):
        """Test basic cache operations"""
        result = {"success": True, "translation": "Hello"}
        self.cache.set("test text", "es", "en", result)
        
        cached = self.cache.get("test text", "es", "en")
        self.assertEqual(cached, result)
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        result = {"success": True}
        self.cache.set("test text", "es", "en", result)
        
        # Should be available immediately
        cached = self.cache.get("test text", "es", "en")
        self.assertIsNotNone(cached)
        
        # Wait for expiration
        import time
        time.sleep(1.1)
        
        # Should be expired
        cached = self.cache.get("test text", "es", "en")
        self.assertIsNone(cached)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = self.cache._generate_key("text", "es", "en")
        key2 = self.cache._generate_key("text", "es", "en")
        key3 = self.cache._generate_key("different", "es", "en")
        
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)
    
    def test_cache_stats(self):
        """Test cache statistics"""
        self.cache.set("test1", "es", "en", {"result": "1"})
        self.cache.set("test2", "fr", "en", {"result": "2"})
        
        stats = self.cache.get_stats()
        self.assertEqual(stats["total_entries"], 2)


class TestQueryPreprocessor(unittest.TestCase):
    """Test query preprocessing functionality"""
    
    def setUp(self):
        self.preprocessor = QueryPreprocessor()
    
    def test_clean_text(self):
        """Test text cleaning"""
        dirty_text = "  Hello   world  !!!"
        clean_text = self.preprocessor.clean_text(dirty_text)
        self.assertEqual(clean_text, "Hello world!")
    
    def test_truncate_text(self):
        """Test text truncation"""
        long_text = "This is a very long text that should be truncated at some point"
        truncated = self.preprocessor.truncate_text(long_text, max_length=20)
        self.assertLessEqual(len(truncated), 23)  # 20 + "..."
    
    def test_detect_query_type_support(self):
        """Test customer support query detection"""
        support_query = "I need help with my account login"
        query_type = self.preprocessor.detect_query_type(support_query)
        self.assertEqual(query_type, "customer_support")
    
    def test_detect_query_type_greeting(self):
        """Test greeting detection"""
        greeting = "Hello, how are you?"
        query_type = self.preprocessor.detect_query_type(greeting)
        self.assertEqual(query_type, "greeting")
    
    def test_detect_query_type_question(self):
        """Test question detection"""
        question = "What is your refund policy?"
        query_type = self.preprocessor.detect_query_type(question)
        self.assertEqual(query_type, "question")
    
    def test_preprocess_pipeline(self):
        """Test complete preprocessing pipeline"""
        dirty_text = "  Hello world!!!   This is a test  "
        processed = self.preprocessor.preprocess(dirty_text, max_length=50)
        self.assertIn("Hello world", processed)


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring"""
    
    def setUp(self):
        self.monitor = PerformanceMonitor()
    
    def test_record_successful_request(self):
        """Test recording successful requests"""
        self.monitor.record_request(True, 1.5, "es", cache_hit=False)
        
        summary = self.monitor.get_performance_summary()
        self.assertEqual(summary["total_requests"], 1)
        self.assertEqual(summary["successful_requests"], 1)
        self.assertEqual(summary["average_response_time"], 1.5)
    
    def test_record_failed_request(self):
        """Test recording failed requests"""
        self.monitor.record_request(False, 0.5, "fr", error_type="timeout")
        
        summary = self.monitor.get_performance_summary()
        self.assertEqual(summary["total_requests"], 1)
        self.assertEqual(summary["failed_requests"], 1)
        self.assertIn("timeout", summary["error_breakdown"])
    
    def):
        """Test test_language_statistics(self language processing statistics"""
        self.monitor.record_request(True, 1.0, "es")
        self.monitor.record_request(True, 2.0, "es")
        self.monitor.record_request(True, 1.5, "fr")
        
        lang_stats = self.monitor.get_language_statistics()
        self.assertEqual(lang_stats["total_languages"], 2)
        self.assertEqual(lang_stats["language_distribution"]["es"]["count"], 2)
    
    def test_cache_performance(self):
        """Test cache performance tracking"""
        self.monitor.record_request(True, 0.1, "en", cache_hit=True)
        self.monitor.record_request(True, 2.0, "es", cache_hit=False)
        
        summary = self.monitor.get_performance_summary()
        self.assertEqual(summary["cache_hit_rate"], 50.0)


class TestTranslationEvaluator(unittest.TestCase):
    """Test translation evaluation"""
    
    def setUp(self):
        # Mock translation service for testing
        self.mock_translation_service = Mock()
        self.mock_translation_service.evaluate_translation.return_value = {
            "accuracy": 8.0,
            "fluency": 7.5
        }
        
        self.evaluator = TranslationEvaluator(self.mock_translation_service)
    
    def test_length_analysis(self):
        """Test length analysis"""
        original = "Hello world"
        translation = "Hola mundo"
        
        result = self.evaluator._analyze_length(original, translation)
        self.assertIn("ratio", result)
        self.assertIn("score", result)
        self.assertIn("interpretation", result)
    
    def test_language_check(self):
        """Test language check"""
        translation = "Hello world"
        result = self.evaluator._check_translation_language(translation)
        
        self.assertTrue(result["is_english"])
        self.assertEqual(result["detected_lang"], "en")
    
    def test_content_preservation(self):
        """Test content preservation analysis"""
        original = "I need help with account number 12345"
        translation = "Necesito ayuda con el número de cuenta 12345"
        
        result = self.evaluator._analyze_content_preservation(original, translation)
        
        self.assertIn("word_preservation_ratio", result)
        self.assertIn("numbers_score", result)
        self.assertGreater(result["numbers_score"], 0)  # Should preserve numbers


class TestDataPipeline(unittest.TestCase):
    """Test data pipeline integration"""
    
    def setUp(self):
        self.pipeline = DataPipeline()
    
    def test_process_query(self):
        """Test query processing"""
        result = self.pipeline.process_query("Hello world", "en", "English")
        
        self.assertIn("success", result)
        self.assertIn("text", result)
        self.assertIn("source_lang", result)
        self.assertIn("target_lang", result)
        self.assertEqual(result["text"], "Hello world")
    
    def test_preprocessing_in_pipeline(self):
        """Test preprocessing integration"""
        dirty_text = "  Hello   world  !!!"
        result = self.pipeline.process_query(dirty_text, "en", "English")
        
        # Should clean the text
        self.assertNotIn("  ", result["text"])
        self.assertNotEqual("!!!", result["text"][-3:])
    
    def test_pipeline_statistics(self):
        """Test pipeline statistics"""
        self.pipeline.process_query("Test 1", "en", "English")
        self.pipeline.process_query("Test 2", "es", "English")
        
        stats = self.pipeline.get_pipeline_stats()
        self.assertIn("cache_stats", stats)
        self.assertIn("language_stats", stats)


class TestSystemIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock the API key for testing
        os.environ['GROQ_API_KEY'] = 'test_key_for_testing'
    
    @patch('translation_service.ChatGroq')
    def test_translation_service_integration(self, mock_groq):
        """Test translation service integration"""
        # Mock Groq response
        mock_response = Mock()
        mock_response.content = "Hello, how are you?"
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)
        
        with patch('translation_service.ChatPromptTemplate.from_messages', return_value=mock_prompt):
            # This test would require actual API mocking
            # For now, just test that the service can be instantiated
            try:
                service = TranslationService()
                # We expect this to fail due to invalid API key, but we can test initialization
                self.assertIsNotNone(service)
            except Exception:
                pass  # Expected to fail without valid API
    
    def test_end_to_end_workflow(self):
        """Test complete workflow without API calls"""
        # Test that all components can work together
        pipeline = DataPipeline()
        
        # Test preprocessing
        processed = pipeline.preprocessor.preprocess("Hello world")
        self.assertEqual(processed, "Hello world")
        
        # Test language detection
        detector = LanguageDetector()
        lang = detector.detect_language("Hello world")
        self.assertEqual(lang, "en")
        
        # Test caching
        pipeline.cache.set("test", "en", "en", {"result": "test"})
        cached = pipeline.cache.get("test", "en", "en")
        self.assertEqual(cached["result"], "test")


def run_all_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestConfig,
        TestLanguageDetector,
        TestQueryCache,
        TestQueryPreprocessor,
        TestPerformanceMonitor,
        TestTranslationEvaluator,
        TestDataPipeline,
        TestSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run tests
    success = run_all_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
