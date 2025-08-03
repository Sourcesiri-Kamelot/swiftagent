#!/usr/bin/env python3
"""
OpenLLM Toolkit - Beginner-Friendly CLI
Simple command-line interface for easy AI interaction
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Color support for terminal output
try:
    from colorama import init as colorama_init, Fore, Back, Style
    colorama_init()
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback without colors
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = DummyColor()
    COLORS_AVAILABLE = False

# Import our toolkit components
try:
    from ..Core.llm_manager import llm_manager, chat, chat_stream
    from ..Tools.file_operations import file_ops
    from ..Tools.image_processor import image_processor, describe_image, extract_text_from_image
except ImportError:
    # Fallback for standalone execution
    sys.path.append(str(Path(__file__).parent.parent))
    from Core.llm_manager import llm_manager, chat, chat_stream
    from Tools.file_operations import file_ops
    from Tools.image_processor import image_processor, describe_image, extract_text_from_image

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise for beginners

class BeginnerCLI:
    """Beginner-friendly command-line interface"""
    
    def __init__(self):
        self.initialized = False
        self.conversation_history = []
    
    def print_colored(self, text: str, color: str = "", style: str = ""):
        """Print colored text if colors are available"""
        if COLORS_AVAILABLE:
            color_code = getattr(Fore, color.upper(), "")
            style_code = getattr(Style, style.upper(), "")
            print(f"{color_code}{style_code}{text}{Style.RESET_ALL}")
        else:
            print(text)
    
    def print_banner(self):
        """Print welcome banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                    🚀 OpenLLM Toolkit                        ║
║              Your Free AI Assistant is Ready!                ║
║                                                               ║
║  💡 Type your questions in plain English                     ║
║  📁 Ask me to read or write files                            ║
║  🖼️  Show me images to analyze                               ║
║  🔧 Get help with any task                                   ║
║                                                               ║
║  Type 'help' for commands or 'quit' to exit                 ║
╚═══════════════════════════════════════════════════════════════╝
        """
        self.print_colored(banner, "cyan", "bright")
    
    def print_help(self):
        """Print help information"""
        help_text = """
🎯 QUICK START GUIDE:

💬 CHAT WITH AI:
   Just type your question: "What is the weather like?"
   Ask for help: "How do I bake a cake?"
   Get explanations: "Explain quantum physics simply"

📁 FILE OPERATIONS:
   read <file>        - Read a file: "read my_document.txt"
   write <file>       - Write to file: "write letter.txt"
   list <folder>      - List files: "list Documents"
   search <term>      - Find files: "search vacation photos"

🖼️  IMAGE ANALYSIS:
   photo <image>      - Analyze image: "photo vacation.jpg"
   text <image>       - Extract text: "text receipt.png" 
   describe <image>   - AI description: "describe artwork.jpg"

🔧 SYSTEM:
   status            - Check system health
   providers         - List AI providers
   clear             - Clear conversation
   help              - Show this help
   quit              - Exit program

💡 EXAMPLES:
   "Write a poem about cats"
   "read config.txt and explain it"
   "photo family.jpg what do you see?"
   "help me organize my files"

Just type naturally - the AI understands context! 🎉
        """
        self.print_colored(help_text, "green")
    
    async def initialize(self):
        """Initialize the toolkit"""
        if self.initialized:
            return
        
        self.print_colored("🔧 Initializing AI providers...", "yellow")
        
        try:
            await llm_manager.initialize_providers()
            if len(llm_manager.providers) == 0:
                self.print_colored("⚠️  Warning: No AI providers available. Some features may be limited.", "red")
            else:
                self.print_colored(f"✅ Initialized {len(llm_manager.providers)} AI providers", "green")
            
            # Check capabilities
            capabilities = image_processor.capabilities
            if not capabilities['basic_processing']:
                self.print_colored("ℹ️  Install Pillow for image processing: pip install Pillow", "blue")
            
            self.initialized = True
            
        except Exception as e:
            self.print_colored(f"❌ Initialization error: {e}", "red")
            self.print_colored("📝 Some features may not work. Continue anyway? (y/n): ", "yellow", end="")
            
            response = input().strip().lower()
            if response in ['y', 'yes']:
                self.initialized = True
            else:
                sys.exit(1)
    
    def parse_command(self, user_input: str) -> tuple[str, List[str]]:
        """Parse user input into command and arguments"""
        parts = user_input.strip().split()
        if not parts:
            return "", []
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Handle special cases
        if command in ['quit', 'exit', 'bye']:
            return "quit", []
        elif command in ['help', '?', 'h']:
            return "help", []
        elif command in ['clear', 'cls']:
            return "clear", []
        elif command in ['status', 'health']:
            return "status", []
        elif command in ['providers', 'models']:
            return "providers", []
        elif command in ['read', 'open', 'cat']:
            return "read", args
        elif command in ['write', 'save', 'create']:
            return "write", args
        elif command in ['list', 'ls', 'dir']:
            return "list", args
        elif command in ['search', 'find']:
            return "search", args
        elif command in ['photo', 'image', 'img']:
            return "photo", args
        elif command in ['text', 'ocr']:
            return "text", args
        elif command in ['describe']:
            return "describe", args
        else:
            # Default to chat
            return "chat", [user_input]
    
    async def handle_chat(self, message: str):
        """Handle chat with AI"""
        try:
            self.print_colored("🤖 AI:", "blue", "bright")
            
            # Stream the response for better UX
            response_chunks = []
            async for chunk in chat_stream(message):
                print(chunk, end="", flush=True)
                response_chunks.append(chunk)
            
            print()  # New line after response
            
            # Save to conversation history
            full_response = "".join(response_chunks)
            self.conversation_history.append({
                "user": message,
                "ai": full_response
            })
            
        except Exception as e:
            self.print_colored(f"❌ Chat error: {e}", "red")
            self.print_colored("💡 Try: Check your internet connection or try a simpler question", "yellow")
    
    async def handle_read_file(self, args: List[str]):
        """Handle file reading"""
        if not args:
            self.print_colored("📁 Which file should I read? Example: read document.txt", "yellow")
            return
        
        file_path = " ".join(args)
        
        try:
            result = file_ops.read_file(file_path)
            if result.success:
                self.print_colored(f"📄 Contents of {file_path}:", "green", "bright")
                self.print_colored("-" * 50, "blue")
                print(result.data[:2000])  # Limit output for readability
                if len(result.data) > 2000:
                    self.print_colored(f"\n... ({len(result.data) - 2000} more characters)", "yellow")
                self.print_colored("-" * 50, "blue")
                
                # Offer to analyze with AI
                self.print_colored("💡 Want me to explain or analyze this file? Just ask!", "cyan")
            else:
                self.print_colored(f"❌ {result.message}", "red")
        except Exception as e:
            self.print_colored(f"❌ Error reading file: {e}", "red")
    
    async def handle_write_file(self, args: List[str]):
        """Handle file writing"""
        if not args:
            self.print_colored("📝 Which file should I create? Example: write letter.txt", "yellow")
            return
        
        file_path = " ".join(args)
        
        self.print_colored(f"📝 Creating {file_path}", "green")
        self.print_colored("Type your content (press Ctrl+D when done, Ctrl+C to cancel):", "yellow")
        
        try:
            content_lines = []
            while True:
                try:
                    line = input()
                    content_lines.append(line)
                except EOFError:
                    break
                except KeyboardInterrupt:
                    self.print_colored("\n❌ Cancelled", "red")
                    return
            
            content = "\n".join(content_lines)
            result = file_ops.write_file(file_path, content)
            
            if result.success:
                self.print_colored(f"✅ {result.message}", "green")
            else:
                self.print_colored(f"❌ {result.message}", "red")
                
        except Exception as e:
            self.print_colored(f"❌ Error writing file: {e}", "red")
    
    async def handle_list_directory(self, args: List[str]):
        """Handle directory listing"""
        directory = " ".join(args) if args else "."
        
        try:
            result = file_ops.list_directory(directory)
            if result.success:
                self.print_colored(f"📁 Contents of {directory}:", "green", "bright")
                
                for item in result.data[:20]:  # Limit to first 20 items
                    icon = "📁" if item['type'] == 'directory' else "📄"
                    safety = "✅" if item['is_safe'] else "⚠️"
                    size = f"({item['size']} bytes)" if item['type'] == 'file' else ""
                    print(f"  {icon} {safety} {item['name']} {size}")
                
                if len(result.data) > 20:
                    self.print_colored(f"... and {len(result.data) - 20} more items", "yellow")
            else:
                self.print_colored(f"❌ {result.message}", "red")
        except Exception as e:
            self.print_colored(f"❌ Error listing directory: {e}", "red")
    
    async def handle_search_files(self, args: List[str]):
        """Handle file search"""
        if not args:
            self.print_colored("🔍 What should I search for? Example: search vacation photos", "yellow")
            return
        
        pattern = " ".join(args)
        directory = "."
        
        try:
            result = file_ops.search_files(directory, pattern, content_search=True)
            if result.success:
                self.print_colored(f"🔍 Search results for '{pattern}':", "green", "bright")
                
                for item in result.data[:10]:  # Limit results
                    match_type = "📝" if item['type'] == 'content_match' else "📄"
                    print(f"  {match_type} {item['name']} - {item['path']}")
                
                if len(result.data) > 10:
                    self.print_colored(f"... and {len(result.data) - 10} more results", "yellow")
                    
                if not result.data:
                    self.print_colored("No files found matching your search.", "yellow")
            else:
                self.print_colored(f"❌ {result.message}", "red")
        except Exception as e:
            self.print_colored(f"❌ Error searching: {e}", "red")
    
    async def handle_analyze_image(self, args: List[str]):
        """Handle image analysis"""
        if not args:
            self.print_colored("🖼️  Which image should I analyze? Example: photo vacation.jpg", "yellow")
            return
        
        image_path = " ".join(args)
        
        try:
            self.print_colored(f"🖼️  Analyzing {image_path}...", "blue")
            
            # Basic analysis
            result = image_processor.comprehensive_analysis(image_path)
            if result.success:
                info = result.image_info
                self.print_colored(f"📏 Dimensions: {info.width} x {info.height} pixels", "green")
                self.print_colored(f"📊 Size: {info.size_bytes // 1024} KB", "green")
                self.print_colored(f"🎨 Format: {info.format.value.upper()}", "green")
                
                if result.text_extraction and result.text_extraction.text.strip():
                    self.print_colored("📝 Text found in image:", "cyan", "bright")
                    print(f"   {result.text_extraction.text[:200]}...")
                
                if result.color_analysis:
                    colors = result.color_analysis.color_palette[:3]
                    self.print_colored(f"🎨 Main colors: {', '.join(colors)}", "magenta")
                
                # Offer AI description
                self.print_colored("🤖 Getting AI description...", "blue")
                description = await describe_image(image_path)
                self.print_colored("🔍 AI sees:", "cyan", "bright")
                print(f"   {description}")
                
            else:
                self.print_colored(f"❌ {result.message}", "red")
        except Exception as e:
            self.print_colored(f"❌ Error analyzing image: {e}", "red")
    
    async def handle_extract_text(self, args: List[str]):
        """Handle text extraction from image"""
        if not args:
            self.print_colored("📝 Which image should I extract text from? Example: text receipt.png", "yellow")
            return
        
        image_path = " ".join(args)
        
        try:
            self.print_colored(f"📝 Extracting text from {image_path}...", "blue")
            text = extract_text_from_image(image_path)
            
            if text.strip():
                self.print_colored("📄 Extracted text:", "green", "bright")
                print(text)
            else:
                self.print_colored("No text found in the image.", "yellow")
        except Exception as e:
            self.print_colored(f"❌ Error extracting text: {e}", "red")
            if "not available" in str(e):
                self.print_colored("💡 Install tesseract: pip install pytesseract", "cyan")
    
    async def handle_describe_image(self, args: List[str]):
        """Handle AI image description"""
        if not args:
            self.print_colored("🖼️  Which image should I describe? Example: describe artwork.jpg", "yellow")
            return
        
        image_path = " ".join(args)
        
        try:
            self.print_colored(f"🤖 AI is looking at {image_path}...", "blue")
            description = await describe_image(image_path)
            
            self.print_colored("🔍 AI description:", "cyan", "bright")
            print(description)
        except Exception as e:
            self.print_colored(f"❌ Error describing image: {e}", "red")
    
    async def handle_status(self):
        """Show system status"""
        self.print_colored("🔧 System Status:", "cyan", "bright")
        
        # LLM providers
        providers = len(llm_manager.providers)
        enabled = sum(1 for p in llm_manager.providers.values() if p.config.enabled)
        self.print_colored(f"🤖 AI Providers: {enabled}/{providers} active", "green")
        
        # Capabilities
        caps = image_processor.capabilities
        self.print_colored(f"🖼️  Image Processing: {'✅' if caps['basic_processing'] else '❌'}", 
                          "green" if caps['basic_processing'] else "red")
        self.print_colored(f"📝 Text Extraction: {'✅' if caps['text_extraction'] else '❌'}", 
                          "green" if caps['text_extraction'] else "red")
        
        # File operations
        safe_dirs = len(file_ops.security.safe_directories)
        self.print_colored(f"📁 File Operations: ✅ ({safe_dirs} safe directories)", "green")
        
        # Recent usage
        stats = llm_manager.get_stats()
        total_requests = stats.get('total_requests', 0)
        self.print_colored(f"📊 Total AI requests: {total_requests}", "blue")
    
    async def handle_providers(self):
        """List AI providers"""
        self.print_colored("🤖 Available AI Providers:", "cyan", "bright")
        
        if not llm_manager.providers:
            self.print_colored("No providers initialized yet.", "yellow")
            return
        
        for name, provider in llm_manager.providers.items():
            status = "✅" if provider.config.enabled else "❌"
            tier = provider.config.tier.value
            self.print_colored(f"  {status} {name} ({tier})", "green" if provider.config.enabled else "red")
    
    def clear_screen(self):
        """Clear the conversation"""
        self.conversation_history = []
        self.print_colored("💫 Conversation cleared!", "green")
    
    async def interactive_mode(self):
        """Main interactive loop"""
        self.print_banner()
        await self.initialize()
        
        self.print_colored("\n💡 Try: 'help me write a poem' or 'read my file.txt'", "cyan")
        
        while True:
            try:
                # Prompt
                prompt = "💬 You: "
                if COLORS_AVAILABLE:
                    prompt = f"{Fore.WHITE}{Style.BRIGHT}💬 You: {Style.RESET_ALL}"
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Parse command
                command, args = self.parse_command(user_input)
                
                # Handle commands
                if command == "quit":
                    self.print_colored("👋 Goodbye! Thanks for using OpenLLM Toolkit!", "cyan")
                    break
                elif command == "help":
                    self.print_help()
                elif command == "clear":
                    self.clear_screen()
                elif command == "status":
                    await self.handle_status()
                elif command == "providers":
                    await self.handle_providers()
                elif command == "read":
                    await self.handle_read_file(args)
                elif command == "write":
                    await self.handle_write_file(args)
                elif command == "list":
                    await self.handle_list_directory(args)
                elif command == "search":
                    await self.handle_search_files(args)
                elif command == "photo":
                    await self.handle_analyze_image(args)
                elif command == "text":
                    await self.handle_extract_text(args)
                elif command == "describe":
                    await self.handle_describe_image(args)
                elif command == "chat":
                    await self.handle_chat(user_input)
                else:
                    await self.handle_chat(user_input)
                
                print()  # Add spacing
                
            except KeyboardInterrupt:
                self.print_colored("\n👋 Goodbye!", "cyan")
                break
            except EOFError:
                self.print_colored("\n👋 Goodbye!", "cyan")
                break
            except Exception as e:
                self.print_colored(f"❌ Unexpected error: {e}", "red")
                self.print_colored("💡 Type 'help' for assistance", "yellow")

def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="OpenLLM Toolkit - Your Free AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  openllm                           # Start interactive mode
  openllm chat "Hello AI"           # Quick chat
  openllm read document.txt         # Read a file
  openllm photo image.jpg           # Analyze an image
  openllm help                      # Show help
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Interactive mode (default)
    subparsers.add_parser('interactive', help='Start interactive mode (default)')
    
    # Quick chat
    chat_parser = subparsers.add_parser('chat', help='Quick chat with AI')
    chat_parser.add_argument('message', nargs='+', help='Message to send to AI')
    
    # File operations
    read_parser = subparsers.add_parser('read', help='Read a file')
    read_parser.add_argument('file', help='File to read')
    
    write_parser = subparsers.add_parser('write', help='Write to a file')
    write_parser.add_argument('file', help='File to write to')
    write_parser.add_argument('content', nargs='*', help='Content to write')
    
    list_parser = subparsers.add_parser('list', help='List directory contents')
    list_parser.add_argument('directory', nargs='?', default='.', help='Directory to list')
    
    # Image operations
    photo_parser = subparsers.add_parser('photo', help='Analyze an image')
    photo_parser.add_argument('image', help='Image file to analyze')
    
    # System commands
    subparsers.add_parser('status', help='Show system status')
    subparsers.add_parser('providers', help='List AI providers')
    subparsers.add_parser('help', help='Show detailed help')
    
    return parser

async def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    cli = BeginnerCLI()
    
    # Handle non-interactive commands
    if args.command == 'chat':
        await cli.initialize()
        message = ' '.join(args.message)
        await cli.handle_chat(message)
    elif args.command == 'read':
        await cli.initialize()
        await cli.handle_read_file([args.file])
    elif args.command == 'write':
        await cli.initialize()
        if args.content:
            content = ' '.join(args.content)
            result = file_ops.write_file(args.file, content)
            print(result.message)
        else:
            await cli.handle_write_file([args.file])
    elif args.command == 'list':
        await cli.initialize()
        await cli.handle_list_directory([args.directory])
    elif args.command == 'photo':
        await cli.initialize()
        await cli.handle_analyze_image([args.image])
    elif args.command == 'status':
        await cli.initialize()
        await cli.handle_status()
    elif args.command == 'providers':
        await cli.initialize()
        await cli.handle_providers()
    elif args.command == 'help':
        cli.print_help()
    else:
        # Default to interactive mode
        await cli.interactive_mode()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)