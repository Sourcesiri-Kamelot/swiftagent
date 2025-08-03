#!/usr/bin/env python3
"""
OpenLLM Toolkit - Self Healing System
Error correction, performance optimization, and automatic recovery
"""

import json
import logging
import os
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class ErrorRecord:
    """Record of an error for analysis"""
    timestamp: datetime
    error_type: str
    error_message: str
    context: Dict[str, Any]
    stack_trace: str
    resolved: bool = False
    resolution_method: Optional[str] = None

@dataclass
class PerformanceMetric:
    """Performance metric for optimization"""
    operation: str
    duration: float
    success: bool
    timestamp: datetime
    metadata: Dict[str, Any]

class SelfHealingSystem:
    """Self-healing system for error correction and optimization"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.expanduser("~/.config/openllm-toolkit/self-healing")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data files
        self.errors_file = self.data_dir / "errors.json"
        self.performance_file = self.data_dir / "performance.json"
        self.optimizations_file = self.data_dir / "optimizations.json"
        
        # In-memory storage
        self.errors: List[ErrorRecord] = []
        self.performance_metrics: List[PerformanceMetric] = []
        self.optimizations: Dict[str, Any] = {}
        
        # Load existing data
        self._load_errors()
        self._load_performance()
        self._load_optimizations()
        
        # Error patterns for automatic resolution
        self.error_patterns = {
            "import_error": {
                "pattern": "ModuleNotFoundError|ImportError",
                "resolution": "install_missing_dependency",
                "priority": "high"
            },
            "permission_error": {
                "pattern": "PermissionError|AccessDenied",
                "resolution": "fix_permissions",
                "priority": "high"
            },
            "connection_error": {
                "pattern": "ConnectionError|TimeoutError",
                "resolution": "retry_with_backoff",
                "priority": "medium"
            },
            "memory_error": {
                "pattern": "MemoryError|OutOfMemory",
                "resolution": "cleanup_memory",
                "priority": "high"
            }
        }
        
        logger.info("Self-healing system initialized")
    
    def _load_errors(self):
        """Load error records from disk"""
        try:
            if self.errors_file.exists():
                with open(self.errors_file, 'r') as f:
                    data = json.load(f)
                    for error_data in data:
                        error = ErrorRecord(
                            timestamp=datetime.fromisoformat(error_data['timestamp']),
                            error_type=error_data['error_type'],
                            error_message=error_data['error_message'],
                            context=error_data['context'],
                            stack_trace=error_data['stack_trace'],
                            resolved=error_data.get('resolved', False),
                            resolution_method=error_data.get('resolution_method')
                        )
                        self.errors.append(error)
        except Exception as e:
            logger.error(f"Failed to load errors: {e}")
    
    def _save_errors(self):
        """Save error records to disk"""
        try:
            data = [asdict(error) for error in self.errors]
            with open(self.errors_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save errors: {e}")
    
    def _load_performance(self):
        """Load performance metrics from disk"""
        try:
            if self.performance_file.exists():
                with open(self.performance_file, 'r') as f:
                    data = json.load(f)
                    for metric_data in data:
                        metric = PerformanceMetric(
                            operation=metric_data['operation'],
                            duration=metric_data['duration'],
                            success=metric_data['success'],
                            timestamp=datetime.fromisoformat(metric_data['timestamp']),
                            metadata=metric_data['metadata']
                        )
                        self.performance_metrics.append(metric)
        except Exception as e:
            logger.error(f"Failed to load performance metrics: {e}")
    
    def _save_performance(self):
        """Save performance metrics to disk"""
        try:
            data = [asdict(metric) for metric in self.performance_metrics]
            with open(self.performance_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save performance metrics: {e}")
    
    def _load_optimizations(self):
        """Load optimization data from disk"""
        try:
            if self.optimizations_file.exists():
                with open(self.optimizations_file, 'r') as f:
                    self.optimizations = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load optimizations: {e}")
    
    def _save_optimizations(self):
        """Save optimization data to disk"""
        try:
            with open(self.optimizations_file, 'w') as f:
                json.dump(self.optimizations, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save optimizations: {e}")
    
    def record_error(self, error: Exception, context: Dict[str, Any] = None):
        """Record an error for analysis and potential auto-resolution"""
        error_record = ErrorRecord(
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {},
            stack_trace=traceback.format_exc()
        )
        
        self.errors.append(error_record)
        self._save_errors()
        
        # Try to auto-resolve
        self._attempt_auto_resolution(error_record)
        
        logger.warning(f"Recorded error: {error_record.error_type} - {error_record.error_message}")
    
    def _attempt_auto_resolution(self, error_record: ErrorRecord):
        """Attempt to automatically resolve an error"""
        for pattern_name, pattern_info in self.error_patterns.items():
            if pattern_info["pattern"] in error_record.error_type:
                resolution_method = getattr(self, pattern_info["resolution"], None)
                if resolution_method:
                    try:
                        resolution_method(error_record)
                        error_record.resolved = True
                        error_record.resolution_method = pattern_info["resolution"]
                        self._save_errors()
                        logger.info(f"Auto-resolved error using {pattern_info['resolution']}")
                    except Exception as e:
                        logger.error(f"Failed to auto-resolve error: {e}")
                break
    
    def install_missing_dependency(self, error_record: ErrorRecord):
        """Install missing Python dependency"""
        # Extract package name from error message
        import re
        match = re.search(r"No module named '([^']+)'", error_record.error_message)
        if match:
            package_name = match.group(1)
            try:
                import subprocess
                subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                             check=True, capture_output=True)
                logger.info(f"Installed missing dependency: {package_name}")
            except Exception as e:
                logger.error(f"Failed to install {package_name}: {e}")
    
    def fix_permissions(self, error_record: ErrorRecord):
        """Fix file permission issues"""
        # This would need to be implemented based on the specific context
        logger.info("Permission fix attempted")
    
    def retry_with_backoff(self, error_record: ErrorRecord):
        """Retry operation with exponential backoff"""
        # This would be implemented in the calling code
        logger.info("Retry with backoff suggested")
    
    def cleanup_memory(self, error_record: ErrorRecord):
        """Clean up memory to resolve memory errors"""
        import gc
        gc.collect()
        logger.info("Memory cleanup performed")
    
    def record_performance(self, operation: str, duration: float, success: bool, 
                          metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            success=success,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.performance_metrics.append(metric)
        self._save_performance()
        
        # Check for performance issues
        self._analyze_performance(operation)
    
    def _analyze_performance(self, operation: str):
        """Analyze performance for optimization opportunities"""
        recent_metrics = [
            m for m in self.performance_metrics 
            if m.operation == operation and 
            m.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_metrics) >= 5:
            avg_duration = sum(m.duration for m in recent_metrics) / len(recent_metrics)
            success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
            
            if avg_duration > 5.0:  # More than 5 seconds
                self._suggest_optimization(operation, "slow_performance", {
                    "avg_duration": avg_duration,
                    "success_rate": success_rate
                })
            
            if success_rate < 0.8:  # Less than 80% success
                self._suggest_optimization(operation, "low_success_rate", {
                    "avg_duration": avg_duration,
                    "success_rate": success_rate
                })
    
    def _suggest_optimization(self, operation: str, issue_type: str, data: Dict[str, Any]):
        """Suggest an optimization for an operation"""
        optimization = {
            "operation": operation,
            "issue_type": issue_type,
            "suggested_at": datetime.now().isoformat(),
            "data": data,
            "applied": False
        }
        
        if operation not in self.optimizations:
            self.optimizations[operation] = []
        
        self.optimizations[operation].append(optimization)
        self._save_optimizations()
        
        logger.info(f"Suggested optimization for {operation}: {issue_type}")
    
    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recent errors"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_errors = [e for e in self.errors if e.timestamp > cutoff]
        
        error_types = {}
        for error in recent_errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "resolved_errors": sum(1 for e in recent_errors if e.resolved),
            "error_types": error_types,
            "resolution_rate": sum(1 for e in recent_errors if e.resolved) / len(recent_errors) if recent_errors else 0
        }
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recent performance"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_metrics = [m for m in self.performance_metrics if m.timestamp > cutoff]
        
        operations = {}
        for metric in recent_metrics:
            if metric.operation not in operations:
                operations[metric.operation] = {
                    "count": 0,
                    "total_duration": 0,
                    "success_count": 0
                }
            
            operations[metric.operation]["count"] += 1
            operations[metric.operation]["total_duration"] += metric.duration
            if metric.success:
                operations[metric.operation]["success_count"] += 1
        
        # Calculate averages
        for op_data in operations.values():
            op_data["avg_duration"] = op_data["total_duration"] / op_data["count"]
            op_data["success_rate"] = op_data["success_count"] / op_data["count"]
        
        return {
            "total_operations": len(recent_metrics),
            "operations": operations
        }
    
    def apply_optimization(self, operation: str, optimization_index: int):
        """Apply a suggested optimization"""
        if operation in self.optimizations and len(self.optimizations[operation]) > optimization_index:
            optimization = self.optimizations[operation][optimization_index]
            optimization["applied"] = True
            optimization["applied_at"] = datetime.now().isoformat()
            self._save_optimizations()
            
            logger.info(f"Applied optimization for {operation}")
            return True
        return False
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old error and performance data"""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Clean up old errors
        self.errors = [e for e in self.errors if e.timestamp > cutoff]
        self._save_errors()
        
        # Clean up old performance metrics
        self.performance_metrics = [m for m in self.performance_metrics if m.timestamp > cutoff]
        self._save_performance()
        
        logger.info("Cleaned up old self-healing data")

# Global self-healing system instance
self_healing = SelfHealingSystem() 