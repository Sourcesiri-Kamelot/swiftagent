#!/usr/bin/env python3
"""
SwiftAgent Toolkit - Universal LLM Manager
Provides unified interface for all LLM providers with intelligent routing
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union, AsyncGenerator, Any
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """Supported LLM provider types"""
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    AZURE = "azure"
    AMAZON_Q = "amazon_q"
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL_AI = "local_ai"
    CUSTOM = "custom"

class ProviderTier(Enum):
    """Provider cost tiers"""
    FREE = "free"
    FREEMIUM = "freemium"
    PAID = "paid"
    ENTERPRISE = "enterprise"

@dataclass
class LLMProvider:
    """LLM Provider configuration"""
    name: str
    type: ProviderType
    tier: ProviderTier
    endpoint: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 4096
    context_window: int = 4096
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_functions: bool = False
    cost_per_token: float = 0.0
    rate_limit: int = 60  # requests per minute
    enabled: bool = True
    priority: int = 1  # 1 = highest priority

@dataclass
class LLMRequest:
    """LLM request structure"""
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    stream: bool = False
    tools: Optional[List[Dict]] = None
    images: Optional[List[str]] = None
    system_prompt: Optional[str] = None

@dataclass
class LLMResponse:
    """LLM response structure"""
    content: str
    provider: str
    model: str
    tokens_used: int
    cost: float
    latency: float
    metadata: Dict[str, Any]

class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self, config: LLMProvider):
        self.config = config
        self.request_count = 0
        self.last_request_time = 0
        
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream response from LLM"""
        pass
    
    async def is_available(self) -> bool:
        """Check if provider is available"""
        try:
            # Simple health check
            test_request = LLMRequest(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            await self.generate(test_request)
            return True
        except Exception as e:
            logger.warning(f"Provider {self.config.name} unavailable: {e}")
            return False
    
    def can_handle_request(self, request: LLMRequest) -> bool:
        """Check if provider can handle the request"""
        if request.images and not self.config.supports_vision:
            return False
        if request.tools and not self.config.supports_functions:
            return False
        return True
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for request"""
        estimated_tokens = sum(len(msg["content"].split()) for msg in request.messages) * 1.3
        return estimated_tokens * self.config.cost_per_token

class LLMManager:
    """Universal LLM Manager with intelligent routing"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.provider_configs: Dict[str, LLMProvider] = {}
        self.usage_stats: Dict[str, Dict] = {}
        self.performance_history: Dict[str, List[float]] = {}
        
    def register_provider(self, provider: BaseLLMProvider):
        """Register a new LLM provider"""
        self.providers[provider.config.name] = provider
        self.provider_configs[provider.config.name] = provider.config
        self.usage_stats[provider.config.name] = {
            "requests": 0,
            "errors": 0,
            "total_tokens": 0,
            "total_cost": 0.0
        }
        self.performance_history[provider.config.name] = []
        logger.info(f"Registered provider: {provider.config.name}")
    
    def get_default_providers(self) -> List[LLMProvider]:
        """Get default provider configurations"""
        return [
            LLMProvider(
                name="ollama-local",
                type=ProviderType.OLLAMA,
                tier=ProviderTier.FREE,
                endpoint="http://localhost:11434",
                model="llama3.1",
                supports_vision=True,
                priority=1
            ),
            LLMProvider(
                name="huggingface-free",
                type=ProviderType.HUGGINGFACE,
                tier=ProviderTier.FREEMIUM,
                endpoint="https://api-inference.huggingface.co",
                model="microsoft/DialoGPT-large",
                priority=2
            ),
            LLMProvider(
                name="groq-free",
                type=ProviderType.GROQ,
                tier=ProviderTier.FREEMIUM,
                endpoint="https://api.groq.com/openai/v1",
                model="llama3-8b-8192",
                supports_streaming=True,
                priority=3
            ),
            LLMProvider(
                name="local-ai",
                type=ProviderType.LOCAL_AI,
                tier=ProviderTier.FREE,
                endpoint="http://localhost:8080",
                model="gpt-3.5-turbo",
                priority=4
            )
        ]
    
    async def initialize_providers(self):
        """Initialize all providers"""
        # Import provider implementations
        from ..Providers.ollama_provider import OllamaProvider
        from ..Providers.huggingface_provider import HuggingFaceProvider
        from ..Providers.groq_provider import GroqProvider
        from ..Providers.local_ai_provider import LocalAIProvider
        
        # Create provider instances
        for config in self.get_default_providers():
            try:
                if config.type == ProviderType.OLLAMA:
                    provider = OllamaProvider(config)
                elif config.type == ProviderType.HUGGINGFACE:
                    provider = HuggingFaceProvider(config)
                elif config.type == ProviderType.GROQ:
                    provider = GroqProvider(config)
                elif config.type == ProviderType.LOCAL_AI:
                    provider = LocalAIProvider(config)
                else:
                    continue
                
                self.register_provider(provider)
            except Exception as e:
                logger.warning(f"Failed to initialize provider {config.name}: {e}")
    
    def select_best_provider(self, request: LLMRequest) -> Optional[BaseLLMProvider]:
        """Select the best provider for a request"""
        available_providers = []
        
        for provider in self.providers.values():
            if not provider.config.enabled:
                continue
            if not provider.can_handle_request(request):
                continue
            
            # Calculate provider score
            score = self._calculate_provider_score(provider, request)
            available_providers.append((provider, score))
        
        if not available_providers:
            return None
        
        # Sort by score (higher is better)
        available_providers.sort(key=lambda x: x[1], reverse=True)
        return available_providers[0][0]
    
    def _calculate_provider_score(self, provider: BaseLLMProvider, request: LLMRequest) -> float:
        """Calculate provider score for selection"""
        score = 0.0
        
        # Priority score (higher priority = higher score)
        score += (10 - provider.config.priority) * 10
        
        # Tier preference (free > freemium > paid)
        tier_scores = {
            ProviderTier.FREE: 50,
            ProviderTier.FREEMIUM: 30,
            ProviderTier.PAID: 10,
            ProviderTier.ENTERPRISE: 5
        }
        score += tier_scores.get(provider.config.tier, 0)
        
        # Performance history
        if provider.config.name in self.performance_history:
            history = self.performance_history[provider.config.name]
            if history:
                avg_latency = sum(history[-10:]) / len(history[-10:])
                score += max(0, 10 - avg_latency)  # Lower latency = higher score
        
        # Error rate
        stats = self.usage_stats.get(provider.config.name, {})
        if stats.get("requests", 0) > 0:
            error_rate = stats.get("errors", 0) / stats["requests"]
            score += (1 - error_rate) * 20  # Lower error rate = higher score
        
        # Cost consideration
        estimated_cost = provider.estimate_cost(request)
        if estimated_cost == 0:
            score += 30  # Free is best
        else:
            score += max(0, 10 - estimated_cost * 1000)  # Lower cost = higher score
        
        return score
    
    async def generate(self, request: LLMRequest, max_retries: int = 3) -> LLMResponse:
        """Generate response with automatic provider selection and fallback"""
        last_error = None
        
        for attempt in range(max_retries):
            provider = self.select_best_provider(request)
            if not provider:
                raise Exception("No available providers for request")
            
            try:
                start_time = time.time()
                response = await provider.generate(request)
                latency = time.time() - start_time
                
                # Update statistics
                self._update_stats(provider.config.name, response, latency, success=True)
                
                return response
                
            except Exception as e:
                last_error = e
                latency = time.time() - start_time
                self._update_stats(provider.config.name, None, latency, success=False)
                
                logger.warning(f"Provider {provider.config.name} failed: {e}")
                
                # Temporarily disable failed provider
                provider.config.enabled = False
                
                # Re-enable after delay (exponential backoff)
                asyncio.create_task(self._re_enable_provider(provider, attempt + 1))
        
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate with provider selection"""
        provider = self.select_best_provider(request)
        if not provider:
            raise Exception("No available providers for streaming")
        
        if not provider.config.supports_streaming:
            # Fallback to regular generation
            response = await self.generate(request)
            yield response.content
            return
        
        try:
            start_time = time.time()
            async for chunk in provider.stream_generate(request):
                yield chunk
            
            latency = time.time() - start_time
            self._update_stats(provider.config.name, None, latency, success=True)
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            raise
    
    def _update_stats(self, provider_name: str, response: Optional[LLMResponse], 
                     latency: float, success: bool):
        """Update provider statistics"""
        stats = self.usage_stats[provider_name]
        stats["requests"] += 1
        
        if success and response:
            stats["total_tokens"] += response.tokens_used
            stats["total_cost"] += response.cost
        else:
            stats["errors"] += 1
        
        # Update performance history
        self.performance_history[provider_name].append(latency)
        # Keep only last 100 entries
        if len(self.performance_history[provider_name]) > 100:
            self.performance_history[provider_name] = self.performance_history[provider_name][-100:]
    
    async def _re_enable_provider(self, provider: BaseLLMProvider, attempt: int):
        """Re-enable provider after delay"""
        delay = min(300, 2 ** attempt)  # Exponential backoff, max 5 minutes
        await asyncio.sleep(delay)
        
        # Check if provider is available before re-enabling
        if await provider.is_available():
            provider.config.enabled = True
            logger.info(f"Re-enabled provider: {provider.config.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "providers": {
                name: {
                    "config": {
                        "type": config.type.value,
                        "tier": config.tier.value,
                        "enabled": config.enabled,
                        "priority": config.priority
                    },
                    "stats": self.usage_stats[name],
                    "avg_latency": sum(self.performance_history[name][-10:]) / len(self.performance_history[name][-10:]) if self.performance_history[name] else 0
                }
                for name, config in self.provider_configs.items()
            },
            "total_requests": sum(stats["requests"] for stats in self.usage_stats.values()),
            "total_cost": sum(stats["total_cost"] for stats in self.usage_stats.values()),
            "total_tokens": sum(stats["total_tokens"] for stats in self.usage_stats.values())
        }

# Global instance
llm_manager = LLMManager()

async def chat(message: str, **kwargs) -> str:
    """Simple chat interface for beginners"""
    request = LLMRequest(
        messages=[{"role": "user", "content": message}],
        **kwargs
    )
    response = await llm_manager.generate(request)
    return response.content

async def chat_stream(message: str, **kwargs) -> AsyncGenerator[str, None]:
    """Simple streaming chat interface"""
    request = LLMRequest(
        messages=[{"role": "user", "content": message}],
        stream=True,
        **kwargs
    )
    async for chunk in llm_manager.stream_generate(request):
        yield chunk

if __name__ == "__main__":
    # Example usage
    async def main():
        await llm_manager.initialize_providers()
        
        # Simple chat
        response = await chat("Hello, how are you?")
        print(f"AI: {response}")
        
        # Streaming chat
        print("AI (streaming): ", end="", flush=True)
        async for chunk in chat_stream("Tell me a short story"):
            print(chunk, end="", flush=True)
        print("\n")
        
        # Show stats
        stats = llm_manager.get_stats()
        print(f"Stats: {json.dumps(stats, indent=2)}")
    
    asyncio.run(main())