"""Short-term memory implementation for AgentCore."""

from typing import List, Dict, Any
from collections import defaultdict
import time


class ShortTermMemory:
    """Manages conversation history with short-term memory."""
    
    def __init__(self, max_messages: int = 20):
        """Initialize memory manager.
        
        Args:
            max_messages: Maximum messages to retain per session
        """
        self.max_messages = max_messages
        self.sessions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to session history.
        
        Args:
            session_id: Unique session identifier
            role: Message role (user/assistant)
            content: Message content
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
        }
        
        self.sessions[session_id].append(message)
        
        # Trim to max messages
        if len(self.sessions[session_id]) > self.max_messages:
            self.sessions[session_id] = self.sessions[session_id][-self.max_messages:]
    
    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of messages in chronological order
        """
        return self.sessions.get(session_id, [])
    
    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session.
        
        Args:
            session_id: Unique session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_context_window(self, session_id: str, num_messages: int = 5) -> str:
        """Get recent messages as formatted context.
        
        Args:
            session_id: Unique session identifier
            num_messages: Number of recent messages to include
            
        Returns:
            Formatted conversation context
        """
        history = self.get_history(session_id)
        recent = history[-num_messages:] if history else []
        
        return "\n".join([
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in recent
        ])
