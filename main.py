"""
Main Application Entry Point for Real-Time Multilingual Query Handler
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import Config
from translation_service import TranslationService
from language_detector import LanguageDetector
from data_pipeline import DataPipeline
from evaluation_system import TranslationEvaluator, PerformanceMonitor, QualityReporter

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

class MultilingualQueryHandler:
    """Main application class orchestrating all services"""
    
    def __init__(self):
        """Initialize all services"""
        self.translation_service = None
        self.language_detector = None
        self.data_pipeline = None
        self.evaluator = None
        self.performance_monitor = None
        self.quality_reporter = None
        
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize all services"""
        try:
            logger.info("Initializing Real-Time Multilingual Query Handler...")
            
            # Validate configuration
            Config.validate()
            logger.info("Configuration validated successfully")
            
            # Initialize core services
            self.translation_service = TranslationService()
            logger.info("Translation service initialized")
            
            self.language_detector = LanguageDetector()
            logger.info("Language detector initialized")
            
            self.data_pipeline = DataPipeline(cache_ttl=Config.CACHE_TTL)
            logger.info("Data pipeline initialized")
            
            # Initialize evaluation system
            self.evaluator = TranslationEvaluator(self.translation_service)
            self.performance_monitor = PerformanceMonitor()
            self.quality_reporter = QualityReporter(self.evaluator, self.performance_monitor)
            logger.info("Evaluation system initialized")
            
            self.initialized = True
            logger.info("All services initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            return False
    
    def health_check(self) -> dict:
        """Perform comprehensive health check"""
        if not self.initialized:
            return {"status": "not_initialized", "error": "Services not initialized"}
        
        health_status = {
            "status": "healthy",
            "services": {},
            "timestamp": self.translation_service.health_check()["timestamp"] if self.translation_service else "N/A"
        }
        
        # Check translation service
        try:
            if self.translation_service:
                translation_health = self.translation_service.health_check()
                health_status["services"]["translation"] = translation_health
        except Exception as e:
            health_status["services"]["translation"] = {"status": "error", "error": str(e)}
        
        # Check language detector
        try:
            if self.language_detector:
                # Simple test
                test_result = self.language_detector.detect_language("Hello world")
                health_status["services"]["language_detector"] = {
                    "status": "healthy" if test_result == "en" else "degraded",
                    "test_result": test_result
                }
        except Exception as e:
            health_status["services"]["language_detector"] = {"status": "error", "error": str(e)}
        
        # Check data pipeline
        try:
            if self.data_pipeline:
                stats = self.data_pipeline.get_pipeline_stats()
                health_status["services"]["data_pipeline"] = {
                    "status": "healthy",
                    "cache_entries": stats["cache_stats"]["total_entries"]
                }
        except Exception as e:
            health_status["services"]["data_pipeline"] = {"status": "error", "error": str(e)}
        
        # Overall status
        service_statuses = [service.get("status", "unknown") for service in health_status["services"].values()]
        if "error" in service_statuses:
            health_status["status"] = "degraded"
        if service_statuses.count("error") > len(service_statuses) // 2:
            health_status["status"] = "unhealthy"
        
        return health_status
    
    def translate_query(self, text: str, source_lang: str = "auto", target_lang: str = "English") -> dict:
        """Process and translate a query"""
        if not self.initialized:
            return {"success": False, "error": "Services not initialized"}
        
        import time
        start_time = time.time()
        
        try:
            # Use data pipeline for processing
            pipeline_result = self.data_pipeline.process_query(text, source_lang, target_lang)
            
            # Perform actual translation
            translation_result = self.translation_service.translate_text(text, source_lang, target_lang)
            
            # Cache the result
            self.data_pipeline.cache_translation_result(text, source_lang, target_lang, translation_result)
            
            # Record performance
            processing_time = time.time() - start_time
            self.performance_monitor.record_request(
                success=translation_result["success"],
                response_time=processing_time,
                source_lang=translation_result.get("source_lang", source_lang),
                error_type=translation_result.get("error") if not translation_result["success"] else None,
                cache_hit=pipeline_result.get("from_cache", False)
            )
            
            # Evaluate translation quality if successful
            evaluation_result = None
            if translation_result["success"]:
                evaluation_result = self.evaluator.evaluate_translation_quality(
                    text, 
                    translation_result["translation"], 
                    translation_result.get("source_lang", source_lang)
                )
                self.quality_reporter.add_evaluation(evaluation_result)
            
            # Combine results
            final_result = {
                **translation_result,
                "evaluation": evaluation_result,
                "pipeline_info": {
                    "from_cache": pipeline_result.get("from_cache", False),
                    "query_type": pipeline_result.get("query_type", "general")
                }
            }
            
            return final_result
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def get_statistics(self) -> dict:
        """Get comprehensive system statistics"""
        if not self.initialized:
            return {"error": "Services not initialized"}
        
        return {
            "health": self.health_check(),
            "performance": self.performance_monitor.get_performance_summary(),
            "pipeline": self.data_pipeline.get_pipeline_stats(),
            "languages": self.performance_monitor.get_language_statistics(),
            "quality_report": self.quality_reporter.generate_quality_report()
        }
    
    def run_streamlit(self, port: int = 8501, host: str = "localhost") -> None:
        """Run the Streamlit web application"""
        if not self.initialized:
            logger.error("Services not initialized - cannot run Streamlit app")
            return
        
        logger.info(f"Starting Streamlit application on {host}:{port}")
        
        try:
            # Use subprocess to run streamlit properly
            import subprocess
            import sys
            
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                "streamlit_app.py",
                "--server.port", str(port),
                "--server.address", host,
                "--server.enableCORS", "false",
                "--server.enableXsrfProtection", "false"
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            subprocess.run(cmd, cwd=Path(__file__).parent)
            
        except KeyboardInterrupt:
            logger.info("Streamlit application stopped by user")
        except Exception as e:
            logger.error(f"Streamlit application error: {str(e)}")


def create_app() -> MultilingualQueryHandler:
    """Create and initialize the application"""
    app = MultilingualQueryHandler()
    
    if not app.initialize():
        raise RuntimeError("Failed to initialize application")
    
    return app


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-Time Multilingual Query Handler")
    parser.add_argument("--mode", choices=["web", "api", "test", "health"], default="web",
                       help="Run mode: web (Streamlit), api (CLI), test (unit tests), health (health check)")
    parser.add_argument("--port", type=int, default=8501, help="Port for web mode")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for web mode")
    
    args = parser.parse_args()
    
    try:
        # Create and initialize app
        app = create_app()
        
        if args.mode == "web":
            logger.info("Starting in web mode...")
            app.run_streamlit(port=args.port, host=args.host)
            
        elif args.mode == "health":
            logger.info("Performing health check...")
            health = app.health_check()
            print(f"Health Status: {health['status']}")
            print(f"Services: {health['services']}")
            
        elif args.mode == "api":
            logger.info("Starting in API mode (interactive CLI)...")
            print("Real-Time Multilingual Query Handler - Interactive Mode")
            print("Type 'exit' to quit, 'health' for status, 'stats' for statistics")
            
            while True:
                try:
                    user_input = input("\nEnter query (or command): ").strip()
                    
                    if user_input.lower() == "exit":
                        break
                    elif user_input.lower() == "health":
                        health = app.health_check()
                        print(f"Health: {health['status']}")
                        continue
                    elif user_input.lower() == "stats":
                        stats = app.get_statistics()
                        print(f"Statistics: {stats['performance']}")
                        continue
                    elif not user_input:
                        continue
                    
                    # Process query
                    result = app.translate_query(user_input)
                    
                    if result["success"]:
                        print(f"✅ Translation: {result['translation']}")
                        print(f"Source: {result['source_lang']} → {result['target_lang']}")
                        print(f"Time: {result['processing_time']:.2f}s")
                        
                        if result.get("evaluation"):
                            print(f"Quality Score: {result['evaluation']['overall_score']:.2f}/10")
                    else:
                        print(f"❌ Error: {result['error']}")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {str(e)}")
            
            print("Goodbye!")
            
        elif args.mode == "test":
            logger.info("Running tests...")
            # Import and run tests
            from test_system import run_all_tests
            run_all_tests()
            
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
