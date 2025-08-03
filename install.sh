#!/bin/bash
"""
OpenLLM Toolkit - One-Click Installer
Automated installation script for complete setup
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.openllm-toolkit"
VENV_DIR="$INSTALL_DIR/venv"
REPO_URL="https://github.com/Sourcesiri-Kamelot/swiftagent.git"

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

print_header() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                 🚀 OpenLLM Toolkit Installer                 ║"
    echo "║              Setting up your free AI assistant...            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            OS="ubuntu"
        elif command -v yum &> /dev/null; then
            OS="centos"
        elif command -v pacman &> /dev/null; then
            OS="arch"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    print_status "Detected OS: $OS"
}

# Function to check and install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    case $OS in
        "ubuntu")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv git curl wget \
                               tesseract-ocr tesseract-ocr-eng \
                               python3-dev build-essential \
                               libffi-dev libssl-dev
            ;;
        "centos")
            sudo yum update -y
            sudo yum install -y python3 python3-pip git curl wget \
                               tesseract tesseract-langpack-eng \
                               python3-devel gcc gcc-c++ make \
                               libffi-devel openssl-devel
            ;;
        "arch")
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm python python-pip git curl wget \
                                       tesseract tesseract-data-eng \
                                       base-devel libffi openssl
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                print_status "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python3 git curl wget tesseract
            ;;
        *)
            print_warning "Unknown OS. Please install Python 3.8+, pip, git, and tesseract manually."
            ;;
    esac
}

# Function to check Python version
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python not found. Please install Python 3.8 or later."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    print_status "Found Python $PYTHON_VERSION"
    
    # Check if Python version is >= 3.8
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_error "Python 3.8 or later is required. Found: $PYTHON_VERSION"
        exit 1
    fi
}

# Function to create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    # Remove existing installation if present
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Removing existing installation..."
        rm -rf "$INSTALL_DIR"
    fi
    
    mkdir -p "$INSTALL_DIR"
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
}

# Function to install OpenLLM Toolkit
install_toolkit() {
    print_status "Installing OpenLLM Toolkit..."
    
    # Clone repository
    cd "$INSTALL_DIR"
    git clone "$REPO_URL" toolkit
    cd toolkit
    
    # Install Python dependencies
    pip install -r requirements.txt
    
    # Install the toolkit in development mode
    pip install -e .
}

# Function to install optional dependencies
install_optional_deps() {
    print_status "Installing optional dependencies for enhanced features..."
    
    # AI/ML libraries
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu || true
    pip install transformers accelerate || true
    
    # Image processing
    pip install opencv-python pillow pytesseract || true
    
    # Additional utilities
    pip install colorama rich click typer || true
    
    # MCP support
    pip install mcp || true
}

# Function to setup Ollama (local LLM)
setup_ollama() {
    print_status "Setting up Ollama (local LLM support)..."
    
    if ! command -v ollama &> /dev/null; then
        case $OS in
            "linux")
                curl -fsSL https://ollama.ai/install.sh | sh
                ;;
            "macos")
                brew install ollama
                ;;
            *)
                print_warning "Please install Ollama manually from https://ollama.ai"
                return
                ;;
        esac
    fi
    
    # Start Ollama service
    if command -v systemctl &> /dev/null; then
        sudo systemctl enable ollama || true
        sudo systemctl start ollama || true
    fi
    
    # Download a small model for testing
    print_status "Downloading a lightweight AI model (this may take a few minutes)..."
    ollama pull llama3.2:1b || print_warning "Failed to download model. You can do this later with: ollama pull llama3.2:1b"
}

# Function to create configuration
create_config() {
    print_status "Creating default configuration..."
    
    CONFIG_DIR="$HOME/.config/openllm-toolkit"
    mkdir -p "$CONFIG_DIR"
    
    cat > "$CONFIG_DIR/config.json" << EOF
{
    "providers": {
        "ollama": {
            "enabled": true,
            "endpoint": "http://localhost:11434",
            "priority": 1
        },
        "huggingface": {
            "enabled": true,
            "api_key": null,
            "priority": 2
        },
        "groq": {
            "enabled": false,
            "api_key": null,
            "priority": 3
        }
    },
    "file_operations": {
        "safe_directories": [
            "$HOME/Documents",
            "$HOME/Downloads",
            "$HOME/Desktop",
            "/tmp",
            "/workspace"
        ],
        "max_file_size_mb": 50
    },
    "image_processing": {
        "max_image_size_mb": 20,
        "auto_install_tesseract": true
    },
    "ui": {
        "use_colors": true,
        "show_help_on_start": true
    }
}
EOF
}

# Function to create launcher scripts
create_launchers() {
    print_status "Creating launcher scripts..."
    
    # Create main launcher
    cat > "$INSTALL_DIR/openllm" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
cd "$INSTALL_DIR/toolkit"
python -m Interface.cli "\$@"
EOF
    chmod +x "$INSTALL_DIR/openllm"
    
    # Create MCP server launcher
    cat > "$INSTALL_DIR/openllm-mcp" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
cd "$INSTALL_DIR/toolkit"
python -m MCP.mcp_server
EOF
    chmod +x "$INSTALL_DIR/openllm-mcp"
    
    # Add to PATH
    SHELL_RC=""
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -f "$HOME/.profile" ]; then
        SHELL_RC="$HOME/.profile"
    fi
    
    if [ -n "$SHELL_RC" ]; then
        if ! grep -q "openllm-toolkit" "$SHELL_RC"; then
            echo "" >> "$SHELL_RC"
            echo "# OpenLLM Toolkit" >> "$SHELL_RC"
            echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
            print_success "Added OpenLLM Toolkit to PATH in $SHELL_RC"
        fi
    fi
}

# Function to test installation
test_installation() {
    print_status "Testing installation..."
    
    source "$VENV_DIR/bin/activate"
    cd "$INSTALL_DIR/toolkit"
    
    # Test basic imports
    python -c "
import sys
sys.path.insert(0, '.')
try:
    from Core.llm_manager import llm_manager
    from Tools.file_operations import file_ops
    from Tools.image_processor import image_processor
    print('✅ All core modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Installation test passed!"
    else
        print_error "Installation test failed!"
        exit 1
    fi
}

# Function to show completion message
show_completion() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║               🎉 Installation Complete! 🎉                   ║"
    echo "║                                                               ║"
    echo "║  Your OpenLLM Toolkit is ready to use!                       ║"
    echo "║                                                               ║"
    echo "║  Quick Start:                                                 ║"
    echo "║    openllm                    # Start interactive mode        ║"
    echo "║    openllm chat \"Hello AI\"     # Quick chat                  ║"
    echo "║    openllm status             # Check system status          ║"
    echo "║                                                               ║"
    echo "║  Files:                                                       ║"
    echo "║    Install dir: $INSTALL_DIR                  ║"
    echo "║    Config: ~/.config/openllm-toolkit/config.json             ║"
    echo "║                                                               ║"
    echo "║  Need help? Run: openllm help                                 ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    print_status "Restart your terminal or run: source ~/.bashrc"
    print_status "Then start with: openllm"
}

# Function to handle errors
handle_error() {
    print_error "Installation failed at step: $1"
    print_error "Check the error messages above for details."
    print_status "You can try running the installer again or install manually."
    exit 1
}

# Main installation flow
main() {
    print_header
    
    # Check if running as root (not recommended)
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root is not recommended. Continue? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_status "Starting OpenLLM Toolkit installation..."
    
    detect_os || handle_error "OS detection"
    
    # Ask for confirmation
    echo -e "${YELLOW}This installer will:${NC}"
    echo "  • Install system dependencies (requires sudo)"
    echo "  • Set up Python virtual environment"
    echo "  • Install OpenLLM Toolkit and dependencies"
    echo "  • Configure Ollama for local AI models"
    echo "  • Create launcher scripts"
    echo ""
    echo -e "${YELLOW}Continue? (Y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Nn]$ ]]; then
        print_status "Installation cancelled."
        exit 0
    fi
    
    install_system_deps || handle_error "system dependencies"
    check_python || handle_error "Python check"
    create_venv || handle_error "virtual environment"
    install_toolkit || handle_error "toolkit installation"
    install_optional_deps || handle_error "optional dependencies"
    setup_ollama || handle_error "Ollama setup"
    create_config || handle_error "configuration"
    create_launchers || handle_error "launcher creation"
    test_installation || handle_error "installation test"
    
    show_completion
}

# Run main function
main "$@"