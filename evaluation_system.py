"""
Evaluation and Metrics System for Real-Time Multilingual Query Handler
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from translation_service import TranslationService
from language_detector import LanguageDetector
from config import Config

logger = logging.getLogger(__name__)

class TranslationEvaluator:
    """Evaluate translation quality using multiple metrics"""
    
    def __init__(self, translation_service: TranslationService):
        self.translation_service = translation_service
        self.language_detector = LanguageDetector()
        
    def evaluate_translation_quality(self, original: str, translation: str, 
                                   source_lang: str) -> Dict[str, Any]:
        """
        Comprehensive translation quality evaluation
        
        Args:
            original (str): Original text
            translation (str): Translated text
            source_lang (str): Source language code
            
        Returns:
            Dict[str, Any]: Quality evaluation results
        """
        evaluation_results = {
            "timestamp": datetime.now().isoformat(),
            "original_length": len(original),
            "translation_length": len(translation),
            "source_lang": source_lang,
            "length_ratio": len(translation) / max(len(original), 1),
            "quality_metrics": {},
            "feedback": {}
        }
        
        # 1. Length analysis
        evaluation_results["quality_metrics"]["length_analysis"] = self._analyze_length(original, translation)
        
        # 2. LLM-based quality assessment
        llm_evaluation = self.translation_service.evaluate_translation(original, translation, source_lang)
        evaluation_results["quality_metrics"]["llm_evaluation"] = llm_evaluation
        
        # 3. Language detection check
        detection_check = self._check_translation_language(translation)
        evaluation_results["quality_metrics"]["language_check"] = detection_check
        
        # 4. Content preservation analysis
        content_preservation = self._analyze_content_preservation(original, translation)
        evaluation_results["quality_metrics"]["content_preservation"] = content_preservation
        
        # 5. Overall quality score
        overall_score = self._calculate_overall_score(evaluation_results["quality_metrics"])
        evaluation_results["overall_score"] = overall_score
        
        # 6. Generate feedback
        evaluation_results["feedback"] = self._generate_feedback(evaluation_results)
        
        return evaluation_results
    
    def _analyze_length(self, original: str, translation: str) -> Dict[str, float]:
        """Analyze length relationship between original and translation"""
        orig_len = len(original)
        trans_len = len(translation)
        
        if orig_len == 0:
            return {"ratio": 0, "score": 0}
        
        ratio = trans_len / orig_len
        
        # Score based on reasonable length ratios (0.5 to 2.0)
        if 0.5 <= ratio <= 2.0:
            score = 10.0
        elif 0.3 <= ratio < 0.5 or 2.0 < ratio <= 3.0:
            score = 7.0
        elif 0.2 <= ratio < 0.3 or 3.0 < ratio <= 4.0:
            score = 5.0
        else:
            score = 2.0
        
        return {
            "ratio": ratio,
            "score": score,
            "interpretation": self._interpret_length_ratio(ratio)
        }
    
    def _interpret_length_ratio(self, ratio: float) -> str:
        """Interpret length ratio for human understanding"""
        if 0.8 <= ratio <= 1.2:
            return "Excellent - Similar length"
        elif 0.5 <= ratio < 0.8 or 1.2 < ratio <= 2.0:
            return "Good - Acceptable length difference"
        elif 0.3 <= ratio < 0.5 or 2.0 < ratio <= 3.0:
            return "Fair - Notable length difference"
        else:
            return "Poor - Significant length difference"
    
    def _check_translation_language(self, translation: str) -> Dict[str, Any]:
        """Check if translation is in English"""
        detection = self.language_detector.detect_with_confidence(translation)
        
        if not detection:
            return {"is_english": False, "confidence": 0, "detected_lang": "unknown"}
        
        is_english = detection["language"] == "en"
        confidence = detection["confidence"] if is_english else detection["confidence"]
        
        return {
            "is_english": is_english,
            "confidence": confidence,
            "detected_lang": detection["language"],
            "score": 10.0 if is_english else max(0, 10.0 - confidence * 10)
        }
    
    def _analyze_content_preservation(self, original: str, translation: str) -> Dict[str, Any]:
        """Analyze if key content is preserved in translation"""
        # Simple heuristics for content preservation
        orig_words = set(original.lower().split())
        trans_words = set(translation.lower().split())
        
        # Check for common words preservation
        common_words = orig_words.intersection(trans_words)
        preservation_ratio = len(common_words) / max(len(orig_words), 1)
        
        # Check for numbers and special characters
        import re
        
        orig_numbers = re.findall(r'\d+', original)
        trans_numbers = re.findall(r'\d+', translation)
        
        numbers_preserved = len(set(orig_numbers).intersection(set(trans_numbers)))
        numbers_total = max(len(orig_numbers), 1)
        
        # Check for URLs, emails
        orig_urls = re.findall(r'http[s]?://\S+', original)
        trans_urls = re.findall(r'http[s]?://\S+', translation)
        
        urls_preserved = len(set(orig_urls).intersection(set(trans_urls)))
        urls_total = max(len(orig_urls), 1)
        
        return {
            "word_preservation_ratio": preservation_ratio,
            "word_preservation_score": min(10.0, preservation_ratio * 10),
            "numbers_preserved": numbers_preserved,
            "numbers_total": numbers_total,
            "numbers_score": (numbers_preserved / numbers_total) * 10 if numbers_total > 0 else 10,
            "urls_preserved": urls_preserved,
            "urls_total": urls_total,
            "urls_score": (urls_preserved / urls_total) * 10 if urls_total > 0 else 10
        }
    
    def _calculate_overall_score(self, quality_metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        scores = []
        
        # Length analysis score
        scores.append(quality_metrics["length_analysis"]["score"])
        
        # LLM evaluation scores
        llm_scores = quality_metrics["llm_evaluation"]
        scores.extend([llm_scores["accuracy"], llm_scores["fluency"]])
        
        # Language check score
        scores.append(quality_metrics["language_check"]["score"])
        
        # Content preservation scores
        content_scores = quality_metrics["content_preservation"]
        scores.extend([
            content_scores["word_preservation_score"],
            content_scores["numbers_score"],
            content_scores["urls_score"]
        ])
        
        return statistics.mean(scores)
    
    def _generate_feedback(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate human-readable feedback"""
        feedback = {
            "summary": "",
            "strengths": [],
            "areas_for_improvement": [],
            "recommendations": []
        }
        
        overall_score = evaluation_results["overall_score"]
        quality_metrics = evaluation_results["quality_metrics"]
        
        # Overall summary
        if overall_score >= 8.0:
            feedback["summary"] = "Excellent translation quality"
        elif overall_score >= 6.0:
            feedback["summary"] = "Good translation quality"
        elif overall_score >= 4.0:
            feedback["summary"] = "Fair translation quality"
        else:
            feedback["summary"] = "Poor translation quality - needs improvement"
        
        # Strengths
        if quality_metrics["language_check"]["is_english"]:
            feedback["strengths"].append("Successfully translated to English")
        
        if quality_metrics["length_analysis"]["score"] >= 8.0:
            feedback["strengths"].append("Appropriate length preservation")
        
        if quality_metrics["content_preservation"]["word_preservation_score"] >= 7.0:
            feedback["strengths"].append("Good content preservation")
        
        # Areas for improvement
        if not quality_metrics["language_check"]["is_english"]:
            feedback["areas_for_improvement"].append("Translation not in English")
        
        if quality_metrics["length_analysis"]["score"] < 6.0:
            feedback["areas_for_improvement"].append("Length significantly different from original")
        
        if quality_metrics["content_preservation"]["word_preservation_score"] < 5.0:
            feedback["areas_for_improvement"].append("Poor content preservation")
        
        # Recommendations
        if overall_score < 6.0:
            feedback["recommendations"].append("Consider re-translating with more specific context")
        
        if quality_metrics["llm_evaluation"]["accuracy"] < 5.0:
            feedback["recommendations"].append("Accuracy could be improved - check for domain-specific terms")
        
        if quality_metrics["llm_evaluation"]["fluency"] < 5.0:
            feedback["recommendations"].append("Fluency issues - consider simplifying the original text")
        
        return feedback


class PerformanceMonitor:
    """Monitor translation performance and system metrics"""
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "languages_processed": defaultdict(int),
            "errors_by_type": defaultdict(int),
            "cache_hits": 0,
            "cache_misses": 0
        }
        self.start_time = datetime.now()
    
    def record_request(self, success: bool, response_time: float, 
                      source_lang: str, error_type: Optional[str] = None,
                      cache_hit: bool = False) -> None:
        """Record a translation request"""
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
            self.metrics["response_times"].append(response_time)
            self.metrics["languages_processed"][source_lang] += 1
        else:
            self.metrics["failed_requests"] += 1
            if error_type:
                self.metrics["errors_by_type"][error_type] += 1
        
        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        uptime = datetime.now() - self.start_time
        
        response_times = self.metrics["response_times"]
        
        summary = {
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": self.metrics["total_requests"],
            "success_rate": (self.metrics["successful_requests"] / 
                           max(self.metrics["total_requests"], 1)) * 100,
            "average_response_time": statistics.mean(response_times) if response_times else 0,
            "median_response_time": statistics.median(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "requests_per_minute": (self.metrics["total_requests"] / 
                                  max(uptime.total_seconds() / 60, 1)),
            "languages_processed": dict(self.metrics["languages_processed"]),
            "cache_hit_rate": (self.metrics["cache_hits"] / 
                             max(self.metrics["cache_hits"] + self.metrics["cache_misses"], 1)) * 100,
            "error_breakdown": dict(self.metrics["errors_by_type"])
        }
        
        return summary
    
    def get_language_statistics(self) -> Dict[str, Any]:
        """Get detailed language processing statistics"""
        total_lang_requests = sum(self.metrics["languages_processed"].values())
        
        lang_stats = {}
        for lang, count in self.metrics["languages_processed"].items():
            lang_stats[lang] = {
                "count": count,
                "percentage": (count / max(total_lang_requests, 1)) * 100
            }
        
        return {
            "total_languages": len(self.metrics["languages_processed"]),
            "language_distribution": lang_stats,
            "most_common_language": max(self.metrics["languages_processed"].items(), 
                                      key=lambda x: x[1])[0] if self.metrics["languages_processed"] else None
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "languages_processed": defaultdict(int),
            "errors_by_type": defaultdict(int),
            "cache_hits": 0,
            "cache_misses": 0
        }
        self.start_time = datetime.now()


class QualityReporter:
    """Generate quality reports and analytics"""
    
    def __init__(self, evaluator: TranslationEvaluator, monitor: PerformanceMonitor):
        self.evaluator = evaluator
        self.monitor = monitor
        self.evaluation_history: List[Dict[str, Any]] = []
    
    def add_evaluation(self, evaluation: Dict[str, Any]) -> None:
        """Add evaluation result to history"""
        self.evaluation_history.append(evaluation)
        
        # Keep only last 1000 evaluations
        if len(self.evaluation_history) > 1000:
            self.evaluation_history = self.evaluation_history[-1000:]
    
    def generate_quality_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        
        # Filter evaluations by time range
        recent_evaluations = [
            eval_result for eval_result in self.evaluation_history
            if datetime.fromisoformat(eval_result["timestamp"]) > cutoff_time
        ]
        
        if not recent_evaluations:
            return {"message": "No evaluations found in the specified time range"}
        
        # Calculate aggregated metrics
        overall_scores = [eval_result["overall_score"] for eval_result in recent_evaluations]
        
        quality_metrics = {
            "time_range_hours": time_range_hours,
            "total_evaluations": len(recent_evaluations),
            "overall_quality": {
                "average_score": statistics.mean(overall_scores),
                "median_score": statistics.median(overall_scores),
                "min_score": min(overall_scores),
                "max_score": max(overall_scores),
                "standard_deviation": statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0
            },
            "metric_breakdown": self._calculate_metric_breakdown(recent_evaluations),
            "language_analysis": self._analyze_by_language(recent_evaluations),
            "performance_summary": self.monitor.get_performance_summary(),
            "quality_trends": self._analyze_quality_trends(recent_evaluations)
        }
        
        return quality_metrics
    
    def _calculate_metric_breakdown(self, evaluations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate breakdown of quality metrics"""
        length_scores = [eval_result["quality_metrics"]["length_analysis"]["score"] 
                        for eval_result in evaluations]
        llm_accuracy = [eval_result["quality_metrics"]["llm_evaluation"]["accuracy"] 
                       for eval_result in evaluations]
        llm_fluency = [eval_result["quality_metrics"]["llm_evaluation"]["fluency"] 
                      for eval_result in evaluations]
        language_scores = [eval_result["quality_metrics"]["language_check"]["score"] 
                          for eval_result in evaluations]
        
        return {
            "length_analysis_avg": statistics.mean(length_scores),
            "llm_accuracy_avg": statistics.mean(llm_accuracy),
            "llm_fluency_avg": statistics.mean(llm_fluency),
            "language_check_avg": statistics.mean(language_scores)
        }
    
    def _analyze_by_language(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze quality by source language"""
        lang_groups = defaultdict(list)
        
        for eval_result in evaluations:
            source_lang = eval_result["source_lang"]
            lang_groups[source_lang].append(eval_result["overall_score"])
        
        lang_analysis = {}
        for lang, scores in lang_groups.items():
            lang_analysis[lang] = {
                "count": len(scores),
                "average_score": statistics.mean(scores),
                "median_score": statistics.median(scores)
            }
        
        return lang_analysis
    
    def _analyze_quality_trends(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze quality trends over time"""
        if len(evaluations) < 2:
            return {"trend": "insufficient_data"}
        
        # Sort by timestamp
        sorted_evaluations = sorted(evaluations, 
                                  key=lambda x: x["timestamp"])
        
        # Calculate trend (simple linear regression)
        scores = [eval_result["overall_score"] for eval_result in sorted_evaluations]
        
        if len(scores) >= 5:
            # Calculate moving average
            window_size = min(5, len(scores) // 3)
            moving_averages = []
            for i in range(window_size - 1, len(scores)):
                window = scores[i - window_size + 1:i + 1]
                moving_averages.append(statistics.mean(window))
            
            # Determine trend
            if len(moving_averages) >= 2:
                recent_avg = statistics.mean(moving_averages[-3:])
                early_avg = statistics.mean(moving_averages[:3])
                
                if recent_avg > early_avg + 0.5:
                    trend = "improving"
                elif recent_avg < early_avg - 0.5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
        else:
            trend = "insufficient_data"
        
        return {
            "trend": trend,
            "latest_score": scores[-1] if scores else 0,
            "first_score": scores[0] if scores else 0,
            "score_change": scores[-1] - scores[0] if len(scores) >= 2 else 0
        }
    
    def export_report(self, report: Dict[str, Any], format: str = "json") -> str:
        """Export quality report in specified format"""
        if format.lower() == "json":
            return json.dumps(report, indent=2)
        elif format.lower() == "text":
            return self._format_report_as_text(report)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _format_report_as_text(self, report: Dict[str, Any]) -> str:
        """Format report as human-readable text"""
        text = "=== Translation Quality Report ===\n\n"
        
        if "message" in report:
            text += f"{report['message']}\n"
            return text
        
        text += f"Time Range: {report['time_range_hours']} hours\n"
        text += f"Total Evaluations: {report['total_evaluations']}\n\n"
        
        # Overall Quality
        overall = report["overall_quality"]
        text += "Overall Quality:\n"
        text += f"  Average Score: {overall['average_score']:.2f}/10\n"
        text += f"  Median Score: {overall['median_score']:.2f}/10\n"
        text += f"  Range: {overall['min_score']:.2f} - {overall['max_score']:.2f}\n\n"
        
        # Metric Breakdown
        metrics = report["metric_breakdown"]
        text += "Quality Metrics:\n"
        text += f"  Length Analysis: {metrics['length_analysis_avg']:.2f}/10\n"
        text += f"  LLM Accuracy: {metrics['llm_accuracy_avg']:.2f}/10\n"
        text += f"  LLM Fluency: {metrics['llm_fluency_avg']:.2f}/10\n"
        text += f"  Language Check: {metrics['language_check_avg']:.2f}/10\n\n"
        
        # Performance Summary
        perf = report["performance_summary"]
        text += "Performance:\n"
        text += f"  Success Rate: {perf['success_rate']:.1f}%\n"
        text += f"  Average Response Time: {perf['average_response_time']:.2f}s\n"
        text += f"  Cache Hit Rate: {perf['cache_hit_rate']:.1f}%\n\n"
        
        return text


# Example usage and testing
if __name__ == "__main__":
    # Test the evaluation system
    from translation_service import TranslationService
    
    # Initialize services
    translation_service = TranslationService()
    evaluator = TranslationEvaluator(translation_service)
    monitor = PerformanceMonitor()
    reporter = QualityReporter(evaluator, monitor)
    
    # Test evaluation
    test_cases = [
        ("Hello, how are you?", "Hola, ¿cómo estás?", "es"),
        ("I need help with my account", "Necesito ayuda con mi cuenta", "es"),
        ("Thank you for your service", "Merci pour votre service", "fr")
    ]
    
    print("=== Translation Evaluation Test ===")
    for original, translation, source_lang in test_cases:
        print(f"\nTesting: {original} -> {translation}")
        
        # Evaluate translation
        evaluation = evaluator.evaluate_translation_quality(original, translation, source_lang)
        
        print(f"Overall Score: {evaluation['overall_score']:.2f}/10")
        print(f"Summary: {evaluation['feedback']['summary']}")
        
        # Record performance
        monitor.record_request(True, 1.5, source_lang, cache_hit=False)
        
        # Add to reporter
        reporter.add_evaluation(evaluation)
    
    # Generate report
    report = reporter.generate_quality_report()
    print(f"\n=== Quality Report ===")
    print(reporter.export_report(report, "text"))
