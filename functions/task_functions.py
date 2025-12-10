"""
Task Functions
Tools for managing tasks
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger


# In-memory task storage (in production, use Supabase)
_tasks: Dict[str, Dict] = {}


def create_task(project_key: str, title: str, 
                description: str = "", priority: str = "medium") -> Dict[str, Any]:
    """
    Create a new task for a project.
    """
    task_id = str(uuid.uuid4())
    
    task = {
        "id": task_id,
        "project_key": project_key,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    _tasks[task_id] = task
    logger.info(f"Created task: {title} for {project_key}")
    
    return {
        "status": "created",
        "task": task
    }


def complete_task(task_id: str) -> Dict[str, Any]:
    """
    Mark a task as completed.
    """
    if task_id not in _tasks:
        return {
            "status": "error",
            "message": f"Task {task_id} not found"
        }
    
    _tasks[task_id]["status"] = "completed"
    _tasks[task_id]["completed_at"] = datetime.now().isoformat()
    
    logger.info(f"Completed task: {task_id}")
    
    return {
        "status": "completed",
        "task": _tasks[task_id]
    }


def get_tasks(project_key: Optional[str] = None, 
              status: Optional[str] = None) -> Dict[str, Any]:
    """
    Get tasks, optionally filtered by project and/or status.
    """
    tasks = list(_tasks.values())
    
    if project_key:
        tasks = [t for t in tasks if t["project_key"] == project_key]
    
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    
    return {
        "count": len(tasks),
        "tasks": tasks
    }


def get_pending_tasks(project_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all pending tasks.
    """
    return get_tasks(project_key=project_key, status="pending")

