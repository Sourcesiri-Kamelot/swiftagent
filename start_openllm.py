#!/usr/bin/env python3
"""
OpenLLM Toolkit - Main Startup Script
Comprehensive startup script that initializes all components and provides multiple interfaces
"""

import asyncio
import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup the environment and check dependencies"""
    logger.info("Setting up OpenLLM Toolkit environment...")
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Check for required directories
    config_dir = Path.home() / ".config" / "openllm-toolkit"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ is required")
        sys.exit(1)
    
    logger.info("Environment setup complete")

def check_dependencies():
    """Check if all required dependencies are available"""
    logger.info("Checking dependencies...")
    
    missing_deps = []
    
    # Core dependencies
    try:
        import aiohttp
    except ImportError:
        missing_deps.append("aiohttp")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    # Optional dependencies
    optional_deps = {
        "fastapi": "Web backend",
        "uvicorn": "Web server",
        "PIL": "Image processing",
        "cv2": "Advanced image processing",
        "pytesseract": "OCR text extraction",
        "mcp": "MCP server"
    }
    
    missing_optional = []
    for dep, description in optional_deps.items():
        try:
            if dep == "PIL":
                import PIL
            elif dep == "cv2":
                import cv2
            elif dep == "pytesseract":
                import pytesseract
            elif dep == "mcp":
                import mcp
            else:
                __import__(dep)
        except ImportError:
            missing_optional.append(f"{dep} ({description})")
    
    if missing_deps:
        logger.error(f"Missing required dependencies: {', '.join(missing_deps)}")
        logger.error("Install with: pip install -r requirements.txt")
        sys.exit(1)
    
    if missing_optional:
        logger.warning(f"Missing optional dependencies: {', '.join(missing_optional)}")
        logger.info("Some features may not be available")
    
    logger.info("Dependency check complete")

async def initialize_components():
    """Initialize all toolkit components"""
    logger.info("Initializing OpenLLM Toolkit components...")
    
    try:
        # Import components
        from Core.llm_manager import llm_manager
        from Core.memory_system import memory_system
        from Core.self_healing import self_healing
        from Core.load_balancer import load_balancer
        from Tools.file_operations import file_ops
        from Tools.image_processor import image_processor
        
        # Initialize LLM providers
        await llm_manager.initialize_providers()
        logger.info(f"Initialized {len(llm_manager.providers)} LLM providers")
        
        # Add providers to load balancer
        for name, provider in llm_manager.providers.items():
            load_balancer.add_provider(name, provider)
        logger.info(f"Added {len(load_balancer.providers)} providers to load balancer")
        
        # Check memory system
        logger.info(f"Memory system: {len(memory_system.memories)} memories loaded")
        
        # Check file operations
        logger.info(f"File operations: {len(file_ops.security.safe_directories)} safe directories")
        
        # Check image processing
        capabilities = image_processor.capabilities
        logger.info(f"Image processing capabilities: {capabilities}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return False

def start_cli():
    """Start the command-line interface"""
    logger.info("Starting CLI interface...")
    
    try:
        from Interface.cli import main as cli_main
        cli_main()
    except Exception as e:
        logger.error(f"Failed to start CLI: {e}")

def start_mcp_server():
    """Start the MCP server"""
    logger.info("Starting MCP server...")
    
    try:
        from MCP.mcp_server import main as mcp_main
        asyncio.run(mcp_main())
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")

def start_web_backend():
    """Start the web backend server"""
    logger.info("Starting web backend...")
    
    try:
        from Interface.web_backend import main as web_main
        web_main()
    except Exception as e:
        logger.error(f"Failed to start web backend: {e}")

def show_status():
    """Show system status"""
    logger.info("Checking system status...")
    
    try:
        from Core.llm_manager import llm_manager
        from Core.memory_system import memory_system
        from Core.self_healing import self_healing
        from Core.load_balancer import load_balancer
        
        print("\n" + "="*50)
        print("OpenLLM Toolkit Status")
        print("="*50)
        
        # LLM Providers
        print(f"\n🤖 LLM Providers: {len(llm_manager.providers)}")
        for name, provider in llm_manager.providers.items():
            status = "✅" if provider.config.enabled else "❌"
            print(f"  {status} {name} ({provider.config.type.value})")
        
        # Memory System
        print(f"\n🧠 Memory System: {len(memory_system.memories)} memories")
        print(f"  Conversations: {len(memory_system.conversations)}")
        print(f"  Preferences: {len(memory_system.preferences)}")
        
        # Self Healing
        error_summary = self_healing.get_error_summary()
        perf_summary = self_healing.get_performance_summary()
        print(f"\n🔧 Self Healing:")
        print(f"  Recent errors: {error_summary['total_errors']}")
        print(f"  Resolution rate: {error_summary['resolution_rate']:.1%}")
        print(f"  Performance metrics: {perf_summary['total_operations']}")
        
        # Load Balancer
        lb_stats = load_balancer.get_stats()
        print(f"\n⚖️ Load Balancer:")
        print(f"  Strategy: {lb_stats['strategy']}")
        print(f"  Available providers: {lb_stats['available_providers']}/{lb_stats['total_providers']}")
        
        print("\n" + "="*50)
        
    except Exception as e:
        logger.error(f"Failed to show status: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="OpenLLM Toolkit - Universal AI Assistant")
    parser.add_argument("--mode", choices=["cli", "mcp", "web", "status"], 
                       default="cli", help="Mode to run in")
    parser.add_argument("--port", type=int, default=8000, help="Web server port")
    parser.add_argument("--host", default="0.0.0.0", help="Web server host")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Setup environment
    setup_environment()
    check_dependencies()
    
    # Initialize components
    if not asyncio.run(initialize_components()):
        logger.error("Failed to initialize components. Exiting.")
        sys.exit(1)
    
    # Start requested mode
    if args.mode == "cli":
        start_cli()
    elif args.mode == "mcp":
        start_mcp_server()
    elif args.mode == "web":
        # Set environment variables for web server
        os.environ["HOST"] = args.host
        os.environ["PORT"] = str(args.port)
        start_web_backend()
    elif args.mode == "status":
        show_status()
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == "__main__":
    main() 