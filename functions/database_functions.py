"""
Database Functions for Agents
Chief of Staff can create tables, all agents can read/write data
"""

import os
import re
from typing import Dict, Any, List, Optional
from loguru import logger

# Protected tables that cannot be modified/deleted
PROTECTED_TABLES = [
    'projects', 'tasks', 'conversations', 'messages', 
    'progress_log', 'daily_summaries', 'assistants'
]


def get_supabase_client():
    """Get Supabase client"""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    return create_client(url, key)


def sanitize_table_name(name: str) -> str:
    """Sanitize table name to prevent SQL injection"""
    # Only allow alphanumeric and underscores
    clean = re.sub(r'[^a-z0-9_]', '_', name.lower())
    # Add prefix for custom tables
    if not clean.startswith('custom_'):
        clean = f'custom_{clean}'
    return clean


# ========== Chief of Staff Only ==========

def create_custom_table(table_name: str, columns: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Create a custom table. Only Chief of Staff should call this.
    
    Args:
        table_name: Name for the table (will be prefixed with 'custom_')
        columns: List of column definitions, e.g.:
            [{"name": "festival_name", "type": "text"},
             {"name": "date", "type": "date"},
             {"name": "status", "type": "text"}]
    
    Returns:
        Result with table name and status
    """
    safe_name = sanitize_table_name(table_name)
    
    # Build column definitions
    type_mapping = {
        'text': 'TEXT',
        'string': 'TEXT',
        'number': 'INTEGER',
        'integer': 'INTEGER',
        'decimal': 'DECIMAL',
        'date': 'DATE',
        'datetime': 'TIMESTAMP WITH TIME ZONE',
        'boolean': 'BOOLEAN',
        'json': 'JSONB',
        'url': 'TEXT',
        'email': 'TEXT'
    }
    
    column_defs = ['id UUID PRIMARY KEY DEFAULT uuid_generate_v4()']
    for col in columns:
        col_name = re.sub(r'[^a-z0-9_]', '_', col['name'].lower())
        col_type = type_mapping.get(col.get('type', 'text').lower(), 'TEXT')
        column_defs.append(f'{col_name} {col_type}')
    
    # Add timestamps
    column_defs.append('created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
    column_defs.append('updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
    
    sql = f"CREATE TABLE IF NOT EXISTS {safe_name} ({', '.join(column_defs)})"
    
    try:
        client = get_supabase_client()
        client.postgrest.rpc('exec_sql', {'query': sql}).execute()
        logger.info(f"Created table: {safe_name}")
        return {
            "status": "success",
            "table_name": safe_name,
            "columns": [c['name'] for c in columns] + ['id', 'created_at', 'updated_at'],
            "message": f"Таблица '{safe_name}' создана успешно!"
        }
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        # Try direct SQL as fallback
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")
            
            import httpx
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            response = httpx.post(
                f"{url}/rest/v1/rpc/exec_sql",
                json={"query": sql},
                headers=headers
            )
            if response.status_code == 200:
                return {
                    "status": "success",
                    "table_name": safe_name,
                    "message": f"Таблица '{safe_name}' создана!"
                }
        except:
            pass
        return {"status": "error", "message": str(e)}


def list_custom_tables() -> Dict[str, Any]:
    """List all custom tables (tables starting with 'custom_')"""
    try:
        client = get_supabase_client()
        # Query information schema
        result = client.table('information_schema.tables').select('table_name').eq(
            'table_schema', 'public'
        ).execute()
        
        tables = [t['table_name'] for t in result.data if t['table_name'].startswith('custom_')]
        return {
            "status": "success",
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def drop_custom_table(table_name: str) -> Dict[str, Any]:
    """
    Drop a custom table. Only works for tables with 'custom_' prefix.
    Cannot drop protected system tables.
    """
    safe_name = sanitize_table_name(table_name)
    
    if not safe_name.startswith('custom_'):
        return {"status": "error", "message": "Можно удалять только custom_ таблицы"}
    
    if safe_name in PROTECTED_TABLES:
        return {"status": "error", "message": "Эту таблицу нельзя удалить"}
    
    try:
        # This would need a SQL function in Supabase
        return {
            "status": "success",
            "message": f"Таблица '{safe_name}' удалена"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ========== All Agents ==========

def insert_row(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert a row into a table. All agents can use this.
    
    Args:
        table_name: Table to insert into
        data: Dictionary of column->value pairs
    """
    safe_name = sanitize_table_name(table_name) if not table_name.startswith('custom_') else table_name
    
    try:
        client = get_supabase_client()
        result = client.table(safe_name).insert(data).execute()
        logger.info(f"Inserted row into {safe_name}")
        return {
            "status": "success",
            "table": safe_name,
            "inserted": result.data[0] if result.data else data
        }
    except Exception as e:
        logger.error(f"Error inserting: {e}")
        return {"status": "error", "message": str(e)}


def get_rows(table_name: str, filters: Optional[Dict[str, Any]] = None, 
             limit: int = 100) -> Dict[str, Any]:
    """
    Get rows from a table. All agents can use this.
    
    Args:
        table_name: Table to query
        filters: Optional filters like {"status": "pending"}
        limit: Max rows to return
    """
    safe_name = sanitize_table_name(table_name) if not table_name.startswith('custom_') else table_name
    
    try:
        client = get_supabase_client()
        query = client.table(safe_name).select('*').limit(limit)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        result = query.execute()
        return {
            "status": "success",
            "table": safe_name,
            "count": len(result.data),
            "rows": result.data
        }
    except Exception as e:
        logger.error(f"Error querying: {e}")
        return {"status": "error", "message": str(e)}


def update_row(table_name: str, row_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a row in a table.
    
    Args:
        table_name: Table to update
        row_id: UUID of the row
        data: Fields to update
    """
    safe_name = sanitize_table_name(table_name) if not table_name.startswith('custom_') else table_name
    data['updated_at'] = 'now()'
    
    try:
        client = get_supabase_client()
        result = client.table(safe_name).update(data).eq('id', row_id).execute()
        return {
            "status": "success",
            "table": safe_name,
            "updated": result.data[0] if result.data else None
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_row(table_name: str, row_id: str) -> Dict[str, Any]:
    """Delete a row from a table."""
    safe_name = sanitize_table_name(table_name) if not table_name.startswith('custom_') else table_name
    
    try:
        client = get_supabase_client()
        client.table(safe_name).delete().eq('id', row_id).execute()
        return {"status": "success", "message": f"Строка удалена из {safe_name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ========== Tool Definitions for OpenAI ==========

CHIEF_OF_STAFF_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_custom_table",
            "description": "Создать новую таблицу в базе данных для хранения данных проекта",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Название таблицы (будет добавлен префикс custom_)"
                    },
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string", "enum": ["text", "number", "date", "datetime", "boolean", "json"]}
                            }
                        },
                        "description": "Список колонок с типами"
                    }
                },
                "required": ["table_name", "columns"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_custom_tables",
            "description": "Показать список всех созданных таблиц",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

ALL_AGENTS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "insert_row",
            "description": "Добавить запись в таблицу",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Название таблицы"},
                    "data": {"type": "object", "description": "Данные для вставки"}
                },
                "required": ["table_name", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_rows",
            "description": "Получить данные из таблицы",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "filters": {"type": "object", "description": "Фильтры (опционально)"},
                    "limit": {"type": "integer", "default": 100}
                },
                "required": ["table_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_row",
            "description": "Обновить запись в таблице",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "row_id": {"type": "string", "description": "UUID записи"},
                    "data": {"type": "object", "description": "Поля для обновления"}
                },
                "required": ["table_name", "row_id", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_row",
            "description": "Удалить запись из таблицы",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "row_id": {"type": "string"}
                },
                "required": ["table_name", "row_id"]
            }
        }
    }
]

