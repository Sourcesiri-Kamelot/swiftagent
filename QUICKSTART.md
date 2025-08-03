# 🚀 OpenLLM Toolkit - Quick Start Guide

Get up and running with OpenLLM Toolkit in under 5 minutes!

## ⚡ One-Click Installation

```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/Sourcesiri-Kamelot/swiftagent/main/install.sh | bash
```

## 🎯 First Steps

### 1. Start the Toolkit
```bash
# Interactive mode (recommended for beginners)
openllm

# Quick chat
openllm chat "Hello, how are you?"

# Check system status
openllm status
```

### 2. Try Basic Commands
```bash
# Chat with AI
openllm chat "Write a poem about cats"

# Read a file
openllm read document.txt

# Analyze an image
openllm photo vacation.jpg

# List files in directory
openllm list Documents
```

### 3. Advanced Usage
```bash
# Extract text from image
openllm text receipt.png

# Search for files
openllm search "vacation photos"

# Get AI description of image
openllm describe artwork.jpg
```

## 🔧 Setup LLM Providers

### Ollama (Local - Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama3.2:1b

# Start Ollama service
ollama serve
```

### HuggingFace (Free Tier)
```bash
# Get free API key from https://huggingface.co/settings/tokens
# Add to ~/.config/openllm-toolkit/.env:
HUGGINGFACE_API_KEY=your_key_here
```

### Groq (Fast Inference)
```bash
# Get API key from https://console.groq.com/
# Add to ~/.config/openllm-toolkit/.env:
GROQ_API_KEY=your_key_here
```

## 📁 File Operations

### Safe Directories
The toolkit can only access files in these safe directories:
- `~/Documents`
- `~/Downloads` 
- `~/Desktop`
- `/tmp`
- `/workspace`

### Examples
```bash
# Read a text file
openllm read ~/Documents/letter.txt

# Write content to file
openllm write ~/Documents/response.txt "This is my response"

# List files in directory
openllm list ~/Downloads

# Search for files
openllm search "invoice" ~/Documents
```

## 🖼️ Image Processing

### Supported Formats
- JPEG, PNG, GIF, BMP, WEBP, TIFF, SVG

### Examples
```bash
# Analyze image
openllm photo ~/Pictures/vacation.jpg

# Extract text from image
openllm text ~/Pictures/receipt.png

# Get AI description
openllm describe ~/Pictures/artwork.jpg
```

## 🤖 MCP Integration

### Start MCP Server
```bash
# Start the MCP server
openllm-mcp

# Or run directly
python -m MCP.mcp_server
```

### Connect to MCP Clients
The toolkit works with any MCP-compatible client:
- Claude Desktop
- Cursor
- Continue
- And more...

## 🔍 Troubleshooting

### Common Issues

**"No AI providers available"**
```bash
# Check if Ollama is running
ollama list

# Start Ollama
ollama serve
```

**"File access denied"**
```bash
# Move file to safe directory
mv file.txt ~/Documents/

# Or add directory to safe list in config
```

**"Image processing failed"**
```bash
# Install Pillow
pip install Pillow

# Install Tesseract for OCR
# Ubuntu: sudo apt install tesseract-ocr
# macOS: brew install tesseract
```

### Get Help
```bash
# Show all commands
openllm help

# Check system status
openllm status

# List providers
openllm providers
```

## 🎉 Next Steps

1. **Explore Features**: Try different commands and see what the toolkit can do
2. **Customize**: Edit `~/.config/openllm-toolkit/config.json` to customize settings
3. **Add Providers**: Configure additional LLM providers for more options
4. **Integrate**: Use the MCP server with your favorite AI clients

## 📞 Support

- **GitHub Issues**: https://github.com/Sourcesiri-Kamelot/swiftagent/issues
- **Documentation**: https://github.com/Sourcesiri-Kamelot/swiftagent#readme
- **Discord**: https://discord.gg/vrySD8qA

---

**Ready to experience the power of free, open-source AI? Start with `openllm` and explore the possibilities!** 🚀 