# SwiftAgent Toolkit - Deploy Button

## Vercel Deploy Button

Add this button to your README or website for one-click deployment:

### Markdown
```markdown
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FSourcesiri-Kamelot%2Fswiftagent&env=SWIFT_AGENT_MODE&env=OLLAMA_HOST&env=HUGGINGFACE_API_KEY&env=GROQ_API_KEY&env-description=SwiftAgent%20Configuration&env-link=https%3A%2F%2Fgithub.com%2FSourcesiri-Kamelot%2Fswiftagent%23environment-variables&project-name=swiftagent-toolkit&repository-name=swiftagent-toolkit&redirect-url=https%3A%2F%2Fswiftagent-toolkit.vercel.app&demo-title=SwiftAgent%20Toolkit&demo-description=Universal%20AI%20toolkit%20with%20free%20LLM%20providers%2C%20file%20operations%2C%20and%20image%20processing&demo-url=https%3A%2F%2Fswiftagent-toolkit.vercel.app&demo-image=https%3A%2F%2Fraw.githubusercontent.com%2FSourcesiri-Kamelot%2Fswiftagent%2Fmain%2Fdocs%2Fdemo-screenshot.png)
```

### HTML
```html
<a href="https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FSourcesiri-Kamelot%2Fswiftagent&env=SWIFT_AGENT_MODE&env=OLLAMA_HOST&env=HUGGINGFACE_API_KEY&env=GROQ_API_KEY&env-description=SwiftAgent%20Configuration&env-link=https%3A%2F%2Fgithub.com%2FSourcesiri-Kamelot%2Fswiftagent%23environment-variables&project-name=swiftagent-toolkit&repository-name=swiftagent-toolkit&redirect-url=https%3A%2F%2Fswiftagent-toolkit.vercel.app&demo-title=SwiftAgent%20Toolkit&demo-description=Universal%20AI%20toolkit%20with%20free%20LLM%20providers%2C%20file%20operations%2C%20and%20image%20processing&demo-url=https%3A%2F%2Fswiftagent-toolkit.vercel.app&demo-image=https%3A%2F%2Fraw.githubusercontent.com%2FSourcesiri-Kamelot%2Fswiftagent%2Fmain%2Fdocs%2Fdemo-screenshot.png">
    <img src="https://vercel.com/button" alt="Deploy with Vercel"/>
</a>
```

### Direct URL
```
https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FSourcesiri-Kamelot%2Fswiftagent&env=SWIFT_AGENT_MODE&env=OLLAMA_HOST&env=HUGGINGFACE_API_KEY&env=GROQ_API_KEY&env-description=SwiftAgent%20Configuration&env-link=https%3A%2F%2Fgithub.com%2FSourcesiri-Kamelot%2Fswiftagent%23environment-variables&project-name=swiftagent-toolkit&repository-name=swiftagent-toolkit&redirect-url=https%3A%2F%2Fswiftagent-toolkit.vercel.app&demo-title=SwiftAgent%20Toolkit&demo-description=Universal%20AI%20toolkit%20with%20free%20LLM%20providers%2C%20file%20operations%2C%20and%20image%20processing&demo-url=https%3A%2F%2Fswiftagent-toolkit.vercel.app&demo-image=https%3A%2F%2Fraw.githubusercontent.com%2FSourcesiri-Kamelot%2Fswiftagent%2Fmain%2Fdocs%2Fdemo-screenshot.png
```

## Environment Variables

The deploy button will prompt users to configure these environment variables:

- `SWIFTAGENT_MODE`: Set to "web", "cli", or "mcp" (default: "web")
- `OLLAMA_HOST`: Ollama server URL (default: "http://localhost:11434")
- `HUGGINGFACE_API_KEY`: HuggingFace API key (optional)
- `GROQ_API_KEY`: Groq API key (optional)

## Features

- **One-click deployment** to Vercel
- **Automatic setup** of all dependencies
- **Free hosting** with Vercel's generous limits
- **Custom domain** support
- **Environment variables** configuration
- **Demo card** with screenshot and description
- **Redirect URL** after successful deployment

## Local Development

For local development without Vercel:

```bash
# Clone the repository
git clone https://github.com/Sourcesiri-Kamelot/swiftagent.git
cd swiftagent

# Install dependencies
pip install -r requirements.txt

# Run in different modes
python start_swiftagent.py --mode web    # Web interface
python start_swiftagent.py --mode cli    # Command line
python start_swiftagent.py --mode mcp    # MCP server
python start_swiftagent.py --mode status # System status
```

## Quick Start

1. Click the "Deploy with Vercel" button
2. Configure environment variables (optional)
3. Deploy to Vercel
4. Access your SwiftAgent Toolkit at the provided URL
5. Start using AI features immediately!

## What Users Get

- 🌐 **Web Interface** - Beautiful UI for AI interactions
- 💻 **CLI Tools** - Command-line interface for power users
- 🤖 **MCP Server** - 25+ AI tools for automation
- 📁 **File Operations** - Read, write, and manage files
- 🖼️ **Image Processing** - Analyze images and extract text
- 🧠 **Memory System** - Persistent conversations and learning
- ⚖️ **Load Balancing** - Multiple free AI providers
- 🔧 **Self-Healing** - Automatic error correction

All completely **FREE** and **open source**! 🚀 