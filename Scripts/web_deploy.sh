#!/bin/bash
# OpenLLM Toolkit - Web Deployment Script
# This script is triggered from the web interface for easy deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    print_status "Detected OS: $OS"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if [[ "$OS" == "macos" ]]; then
        if ! command_exists brew; then
            print_status "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        print_status "Installing Python and Git..."
        brew install python git
        
    elif [[ "$OS" == "linux" ]]; then
        if command_exists apt-get; then
            print_status "Installing dependencies with apt..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip git curl
        elif command_exists yum; then
            print_status "Installing dependencies with yum..."
            sudo yum install -y python3 python3-pip git curl
        fi
        
    elif [[ "$OS" == "windows" ]]; then
        print_warning "Windows detected. Please install Python and Git manually."
        print_status "Download Python from: https://python.org"
        print_status "Download Git from: https://git-scm.com"
    fi
}

# Function to install Ollama
install_ollama() {
    print_status "Installing Ollama..."
    
    if [[ "$OS" == "macos" ]]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OS" == "linux" ]]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        print_warning "Please install Ollama manually from: https://ollama.ai"
    fi
    
    # Start Ollama service
    print_status "Starting Ollama service..."
    ollama serve &
    sleep 5
    
    # Pull a default model
    print_status "Downloading default AI model (llama3:8b)..."
    ollama pull llama3:8b || print_warning "Failed to pull model, continuing..."
}

# Function to setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Create virtual environment
    python3 -m venv openllm-env
    source openllm-env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
}

# Function to clone repository
clone_repo() {
    print_status "Cloning OpenLLM Toolkit repository..."
    
    if [ -d "openllm-toolkit" ]; then
        print_status "Repository already exists, updating..."
        cd openllm-toolkit
        git pull origin main
    else
        git clone https://github.com/Sourcesiri-Kamelot/swiftagent.git openllm-toolkit
        cd openllm-toolkit
    fi
}

# Function to create launcher scripts
create_launchers() {
    print_status "Creating launcher scripts..."
    
    # Create openllm command
    cat > /usr/local/bin/openllm << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/openllm-toolkit"
source openllm-env/bin/activate
python start_openllm.py "$@"
EOF
    
    chmod +x /usr/local/bin/openllm
    
    # Create web launcher
    cat > /usr/local/bin/openllm-web << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/openllm-toolkit"
source openllm-env/bin/activate
python start_openllm.py --mode web
EOF
    
    chmod +x /usr/local/bin/openllm-web
}

# Function to test installation
test_installation() {
    print_status "Testing installation..."
    
    cd openllm-toolkit
    source openllm-env/bin/activate
    
    # Test basic functionality
    if python -c "import sys; print('Python OK')"; then
        print_success "Python environment working"
    else
        print_error "Python environment failed"
        return 1
    fi
    
    # Test toolkit startup
    if timeout 10s python start_openllm.py --mode status > /dev/null 2>&1; then
        print_success "OpenLLM Toolkit startup test passed"
    else
        print_warning "Startup test failed, but installation may still work"
    fi
}

# Function to show completion message
show_completion() {
    print_success "🎉 OpenLLM Toolkit installation complete!"
    echo
    echo "🚀 Quick Start Commands:"
    echo "  • Web Interface: openllm-web"
    echo "  • Command Line: openllm"
    echo "  • Status Check: openllm --mode status"
    echo
    echo "📱 Web Interface: http://localhost:8000"
    echo "💻 CLI Commands: openllm chat 'Hello AI'"
    echo "🤖 MCP Server: openllm --mode mcp"
    echo
    echo "📖 Documentation: https://github.com/Sourcesiri-Kamelot/swiftagent"
    echo "💬 Community: GitHub Discussions"
    echo
    print_success "Ready to use OpenLLM Toolkit!"
}

# Function to handle errors
handle_error() {
    print_error "Installation failed at: $1"
    print_error "Please check the error messages above and try again."
    print_error "For help, visit: https://github.com/Sourcesiri-Kamelot/swiftagent/issues"
    exit 1
}

# Main installation function
main() {
    print_status "🚀 Starting OpenLLM Toolkit deployment..."
    echo
    
    # Detect OS
    detect_os || handle_error "OS detection"
    
    # Install system dependencies
    install_system_deps || handle_error "system dependencies"
    
    # Install Ollama
    install_ollama || handle_error "Ollama installation"
    
    # Clone repository
    clone_repo || handle_error "repository cloning"
    
    # Setup Python environment
    setup_python_env || handle_error "Python environment"
    
    # Create launchers
    create_launchers || handle_error "launcher creation"
    
    # Test installation
    test_installation || handle_error "installation test"
    
    # Show completion
    show_completion
}

# Run main function
main "$@" 