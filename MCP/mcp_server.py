#!/usr/bin/env python3
"""
OpenLLM Toolkit - MCP Server
Comprehensive Model Context Protocol server integrating all toolkit features
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP library not available. Install with: pip install mcp")
    sys.exit(1)

# Import our toolkit components
try:
    from ..Core.llm_manager import llm_manager, LLMRequest, chat, chat_stream
    from ..Tools.file_operations import file_ops, read_file, write_file, list_files
    from ..Tools.image_processor import image_processor, read_image, extract_text_from_image, describe_image
except ImportError:
    # Fallback for standalone execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from Core.llm_manager import llm_manager, LLMRequest, chat, chat_stream
    from Tools.file_operations import file_ops, read_file, write_file, list_files
    from Tools.image_processor import image_processor, read_image, extract_text_from_image, describe_image

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server("openllm-toolkit")

# Tool definitions
TOOLS = [
    # Chat and LLM tools
    {
        "name": "chat",
        "description": "Chat with AI using the best available LLM provider",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to send to the AI"
                },
                "temperature": {
                    "type": "number",
                    "description": "Response creativity (0.0-1.0)",
                    "default": 0.7
                },
                "max_tokens": {
                    "type": "integer", 
                    "description": "Maximum response length",
                    "default": 2000
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "chat_stream",
        "description": "Stream chat response from AI",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to send to the AI"
                },
                "temperature": {
                    "type": "number",
                    "description": "Response creativity (0.0-1.0)",
                    "default": 0.7
                }
            },
            "required": ["message"]
        }
    },
    
    # File operation tools
    {
        "name": "read_file",
        "description": "Read text content from a file safely",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read"
                },
                "encoding": {
                    "type": "string",
                    "description": "Text encoding (auto-detected if not specified)"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file safely",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string", 
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                },
                "encoding": {
                    "type": "string",
                    "description": "Text encoding (default: utf-8)",
                    "default": "utf-8"
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Create parent directories if needed",
                    "default": True
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "list_directory",
        "description": "List contents of a directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to the directory to list"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Include subdirectories recursively",
                    "default": False
                },
                "include_hidden": {
                    "type": "boolean", 
                    "description": "Include hidden files and directories",
                    "default": False
                }
            },
            "required": ["directory_path"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for files by name or content",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory to search in"
                },
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (filename or content)"
                },
                "content_search": {
                    "type": "boolean",
                    "description": "Search inside file contents",
                    "default": False
                }
            },
            "required": ["directory", "pattern"]
        }
    },
    {
        "name": "delete_file",
        "description": "Safely delete a file (moves to trash)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to delete"
                },
                "confirm": {
                    "type": "boolean",
                    "description": "Explicit confirmation required",
                    "default": False
                }
            },
            "required": ["file_path", "confirm"]
        }
    },
    
    # Image processing tools
    {
        "name": "analyze_image",
        "description": "Analyze an image and extract information",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "include_text": {
                    "type": "boolean",
                    "description": "Extract text from image using OCR",
                    "default": True
                },
                "include_colors": {
                    "type": "boolean",
                    "description": "Analyze image colors",
                    "default": True
                },
                "include_quality": {
                    "type": "boolean",
                    "description": "Assess image quality",
                    "default": True
                }
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "describe_image",
        "description": "Get AI description of an image using vision models",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "prompt": {
                    "type": "string",
                    "description": "Question or prompt about the image",
                    "default": "Describe this image in detail"
                }
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "extract_text_from_image",
        "description": "Extract text from an image using OCR",
        "inputSchema": {
            "type": "object", 
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                }
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "create_thumbnail",
        "description": "Create a thumbnail of an image",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the source image"
                },
                "output_path": {
                    "type": "string", 
                    "description": "Path for the thumbnail output"
                },
                "width": {
                    "type": "integer",
                    "description": "Thumbnail width in pixels",
                    "default": 256
                },
                "height": {
                    "type": "integer",
                    "description": "Thumbnail height in pixels", 
                    "default": 256
                }
            },
            "required": ["image_path", "output_path"]
        }
    },
    
    # System and utility tools
    {
        "name": "get_llm_stats",
        "description": "Get statistics about LLM provider usage",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_llm_providers",
        "description": "List available LLM providers and their status",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_capabilities",
        "description": "Get toolkit capabilities and available features",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "health_check",
        "description": "Check the health status of all toolkit components",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """Return list of available tools"""
    return [
        types.Tool(
            name=tool["name"],
            description=tool["description"],
            inputSchema=tool["inputSchema"]
        )
        for tool in TOOLS
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    try:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")
        
        # Chat and LLM tools
        if name == "chat":
            message = arguments["message"]
            temperature = arguments.get("temperature", 0.7)
            max_tokens = arguments.get("max_tokens", 2000)
            
            response = await chat(message, temperature=temperature, max_tokens=max_tokens)
            return [types.TextContent(type="text", text=response)]
        
        elif name == "chat_stream":
            message = arguments["message"]
            temperature = arguments.get("temperature", 0.7)
            
            response_chunks = []
            async for chunk in chat_stream(message, temperature=temperature):
                response_chunks.append(chunk)
            
            full_response = "".join(response_chunks)
            return [types.TextContent(type="text", text=full_response)]
        
        # File operation tools
        elif name == "read_file":
            file_path = arguments["file_path"]
            encoding = arguments.get("encoding")
            
            result = file_ops.read_file(file_path, encoding=encoding)
            if result.success:
                return [types.TextContent(
                    type="text", 
                    text=f"File read successfully:\n\n{result.data}"
                )]
            else:
                return [types.TextContent(type="text", text=f"Error: {result.message}")]
        
        elif name == "write_file":
            file_path = arguments["file_path"]
            content = arguments["content"]
            encoding = arguments.get("encoding", "utf-8")
            create_dirs = arguments.get("create_dirs", True)
            
            result = file_ops.write_file(file_path, content, encoding=encoding, create_dirs=create_dirs)
            return [types.TextContent(type="text", text=result.message)]
        
        elif name == "list_directory":
            directory_path = arguments["directory_path"]
            recursive = arguments.get("recursive", False)
            include_hidden = arguments.get("include_hidden", False)
            
            result = file_ops.list_directory(directory_path, recursive=recursive, include_hidden=include_hidden)
            if result.success:
                files_info = json.dumps(result.data, indent=2)
                return [types.TextContent(
                    type="text",
                    text=f"Directory listing for {directory_path}:\n\n{files_info}"
                )]
            else:
                return [types.TextContent(type="text", text=f"Error: {result.message}")]
        
        elif name == "search_files":
            directory = arguments["directory"]
            pattern = arguments["pattern"]
            content_search = arguments.get("content_search", False)
            
            result = file_ops.search_files(directory, pattern, content_search=content_search)
            if result.success:
                search_results = json.dumps(result.data, indent=2)
                return [types.TextContent(
                    type="text",
                    text=f"Search results for '{pattern}' in {directory}:\n\n{search_results}"
                )]
            else:
                return [types.TextContent(type="text", text=f"Error: {result.message}")]
        
        elif name == "delete_file":
            file_path = arguments["file_path"]
            confirm = arguments.get("confirm", False)
            
            result = file_ops.delete_file(file_path, confirm=confirm)
            return [types.TextContent(type="text", text=result.message)]
        
        # Image processing tools
        elif name == "analyze_image":
            image_path = arguments["image_path"]
            include_text = arguments.get("include_text", True)
            include_colors = arguments.get("include_colors", True)
            include_quality = arguments.get("include_quality", True)
            
            from ..Tools.image_processor import AnalysisType
            analysis_types = [AnalysisType.BASIC_INFO]
            
            if include_text:
                analysis_types.append(AnalysisType.TEXT_EXTRACTION)
            if include_colors:
                analysis_types.append(AnalysisType.COLOR_ANALYSIS)
            if include_quality:
                analysis_types.append(AnalysisType.QUALITY_ASSESSMENT)
            
            result = image_processor.comprehensive_analysis(image_path, analysis_types)
            
            if result.success:
                # Convert result to serializable format
                result_dict = {
                    "success": result.success,
                    "message": result.message,
                    "image_info": asdict(result.image_info) if result.image_info else None,
                    "text_extraction": asdict(result.text_extraction) if result.text_extraction else None,
                    "color_analysis": asdict(result.color_analysis) if result.color_analysis else None,
                    "quality_score": result.quality_score,
                    "metadata": result.metadata
                }
                
                analysis_json = json.dumps(result_dict, indent=2, default=str)
                return [types.TextContent(
                    type="text",
                    text=f"Image analysis for {image_path}:\n\n{analysis_json}"
                )]
            else:
                return [types.TextContent(type="text", text=f"Error: {result.message}")]
        
        elif name == "describe_image":
            image_path = arguments["image_path"]
            prompt = arguments.get("prompt", "Describe this image in detail")
            
            description = await describe_image(image_path, prompt)
            return [types.TextContent(
                type="text",
                text=f"Image description:\n\n{description}"
            )]
        
        elif name == "extract_text_from_image":
            image_path = arguments["image_path"]
            
            try:
                text = extract_text_from_image(image_path)
                return [types.TextContent(
                    type="text",
                    text=f"Extracted text from {image_path}:\n\n{text}"
                )]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error extracting text: {str(e)}")]
        
        elif name == "create_thumbnail":
            image_path = arguments["image_path"]
            output_path = arguments["output_path"]
            width = arguments.get("width", 256)
            height = arguments.get("height", 256)
            
            success = image_processor.create_thumbnail(image_path, output_path, (width, height))
            if success:
                return [types.TextContent(
                    type="text",
                    text=f"Thumbnail created successfully: {output_path}"
                )]
            else:
                return [types.TextContent(type="text", text="Failed to create thumbnail")]
        
        # System and utility tools
        elif name == "get_llm_stats":
            stats = llm_manager.get_stats()
            stats_json = json.dumps(stats, indent=2)
            return [types.TextContent(
                type="text",
                text=f"LLM Usage Statistics:\n\n{stats_json}"
            )]
        
        elif name == "list_llm_providers":
            providers_info = {}
            for name, provider in llm_manager.providers.items():
                providers_info[name] = {
                    "type": provider.config.type.value,
                    "tier": provider.config.tier.value,
                    "enabled": provider.config.enabled,
                    "priority": provider.config.priority,
                    "endpoint": provider.config.endpoint,
                    "supports_streaming": provider.config.supports_streaming,
                    "supports_vision": provider.config.supports_vision,
                    "supports_functions": provider.config.supports_functions
                }
            
            providers_json = json.dumps(providers_info, indent=2)
            return [types.TextContent(
                type="text",
                text=f"Available LLM Providers:\n\n{providers_json}"
            )]
        
        elif name == "get_capabilities":
            capabilities = {
                "llm_management": {
                    "providers_available": len(llm_manager.providers),
                    "supports_streaming": True,
                    "supports_vision": True,
                    "supports_functions": True
                },
                "file_operations": {
                    "read_files": True,
                    "write_files": True,
                    "list_directories": True,
                    "search_files": True,
                    "safe_deletion": True
                },
                "image_processing": image_processor.capabilities,
                "mcp_server": {
                    "tools_available": len(TOOLS),
                    "version": "1.0.0"
                }
            }
            
            capabilities_json = json.dumps(capabilities, indent=2)
            return [types.TextContent(
                type="text",
                text=f"OpenLLM Toolkit Capabilities:\n\n{capabilities_json}"
            )]
        
        elif name == "health_check":
            health_status = {
                "llm_manager": {
                    "status": "healthy" if llm_manager.providers else "no_providers",
                    "providers_count": len(llm_manager.providers),
                    "enabled_providers": sum(1 for p in llm_manager.providers.values() if p.config.enabled)
                },
                "file_operations": {
                    "status": "healthy",
                    "max_file_size_mb": file_ops.max_file_size // (1024 * 1024),
                    "safe_directories_count": len(file_ops.security.safe_directories)
                },
                "image_processing": {
                    "status": "healthy" if image_processor.capabilities["basic_processing"] else "limited",
                    "capabilities": image_processor.capabilities
                },
                "mcp_server": {
                    "status": "healthy",
                    "tools_count": len(TOOLS)
                }
            }
            
            overall_status = "healthy"
            if health_status["llm_manager"]["status"] == "no_providers":
                overall_status = "degraded"
            if not health_status["image_processing"]["capabilities"]["basic_processing"]:
                overall_status = "limited"
            
            health_status["overall"] = overall_status
            
            health_json = json.dumps(health_status, indent=2)
            return [types.TextContent(
                type="text",
                text=f"Health Check Results:\n\n{health_json}"
            )]
        
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

async def main():
    """Main MCP server entry point"""
    logger.info("Starting OpenLLM Toolkit MCP Server...")
    
    # Initialize LLM providers
    try:
        await llm_manager.initialize_providers()
        logger.info(f"Initialized {len(llm_manager.providers)} LLM providers")
    except Exception as e:
        logger.warning(f"Failed to initialize some LLM providers: {e}")
    
    # Check capabilities
    logger.info(f"Image processing capabilities: {image_processor.capabilities}")
    logger.info(f"File operations ready with {len(file_ops.security.safe_directories)} safe directories")
    
    # Start MCP server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("OpenLLM Toolkit MCP Server is ready!")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())