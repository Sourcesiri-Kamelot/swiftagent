#!/bin/bash
# OpenLLM Toolkit - Quick Start Script
# Automates setup for complete beginners

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 OpenLLM Toolkit - Quick Start${NC}"
echo -e "${BLUE}Setting up your free AI assistant...${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Don't run as root! This script will ask for sudo when needed.${NC}"
    exit 1
fi

# Function to print status
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

# Detect OS
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
    else
        OS="unknown"
    fi
    print_status "Detected OS: $OS"
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    case $OS in
        "ubuntu")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv git curl wget \
                               tesseract-ocr tesseract-ocr-eng
            ;;
        "centos")
            sudo yum update -y
            sudo yum install -y python3 python3-pip git curl wget \
                               tesseract tesseract-langpack-eng
            ;;
        "arch")
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm python python-pip git curl wget \
                                       tesseract tesseract-data-eng
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

# Install Ollama
install_ollama() {
    print_status "Installing Ollama (local AI models)..."
    
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
    
    # Download a small model
    print_status "Downloading a lightweight AI model (this may take a few minutes)..."
    ollama pull llama3.2:1b || print_warning "Failed to download model. You can do this later with: ollama pull llama3.2:1b"
}

# Install OpenLLM Toolkit
install_toolkit() {
    print_status "Installing OpenLLM Toolkit..."
    
    # Create installation directory
    INSTALL_DIR="$HOME/.openllm-toolkit"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Clone repository
    if [ ! -d "toolkit" ]; then
        git clone https://github.com/Sourcesiri-Kamelot/swiftagent.git toolkit
    fi
    
    cd toolkit
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    
    # Install the toolkit
    pip install -e .
    
    print_success "OpenLLM Toolkit installed successfully!"
}

# Create launcher script
create_launcher() {
    print_status "Creating launcher script..."
    
    INSTALL_DIR="$HOME/.openllm-toolkit"
    
    # Create main launcher
    cat > "$INSTALL_DIR/openllm" << 'EOF'
#!/bin/bash
source "$HOME/.openllm-toolkit/venv/bin/activate"
cd "$HOME/.openllm-toolkit/toolkit"
python -m Interface.cli "$@"
EOF
    chmod +x "$INSTALL_DIR/openllm"
    
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

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    INSTALL_DIR="$HOME/.openllm-toolkit"
    cd "$INSTALL_DIR/toolkit"
    source venv/bin/activate
    
    # Test basic functionality
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

# Show completion message
show_completion() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║               🎉 Setup Complete! 🎉                           ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║  Your OpenLLM Toolkit is ready to use!                       ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║  Quick Start:                                                 ║${NC}"
    echo -e "${GREEN}║    openllm                    # Start interactive mode        ║${NC}"
    echo -e "${GREEN}║    openllm chat \"Hello AI\"     # Quick chat                  ║${NC}"
    echo -e "${GREEN}║    openllm status             # Check system status          ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║  Need help? Run: openllm help                                 ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_status "Restart your terminal or run: source ~/.bashrc"
    print_status "Then start with: openllm"
}

# Main installation flow
main() {
    print_status "Starting OpenLLM Toolkit quick setup..."
    
    detect_os
    install_system_deps
    install_ollama
    install_toolkit
    create_launcher
    test_installation
    show_completion
}

# Run main function
main "$@" 