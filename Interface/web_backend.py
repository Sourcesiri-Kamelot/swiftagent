#!/usr/bin/env python3
"""
SwiftAgent Toolkit - Web Backend API
FastAPI-based web backend with load balancing and all toolkit features
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not available. Install with: pip install fastapi uvicorn")

# Import our toolkit components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from Core.llm_manager import llm_manager, LLMRequest, chat, chat_stream
from Core.memory_system import memory_system
from Core.self_healing import self_healing
from Core.load_balancer import load_balancer
from Tools.file_operations import file_ops
from Tools.image_processor import image_processor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str = Field(..., description="Message to send to AI")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Response creativity")
    max_tokens: int = Field(2000, ge=1, le=10000, description="Maximum response length")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")

class FileReadRequest(BaseModel):
    file_path: str = Field(..., description="Path to file to read")
    encoding: Optional[str] = Field(None, description="Text encoding")

class FileWriteRequest(BaseModel):
    file_path: str = Field(..., description="Path to file to write")
    content: str = Field(..., description="Content to write")
    encoding: str = Field("utf-8", description="Text encoding")

class ImageAnalysisRequest(BaseModel):
    image_path: str = Field(..., description="Path to image file")
    include_text: bool = Field(True, description="Extract text from image")
    include_colors: bool = Field(True, description="Analyze image colors")
    include_quality: bool = Field(True, description="Assess image quality")

class MemoryRequest(BaseModel):
    content: Dict[str, Any] = Field(..., description="Memory content")
    memory_type: str = Field("conversation", description="Type of memory")
    tags: List[str] = Field([], description="Memory tags")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="Memory importance")

# Create FastAPI app
app = FastAPI(
    title="SwiftAgent Toolkit API",
    description="Universal AI toolkit with file operations, image processing, and memory",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
@app.on_event("startup")
async def startup_event():
    """Initialize toolkit components on startup"""
    try:
        # Initialize LLM providers
        await llm_manager.initialize_providers()
        
        # Add providers to load balancer
        for name, provider in llm_manager.providers.items():
            cost_per_token = 0.0  # Free providers
            if "openai" in name.lower():
                cost_per_token = 0.002  # Approximate OpenAI cost
            elif "anthropic" in name.lower():
                cost_per_token = 0.0015  # Approximate Anthropic cost
            
            load_balancer.add_provider(name, provider, cost_per_token)
        
        logger.info(f"Initialized {len(llm_manager.providers)} LLM providers")
        logger.info(f"Memory system: {len(memory_system.memories)} memories")
        logger.info("Web backend ready!")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "llm_providers": len(llm_manager.providers),
            "memory_system": len(memory_system.memories),
            "load_balancer": load_balancer.get_stats()
        }
    }

# Chat endpoints
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with AI using load balancing"""
    try:
        start_time = time.time()
        
        # Create LLM request
        llm_request = LLMRequest(
            messages=[{"role": "user", "content": request.message}],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Execute with load balancing
        response = await load_balancer.execute_request(llm_request)
        
        if not response:
            raise HTTPException(status_code=503, detail="No available AI providers")
        
        # Record performance
        duration = time.time() - start_time
        self_healing.record_performance("chat", duration, True, {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "provider": response.provider
        })
        
        # Add to memory if user_id provided
        if request.user_id:
            memory_system.add_memory({
                "message": request.message,
                "response": response.content,
                "user_id": request.user_id,
                "session_id": request.session_id
            }, memory_type="conversation", importance=0.7)
        
        return {
            "response": response.content,
            "provider": response.provider,
            "model": response.model,
            "tokens_used": response.tokens_used,
            "cost": response.cost,
            "duration": duration
        }
        
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "chat", "request": request.dict()})
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/chat/stream")
async def chat_stream_endpoint(websocket: WebSocket):
    """Streaming chat endpoint"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Create LLM request
            llm_request = LLMRequest(
                messages=[{"role": "user", "content": request_data["message"]}],
                temperature=request_data.get("temperature", 0.7),
                max_tokens=request_data.get("max_tokens", 2000)
            )
            
            # Stream response
            async for chunk in chat_stream(request_data["message"], temperature=request_data.get("temperature", 0.7)):
                await websocket.send_text(json.dumps({
                    "chunk": chunk,
                    "type": "content"
                }))
            
            await websocket.send_text(json.dumps({
                "type": "complete"
            }))
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "error": str(e),
            "type": "error"
        }))

# File operation endpoints
@app.post("/files/read")
async def read_file_endpoint(request: FileReadRequest):
    """Read file content"""
    try:
        result = file_ops.read_file(request.file_path, encoding=request.encoding)
        
        if result.success:
            return {
                "success": True,
                "content": result.data,
                "file_info": result.metadata
            }
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "read_file", "request": request.dict()})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/write")
async def write_file_endpoint(request: FileWriteRequest):
    """Write content to file"""
    try:
        result = file_ops.write_file(
            request.file_path, 
            request.content, 
            encoding=request.encoding
        )
        
        return {
            "success": True,
            "message": result.message
        }
        
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "write_file", "request": request.dict()})
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/list/{directory:path}")
async def list_directory_endpoint(directory: str, recursive: bool = False):
    """List directory contents"""
    try:
        result = file_ops.list_directory(directory, recursive=recursive)
        
        if result.success:
            return {
                "success": True,
                "files": result.data
            }
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "list_directory", "directory": directory})
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/search")
async def search_files_endpoint(directory: str, pattern: str, content_search: bool = False):
    """Search for files"""
    try:
        result = file_ops.search_files(directory, pattern, content_search=content_search)
        
        if result.success:
            return {
                "success": True,
                "results": result.data
            }
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "search_files", "directory": directory, "pattern": pattern})
        raise HTTPException(status_code=500, detail=str(e))

# Image processing endpoints
@app.post("/images/analyze")
async def analyze_image_endpoint(request: ImageAnalysisRequest):
    """Analyze image"""
    try:
        from Tools.image_processor import AnalysisType
        
        analysis_types = [AnalysisType.BASIC_INFO]
        if request.include_text:
            analysis_types.append(AnalysisType.TEXT_EXTRACTION)
        if request.include_colors:
            analysis_types.append(AnalysisType.COLOR_ANALYSIS)
        if request.include_quality:
            analysis_types.append(AnalysisType.QUALITY_ASSESSMENT)
        
        result = image_processor.comprehensive_analysis(request.image_path, analysis_types)
        
        if result.success:
            return {
                "success": True,
                "analysis": {
                    "image_info": result.image_info.__dict__ if result.image_info else None,
                    "text_extraction": result.text_extraction.__dict__ if result.text_extraction else None,
                    "color_analysis": result.color_analysis.__dict__ if result.color_analysis else None,
                    "quality_score": result.quality_score
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "analyze_image", "request": request.dict()})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/images/extract-text")
async def extract_text_endpoint(image_path: str):
    """Extract text from image"""
    try:
        text = image_processor.extract_text_tesseract(image_path)
        return {
            "success": True,
            "text": text
        }
        
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "extract_text", "image_path": image_path})
        raise HTTPException(status_code=500, detail=str(e))

# Memory endpoints
@app.post("/memory/add")
async def add_memory_endpoint(request: MemoryRequest):
    """Add memory entry"""
    try:
        memory_id = memory_system.add_memory(
            request.content,
            request.memory_type,
            request.tags,
            request.importance
        )
        
        return {
            "success": True,
            "memory_id": memory_id
        }
        
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "add_memory", "request": request.dict()})
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/search")
async def search_memories_endpoint(query: str, memory_type: Optional[str] = None, limit: int = 10):
    """Search memories"""
    try:
        memories = memory_system.search_memories(query, memory_type, limit)
        
        return {
            "success": True,
            "memories": [memory.__dict__ for memory in memories]
        }
        
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "search_memories", "query": query})
        raise HTTPException(status_code=500, detail=str(e))

# System endpoints
@app.get("/system/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        return {
            "llm_manager": llm_manager.get_stats(),
            "load_balancer": load_balancer.get_stats(),
            "memory_system": {
                "memories_count": len(memory_system.memories),
                "conversations_count": len(memory_system.conversations)
            },
            "self_healing": {
                "error_summary": self_healing.get_error_summary(),
                "performance_summary": self_healing.get_performance_summary()
            }
        }
        
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "system_stats"})
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/providers")
async def get_providers():
    """Get available LLM providers"""
    try:
        providers = {}
        for name, provider in llm_manager.providers.items():
            providers[name] = {
                "type": provider.config.type.value,
                "tier": provider.config.tier.value,
                "enabled": provider.config.enabled,
                "endpoint": provider.config.endpoint,
                "model": provider.config.model
            }
        
        return {
            "success": True,
            "providers": providers
        }
        
    except Exception as e:
        self_healing.record_error(e, {"endpoint": "get_providers"})
        raise HTTPException(status_code=500, detail=str(e))

# Main function
def main():
    """Run the web backend server"""
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available. Install with: pip install fastapi uvicorn")
        return
    
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main() 