import sqlite3
import os
import json
from datetime import datetime

class MemoryManager:
    """
    Manages long-term memory for the Agentic Orchestrator and Neural Automater.
    Stores facts, user preferences, past executions, and synthesized knowledge.
    """
    def __init__(self, db_path="agent_memory.db"):
        self.db_path = os.path.join(os.getcwd(), db_path)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for memory storage."""
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.db.cursor()
        
        # Core memory items (Key-Value/JSON structure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                accessed_count INTEGER DEFAULT 0,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Interaction log (for short-term context/reflection)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                context_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.db.commit()

    def store_memory(self, category: str, key: str, content: str):
        """
        Store a piece of knowledge or preference.
        If the key exists, update it.
        """
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO memories (category, key, content)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET 
                content = excluded.content,
                timestamp = CURRENT_TIMESTAMP
        ''', (category, key, content))
        self.db.commit()

    def retrieve_memory(self, key: str) -> str:
        """Retrieve a specific memory by key, updating access stats."""
        cursor = self.db.cursor()
        cursor.execute('SELECT content FROM memories WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row:
            # Update access stats
            cursor.execute('''
                UPDATE memories 
                SET accessed_count = accessed_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE key = ?
            ''', (key,))
            self.db.commit()
            return row[0]
        return None

    def search_memories(self, category=None, keyword=None, limit=10):
        """Search memories by category or keyword in content/key."""
        cursor = self.db.cursor()
        query = "SELECT category, key, content FROM memories WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
            
        if keyword:
            query += " AND (content LIKE ? OR key LIKE ?)"
            params.append(f"%{keyword}%")
            params.append(f"%{keyword}%")
            
        query += " ORDER BY last_accessed DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "category": row[0],
                "key": row[1],
                "content": row[2]
            })
        return results

    def get_all_summarized(self, max_length=1500) -> str:
        """
        Returns a summarized block of all memories to inject 
        into the LLM context prompt.
        """
        memories = self.search_memories(limit=50) # top 50 recently accessed
        if not memories:
            return "No previous memories stored."
            
        summary = "--- LONG TERM MEMORY ---\n"
        for mem in memories:
            entry = f"[{mem['category']}] {mem['key']}: {mem['content']}\n"
            if len(summary) + len(entry) > max_length:
                summary += "... (truncated)"
                break
            summary += entry
            
        return summary

    def log_interaction(self, role: str, content: str, context_data: dict = None):
        """Log a recent interaction or agent thought process."""
        cursor = self.db.cursor()
        context_str = json.dumps(context_data) if context_data else None
        cursor.execute('''
            INSERT INTO interaction_log (role, content, context_data)
            VALUES (?, ?, ?)
        ''', (role, content, context_str))
        self.db.commit()

    def get_recent_interactions(self, limit=5):
        """Get the most recent thoughts/interactions"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT role, content, timestamp 
            FROM interaction_log 
            ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        # Return in chronological order
        return [{"role": r[0], "content": r[1], "time": r[2]} for r in reversed(rows)]
    
    def clear_memory(self, category=None):
        """Clear memories, optionally by category"""
        cursor = self.db.cursor()
        if category:
            cursor.execute("DELETE FROM memories WHERE category = ?", (category,))
        else:
            cursor.execute("DELETE FROM memories")
        self.db.commit()

# Example usage/singleton
memory_store = MemoryManager()
