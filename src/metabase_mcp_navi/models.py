"""
Data models for Metabase entities.
Provides type-safe representations of Metabase objects.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Database:
    """Represents a Metabase database connection."""
    id: int
    name: str
    engine: str
    description: Optional[str] = None
    tables: List["Table"] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Database":
        return cls(
            id=data["id"],
            name=data["name"],
            engine=data.get("engine", "unknown"),
            description=data.get("description")
        )


@dataclass
class Table:
    """Represents a database table in Metabase."""
    id: int
    name: str
    display_name: str
    schema: Optional[str] = None
    database_id: Optional[int] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Table":
        return cls(
            id=data["id"],
            name=data["name"],
            display_name=data.get("display_name", data["name"]),
            schema=data.get("schema"),
            database_id=data.get("db_id")
        )


@dataclass
class Card:
    """Represents a Metabase card (saved question)."""
    id: int
    name: str
    description: Optional[str] = None
    display: Optional[str] = None
    database_id: Optional[int] = None
    collection_id: Optional[int] = None
    query_type: Optional[str] = None
    creator_id: Optional[int] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Card":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            display=data.get("display"),
            database_id=data.get("database_id"),
            collection_id=data.get("collection_id"),
            query_type=data.get("query_type"),
            creator_id=data.get("creator_id")
        )


@dataclass
class Dashboard:
    """Represents a Metabase dashboard."""
    id: int
    name: str
    description: Optional[str] = None
    collection_id: Optional[int] = None
    creator_id: Optional[int] = None
    cards: List["DashboardCard"] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Dashboard":
        cards = []
        for dashcard in data.get("dashcards", data.get("ordered_cards", [])):
            if dashcard.get("card"):
                cards.append(DashboardCard.from_api(dashcard))
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            collection_id=data.get("collection_id"),
            creator_id=data.get("creator_id"),
            cards=cards,
            parameters=data.get("parameters", [])
        )


@dataclass
class DashboardCard:
    """Represents a card within a dashboard."""
    id: int
    card_id: int
    card_name: str
    row: int = 0
    col: int = 0
    size_x: int = 4
    size_y: int = 4
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "DashboardCard":
        card_data = data.get("card", {})
        return cls(
            id=data["id"],
            card_id=card_data.get("id", 0),
            card_name=card_data.get("name", "Unnamed"),
            row=data.get("row", 0),
            col=data.get("col", 0),
            size_x=data.get("size_x", 4),
            size_y=data.get("size_y", 4)
        )


@dataclass
class Collection:
    """Represents a Metabase collection."""
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Collection":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            parent_id=data.get("parent_id")
        )


@dataclass
class QueryResult:
    """Represents the result of a query execution."""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    running_time: Optional[int] = None  # milliseconds
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "QueryResult":
        result_data = data.get("data", data)
        cols = result_data.get("cols", [])
        columns = [c.get("display_name", c.get("name", f"col_{i}")) 
                   for i, c in enumerate(cols)]
        rows = result_data.get("rows", [])
        
        return cls(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            running_time=data.get("running_time")
        )
    
    def to_markdown_table(self, max_rows: int = 50) -> str:
        """Convert query result to markdown table."""
        if not self.columns:
            return "No results"
        
        # Header
        header = "| " + " | ".join(str(c) for c in self.columns) + " |"
        separator = "| " + " | ".join("---" for _ in self.columns) + " |"
        
        # Rows
        display_rows = self.rows[:max_rows]
        row_strings = []
        for row in display_rows:
            cells = [str(cell) if cell is not None else "NULL" for cell in row]
            # Truncate long cells
            cells = [c[:50] + "..." if len(c) > 50 else c for c in cells]
            row_strings.append("| " + " | ".join(cells) + " |")
        
        result = [header, separator] + row_strings
        
        if len(self.rows) > max_rows:
            result.append(f"\n*... {len(self.rows) - max_rows} more rows*")
        
        return "\n".join(result)
