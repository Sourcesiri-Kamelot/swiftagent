# SwiftAgent Toolkit - MCP Module
# This file makes the MCP directory a Python package

from .mcp_server import server, main

__all__ = [
    'server',
    'main'
] 