#!/usr/bin/env python3
"""
SwiftAgent Toolkit - Ollama Provider
Local LLM hosting provider implementation
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator, Any
import aiohttp

from ..Core.llm_manager import BaseLLMProvider, LLMRequest, LLMResponse, LLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, config: LLMProvider):
        super().__init__(config)
        self.session = None
        self.base_url = config.endpoint.rstrip('/')
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return self.session
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Ollama API"""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from Ollama"""
        try:
            # Prepare messages for Ollama
            messages = []
            for msg in request.messages:
                if msg["role"] == "system":
                    # Ollama doesn't support system messages directly
                    # We'll prepend to the first user message
                    continue
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add system prompt to first user message if present
            if request.system_prompt and messages:
                if messages[0]["role"] == "user":
                    messages[0]["content"] = f"{request.system_prompt}\n\n{messages[0]['content']}"
            
            # Prepare request data
            data = {
                "model": request.model or self.config.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens or self.config.max_tokens
                }
            }
            
            # Make request
            response_data = await self._make_request("/api/chat", data)
            
            # Parse response
            content = response_data.get("message", {}).get("content", "")
            usage = response_data.get("usage", {})
            
            return LLMResponse(
                content=content,
                provider=self.config.name,
                model=data["model"],
                tokens_used=usage.get("total_tokens", 0),
                cost=0.0,  # Ollama is free
                latency=0.0,  # Will be calculated by manager
                metadata={
                    "ollama_response": response_data,
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate from Ollama"""
        try:
            # Prepare messages (same as generate)
            messages = []
            for msg in request.messages:
                if msg["role"] == "system":
                    continue
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            if request.system_prompt and messages:
                if messages[0]["role"] == "user":
                    messages[0]["content"] = f"{request.system_prompt}\n\n{messages[0]['content']}"
            
            # Prepare request data
            data = {
                "model": request.model or self.config.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens or self.config.max_tokens
                }
            }
            
            # Make streaming request
            session = await self._get_session()
            url = f"{self.base_url}/api/chat"
            
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama streaming error {response.status}: {error_text}")
                
                async for line in response.content:
                    if line:
                        try:
                            chunk_data = json.loads(line.decode('utf-8'))
                            if "message" in chunk_data:
                                content = chunk_data["message"].get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.warning(f"Error parsing Ollama stream chunk: {e}")
                            continue
            
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/tags"
            
            async with session.get(url) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            response_data = await self._make_request("/api/tags", {})
            models = response_data.get("models", [])
            return [model["name"] for model in models]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model to Ollama"""
        try:
            data = {"name": model_name}
            await self._make_request("/api/pull", data)
            return True
        except Exception as e:
            logger.error(f"Failed to pull Ollama model {model_name}: {e}")
            return False
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close() 