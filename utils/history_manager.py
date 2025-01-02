from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3
import logging

class HistoryEntry:
    def __init__(self, 
                 query: str,
                 module: str,
                 timestamp: float = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.query = query
        self.module = module
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'module': self.module,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryEntry':
        return cls(
            query=data['query'],
            module=data['module'],
            timestamp=data['timestamp'],
            metadata=data.get('metadata', {})
        )

class HistoryManager:
    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self.db_path = Path.home() / '.omnibar' / 'history.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._setup_database()
        self.logger = logging.getLogger('HistoryManager')

    def _setup_database(self):
        """Initialize SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        module TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        metadata TEXT,
                        UNIQUE(query, module, timestamp)
                    )
                """)
                
                # Create indices
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON history(timestamp DESC)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_module 
                    ON history(module)
                """)
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error setting up database: {e}")
            raise

    def add_entry(self, entry: HistoryEntry):
        """Add a new history entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert new entry
                cursor.execute("""
                    INSERT INTO history (query, module, timestamp, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    entry.query,
                    entry.module,
                    entry.timestamp,
                    json.dumps(entry.metadata)
                ))
                
                # Remove old entries if exceeding max_entries
                cursor.execute("""
                    DELETE FROM history 
                    WHERE id IN (
                        SELECT id FROM history 
                        ORDER BY timestamp DESC 
                        LIMIT -1 OFFSET ?
                    )
                """, (self.max_entries,))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error adding history entry: {e}")

    def get_entries(self, 
                    limit: int = 100, 
                    offset: int = 0,
                    module: Optional[str] = None,
                    start_time: Optional[float] = None,
                    end_time: Optional[float] = None) -> List[HistoryEntry]:
        """Get history entries with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT query, module, timestamp, metadata FROM history WHERE 1=1"
                params = []
                
                if module:
                    query += " AND module = ?"
                    params.append(module)
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time)
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                return [
                    HistoryEntry(
                        query=row[0],
                        module=row[1],
                        timestamp=row[2],
                        metadata=json.loads(row[3]) if row[3] else None
                    )
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            self.logger.error(f"Error getting history entries: {e}")
            return []

    def search_history(self, 
                      search_term: str,
                      limit: int = 100) -> List[HistoryEntry]:
        """Search history entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT query, module, timestamp, metadata
                    FROM history
                    WHERE query LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (f"%{search_term}%", limit))
                
                return [
                    HistoryEntry(
                        query=row[0],
                        module=row[1],
                        timestamp=row[2],
                        metadata=json.loads(row[3]) if row[3] else None
                    )
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            self.logger.error(f"Error searching history: {e}")
            return []

    def get_recent_modules(self, days: int = 7) -> Dict[str, int]:
        """Get frequency of module usage in recent history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_time = time.time() - (days * 86400)
                cursor.execute("""
                    SELECT module, COUNT(*) as count
                    FROM history
                    WHERE timestamp >= ?
                    GROUP BY module
                    ORDER BY count DESC
                """, (start_time,))
                
                return dict(cursor.fetchall())
        except Exception as e:
            self.logger.error(f"Error getting module usage: {e}")
            return {}

    def get_popular_queries(self, 
                          limit: int = 10,
                          days: Optional[int] = None) -> List[tuple]:
        """Get most frequently used queries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT query, COUNT(*) as count
                    FROM history
                """
                
                params = []
                if days is not None:
                    query += " WHERE timestamp >= ?"
                    params.append(time.time() - (days * 86400))
                
                query += """
                    GROUP BY query
                    ORDER BY count DESC
                    LIMIT ?
                """
                params.append(limit)
                
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error getting popular queries: {e}")
            return []

    def clear_history(self, 
                     before_date: Optional[float] = None,
                     module: Optional[str] = None):
        """Clear history entries with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "DELETE FROM history WHERE 1=1"
                params = []
                
                if before_date:
                    query += " AND timestamp < ?"
                    params.append(before_date)
                
                if module:
                    query += " AND module = ?"
                    params.append(module)
                
                cursor.execute(query, params)
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error clearing history: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get history statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total entries
                cursor.execute("SELECT COUNT(*) FROM history")
                stats['total_entries'] = cursor.fetchone()[0]
                
                # Entries per module
                cursor.execute("""
                    SELECT module, COUNT(*) as count
                    FROM history
                    GROUP BY module
                """)
                stats['entries_per_module'] = dict(cursor.fetchall())
                
                # Date range
                cursor.execute("""
                    SELECT MIN(timestamp), MAX(timestamp)
                    FROM history
                """)
                min_time, max_time = cursor.fetchone()
                stats['date_range'] = {
                    'start': datetime.fromtimestamp(min_time).isoformat() if min_time else None,
                    'end': datetime.fromtimestamp(max_time).isoformat() if max_time else None
                }
                
                return stats
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}

    def export_history(self, output_path: Path):
        """Export history to JSON file"""
        try:
            entries = self.get_entries(limit=self.max_entries)
            
            with open(output_path, 'w') as f:
                json.dump(
                    [entry.to_dict() for entry in entries],
                    f,
                    indent=2
                )
        except Exception as e:
            self.logger.error(f"Error exporting history: {e}")
            raise

    def import_history(self, input_path: Path):
        """Import history from JSON file"""
        try:
            with open(input_path, 'r') as f:
                entries_data = json.load(f)
            
            # Clear existing history first
            self.clear_history()
            
            # Import entries
            for entry_data in entries_data:
                entry = HistoryEntry.from_dict(entry_data)
                self.add_entry(entry)
                
        except Exception as e:
            self.logger.error(f"Error importing history: {e}")
            raise

    def cleanup(self):
        """Cleanup old entries and optimize database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove entries older than 1 year
                old_time = time.time() - (365 * 86400)
                cursor.execute(
                    "DELETE FROM history WHERE timestamp < ?",
                    (old_time,)
                )
                
                # Optimize database
                cursor.execute("VACUUM")
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def get_suggestions(self, partial_query: str, 
                       limit: int = 5) -> List[HistoryEntry]:
        """Get suggestions based on partial query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT query, module, timestamp, metadata, COUNT(*) as count
                    FROM history
                    WHERE query LIKE ?
                    GROUP BY query
                    ORDER BY count DESC, timestamp DESC
                    LIMIT ?
                """, (f"{partial_query}%", limit))
                
                return [
                    HistoryEntry(
                        query=row[0],
                        module=row[1],
                        timestamp=row[2],
                        metadata=json.loads(row[3]) if row[3] else None
                    )
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            self.logger.error(f"Error getting suggestions: {e}")
            return []

    def merge_duplicates(self):
        """Merge duplicate entries while preserving timestamps"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find and merge duplicates
                cursor.execute("""
                    DELETE FROM history 
                    WHERE id NOT IN (
                        SELECT MIN(id)
                        FROM history
                        GROUP BY query, module, date(timestamp)
                    )
                """)
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error merging duplicates: {e}")

    def optimize_database(self):
        """Perform database optimization"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove unused space
                cursor.execute("VACUUM")
                
                # Rebuild indices
                cursor.execute("REINDEX")
                
                # Analyze tables for query optimization
                cursor.execute("ANALYZE")
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error optimizing database: {e}")