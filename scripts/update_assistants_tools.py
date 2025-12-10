#!/usr/bin/env python3
"""
Update OpenAI Assistants with database tools
Run this once to add functions to all assistants
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Assistant IDs
ASSISTANTS = {
    "chief_of_staff": "asst_YNkTp9OaRExKr2wiOfEddC9Y",
    "deep_listening": "asst_8KgaIluAcNi8H6KtPr7VWes1",
    "lsrc_tech": "asst_VhubS5qiL248WeCTqADu4yBZ",
    "documentary": "asst_wASgEj7SQEDuLkCsQy5voGVL",
    "billboards_experiments": "asst_P4bSUVW1kAY3keK3Gt2Jk3Yf",
    "digital_presence": "asst_6Y5LPMYw9guLDgOB7lYr3B4O",
}

# Tools for Chief of Staff only
CREATE_TABLE_TOOL = {
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
                        },
                        "required": ["name", "type"]
                    },
                    "description": "Список колонок с типами"
                }
            },
            "required": ["table_name", "columns"]
        }
    }
}

# Tools for ALL agents
DATA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "insert_row",
            "description": "Добавить новую запись в таблицу базы данных",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Название таблицы (например: custom_festivals)"
                    },
                    "data": {
                        "type": "object",
                        "description": "Данные для добавления в виде {колонка: значение}"
                    }
                },
                "required": ["table_name", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_rows",
            "description": "Получить записи из таблицы базы данных",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Название таблицы"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Фильтры для поиска (опционально)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимум записей (по умолчанию 100)"
                    }
                },
                "required": ["table_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_row",
            "description": "Обновить существующую запись в таблице",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Название таблицы"
                    },
                    "row_id": {
                        "type": "string",
                        "description": "UUID записи для обновления"
                    },
                    "data": {
                        "type": "object",
                        "description": "Поля для обновления"
                    }
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
                    "table_name": {
                        "type": "string",
                        "description": "Название таблицы"
                    },
                    "row_id": {
                        "type": "string",
                        "description": "UUID записи для удаления"
                    }
                },
                "required": ["table_name", "row_id"]
            }
        }
    }
]


def update_assistant(assistant_id: str, name: str, is_chief: bool = False):
    """Update an assistant with database tools"""
    
    # Get current assistant to preserve existing tools
    assistant = client.beta.assistants.retrieve(assistant_id)
    
    # Get existing tools (keep code_interpreter, file_search, etc.)
    existing_tools = [t for t in assistant.tools if t.type != "function"]
    existing_functions = [t for t in assistant.tools if t.type == "function"]
    
    # Filter out our database functions if they already exist
    our_function_names = {"create_custom_table", "insert_row", "get_rows", "update_row", "delete_row"}
    other_functions = [t for t in existing_functions if t.function.name not in our_function_names]
    
    # Build new tools list
    new_tools = existing_tools + other_functions + DATA_TOOLS
    
    # Add create_table only for Chief of Staff
    if is_chief:
        new_tools.append(CREATE_TABLE_TOOL)
    
    # Update assistant
    client.beta.assistants.update(
        assistant_id,
        tools=new_tools
    )
    
    print(f"✅ {name}: добавлено {len(DATA_TOOLS) + (1 if is_chief else 0)} функций")


def main():
    print("\n🔧 Обновляю ассистентов с функциями базы данных...\n")
    
    for name, assistant_id in ASSISTANTS.items():
        is_chief = name == "chief_of_staff"
        try:
            update_assistant(assistant_id, name, is_chief)
        except Exception as e:
            print(f"❌ {name}: ошибка - {e}")
    
    print("\n✨ Готово! Все ассистенты обновлены.\n")
    print("Chief of Staff может создавать таблицы (create_custom_table)")
    print("Все агенты могут: insert_row, get_rows, update_row, delete_row\n")


if __name__ == "__main__":
    main()

