#!/usr/bin/env python3
"""
SwiftAgent Toolkit - Memory System
Persistent memory for conversations, preferences, and learning
"""

import json
import logging
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """A single memory entry"""
    id: str
    timestamp: datetime
    type: str  # 'conversation', 'preference', 'learning', 'fact'
    content: Dict[str, Any]
    tags: List[str]
    importance: float  # 0.0 to 1.0
    access_count: int
    last_accessed: datetime

@dataclass
class ConversationMemory:
    """Conversation memory structure"""
    session_id: str
    user_id: str
    messages: List[Dict[str, str]]
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None

class MemorySystem:
    """Persistent memory system for SwiftAgent Toolkit"""
        self.name = name
        self.data_dir = os.path.expanduser("~/.config/swiftagent-toolkit/memory")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory storage files
        self.memories_file = self.data_dir / "memories.json"
        self.conversations_file = self.data_dir / "conversations.json"
        self.preferences_file = self.data_dir / "preferences.json"
        self.learning_file = self.data_dir / "learning.json"
        
        # In-memory cache
        self.memories: Dict[str, MemoryEntry] = {}
        self.conversations: Dict[str, ConversationMemory] = {}
        self.preferences: Dict[str, Any] = {}
        self.learning: Dict[str, Any] = {}
        
        # Load existing data
        self._load_memories()
        self._load_conversations()
        self._load_preferences()
        self._load_learning()
        
        logger.info(f"Memory system initialized with {len(self.memories)} memories")
    
    def _load_memories(self):
        """Load memories from disk"""
        try:
            if self.memories_file.exists():
                with open(self.memories_file, 'r') as f:
                    data = json.load(f)
                    for memory_data in data.values():
                        memory = MemoryEntry(
                            id=memory_data['id'],
                            timestamp=datetime.fromisoformat(memory_data['timestamp']),
                            type=memory_data['type'],
                            content=memory_data['content'],
                            tags=memory_data['tags'],
                            importance=memory_data['importance'],
                            access_count=memory_data['access_count'],
                            last_accessed=datetime.fromisoformat(memory_data['last_accessed'])
                        )
                        self.memories[memory.id] = memory
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
    
    def _save_memories(self):
        """Save memories to disk"""
        try:
            data = {}
            for memory in self.memories.values():
                data[memory.id] = {
                    'id': memory.id,
                    'timestamp': memory.timestamp.isoformat(),
                    'type': memory.type,
                    'content': memory.content,
                    'tags': memory.tags,
                    'importance': memory.importance,
                    'access_count': memory.access_count,
                    'last_accessed': memory.last_accessed.isoformat()
                }
            
            with open(self.memories_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memories: {e}")
    
    def _load_conversations(self):
        """Load conversations from disk"""
        try:
            if self.conversations_file.exists():
                with open(self.conversations_file, 'r') as f:
                    data = json.load(f)
                    for conv_data in data.values():
                        conversation = ConversationMemory(
                            session_id=conv_data['session_id'],
                            user_id=conv_data['user_id'],
                            messages=conv_data['messages'],
                            context=conv_data['context'],
                            created_at=datetime.fromisoformat(conv_data['created_at']),
                            updated_at=datetime.fromisoformat(conv_data['updated_at']),
                            summary=conv_data.get('summary')
                        )
                        self.conversations[conversation.session_id] = conversation
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")
    
    def _save_conversations(self):
        """Save conversations to disk"""
        try:
            data = {}
            for conversation in self.conversations.values():
                data[conversation.session_id] = {
                    'session_id': conversation.session_id,
                    'user_id': conversation.user_id,
                    'messages': conversation.messages,
                    'context': conversation.context,
                    'created_at': conversation.created_at.isoformat(),
                    'updated_at': conversation.updated_at.isoformat(),
                    'summary': conversation.summary
                }
            
            with open(self.conversations_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversations: {e}")
    
    def _load_preferences(self):
        """Load user preferences"""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r') as f:
                    self.preferences = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load preferences: {e}")
    
    def _save_preferences(self):
        """Save user preferences"""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def _load_learning(self):
        """Load learning data"""
        try:
            if self.learning_file.exists():
                with open(self.learning_file, 'r') as f:
                    self.learning = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load learning: {e}")
    
    def _save_learning(self):
        """Save learning data"""
        try:
            with open(self.learning_file, 'w') as f:
                json.dump(self.learning, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save learning: {e}")
    
    def add_memory(self, content: Dict[str, Any], memory_type: str = "conversation", 
                   tags: List[str] = None, importance: float = 0.5) -> str:
        """Add a new memory entry"""
        memory_id = hashlib.md5(f"{content}{datetime.now()}".encode()).hexdigest()
        
        memory = MemoryEntry(
            id=memory_id,
            timestamp=datetime.now(),
            type=memory_type,
            content=content,
            tags=tags or [],
            importance=importance,
            access_count=0,
            last_accessed=datetime.now()
        )
        
        self.memories[memory_id] = memory
        self._save_memories()
        
        logger.info(f"Added memory: {memory_id} ({memory_type})")
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a specific memory by ID"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            self._save_memories()
            return memory
        return None
    
    def search_memories(self, query: str, memory_type: str = None, 
                       limit: int = 10) -> List[MemoryEntry]:
        """Search memories by content or tags"""
        results = []
        
        for memory in self.memories.values():
            if memory_type and memory.type != memory_type:
                continue
            
            # Search in content
            content_str = json.dumps(memory.content, default=str).lower()
            if query.lower() in content_str:
                results.append(memory)
                continue
            
            # Search in tags
            if any(query.lower() in tag.lower() for tag in memory.tags):
                results.append(memory)
                continue
        
        # Sort by relevance (importance + recency)
        results.sort(key=lambda m: m.importance + (datetime.now() - m.last_accessed).days * 0.01, reverse=True)
        
        return results[:limit]
    
    def add_conversation(self, session_id: str, user_id: str, 
                        messages: List[Dict[str, str]], context: Dict[str, Any] = None):
        """Add or update a conversation"""
        conversation = ConversationMemory(
            session_id=session_id,
            user_id=user_id,
            messages=messages,
            context=context or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.conversations[session_id] = conversation
        self._save_conversations()
        
        # Also add as memory
        self.add_memory({
            'session_id': session_id,
            'user_id': user_id,
            'messages': messages[-5:],  # Last 5 messages
            'context': context
        }, memory_type="conversation", importance=0.7)
    
    def get_conversation(self, session_id: str) -> Optional[ConversationMemory]:
        """Get a conversation by session ID"""
        return self.conversations.get(session_id)
    
    def update_conversation(self, session_id: str, messages: List[Dict[str, str]], 
                          context: Dict[str, Any] = None):
        """Update an existing conversation"""
        if session_id in self.conversations:
            conversation = self.conversations[session_id]
            conversation.messages = messages
            if context:
                conversation.context.update(context)
            conversation.updated_at = datetime.now()
            self._save_conversations()
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference"""
        self.preferences[key] = value
        self._save_preferences()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.preferences.get(key, default)
    
    def add_learning(self, topic: str, content: Dict[str, Any]):
        """Add learning data"""
        if topic not in self.learning:
            self.learning[topic] = []
        
        self.learning[topic].append({
            'timestamp': datetime.now().isoformat(),
            'content': content
        })
        self._save_learning()
    
    def get_learning(self, topic: str) -> List[Dict[str, Any]]:
        """Get learning data for a topic"""
        return self.learning.get(topic, [])
    
    def get_context_for_query(self, query: str, user_id: str = None, 
                            limit: int = 5) -> Dict[str, Any]:
        """Get relevant context for a query"""
        context = {
            'memories': [],
            'conversations': [],
            'preferences': {},
            'learning': {}
        }
        
        # Search relevant memories
        memories = self.search_memories(query, limit=limit)
        context['memories'] = [asdict(m) for m in memories]
        
        # Get recent conversations for user
        if user_id:
            user_conversations = [
                conv for conv in self.conversations.values() 
                if conv.user_id == user_id
            ]
            user_conversations.sort(key=lambda c: c.updated_at, reverse=True)
            context['conversations'] = [asdict(c) for c in user_conversations[:3]]
        
        # Get relevant preferences
        query_words = query.lower().split()
        for key, value in self.preferences.items():
            if any(word in key.lower() for word in query_words):
                context['preferences'][key] = value
        
        # Get relevant learning
        for topic, learning_data in self.learning.items():
            if any(word in topic.lower() for word in query_words):
                context['learning'][topic] = learning_data[-3:]  # Last 3 entries
        
        return context
    
    def cleanup_old_memories(self, days: int = 30):
        """Clean up old memories to save space"""
        cutoff = datetime.now() - timedelta(days=days)
        old_memories = [
            memory_id for memory_id, memory in self.memories.items()
            if memory.timestamp < cutoff and memory.importance < 0.3
        ]
        
        for memory_id in old_memories:
            del self.memories[memory_id]
        
        self._save_memories()
        logger.info(f"Cleaned up {len(old_memories)} old memories")

# Global memory system instance
memory_system = MemorySystem() 