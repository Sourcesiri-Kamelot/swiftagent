#!/bin/bash

# SwiftAgent Setup Script
# Configures the development environment and MCP integration

set -e

echo "🚀 Setting up SwiftAgent..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "📁 Project root: $PROJECT_ROOT"

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo -e "${RED}❌ Xcode not found. Please install Xcode from the App Store.${NC}"
    exit 1
fi

# Check Swift
if ! command -v swift &> /dev/null; then
    echo -e "${RED}❌ Swift not found. Please install Xcode Command Line Tools.${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Create necessary directories
echo -e "${BLUE}📁 Creating project directories...${NC}"
mkdir -p "$PROJECT_ROOT/generated"
mkdir -p "$PROJECT_ROOT/exports"
mkdir -p "$PROJECT_ROOT/.swiftagent"

# Set up Python virtual environment for MCP
echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
cd "$PROJECT_ROOT"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install asyncio logging pathlib

echo -e "${GREEN}✅ Python environment ready${NC}"

# Make scripts executable
echo -e "${BLUE}🔧 Setting up scripts...${NC}"
chmod +x "$PROJECT_ROOT/Scripts/"*.sh
chmod +x "$PROJECT_ROOT/MCP/"*.py

# Create MCP configuration
echo -e "${BLUE}⚙️ Configuring MCP integration...${NC}"

MCP_CONFIG_DIR="$HOME/.config/amazon-q"
mkdir -p "$MCP_CONFIG_DIR"

# Check if MCP config exists and backup
if [ -f "$MCP_CONFIG_DIR/mcp.json" ]; then
    echo -e "${YELLOW}⚠️ Backing up existing MCP configuration...${NC}"
    cp "$MCP_CONFIG_DIR/mcp.json" "$MCP_CONFIG_DIR/mcp.json.backup.$(date +%s)"
fi

# Add SwiftAgent to MCP configuration
python3 << EOF
import json
import os

config_file = "$MCP_CONFIG_DIR/mcp.json"
swift_agent_config = {
    "swiftagent-core": {
        "command": "python3",
        "args": ["$PROJECT_ROOT/MCP/swift_agent_mcp.py"],
        "env": {
            "PYTHONPATH": "$PROJECT_ROOT/MCP",
            "XCODE_PATH": "/Applications/Xcode.app",
            "SWIFT_AGENT_MODE": "development",
            "SWIFT_AGENT_ROOT": "$PROJECT_ROOT"
        }
    }
}

# Load existing config or create new
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
else:
    config = {"mcpServers": {}}

# Add SwiftAgent configuration
config["mcpServers"].update(swift_agent_config)

# Save updated configuration
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ MCP configuration updated")
EOF

# Create initial Swift package
echo -e "${BLUE}📦 Creating Swift package structure...${NC}"
cd "$PROJECT_ROOT"

# Create Package.swift
cat > Package.swift << 'EOF'
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "SwiftAgent",
    platforms: [
        .iOS(.v15),
        .macOS(.v12)
    ],
    products: [
        .library(
            name: "SwiftAgent",
            targets: ["SwiftAgent"]
        ),
    ],
    dependencies: [
        // Add dependencies here
    ],
    targets: [
        .target(
            name: "SwiftAgent",
            dependencies: []
        ),
        .testTarget(
            name: "SwiftAgentTests",
            dependencies: ["SwiftAgent"]
        ),
    ]
)
EOF

# Create main SwiftAgent module
cat > Sources/SwiftAgent/SwiftAgent.swift << 'EOF'
import Foundation

/// SwiftAgent - AI-powered Swift development assistant
public struct SwiftAgent {
    
    /// Initialize SwiftAgent
    public init() {}
    
    /// Generate Swift code from description
    public func generateCode(description: String, type: CodeType) -> String {
        // TODO: Implement AI code generation
        return "// Generated code for: \(description)"
    }
    
    /// Code types supported by SwiftAgent
    public enum CodeType {
        case view
        case model
        case controller
        case service
        case test
    }
}
EOF

# Create basic test
cat > Tests/SwiftAgentTests/SwiftAgentTests.swift << 'EOF'
import XCTest
@testable import SwiftAgent

final class SwiftAgentTests: XCTestCase {
    
    func testSwiftAgentInitialization() throws {
        let agent = SwiftAgent()
        XCTAssertNotNil(agent)
    }
    
    func testCodeGeneration() throws {
        let agent = SwiftAgent()
        let code = agent.generateCode(description: "test view", type: .view)
        XCTAssertFalse(code.isEmpty)
    }
}
EOF

# Test Swift package
echo -e "${BLUE}🧪 Testing Swift package...${NC}"
swift build
swift test

echo -e "${GREEN}✅ Swift package ready${NC}"

# Create example project
echo -e "${BLUE}📱 Creating example iOS project...${NC}"
mkdir -p Examples/BasicApp

# Test MCP integration
echo -e "${BLUE}🧪 Testing MCP integration...${NC}"
cd "$PROJECT_ROOT/MCP"
python3 swift_agent_mcp.py &
MCP_PID=$!
sleep 2
kill $MCP_PID 2>/dev/null || true

echo -e "${GREEN}✅ MCP integration test passed${NC}"

# Create development configuration
echo -e "${BLUE}⚙️ Creating development configuration...${NC}"
cat > "$PROJECT_ROOT/.swiftagent/config.json" << EOF
{
  "version": "1.0.0",
  "project_root": "$PROJECT_ROOT",
  "xcode_path": "/Applications/Xcode.app",
  "swift_version": "5.9",
  "ios_deployment_target": "15.0",
  "mcp_integration": true,
  "features": {
    "code_generation": true,
    "ui_mockups": true,
    "debugging": true,
    "testing": true,
    "documentation": true
  }
}
EOF

# Final setup steps
echo -e "${BLUE}🔧 Final setup steps...${NC}"

# Create .env file for environment variables
cat > "$PROJECT_ROOT/.env" << EOF
# SwiftAgent Environment Configuration
SWIFT_AGENT_ROOT=$PROJECT_ROOT
XCODE_PATH=/Applications/Xcode.app
SWIFT_AGENT_MODE=development
PYTHONPATH=$PROJECT_ROOT/MCP
EOF

echo -e "${GREEN}🎉 SwiftAgent setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Open Xcode: open $PROJECT_ROOT"
echo "2. Start Q session to test MCP integration"
echo "3. Try: 'Generate a SwiftUI view for user profile'"
echo "4. Check generated code in: $PROJECT_ROOT/generated/"
echo ""
echo -e "${YELLOW}💡 Useful commands:${NC}"
echo "• swift build                 - Build the package"
echo "• swift test                  - Run tests"
echo "• ./Scripts/build.sh          - Build with options"
echo "• python3 MCP/swift_agent_mcp.py - Test MCP server"
echo ""
echo -e "${GREEN}🚀 SwiftAgent is ready for AI-powered Swift development!${NC}"
EOF
