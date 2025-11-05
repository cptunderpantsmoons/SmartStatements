"""
Metrics Collector for AI Financial Statement Generation System
Handles Prometheus metrics and performance monitoring
"""
import time
from typing import Dict, Any, List
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from datetime import datetime, timezone

from ..config.settings import config


class MetricsCollector:
    """Collects and exposes system metrics"""
    
    def __init__(self):
        """Initialize metrics collector"""
        # Define Prometheus metrics
        self.ai_requests_total = Counter(
            'ai_requests_total',
            'Total AI model requests',
            ['model', 'operation_type', 'status']
        )
        
        self.ai_request_latency = Histogram(
            'ai_request_latency_seconds',
            'AI request latency in seconds',
            ['model', 'operation_type']
        )
        
        self.ai_tokens_used = Counter(
            'ai_tokens_used_total',
            'Total AI tokens used',
            ['model', 'operation_type']
        )
        
        self.ai_cost_usd = Counter(
            'ai_cost_usd_total',
            'Total AI cost in USD',
            ['model', 'operation_type']
        )
        
        self.workflow_duration = Histogram(
            'workflow_duration_seconds',
            'Total workflow duration in seconds'
        )
        
        self.active_workflows = Gauge(
            'active_workflows',
            'Number of currently active workflows'
        )
        
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['model']
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['model']
        )
        
        self.file_processing = Counter(
            'files_processed_total',
            'Total files processed',
            ['file_type', 'status']
        )
        
        # Start metrics server
        try:
            start_http_server(config.metrics_port)
            print(f"Started metrics server on port {config.metrics_port}")
        except Exception as e:
            print(f"Failed to start metrics server: {str(e)}")
    
    def record_ai_request(self, model: str, operation_type: str, latency_seconds: float, 
                        token_count: int = None, cost_usd: float = None, success: bool = True):
        """Record AI request metrics"""
        status = 'success' if success else 'error'
        
        self.ai_requests_total.labels(
            model=model, 
            operation_type=operation_type, 
            status=status
        ).inc()
        
        self.ai_request_latency.labels(
            model=model, 
            operation_type=operation_type
        ).observe(latency_seconds)
        
        if token_count:
            self.ai_tokens_used.labels(
                model=model, 
                operation_type=operation_type
            ).inc(token_count)
        
        if cost_usd:
            self.ai_cost_usd.labels(
                model=model, 
                operation_type=operation_type
            ).inc(cost_usd)
    
    def record_workflow_start(self):
        """Record workflow start"""
        self.active_workflows.inc()
    
    def record_workflow_completion(self, duration_seconds: float, steps_count: int, score: float):
        """Record successful workflow completion"""
        self.active_workflows.dec()
        self.workflow_duration.observe(duration_seconds)
        
        # Record file processing metrics
        self.file_processing.labels(
            file_type='unknown',
            status='success'
        ).inc()
    
    def record_workflow_error(self, error_message: str):
        """Record workflow error"""
        self.active_workflows.dec()
        
        # Record file processing metrics
        self.file_processing.labels(
            file_type='unknown',
            status='error'
        ).inc()
    
    def record_cache_hit(self, model: str):
        """Record cache hit"""
        self.cache_hits.labels(model=model).inc()
    
    def record_cache_miss(self, model: str):
        """Record cache miss"""
        self.cache_misses.labels(model=model).inc()
    
    def record_file_processing(self, file_type: str, status: str):
        """Record file processing metrics"""
        self.file_processing.labels(
            file_type=file_type,
            status=status
        ).inc()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        try:
            # Collect metrics data
            metrics_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'ai_requests': {
                    'total': self._get_counter_value(self.ai_requests_total),
                    'by_model': self._get_counter_labels(self.ai_requests_total, 'model'),
                    'by_operation': self._get_counter_labels(self.ai_requests_total, 'operation_type'),
                    'by_status': self._get_counter_labels(self.ai_requests_total, 'status')
                },
                'ai_latency': {
                    'count': self._get_histogram_count(self.ai_request_latency),
                    'sum': self._get_histogram_sum(self.ai_request_latency),
                    'avg': self._get_histogram_avg(self.ai_request_latency)
                },
                'tokens_used': {
                    'total': self._get_counter_value(self.ai_tokens_used),
                    'by_model': self._get_counter_labels(self.ai_tokens_used, 'model')
                },
                'cost_usd': {
                    'total': self._get_counter_value(self.ai_cost_usd),
                    'by_model': self._get_counter_labels(self.ai_cost_usd, 'model')
                },
                'workflow': {
                    'active': self.active_workflows._value._value,
                    'duration_count': self._get_histogram_count(self.workflow_duration),
                    'duration_avg': self._get_histogram_avg(self.workflow_duration)
                },
                'cache': {
                    'hits': self._get_counter_value(self.cache_hits),
                    'misses': self._get_counter_value(self.cache_misses),
                    'hit_rate': self._calculate_hit_rate()
                },
                'files_processed': {
                    'total': self._get_counter_value(self.file_processing),
                    'by_type': self._get_counter_labels(self.file_processing, 'file_type'),
                    'by_status': self._get_counter_labels(self.file_processing, 'status')
                }
            }
            
            return metrics_data
            
        except Exception as e:
            print(f"Error collecting metrics summary: {str(e)}")
            return {'error': str(e)}
    
    def _get_counter_value(self, counter) -> float:
        """Get total value from counter"""
        try:
            return counter._value._value
        except:
            return 0.0
    
    def _get_counter_labels(self, counter, label_name: str) -> Dict[str, float]:
        """Get counter values by label"""
        try:
            result = {}
            for sample in counter._metrics:
                labels = sample.labels
                if label_name in labels:
                    key = labels[label_name]
                    result[key] = sample.samples[0].value if sample.samples else 0
            return result
        except:
            return {}
    
    def _get_histogram_count(self, histogram) -> float:
        """Get count from histogram"""
        try:
            return histogram._sum._value / histogram._sum._value if histogram._sum._value > 0 else 0
        except:
            return 0.0
    
    def _get_histogram_sum(self, histogram) -> float:
        """Get sum from histogram"""
        try:
            return histogram._sum._value
        except:
            return 0.0
    
    def _get_histogram_avg(self, histogram) -> float:
        """Get average from histogram"""
        try:
            count = self._get_histogram_count(histogram)
            total = self._get_histogram_sum(histogram)
            return total / count if count > 0 else 0.0
        except:
            return 0.0
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        try:
            hits = self._get_counter_value(self.cache_hits)
            misses = self._get_counter_value(self.cache_misses)
            total = hits + misses
            return (hits / total * 100) if total > 0 else 0.0
        except:
            return 0.0
    
    def reset_metrics(self):
        """Reset all metrics (for testing)"""
        try:
            self.ai_requests_total.clear()
            self.ai_request_latency.clear()
            self.ai_tokens_used.clear()
            self.ai_cost_usd.clear()
            self.workflow_duration.clear()
            self.active_workflows.set(0)
            self.cache_hits.clear()
            self.cache_misses.clear()
            self.file_processing.clear()
            print("Metrics reset successfully")
        except Exception as e:
            print(f"Error resetting metrics: {str(e)}")
