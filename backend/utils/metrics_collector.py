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
            from prometheus_client import generate_latest, REGISTRY
            
            # Generate metrics in Prometheus format
            metrics_text = generate_latest(REGISTRY).decode('utf-8')
            
            # Parse metrics for summary
            metrics_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'ai_requests': self._parse_metric_from_text(metrics_text, 'ai_requests_total'),
                'ai_latency': self._parse_histogram_from_text(metrics_text, 'ai_request_latency_seconds'),
                'tokens_used': self._parse_metric_from_text(metrics_text, 'ai_tokens_used_total'),
                'cost_usd': self._parse_metric_from_text(metrics_text, 'ai_cost_usd_total'),
                'workflow': self._parse_workflow_metrics(metrics_text),
                'cache': self._parse_cache_metrics(metrics_text),
                'files_processed': self._parse_metric_from_text(metrics_text, 'files_processed_total'),
                'raw_metrics': metrics_text
            }
            
            return metrics_data
            
        except Exception as e:
            print(f"Error collecting metrics summary: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.now(timezone.utc).isoformat()}
    
    def _parse_metric_from_text(self, metrics_text: str, metric_name: str) -> Dict[str, Any]:
        """Parse a metric from Prometheus text format"""
        try:
            lines = metrics_text.split('\n')
            values = {}
            total = 0.0
            
            for line in lines:
                if line.startswith(metric_name):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            value = float(parts[-1])
                            total += value
                            
                            # Extract labels
                            if '{' in parts[0]:
                                label_section = parts[0].split('{')[1].split('}')[0]
                                values[label_section] = value
                            else:
                                values['default'] = value
                        except (ValueError, IndexError):
                            pass
            
            return {'total': total, 'by_label': values}
        except Exception:
            return {'total': 0.0, 'by_label': {}}
    
    def _parse_histogram_from_text(self, metrics_text: str, metric_name: str) -> Dict[str, Any]:
        """Parse histogram metrics from Prometheus text format"""
        try:
            lines = metrics_text.split('\n')
            count = 0.0
            total_sum = 0.0
            
            for line in lines:
                if line.startswith(f"{metric_name}_count"):
                    parts = line.split()
                    if len(parts) >= 2:
                        count += float(parts[-1])
                elif line.startswith(f"{metric_name}_sum"):
                    parts = line.split()
                    if len(parts) >= 2:
                        total_sum += float(parts[-1])
            
            avg = (total_sum / count) if count > 0 else 0.0
            
            return {
                'count': count,
                'sum': total_sum,
                'avg': avg
            }
        except Exception:
            return {'count': 0.0, 'sum': 0.0, 'avg': 0.0}
    
    def _parse_workflow_metrics(self, metrics_text: str) -> Dict[str, Any]:
        """Parse workflow-specific metrics"""
        try:
            active = 0.0
            duration_data = self._parse_histogram_from_text(metrics_text, 'workflow_duration_seconds')
            
            lines = metrics_text.split('\n')
            for line in lines:
                if line.startswith('active_workflows'):
                    parts = line.split()
                    if len(parts) >= 2:
                        active = float(parts[-1])
                        break
            
            return {
                'active': active,
                'duration_count': duration_data['count'],
                'duration_avg': duration_data['avg']
            }
        except Exception:
            return {'active': 0.0, 'duration_count': 0.0, 'duration_avg': 0.0}
    
    def _parse_cache_metrics(self, metrics_text: str) -> Dict[str, Any]:
        """Parse cache metrics and calculate hit rate"""
        try:
            hits_data = self._parse_metric_from_text(metrics_text, 'cache_hits_total')
            misses_data = self._parse_metric_from_text(metrics_text, 'cache_misses_total')
            
            hits = hits_data['total']
            misses = misses_data['total']
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0.0
            
            return {
                'hits': hits,
                'misses': misses,
                'hit_rate': hit_rate
            }
        except Exception:
            return {'hits': 0.0, 'misses': 0.0, 'hit_rate': 0.0}
    
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
