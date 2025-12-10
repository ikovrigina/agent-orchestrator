"""
Project Functions
Tools that assistants can use to manage projects
"""

import os
import yaml
from typing import Dict, Any, Optional
from loguru import logger


def load_projects_config() -> Dict:
    """Load projects configuration"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "config", 
        "projects.yaml"
    )
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_project_status(project_key: str) -> Dict[str, Any]:
    """
    Get current status and info for a specific project.
    Used by assistants to check project state.
    """
    config = load_projects_config()
    projects = config.get("projects", {})
    
    if project_key not in projects:
        return {
            "error": f"Project '{project_key}' not found",
            "available_projects": list(projects.keys())
        }
    
    project = projects[project_key]
    return {
        "project_key": project_key,
        "name": project.get("name"),
        "type": project.get("type"),
        "status": project.get("status"),
        "priority": project.get("priority"),
        "description": project.get("description"),
        "current_focus": project.get("current_focus"),
        "next_steps": project.get("next_steps", [])
    }


def get_all_projects_overview() -> Dict[str, Any]:
    """
    Get a brief overview of all projects.
    """
    config = load_projects_config()
    projects = config.get("projects", {})
    
    overview = {
        "total_projects": len(projects),
        "focus_this_week": config.get("focus_this_week", []),
        "time_allocation": config.get("time_allocation", {}),
        "projects": []
    }
    
    for key, project in projects.items():
        overview["projects"].append({
            "key": key,
            "name": project.get("name"),
            "status": project.get("status"),
            "priority": project.get("priority"),
            "current_focus": project.get("current_focus")
        })
    
    return overview


def get_today_focus() -> Dict[str, Any]:
    """
    Get suggested focus for today based on priorities.
    """
    config = load_projects_config()
    projects = config.get("projects", {})
    
    # Find high priority projects
    high_priority = [
        {"key": k, "name": v.get("name"), "focus": v.get("current_focus")}
        for k, v in projects.items()
        if v.get("priority") == "high"
    ]
    
    return {
        "focus_this_week": config.get("focus_this_week", []),
        "time_allocation": config.get("time_allocation", {}),
        "high_priority_projects": high_priority,
        "suggestion": "Focus on high-priority items first, then allocate time based on the time_allocation percentages."
    }


def log_progress(project_key: str, description: str, 
                 event_type: str = "note") -> Dict[str, Any]:
    """
    Log a progress update for a project.
    In production, this would write to Supabase.
    """
    logger.info(f"Progress logged for {project_key}: {description}")
    
    return {
        "status": "logged",
        "project_key": project_key,
        "event_type": event_type,
        "description": description
    }

