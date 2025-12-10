"""
Supabase Database Manager
Handles all database operations for the orchestrator
"""

import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from loguru import logger
import yaml


class SupabaseManager:
    """Manages all Supabase database operations"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.client: Client = create_client(url, key)
        self._load_projects_config()
    
    def _load_projects_config(self):
        """Load projects configuration from YAML"""
        config_path = os.path.join(os.path.dirname(__file__), "config", "projects.yaml")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.projects_config = yaml.safe_load(f)
        else:
            self.projects_config = {}
    
    # ========== Projects ==========
    
    def get_project(self, project_key: str) -> Optional[Dict]:
        """Get a project by its key"""
        result = self.client.table("projects").select("*").eq("project_key", project_key).execute()
        return result.data[0] if result.data else None
    
    def get_all_projects(self) -> List[Dict]:
        """Get all projects"""
        result = self.client.table("projects").select("*").order("priority").execute()
        return result.data
    
    def create_project(self, project_key: str, name: str, project_type: str, 
                       status: str = "active", priority: str = "medium",
                       description: str = "", current_focus: str = "") -> Dict:
        """Create a new project"""
        data = {
            "project_key": project_key,
            "name": name,
            "type": project_type,
            "status": status,
            "priority": priority,
            "description": description,
            "current_focus": current_focus
        }
        result = self.client.table("projects").insert(data).execute()
        logger.info(f"Created project: {project_key}")
        return result.data[0]
    
    def update_project(self, project_key: str, updates: Dict) -> Optional[Dict]:
        """Update a project"""
        updates["updated_at"] = datetime.now().isoformat()
        result = self.client.table("projects").update(updates).eq("project_key", project_key).execute()
        if result.data:
            logger.info(f"Updated project: {project_key}")
        return result.data[0] if result.data else None
    
    def sync_projects_from_config(self):
        """Sync projects from YAML config to database"""
        if not self.projects_config.get("projects"):
            logger.warning("No projects in config")
            return
        
        for key, config in self.projects_config["projects"].items():
            existing = self.get_project(key)
            if existing:
                self.update_project(key, {
                    "name": config["name"],
                    "type": config["type"],
                    "status": config["status"],
                    "priority": config["priority"],
                    "description": config.get("description", ""),
                    "current_focus": config.get("current_focus", "")
                })
            else:
                self.create_project(
                    project_key=key,
                    name=config["name"],
                    project_type=config["type"],
                    status=config["status"],
                    priority=config["priority"],
                    description=config.get("description", ""),
                    current_focus=config.get("current_focus", "")
                )
        logger.info("Projects synced from config")
    
    # ========== Tasks ==========
    
    def get_tasks(self, project_key: Optional[str] = None, 
                  status: Optional[str] = None) -> List[Dict]:
        """Get tasks, optionally filtered by project and/or status"""
        query = self.client.table("tasks").select("*, projects(project_key, name)")
        
        if project_key:
            # First get project ID
            project = self.get_project(project_key)
            if project:
                query = query.eq("project_id", project["id"])
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("priority").order("created_at", desc=True).execute()
        return result.data
    
    def get_pending_tasks(self, project_key: Optional[str] = None) -> List[Dict]:
        """Get all pending tasks"""
        return self.get_tasks(project_key=project_key, status="pending")
    
    def create_task(self, project_key: str, title: str, 
                    description: str = "", priority: str = "medium",
                    assigned_to: Optional[str] = None,
                    due_date: Optional[datetime] = None) -> Optional[Dict]:
        """Create a new task"""
        project = self.get_project(project_key)
        if not project:
            logger.error(f"Project not found: {project_key}")
            return None
        
        data = {
            "project_id": project["id"],
            "title": title,
            "description": description,
            "priority": priority,
            "status": "pending",
            "assigned_to": assigned_to,
            "due_date": due_date.isoformat() if due_date else None
        }
        result = self.client.table("tasks").insert(data).execute()
        logger.info(f"Created task: {title} for {project_key}")
        return result.data[0] if result.data else None
    
    def update_task(self, task_id: str, updates: Dict) -> Optional[Dict]:
        """Update a task"""
        result = self.client.table("tasks").update(updates).eq("id", task_id).execute()
        return result.data[0] if result.data else None
    
    def complete_task(self, task_id: str) -> Optional[Dict]:
        """Mark a task as completed"""
        updates = {
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }
        result = self.update_task(task_id, updates)
        if result:
            logger.info(f"Completed task: {task_id}")
        return result
    
    # ========== Conversations (OpenAI Threads) ==========
    
    def create_conversation(self, thread_id: str, assistant_id: str,
                           assistant_name: str, project_id: Optional[str] = None,
                           context: str = "") -> Dict:
        """Create a new conversation record"""
        data = {
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "assistant_name": assistant_name,
            "project_id": project_id,
            "context": context
        }
        result = self.client.table("conversations").insert(data).execute()
        return result.data[0]
    
    def get_conversation(self, thread_id: str) -> Optional[Dict]:
        """Get conversation by thread ID"""
        result = self.client.table("conversations").select("*").eq("thread_id", thread_id).execute()
        return result.data[0] if result.data else None
    
    def update_conversation_activity(self, thread_id: str):
        """Update last activity timestamp"""
        self.client.table("conversations").update({
            "last_activity": datetime.now().isoformat()
        }).eq("thread_id", thread_id).execute()
    
    # ========== Messages ==========
    
    def log_message(self, conversation_id: str, role: str, content: str) -> Dict:
        """Log a message in a conversation"""
        data = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content
        }
        result = self.client.table("messages").insert(data).execute()
        return result.data[0]
    
    def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict]:
        """Get messages for a conversation"""
        result = self.client.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at", desc=True).limit(limit).execute()
        return result.data
    
    # ========== Progress Log ==========
    
    def log_progress(self, project_key: str, event_type: str, 
                     description: str, metadata: Optional[Dict] = None) -> Optional[Dict]:
        """Log a progress event"""
        project = self.get_project(project_key)
        if not project:
            logger.error(f"Project not found: {project_key}")
            return None
        
        data = {
            "project_id": project["id"],
            "event_type": event_type,
            "description": description,
            "metadata": metadata or {}
        }
        result = self.client.table("progress_log").insert(data).execute()
        logger.info(f"Logged progress for {project_key}: {event_type}")
        return result.data[0] if result.data else None
    
    def get_progress(self, project_key: Optional[str] = None, 
                     days: int = 7) -> List[Dict]:
        """Get progress log entries"""
        query = self.client.table("progress_log").select("*, projects(project_key, name)")
        
        if project_key:
            project = self.get_project(project_key)
            if project:
                query = query.eq("project_id", project["id"])
        
        # Filter by date (last N days)
        from_date = (datetime.now() - timedelta(days=days)).isoformat()
        query = query.gte("created_at", from_date)
        
        result = query.order("created_at", desc=True).execute()
        return result.data
    
    # ========== Daily Summaries ==========
    
    def create_daily_summary(self, summary: str, projects_status: Dict,
                            tasks_completed: int = 0, tasks_created: int = 0) -> Dict:
        """Create or update daily summary"""
        today = date.today().isoformat()
        
        # Check if summary exists for today
        existing = self.client.table("daily_summaries").select("*").eq("date", today).execute()
        
        data = {
            "date": today,
            "summary": summary,
            "projects_status": projects_status,
            "tasks_completed": tasks_completed,
            "tasks_created": tasks_created
        }
        
        if existing.data:
            result = self.client.table("daily_summaries").update(data).eq("date", today).execute()
        else:
            result = self.client.table("daily_summaries").insert(data).execute()
        
        return result.data[0]
    
    def get_daily_summary(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """Get daily summary"""
        target = (target_date or date.today()).isoformat()
        result = self.client.table("daily_summaries").select("*").eq("date", target).execute()
        return result.data[0] if result.data else None
    
    # ========== Assistants Registry ==========
    
    def register_assistant(self, assistant_id: str, name: str, role: str,
                          project_key: Optional[str] = None,
                          instructions: str = "") -> Dict:
        """Register an OpenAI assistant"""
        data = {
            "assistant_id": assistant_id,
            "name": name,
            "role": role,
            "project_key": project_key,
            "instructions": instructions,
            "is_active": True
        }
        result = self.client.table("assistants").upsert(data, on_conflict="assistant_id").execute()
        logger.info(f"Registered assistant: {name}")
        return result.data[0]
    
    def get_assistant(self, assistant_id: str) -> Optional[Dict]:
        """Get assistant by OpenAI ID"""
        result = self.client.table("assistants").select("*").eq("assistant_id", assistant_id).execute()
        return result.data[0] if result.data else None
    
    def get_all_assistants(self, active_only: bool = True) -> List[Dict]:
        """Get all registered assistants"""
        query = self.client.table("assistants").select("*")
        if active_only:
            query = query.eq("is_active", True)
        result = query.execute()
        return result.data
    
    # ========== Utility Methods ==========
    
    def get_project_with_tasks(self, project_key: str) -> Optional[Dict]:
        """Get a project with its pending tasks"""
        project = self.get_project(project_key)
        if not project:
            return None
        
        tasks = self.get_pending_tasks(project_key)
        project["tasks"] = tasks
        return project
    
    def get_today_focus(self) -> Dict:
        """Get today's focus based on config and status"""
        focus = {
            "week_focus": self.projects_config.get("focus_this_week", []),
            "time_allocation": self.projects_config.get("time_allocation", {}),
            "high_priority_tasks": [],
            "projects_needing_attention": []
        }
        
        # Get high priority pending tasks
        all_tasks = self.get_tasks(status="pending")
        focus["high_priority_tasks"] = [
            t for t in all_tasks if t.get("priority") == "high"
        ][:5]
        
        # Get projects with high priority
        projects = self.get_all_projects()
        focus["projects_needing_attention"] = [
            p for p in projects if p.get("priority") == "high"
        ]
        
        return focus


# Import missing
from datetime import timedelta


# Singleton instance
_manager: Optional[SupabaseManager] = None

def get_manager() -> SupabaseManager:
    """Get or create the Supabase manager singleton"""
    global _manager
    if _manager is None:
        _manager = SupabaseManager()
    return _manager

