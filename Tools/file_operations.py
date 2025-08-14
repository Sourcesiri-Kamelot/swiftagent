#!/usr/bin/env python3
"""
SwiftAgent Toolkit - Secure File Operations
Provides safe file read/write operations with permission management
"""

import os
import json
import hashlib
import mimetypes
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class FilePermission(Enum):
    """File operation permissions"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    CREATE = "create"

class FileType(Enum):
    """Supported file types"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    CODE = "code"
    DATA = "data"
    BINARY = "binary"
    ARCHIVE = "archive"

@dataclass
class FileInfo:
    """File information structure"""
    path: str
    name: str
    size: int
    type: FileType
    mime_type: str
    permissions: List[FilePermission]
    is_safe: bool
    encoding: Optional[str] = None
    hash: Optional[str] = None

@dataclass
class FileOperationResult:
    """Result of file operation"""
    success: bool
    message: str
    data: Optional[Any] = None
    file_info: Optional[FileInfo] = None

class SecurityManager:
    """Manages file operation security"""
    
    def __init__(self):
        # Safe directories (can be configured by user)
        self.safe_directories = [
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Desktop"),
            "/tmp",
            "/workspace"  # Common workspace directory
        ]
        
        # Dangerous file extensions
        self.dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif',
            '.sh', '.bash', '.zsh', '.fish', '.ps1',
            '.vbs', '.js', '.jar', '.app', '.deb', '.rpm'
        }
        
        # Safe text file extensions
        self.text_extensions = {
            '.txt', '.md', '.json', '.yaml', '.yml', '.xml',
            '.csv', '.tsv', '.log', '.ini', '.cfg', '.conf'
        }
        
        # Code file extensions
        self.code_extensions = {
            '.py', '.js', '.ts', '.html', '.css', '.java',
            '.cpp', '.c', '.h', '.go', '.rs', '.php',
            '.rb', '.swift', '.kt', '.scala', '.r'
        }
        
        # Image file extensions
        self.image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
            '.webp', '.tiff', '.tif', '.ico'
        }
        
        # Document file extensions
        self.document_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.ppt', '.pptx', '.rtf', '.odt', '.ods', '.odp'
        }
    
    def is_safe_path(self, file_path: str) -> bool:
        """Check if file path is safe to access"""
        try:
            path = Path(file_path).resolve()
            
            # Check if path is in safe directories
            for safe_dir in self.safe_directories:
                if str(path).startswith(str(Path(safe_dir).resolve())):
                    return True
            
            # Check for path traversal attempts
            if '..' in str(path) or str(path).startswith('/'):
                logger.warning(f"Potential path traversal: {file_path}")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking path safety: {e}")
            return False
    
    def is_safe_extension(self, file_path: str) -> bool:
        """Check if file extension is safe"""
        extension = Path(file_path).suffix.lower()
        return extension not in self.dangerous_extensions
    
    def get_file_type(self, file_path: str) -> FileType:
        """Determine file type from extension"""
        extension = Path(file_path).suffix.lower()
        
        if extension in self.text_extensions:
            return FileType.TEXT
        elif extension in self.code_extensions:
            return FileType.CODE
        elif extension in self.image_extensions:
            return FileType.IMAGE
        elif extension in self.document_extensions:
            return FileType.DOCUMENT
        elif extension in {'.json', '.xml', '.csv', '.yml', '.yaml'}:
            return FileType.DATA
        elif extension in {'.zip', '.tar', '.gz', '.rar', '.7z'}:
            return FileType.ARCHIVE
        else:
            return FileType.BINARY
    
    def get_permissions(self, file_path: str) -> List[FilePermission]:
        """Get allowed permissions for file"""
        permissions = []
        
        if self.is_safe_path(file_path) and self.is_safe_extension(file_path):
            permissions.extend([
                FilePermission.READ,
                FilePermission.WRITE,
                FilePermission.CREATE
            ])
            
            # Only allow deletion for certain file types
            file_type = self.get_file_type(file_path)
            if file_type in [FileType.TEXT, FileType.CODE, FileType.DATA]:
                permissions.append(FilePermission.DELETE)
        
        return permissions

class FileOperations:
    """Secure file operations manager"""
    
    def __init__(self):
        self.security = SecurityManager()
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.encoding_fallbacks = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
    
    def get_file_info(self, file_path: str) -> FileInfo:
        """Get comprehensive file information"""
        path = Path(file_path)
        
        # Basic file info
        size = path.stat().st_size if path.exists() else 0
        mime_type, _ = mimetypes.guess_type(str(path))
        file_type = self.security.get_file_type(file_path)
        permissions = self.security.get_permissions(file_path)
        is_safe = self.security.is_safe_path(file_path) and self.security.is_safe_extension(file_path)
        
        # Generate file hash for integrity
        file_hash = None
        if path.exists() and size < self.max_file_size:
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                    file_hash = hashlib.sha256(content).hexdigest()[:16]
            except Exception:
                pass
        
        return FileInfo(
            path=str(path),
            name=path.name,
            size=size,
            type=file_type,
            mime_type=mime_type or "application/octet-stream",
            permissions=permissions,
            is_safe=is_safe,
            hash=file_hash
        )
    
    def read_file(self, file_path: str, encoding: Optional[str] = None) -> FileOperationResult:
        """Read file content safely"""
        try:
            file_info = self.get_file_info(file_path)
            
            if not file_info.is_safe:
                return FileOperationResult(
                    success=False,
                    message="File access denied: unsafe path or file type",
                    file_info=file_info
                )
            
            if FilePermission.READ not in file_info.permissions:
                return FileOperationResult(
                    success=False,
                    message="File access denied: no read permission",
                    file_info=file_info
                )
            
            path = Path(file_path)
            if not path.exists():
                return FileOperationResult(
                    success=False,
                    message="File not found",
                    file_info=file_info
                )
            
            if file_info.size > self.max_file_size:
                return FileOperationResult(
                    success=False,
                    message=f"File too large: {file_info.size} bytes (max: {self.max_file_size})",
                    file_info=file_info
                )
            
            # Handle different file types
            if file_info.type == FileType.BINARY:
                # Read binary files as base64
                with open(path, 'rb') as f:
                    import base64
                    content = base64.b64encode(f.read()).decode('ascii')
                    return FileOperationResult(
                        success=True,
                        message=f"Binary file read successfully (base64 encoded)",
                        data=content,
                        file_info=file_info
                    )
            
            # Try to read as text with encoding detection
            content = None
            used_encoding = encoding
            
            if encoding:
                encodings_to_try = [encoding]
            else:
                encodings_to_try = self.encoding_fallbacks
            
            for enc in encodings_to_try:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        content = f.read()
                        used_encoding = enc
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return FileOperationResult(
                    success=False,
                    message="Could not decode file with any supported encoding",
                    file_info=file_info
                )
            
            file_info.encoding = used_encoding
            
            return FileOperationResult(
                success=True,
                message=f"File read successfully ({used_encoding} encoding)",
                data=content,
                file_info=file_info
            )
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                message=f"Error reading file: {str(e)}"
            )
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', 
                   create_dirs: bool = True) -> FileOperationResult:
        """Write content to file safely"""
        try:
            file_info = self.get_file_info(file_path)
            
            if not file_info.is_safe:
                return FileOperationResult(
                    success=False,
                    message="File access denied: unsafe path or file type",
                    file_info=file_info
                )
            
            path = Path(file_path)
            
            # Check permissions
            if path.exists():
                if FilePermission.WRITE not in file_info.permissions:
                    return FileOperationResult(
                        success=False,
                        message="File access denied: no write permission",
                        file_info=file_info
                    )
            else:
                if FilePermission.CREATE not in file_info.permissions:
                    return FileOperationResult(
                        success=False,
                        message="File access denied: no create permission",
                        file_info=file_info
                    )
            
            # Create directories if needed
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if file exists
            backup_path = None
            if path.exists():
                backup_path = path.with_suffix(path.suffix + '.backup')
                shutil.copy2(path, backup_path)
            
            try:
                # Write content
                with open(path, 'w', encoding=encoding) as f:
                    f.write(content)
                
                # Update file info
                file_info = self.get_file_info(file_path)
                file_info.encoding = encoding
                
                return FileOperationResult(
                    success=True,
                    message=f"File written successfully ({len(content)} characters)",
                    file_info=file_info
                )
                
            except Exception as e:
                # Restore backup if write failed
                if backup_path and backup_path.exists():
                    shutil.copy2(backup_path, path)
                raise e
            
            finally:
                # Clean up backup
                if backup_path and backup_path.exists():
                    backup_path.unlink()
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                message=f"Error writing file: {str(e)}"
            )
    
    def list_directory(self, dir_path: str, recursive: bool = False, 
                      include_hidden: bool = False) -> FileOperationResult:
        """List directory contents safely"""
        try:
            if not self.security.is_safe_path(dir_path):
                return FileOperationResult(
                    success=False,
                    message="Directory access denied: unsafe path"
                )
            
            path = Path(dir_path)
            if not path.exists():
                return FileOperationResult(
                    success=False,
                    message="Directory not found"
                )
            
            if not path.is_dir():
                return FileOperationResult(
                    success=False,
                    message="Path is not a directory"
                )
            
            files = []
            
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for item in path.glob(pattern):
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                file_info = self.get_file_info(str(item))
                files.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': file_info.size,
                    'file_type': file_info.type.value,
                    'is_safe': file_info.is_safe,
                    'permissions': [p.value for p in file_info.permissions]
                })
            
            # Sort files: directories first, then by name
            files.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
            
            return FileOperationResult(
                success=True,
                message=f"Listed {len(files)} items",
                data=files
            )
            
        except Exception as e:
            logger.error(f"Error listing directory {dir_path}: {e}")
            return FileOperationResult(
                success=False,
                message=f"Error listing directory: {str(e)}"
            )
    
    def delete_file(self, file_path: str, confirm: bool = False) -> FileOperationResult:
        """Delete file safely"""
        try:
            file_info = self.get_file_info(file_path)
            
            if not file_info.is_safe:
                return FileOperationResult(
                    success=False,
                    message="File access denied: unsafe path or file type",
                    file_info=file_info
                )
            
            if FilePermission.DELETE not in file_info.permissions:
                return FileOperationResult(
                    success=False,
                    message="File access denied: no delete permission",
                    file_info=file_info
                )
            
            if not confirm:
                return FileOperationResult(
                    success=False,
                    message="Deletion requires explicit confirmation",
                    file_info=file_info
                )
            
            path = Path(file_path)
            if not path.exists():
                return FileOperationResult(
                    success=False,
                    message="File not found",
                    file_info=file_info
                )
            
            # Move to trash directory instead of permanent deletion
            trash_dir = Path.home() / ".swiftagent_trash"
            trash_dir.mkdir(exist_ok=True)
            
            import time
            timestamp = int(time.time())
            trash_path = trash_dir / f"{path.name}_{timestamp}"
            
            shutil.move(str(path), str(trash_path))
            
            return FileOperationResult(
                success=True,
                message=f"File moved to trash: {trash_path}",
                data=str(trash_path),
                file_info=file_info
            )
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                message=f"Error deleting file: {str(e)}"
            )
    
    def search_files(self, directory: str, pattern: str, content_search: bool = False) -> FileOperationResult:
        """Search for files by name or content"""
        try:
            if not self.security.is_safe_path(directory):
                return FileOperationResult(
                    success=False,
                    message="Directory access denied: unsafe path"
                )
            
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return FileOperationResult(
                    success=False,
                    message="Invalid directory path"
                )
            
            results = []
            
            # Search by filename
            for item in path.rglob(f"*{pattern}*"):
                if item.is_file():
                    file_info = self.get_file_info(str(item))
                    if file_info.is_safe:
                        results.append({
                            'path': str(item),
                            'name': item.name,
                            'type': 'filename_match',
                            'size': file_info.size,
                            'file_type': file_info.type.value
                        })
            
            # Search file contents if requested
            if content_search:
                for item in path.rglob("*"):
                    if item.is_file():
                        file_info = self.get_file_info(str(item))
                        if (file_info.is_safe and 
                            file_info.type in [FileType.TEXT, FileType.CODE, FileType.DATA] and
                            file_info.size < 1024 * 1024):  # 1MB limit for content search
                            
                            try:
                                result = self.read_file(str(item))
                                if result.success and pattern.lower() in result.data.lower():
                                    results.append({
                                        'path': str(item),
                                        'name': item.name,
                                        'type': 'content_match',
                                        'size': file_info.size,
                                        'file_type': file_info.type.value
                                    })
                            except Exception:
                                continue
            
            return FileOperationResult(
                success=True,
                message=f"Found {len(results)} matches",
                data=results
            )
            
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return FileOperationResult(
                success=False,
                message=f"Error searching files: {str(e)}"
            )

# Global instance
file_ops = FileOperations()

# Convenience functions for simple usage
def read_file(path: str) -> str:
    """Simple file reading for beginners"""
    result = file_ops.read_file(path)
    if result.success:
        return result.data
    else:
        raise Exception(result.message)

def write_file(path: str, content: str):
    """Simple file writing for beginners"""
    result = file_ops.write_file(path, content)
    if not result.success:
        raise Exception(result.message)

def list_files(directory: str) -> List[Dict]:
    """Simple directory listing for beginners"""
    result = file_ops.list_directory(directory)
    if result.success:
        return result.data
    else:
        raise Exception(result.message)

if __name__ == "__main__":
    # Example usage
    ops = FileOperations()
    
    # Test reading a file
    result = ops.read_file("test.txt")
    print(f"Read result: {result.message}")
    
    # Test writing a file
    result = ops.write_file("test_output.txt", "Hello from SwiftAgent Toolkit!")
    print(f"Write result: {result.message}")
    
    # Test listing directory
    result = ops.list_directory(".")
    print(f"Directory listing: {len(result.data) if result.success else 'Failed'}")