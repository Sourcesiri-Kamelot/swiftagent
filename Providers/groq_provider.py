#!/usr/bin/env python3
"""
OpenLLM Toolkit - Groq Provider
Fast inference with free tier
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator, Any
import aiohttp
import os

from ..Core.llm_manager import BaseLLMProvider, LLMRequest, LLMResponse, LLMProvider

logger = logging.getLogger(__name__)

class GroqProvider(BaseLLMProvider):
    """Groq fast inference provider"""
    
    def __init__(self, config: LLMProvider):
        super().__init__(config)
        self.session = None
        self.api_key = config.api_key or os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1"
        
        # Free models available on Groq
        self.free_models = {
            "llama3-8b-8192": "llama3-8b-8192",
            "llama3-70b-8192": "llama3-70b-8192", 
            "mixtral-8x7b-32768": "mixtral-8x7b-32768",
            "gemma2-9b-it": "gemma2-9b-it"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {
                "Content-Type": "application/json"
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return self.session
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Groq API"""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Groq API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Groq request failed: {e}")
            raise
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from Groq"""
        try:
            # Use default model if none specified
            model = request.model or self.config.model or "llama3-8b-8192"
            
            # Prepare messages in OpenAI format
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            # Add user messages
            for msg in request.messages:
                if msg["role"] in ["user", "assistant", "system"]:
                    messages.append(msg)
            
            # Prepare request data
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": request.max_tokens or 1000,
                "temperature": request.temperature,
                "stream": False
            }
            
            # Make request
            response_data = await self._make_request("/chat/completions", data)
            
            # Parse response
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = response_data.get("usage", {})
            
            return LLMResponse(
                content=content,
                provider=self.config.name,
                model=model,
                tokens_used=usage.get("total_tokens", 0),
                cost=0.0,  # Groq free tier
                latency=0.0,  # Will be calculated by manager
                metadata={
                    "groq_response": response_data,
                    "model": model,
                    "usage": usage
                }
            )
            
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate from Groq"""
        try:
            # Use default model if none specified
            model = request.model or self.config.model or "llama3-8b-8192"
            
            # Prepare messages in OpenAI format
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            # Add user messages
            for msg in request.messages:
                if msg["role"] in ["user", "assistant", "system"]:
                    messages.append(msg)
            
            # Prepare request data
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": request.max_tokens or 1000,
                "temperature": request.temperature,
                "stream": True
            }
            
            # Make streaming request
            session = await self._get_session()
            url = f"{self.base_url}/chat/completions"
            
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Groq streaming error {response.status}: {error_text}")
                
                async for line in response.content:
                    if line:
                        try:
                            line_text = line.decode('utf-8').strip()
                            if line_text.startswith('data: '):
                                json_str = line_text[6:]  # Remove 'data: ' prefix
                                if json_str == '[DONE]':
                                    break
                                
                                chunk_data = json.loads(json_str)
                                if 'choices' in chunk_data and chunk_data['choices']:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        yield content
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.warning(f"Error parsing Groq stream chunk: {e}")
                            continue
            
        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if Groq is available"""
        try:
            if not self.api_key:
                return False
                
            session = await self._get_session()
            # Test with a simple request
            test_data = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 1
            }
            url = f"{self.base_url}/chat/completions"
            
            async with session.post(url, json=test_data) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models"""
        return list(self.free_models.keys())
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close() 