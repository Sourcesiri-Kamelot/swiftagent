#!/usr/bin/env python3
"""
OpenLLM Toolkit - HuggingFace Provider
Free AI models from HuggingFace
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator, Any
import aiohttp
import os

from ..Core.llm_manager import BaseLLMProvider, LLMRequest, LLMResponse, LLMProvider

logger = logging.getLogger(__name__)

class HuggingFaceProvider(BaseLLMProvider):
    """HuggingFace free AI provider"""
    
    def __init__(self, config: LLMProvider):
        super().__init__(config)
        self.session = None
        self.api_key = config.api_key or os.getenv('HUGGINGFACE_API_KEY')
        self.base_url = "https://api-inference.huggingface.co"
        
        # Free models that work well
        self.free_models = {
            "microsoft/DialoGPT-large": "text-generation",
            "gpt2": "text-generation", 
            "distilgpt2": "text-generation",
            "microsoft/DialoGPT-medium": "text-generation",
            "EleutherAI/gpt-neo-125M": "text-generation"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return self.session
    
    async def _make_request(self, model: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to HuggingFace API"""
        session = await self._get_session()
        url = f"{self.base_url}/models/{model}"
        
        try:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HuggingFace API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"HuggingFace request failed: {e}")
            raise
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from HuggingFace"""
        try:
            # Use default model if none specified
            model = request.model or self.config.model or "microsoft/DialoGPT-large"
            
            # Prepare input text
            messages = request.messages
            if request.system_prompt:
                input_text = f"{request.system_prompt}\n\n"
            else:
                input_text = ""
            
            # Combine messages
            for msg in messages:
                if msg["role"] == "user":
                    input_text += f"User: {msg['content']}\n"
                elif msg["role"] == "assistant":
                    input_text += f"Assistant: {msg['content']}\n"
            
            # Add assistant prefix for generation
            input_text += "Assistant: "
            
            # Prepare request data
            data = {
                "inputs": input_text,
                "parameters": {
                    "max_new_tokens": request.max_tokens or 100,
                    "temperature": request.temperature,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            # Make request
            response_data = await self._make_request(model, data)
            
            # Parse response
            if isinstance(response_data, list) and len(response_data) > 0:
                content = response_data[0].get("generated_text", "")
                # Extract only the new generated part
                if "Assistant: " in content:
                    content = content.split("Assistant: ")[-1]
            else:
                content = str(response_data)
            
            return LLMResponse(
                content=content,
                provider=self.config.name,
                model=model,
                tokens_used=len(content.split()),  # Rough estimate
                cost=0.0,  # HuggingFace free tier
                latency=0.0,  # Will be calculated by manager
                metadata={
                    "huggingface_response": response_data,
                    "model": model
                }
            )
            
        except Exception as e:
            logger.error(f"HuggingFace generation failed: {e}")
            raise
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate from HuggingFace (not supported in free tier)"""
        # HuggingFace free tier doesn't support streaming
        # Fallback to regular generation
        response = await self.generate(request)
        yield response.content
    
    async def is_available(self) -> bool:
        """Check if HuggingFace is available"""
        try:
            session = await self._get_session()
            # Test with a simple model
            test_data = {"inputs": "Hello"}
            url = f"{self.base_url}/models/gpt2"
            
            async with session.post(url, json=test_data) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List available free models"""
        return list(self.free_models.keys())
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close() 