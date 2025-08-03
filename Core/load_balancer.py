#!/usr/bin/env python3
"""
OpenLLM Toolkit - Load Balancer
Distributes requests across multiple LLM providers for optimal performance
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .llm_manager import LLMRequest, LLMResponse, BaseLLMProvider

logger = logging.getLogger(__name__)

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    COST_OPTIMIZED = "cost_optimized"
    AVAILABILITY = "availability"

@dataclass
class ProviderStats:
    """Statistics for a provider"""
    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    last_used: float = 0.0
    is_available: bool = True
    cost_per_token: float = 0.0
    current_load: int = 0

class LoadBalancer:
    """Load balancer for distributing requests across LLM providers"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN):
        self.strategy = strategy
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.stats: Dict[str, ProviderStats] = {}
        self.current_index = 0
        self.last_update = time.time()
        
        logger.info(f"Load balancer initialized with strategy: {strategy.value}")
    
    def add_provider(self, name: str, provider: BaseLLMProvider, cost_per_token: float = 0.0):
        """Add a provider to the load balancer"""
        self.providers[name] = provider
        self.stats[name] = ProviderStats(
            name=name,
            cost_per_token=cost_per_token
        )
        logger.info(f"Added provider to load balancer: {name}")
    
    def remove_provider(self, name: str):
        """Remove a provider from the load balancer"""
        if name in self.providers:
            del self.providers[name]
            del self.stats[name]
            logger.info(f"Removed provider from load balancer: {name}")
    
    def get_next_provider(self, request: LLMRequest) -> Optional[Tuple[str, BaseLLMProvider]]:
        """Get the next provider based on the load balancing strategy"""
        available_providers = [
            (name, provider) for name, provider in self.providers.items()
            if self.stats[name].is_available
        ]
        
        if not available_providers:
            logger.warning("No available providers in load balancer")
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin(available_providers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(available_providers)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(available_providers)
        elif self.strategy == LoadBalancingStrategy.RESPONSE_TIME:
            return self._response_time(available_providers)
        elif self.strategy == LoadBalancingStrategy.COST_OPTIMIZED:
            return self._cost_optimized(available_providers)
        elif self.strategy == LoadBalancingStrategy.AVAILABILITY:
            return self._availability(available_providers)
        else:
            return available_providers[0]
    
    def _round_robin(self, available_providers: List[Tuple[str, BaseLLMProvider]]) -> Tuple[str, BaseLLMProvider]:
        """Round-robin selection"""
        provider = available_providers[self.current_index % len(available_providers)]
        self.current_index += 1
        return provider
    
    def _weighted_round_robin(self, available_providers: List[Tuple[str, BaseLLMProvider]]) -> Tuple[str, BaseLLMProvider]:
        """Weighted round-robin based on success rate and response time"""
        weights = []
        for name, _ in available_providers:
            stats = self.stats[name]
            if stats.total_requests == 0:
                weight = 1.0
            else:
                success_rate = stats.successful_requests / stats.total_requests
                response_factor = max(0.1, 1.0 / (stats.average_response_time + 0.1))
                weight = success_rate * response_factor
            weights.append(weight)
        
        # Select provider based on weights
        total_weight = sum(weights)
        if total_weight == 0:
            return available_providers[0]
        
        import random
        rand = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if rand <= cumulative:
                return available_providers[i]
        
        return available_providers[0]
    
    def _least_connections(self, available_providers: List[Tuple[str, BaseLLMProvider]]) -> Tuple[str, BaseLLMProvider]:
        """Select provider with least current load"""
        return min(available_providers, key=lambda x: self.stats[x[0]].current_load)
    
    def _response_time(self, available_providers: List[Tuple[str, BaseLLMProvider]]) -> Tuple[str, BaseLLMProvider]:
        """Select provider with best average response time"""
        return min(available_providers, key=lambda x: self.stats[x[0]].average_response_time)
    
    def _cost_optimized(self, available_providers: List[Tuple[str, BaseLLMProvider]]) -> Tuple[str, BaseLLMProvider]:
        """Select provider with lowest cost per token"""
        return min(available_providers, key=lambda x: self.stats[x[0]].cost_per_token)
    
    def _availability(self, available_providers: List[Tuple[str, BaseLLMProvider]]) -> Tuple[str, BaseLLMProvider]:
        """Select provider with highest availability (success rate)"""
        def availability_score(provider_tuple):
            name = provider_tuple[0]
            stats = self.stats[name]
            if stats.total_requests == 0:
                return 1.0
            return stats.successful_requests / stats.total_requests
        
        return max(available_providers, key=availability_score)
    
    async def execute_request(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Execute a request using load balancing"""
        start_time = time.time()
        
        # Get next provider
        provider_info = self.get_next_provider(request)
        if not provider_info:
            return None
        
        provider_name, provider = provider_info
        stats = self.stats[provider_name]
        
        # Update stats
        stats.total_requests += 1
        stats.current_load += 1
        stats.last_used = time.time()
        
        try:
            # Execute request
            response = await provider.generate(request)
            
            # Update success stats
            stats.successful_requests += 1
            response_time = time.time() - start_time
            stats.total_response_time += response_time
            stats.average_response_time = stats.total_response_time / stats.total_requests
            
            logger.info(f"Request completed via {provider_name} in {response_time:.2f}s")
            return response
            
        except Exception as e:
            # Update failure stats
            stats.failed_requests += 1
            response_time = time.time() - start_time
            stats.total_response_time += response_time
            stats.average_response_time = stats.total_response_time / stats.total_requests
            
            logger.error(f"Request failed via {provider_name}: {e}")
            
            # Mark provider as unavailable if too many failures
            failure_rate = stats.failed_requests / stats.total_requests
            if failure_rate > 0.5 and stats.total_requests > 10:
                stats.is_available = False
                logger.warning(f"Marked {provider_name} as unavailable due to high failure rate")
            
            return None
        
        finally:
            stats.current_load -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        return {
            "strategy": self.strategy.value,
            "total_providers": len(self.providers),
            "available_providers": sum(1 for stats in self.stats.values() if stats.is_available),
            "providers": {
                name: {
                    "total_requests": stats.total_requests,
                    "successful_requests": stats.successful_requests,
                    "failed_requests": stats.failed_requests,
                    "success_rate": stats.successful_requests / stats.total_requests if stats.total_requests > 0 else 0,
                    "average_response_time": stats.average_response_time,
                    "current_load": stats.current_load,
                    "is_available": stats.is_available,
                    "cost_per_token": stats.cost_per_token
                }
                for name, stats in self.stats.items()
            }
        }
    
    def reset_provider(self, name: str):
        """Reset a provider's availability status"""
        if name in self.stats:
            self.stats[name].is_available = True
            logger.info(f"Reset availability for provider: {name}")
    
    def cleanup_inactive_providers(self, timeout_seconds: int = 300):
        """Mark providers as unavailable if they haven't been used recently"""
        current_time = time.time()
        for name, stats in self.stats.items():
            if current_time - stats.last_used > timeout_seconds and stats.current_load == 0:
                stats.is_available = False
                logger.info(f"Marked {name} as inactive due to timeout")

# Global load balancer instance
load_balancer = LoadBalancer() 