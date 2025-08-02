#!/usr/bin/env python3
"""
SwiftAgent MCP Server
AI-powered Swift development assistant with SoulCore integration
"""

import os
import json
import asyncio
import logging
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SwiftAgentMCP:
    """SwiftAgent MCP server for AI-powered Swift development"""
    
    def __init__(self):
        self.xcode_path = os.getenv('XCODE_PATH', '/Applications/Xcode.app')
        self.swift_path = os.path.join(self.xcode_path, 'Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swift')
        self.project_root = Path(__file__).parent.parent
        
        # Tool registry
        self.tools = {}
        self.register_tools()
        
    def register_tools(self):
        """Register all SwiftAgent MCP tools"""
        self.tools = {
            "swift_code_generation": {
                "name": "swift_code_generation",
                "description": "Generate Swift code from natural language descriptions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Natural language description of the code to generate"
                        },
                        "code_type": {
                            "type": "string",
                            "enum": ["class", "struct", "enum", "protocol", "extension", "function", "view", "model"],
                            "description": "Type of Swift code to generate"
                        },
                        "framework": {
                            "type": "string",
                            "enum": ["SwiftUI", "UIKit", "Foundation", "Combine", "CoreData"],
                            "description": "iOS framework to use"
                        },
                        "style": {
                            "type": "string",
                            "enum": ["modern", "legacy", "minimal", "comprehensive"],
                            "description": "Code style preference"
                        }
                    },
                    "required": ["description", "code_type"]
                },
                "handler": self.swift_code_generation
            },
            "ios_ui_mockup": {
                "name": "ios_ui_mockup",
                "description": "Create iOS interface mockups and SwiftUI code",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "screen_type": {
                            "type": "string",
                            "enum": ["list", "detail", "form", "tab", "navigation", "modal", "custom"],
                            "description": "Type of iOS screen to create"
                        },
                        "components": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "UI components to include"
                        },
                        "data_source": {
                            "type": "string",
                            "enum": ["static", "api", "coredata", "userdefaults"],
                            "description": "Data source for the UI"
                        },
                        "theme": {
                            "type": "string",
                            "enum": ["light", "dark", "auto", "custom"],
                            "description": "UI theme"
                        }
                    },
                    "required": ["screen_type"]
                },
                "handler": self.ios_ui_mockup
            },
            "swift_debugging": {
                "name": "swift_debugging",
                "description": "Intelligent Swift debugging and error resolution",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "error_message": {
                            "type": "string",
                            "description": "Swift compiler or runtime error message"
                        },
                        "code_context": {
                            "type": "string",
                            "description": "Relevant Swift code context"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the Swift file with the error"
                        }
                    },
                    "required": ["error_message"]
                },
                "handler": self.swift_debugging
            },
            "ios_project_setup": {
                "name": "ios_project_setup",
                "description": "Create and configure new iOS projects",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "Name of the iOS project"
                        },
                        "template": {
                            "type": "string",
                            "enum": ["app", "framework", "library", "game", "widget"],
                            "description": "Project template type"
                        },
                        "ui_framework": {
                            "type": "string",
                            "enum": ["SwiftUI", "UIKit", "Mixed"],
                            "description": "UI framework to use"
                        },
                        "features": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Features to include (CoreData, CloudKit, etc.)"
                        }
                    },
                    "required": ["project_name", "template"]
                },
                "handler": self.ios_project_setup
            },
            "swift_testing": {
                "name": "swift_testing",
                "description": "Generate Swift unit and UI tests",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_code": {
                            "type": "string",
                            "description": "Swift code to generate tests for"
                        },
                        "test_type": {
                            "type": "string",
                            "enum": ["unit", "ui", "integration", "performance"],
                            "description": "Type of tests to generate"
                        },
                        "coverage_target": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Target code coverage percentage"
                        }
                    },
                    "required": ["target_code", "test_type"]
                },
                "handler": self.swift_testing
            },
            "swift_documentation": {
                "name": "swift_documentation",
                "description": "Generate Swift code documentation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source_path": {
                            "type": "string",
                            "description": "Path to Swift source files"
                        },
                        "doc_format": {
                            "type": "string",
                            "enum": ["swift-docc", "jazzy", "markdown"],
                            "description": "Documentation format"
                        },
                        "include_examples": {
                            "type": "boolean",
                            "description": "Include code examples in documentation"
                        }
                    },
                    "required": ["source_path"]
                },
                "handler": self.swift_documentation
            }
        }
    
    async def swift_code_generation(self, description: str, code_type: str, 
                                   framework: str = "SwiftUI", style: str = "modern") -> Dict[str, Any]:
        """Generate Swift code from natural language descriptions"""
        try:
            logger.info(f"🔨 Generating {code_type} code: {description}")
            
            # Code generation templates
            templates = {
                "view": self._generate_swiftui_view,
                "model": self._generate_data_model,
                "class": self._generate_swift_class,
                "struct": self._generate_swift_struct,
                "enum": self._generate_swift_enum,
                "protocol": self._generate_swift_protocol,
                "function": self._generate_swift_function
            }
            
            if code_type in templates:
                generated_code = await templates[code_type](description, framework, style)
                
                # Save generated code
                filename = f"{description.lower().replace(' ', '_')}_{code_type}.swift"
                output_path = self.project_root / "generated" / filename
                output_path.parent.mkdir(exist_ok=True)
                
                with open(output_path, 'w') as f:
                    f.write(generated_code)
                
                return {
                    "success": True,
                    "code_type": code_type,
                    "framework": framework,
                    "style": style,
                    "generated_code": generated_code,
                    "file_path": str(output_path),
                    "description": description
                }
            else:
                return {"success": False, "error": f"Unsupported code type: {code_type}"}
                
        except Exception as e:
            logger.error(f"❌ Code generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def ios_ui_mockup(self, screen_type: str, components: List[str] = None,
                           data_source: str = "static", theme: str = "auto") -> Dict[str, Any]:
        """Create iOS interface mockups and SwiftUI code"""
        try:
            logger.info(f"📱 Creating {screen_type} UI mockup")
            
            components = components or []
            
            # Generate SwiftUI view based on screen type
            swiftui_code = await self._generate_ios_screen(screen_type, components, data_source, theme)
            
            # Create preview code
            preview_code = f"""
struct ContentView_Previews: PreviewProvider {{
    static var previews: some View {{
        {screen_type.capitalize()}View()
            .preferredColorScheme(.{theme if theme != 'auto' else 'light'})
    }}
}}
"""
            
            complete_code = swiftui_code + preview_code
            
            # Save mockup
            filename = f"{screen_type}_mockup.swift"
            output_path = self.project_root / "generated" / filename
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(complete_code)
            
            return {
                "success": True,
                "screen_type": screen_type,
                "components": components,
                "data_source": data_source,
                "theme": theme,
                "swiftui_code": complete_code,
                "file_path": str(output_path)
            }
            
        except Exception as e:
            logger.error(f"❌ UI mockup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def swift_debugging(self, error_message: str, code_context: str = "",
                             file_path: str = "") -> Dict[str, Any]:
        """Intelligent Swift debugging and error resolution"""
        try:
            logger.info(f"🐛 Debugging Swift error: {error_message[:50]}...")
            
            # Common Swift error patterns and solutions
            error_solutions = {
                "Index out of range": {
                    "cause": "Accessing array element beyond bounds",
                    "solution": "Add bounds checking before array access",
                    "code_fix": "if index < array.count { /* access array[index] */ }"
                },
                "Unexpectedly found nil": {
                    "cause": "Force unwrapping nil optional value",
                    "solution": "Use optional binding or nil coalescing",
                    "code_fix": "if let value = optionalValue { /* use value */ }"
                },
                "Cannot convert value": {
                    "cause": "Type mismatch in assignment or function call",
                    "solution": "Check types and add proper casting",
                    "code_fix": "let result = Type(value) or value as? Type"
                },
                "Use of unresolved identifier": {
                    "cause": "Variable or function not declared or imported",
                    "solution": "Declare variable or import required module",
                    "code_fix": "import ModuleName or declare the identifier"
                }
            }
            
            # Find matching error pattern
            solution = None
            for pattern, sol in error_solutions.items():
                if pattern.lower() in error_message.lower():
                    solution = sol
                    break
            
            if not solution:
                solution = {
                    "cause": "Unknown error pattern",
                    "solution": "Review Swift documentation and error context",
                    "code_fix": "Check syntax and type requirements"
                }
            
            return {
                "success": True,
                "error_message": error_message,
                "file_path": file_path,
                "diagnosis": solution["cause"],
                "solution": solution["solution"],
                "suggested_fix": solution["code_fix"],
                "additional_resources": [
                    "https://docs.swift.org/swift-book/",
                    "https://developer.apple.com/documentation/swift"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Debugging failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def ios_project_setup(self, project_name: str, template: str,
                               ui_framework: str = "SwiftUI", features: List[str] = None) -> Dict[str, Any]:
        """Create and configure new iOS projects"""
        try:
            logger.info(f"📱 Setting up iOS project: {project_name}")
            
            features = features or []
            project_path = self.project_root / "Examples" / project_name
            
            # Create project structure
            await self._create_project_structure(project_path, template, ui_framework, features)
            
            # Generate Package.swift if needed
            if template in ["framework", "library"]:
                package_swift = await self._generate_package_swift(project_name, template)
                with open(project_path / "Package.swift", 'w') as f:
                    f.write(package_swift)
            
            return {
                "success": True,
                "project_name": project_name,
                "template": template,
                "ui_framework": ui_framework,
                "features": features,
                "project_path": str(project_path),
                "next_steps": [
                    f"cd {project_path}",
                    "open *.xcodeproj" if template == "app" else "swift build"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Project setup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def swift_testing(self, target_code: str, test_type: str,
                           coverage_target: float = 80.0) -> Dict[str, Any]:
        """Generate Swift unit and UI tests"""
        try:
            logger.info(f"🧪 Generating {test_type} tests")
            
            test_code = await self._generate_test_code(target_code, test_type, coverage_target)
            
            # Save test file
            filename = f"Generated{test_type.capitalize()}Tests.swift"
            output_path = self.project_root / "Tests" / filename
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(test_code)
            
            return {
                "success": True,
                "test_type": test_type,
                "coverage_target": coverage_target,
                "test_code": test_code,
                "file_path": str(output_path),
                "run_command": f"swift test --filter {filename.replace('.swift', '')}"
            }
            
        except Exception as e:
            logger.error(f"❌ Test generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def swift_documentation(self, source_path: str, doc_format: str = "swift-docc",
                                 include_examples: bool = True) -> Dict[str, Any]:
        """Generate Swift code documentation"""
        try:
            logger.info(f"📚 Generating documentation for: {source_path}")
            
            # Generate documentation based on format
            if doc_format == "swift-docc":
                doc_content = await self._generate_docc_documentation(source_path, include_examples)
            else:
                doc_content = await self._generate_markdown_documentation(source_path, include_examples)
            
            # Save documentation
            doc_path = self.project_root / "Documentation" / f"Generated_{doc_format}.md"
            doc_path.parent.mkdir(exist_ok=True)
            
            with open(doc_path, 'w') as f:
                f.write(doc_content)
            
            return {
                "success": True,
                "source_path": source_path,
                "doc_format": doc_format,
                "include_examples": include_examples,
                "documentation": doc_content,
                "output_path": str(doc_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Documentation generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Helper methods for code generation
    async def _generate_swiftui_view(self, description: str, framework: str, style: str) -> str:
        """Generate SwiftUI view code"""
        view_name = description.replace(' ', '').title() + "View"
        
        return f"""
import SwiftUI

struct {view_name}: View {{
    var body: some View {{
        VStack {{
            Text("{description}")
                .font(.title)
                .padding()
            
            // TODO: Implement {description} functionality
        }}
        .navigationTitle("{description}")
    }}
}}

struct {view_name}_Previews: PreviewProvider {{
    static var previews: some View {{
        {view_name}()
    }}
}}
"""
    
    async def _generate_data_model(self, description: str, framework: str, style: str) -> str:
        """Generate data model code"""
        model_name = description.replace(' ', '').title()
        
        if framework == "CoreData":
            return f"""
import CoreData
import Foundation

@objc({model_name})
public class {model_name}: NSManagedObject {{
    // TODO: Add Core Data properties for {description}
}}

extension {model_name} {{
    @nonobjc public class func fetchRequest() -> NSFetchRequest<{model_name}> {{
        return NSFetchRequest<{model_name}>(entityName: "{model_name}")
    }}
    
    // TODO: Add @NSManaged properties
}}
"""
        else:
            return f"""
import Foundation

struct {model_name}: Codable, Identifiable {{
    let id = UUID()
    
    // TODO: Add properties for {description}
    
    init() {{
        // TODO: Initialize properties
    }}
}}
"""
    
    async def _generate_swift_class(self, description: str, framework: str, style: str) -> str:
        """Generate Swift class code"""
        class_name = description.replace(' ', '').title()
        
        return f"""
import Foundation

class {class_name} {{
    // MARK: - Properties
    
    // TODO: Add properties for {description}
    
    // MARK: - Initialization
    
    init() {{
        // TODO: Initialize {description}
    }}
    
    // MARK: - Methods
    
    // TODO: Add methods for {description}
}}
"""
    
    async def _generate_swift_struct(self, description: str, framework: str, style: str) -> str:
        """Generate Swift struct code"""
        struct_name = description.replace(' ', '').title()
        
        return f"""
import Foundation

struct {struct_name} {{
    // TODO: Add properties for {description}
    
    init() {{
        // TODO: Initialize {description}
    }}
    
    // TODO: Add methods for {description}
}}
"""
    
    async def _generate_swift_enum(self, description: str, framework: str, style: str) -> str:
        """Generate Swift enum code"""
        enum_name = description.replace(' ', '').title()
        
        return f"""
import Foundation

enum {enum_name} {{
    // TODO: Add cases for {description}
    
    // TODO: Add computed properties and methods
}}
"""
    
    async def _generate_swift_protocol(self, description: str, framework: str, style: str) -> str:
        """Generate Swift protocol code"""
        protocol_name = description.replace(' ', '').title() + "Protocol"
        
        return f"""
import Foundation

protocol {protocol_name} {{
    // TODO: Add requirements for {description}
}}
"""
    
    async def _generate_swift_function(self, description: str, framework: str, style: str) -> str:
        """Generate Swift function code"""
        function_name = description.lower().replace(' ', '_')
        
        return f"""
import Foundation

func {function_name}() {{
    // TODO: Implement {description}
}}
"""
    
    async def _generate_ios_screen(self, screen_type: str, components: List[str], 
                                  data_source: str, theme: str) -> str:
        """Generate iOS screen SwiftUI code"""
        screen_name = f"{screen_type.capitalize()}View"
        
        return f"""
import SwiftUI

struct {screen_name}: View {{
    var body: some View {{
        NavigationView {{
            VStack {{
                Text("{screen_type.capitalize()} Screen")
                    .font(.largeTitle)
                    .padding()
                
                // TODO: Add {', '.join(components)} components
                // Data source: {data_source}
                
                Spacer()
            }}
            .navigationTitle("{screen_type.capitalize()}")
        }}
    }}
}}
"""
    
    async def _create_project_structure(self, project_path: Path, template: str, 
                                       ui_framework: str, features: List[str]):
        """Create iOS project directory structure"""
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create basic structure
        (project_path / "Sources").mkdir(exist_ok=True)
        (project_path / "Tests").mkdir(exist_ok=True)
        (project_path / "Resources").mkdir(exist_ok=True)
        
        # Create main app file
        if template == "app":
            app_code = f"""
import SwiftUI

@main
struct {project_path.name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}
"""
            with open(project_path / "Sources" / f"{project_path.name}App.swift", 'w') as f:
                f.write(app_code)
    
    async def _generate_package_swift(self, project_name: str, template: str) -> str:
        """Generate Package.swift file"""
        return f"""
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "{project_name}",
    platforms: [
        .iOS(.v15),
        .macOS(.v12)
    ],
    products: [
        .library(
            name: "{project_name}",
            targets: ["{project_name}"]
        ),
    ],
    dependencies: [
        // Add package dependencies here
    ],
    targets: [
        .target(
            name: "{project_name}",
            dependencies: []
        ),
        .testTarget(
            name: "{project_name}Tests",
            dependencies: ["{project_name}"]
        ),
    ]
)
"""
    
    async def _generate_test_code(self, target_code: str, test_type: str, coverage_target: float) -> str:
        """Generate test code for target Swift code"""
        return f"""
import XCTest
@testable import SwiftAgent

final class Generated{test_type.capitalize()}Tests: XCTestCase {{
    
    override func setUpWithError() throws {{
        // Put setup code here
    }}
    
    override func tearDownWithError() throws {{
        // Put teardown code here
    }}
    
    func testExample() throws {{
        // TODO: Add {test_type} tests for target code
        // Target coverage: {coverage_target}%
    }}
    
    func testPerformanceExample() throws {{
        measure {{
            // TODO: Add performance tests
        }}
    }}
}}
"""
    
    async def _generate_docc_documentation(self, source_path: str, include_examples: bool) -> str:
        """Generate Swift-DocC documentation"""
        return f"""
# SwiftAgent Documentation

## Overview

Generated documentation for Swift code at: {source_path}

## Topics

### Getting Started
- <doc:QuickStart>
- <doc:Installation>

### API Reference
- <doc:Classes>
- <doc:Structs>
- <doc:Protocols>

{"### Examples" if include_examples else ""}
{"- <doc:CodeExamples>" if include_examples else ""}
{"- <doc:Tutorials>" if include_examples else ""}
"""
    
    async def _generate_markdown_documentation(self, source_path: str, include_examples: bool) -> str:
        """Generate Markdown documentation"""
        return f"""
# SwiftAgent Documentation

## Overview

This documentation covers the Swift code located at: `{source_path}`

## API Reference

### Classes

TODO: Document classes

### Structs

TODO: Document structs

### Protocols

TODO: Document protocols

{"## Examples" if include_examples else ""}

{"TODO: Add code examples" if include_examples else ""}
"""

# MCP Server integration
def register_mcp_tools():
    """Register tools with MCP server"""
    swift_agent = SwiftAgentMCP()
    return swift_agent.tools

if __name__ == "__main__":
    # Test the tools
    async def test_tools():
        agent = SwiftAgentMCP()
        
        # Test code generation
        result = await agent.swift_code_generation(
            description="user profile view",
            code_type="view",
            framework="SwiftUI"
        )
        print("Code Generation Result:", json.dumps(result, indent=2))
        
        # Test UI mockup
        result = await agent.ios_ui_mockup(
            screen_type="list",
            components=["navigation", "search", "cells"],
            theme="dark"
        )
        print("UI Mockup Result:", json.dumps(result, indent=2))
    
    asyncio.run(test_tools())
