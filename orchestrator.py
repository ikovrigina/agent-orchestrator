"""
Agent Orchestrator
Manages communication between Chief of Staff and specialist agents
"""

import os
import json
import time
from typing import Optional, Dict, Any, Generator
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI
from loguru import logger
from dotenv import load_dotenv

from assistants_config import ASSISTANTS, CHIEF_OF_STAFF_ID, get_specialist_for_topic

load_dotenv()


class AgentRole(Enum):
    CHIEF_OF_STAFF = "chief_of_staff"
    DEEP_LISTENING = "deep_listening"
    LSRC_TECH = "lsrc_tech"
    DOCUMENTARY = "documentary"
    BILLBOARDS_EXPERIMENTS = "billboards_experiments"
    DIGITAL_PRESENCE = "digital_presence"


@dataclass
class AgentResponse:
    """Response from an agent"""
    agent_name: str
    content: str
    thread_id: str
    delegated_to: Optional[str] = None
    metadata: Optional[Dict] = None


class Orchestrator:
    """
    Main orchestrator that routes messages through Chief of Staff
    and delegates to specialist agents as needed.
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.threads: Dict[str, str] = {}  # agent_key -> thread_id
        self.active_thread: Optional[str] = None
        
        logger.info("Orchestrator initialized")
    
    def _get_or_create_thread(self, agent_key: str = "chief_of_staff") -> str:
        """Get existing thread or create a new one for an agent"""
        if agent_key not in self.threads:
            thread = self.client.beta.threads.create()
            self.threads[agent_key] = thread.id
            logger.info(f"Created new thread {thread.id} for {agent_key}")
        return self.threads[agent_key]
    
    def _get_assistant_id(self, agent_key: str) -> str:
        """Get OpenAI assistant ID for an agent key"""
        if agent_key not in ASSISTANTS:
            raise ValueError(f"Unknown agent: {agent_key}")
        return ASSISTANTS[agent_key]["id"]
    
    def _run_assistant(self, thread_id: str, assistant_id: str, 
                       additional_instructions: Optional[str] = None) -> str:
        """Run an assistant on a thread and wait for completion"""
        run_params = {
            "thread_id": thread_id,
            "assistant_id": assistant_id
        }
        if additional_instructions:
            run_params["additional_instructions"] = additional_instructions
        
        run = self.client.beta.threads.runs.create(**run_params)
        
        # Poll for completion
        while run.status in ["queued", "in_progress"]:
            time.sleep(0.5)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        if run.status == "failed":
            logger.error(f"Run failed: {run.last_error}")
            raise Exception(f"Assistant run failed: {run.last_error}")
        
        if run.status == "requires_action":
            # Handle function calls if needed
            return self._handle_function_calls(thread_id, run)
        
        # Get the latest message
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id,
            limit=1,
            order="desc"
        )
        
        if messages.data:
            content = messages.data[0].content[0]
            if hasattr(content, 'text'):
                return content.text.value
        
        return ""
    
    def _handle_function_calls(self, thread_id: str, run) -> str:
        """Handle function calls from assistants"""
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            logger.info(f"Function call: {function_name}({arguments})")
            
            # Handle delegation to specialists
            if function_name == "delegate_to_specialist":
                specialist = arguments.get("specialist")
                task = arguments.get("task")
                result = self.ask_specialist(specialist, task)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })
            elif function_name == "get_project_status":
                # Return project status from config or database
                result = self._get_project_status(arguments.get("project"))
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })
            else:
                # Default: return empty result
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"status": "ok"})
                })
        
        # Submit tool outputs
        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
        
        # Continue polling
        while run.status in ["queued", "in_progress"]:
            time.sleep(0.5)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        # Get the response
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id,
            limit=1,
            order="desc"
        )
        
        if messages.data:
            content = messages.data[0].content[0]
            if hasattr(content, 'text'):
                return content.text.value
        
        return ""
    
    def _get_project_status(self, project: str) -> Dict:
        """Get project status (can be extended to use database)"""
        # For now, return from config
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), "config", "projects.yaml")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                projects = config.get("projects", {})
                if project in projects:
                    return projects[project]
        except Exception as e:
            logger.error(f"Error loading project config: {e}")
        
        return {"status": "unknown", "message": f"Project {project} not found"}
    
    def ask(self, message: str, context: Optional[str] = None) -> AgentResponse:
        """
        Send a message to Chief of Staff.
        Chief of Staff decides whether to handle it or delegate.
        """
        thread_id = self._get_or_create_thread("chief_of_staff")
        
        # Add context if provided
        full_message = message
        if context:
            full_message = f"Context: {context}\n\nRequest: {message}"
        
        # Add message to thread
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=full_message
        )
        
        logger.info(f"Sent to Chief of Staff: {message[:100]}...")
        
        # Run Chief of Staff
        response = self._run_assistant(thread_id, CHIEF_OF_STAFF_ID)
        
        return AgentResponse(
            agent_name="Chief of Staff",
            content=response,
            thread_id=thread_id
        )
    
    def ask_specialist(self, specialist_key: str, message: str) -> str:
        """
        Directly ask a specialist agent.
        Used by Chief of Staff for delegation.
        """
        if specialist_key not in ASSISTANTS:
            return f"Unknown specialist: {specialist_key}"
        
        thread_id = self._get_or_create_thread(specialist_key)
        assistant_id = self._get_assistant_id(specialist_key)
        
        # Add message to thread
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        logger.info(f"Sent to {specialist_key}: {message[:100]}...")
        
        # Run specialist
        response = self._run_assistant(thread_id, assistant_id)
        
        return response
    
    def ask_with_auto_routing(self, message: str) -> AgentResponse:
        """
        Smart routing: detect topic and route to appropriate specialist,
        or go through Chief of Staff for complex requests.
        """
        # Try to detect specialist from message
        specialist = get_specialist_for_topic(message)
        
        if specialist:
            logger.info(f"Auto-routing to specialist: {specialist}")
            response = self.ask_specialist(specialist, message)
            return AgentResponse(
                agent_name=ASSISTANTS[specialist]["name"],
                content=response,
                thread_id=self.threads.get(specialist, ""),
                delegated_to=specialist
            )
        else:
            # Default to Chief of Staff
            return self.ask(message)
    
    def broadcast(self, message: str) -> Dict[str, str]:
        """
        Send a message to all specialists and collect responses.
        Useful for status updates or announcements.
        """
        responses = {}
        
        for agent_key, agent_info in ASSISTANTS.items():
            if agent_info["role"] == "specialist":
                try:
                    response = self.ask_specialist(agent_key, message)
                    responses[agent_key] = response
                except Exception as e:
                    logger.error(f"Error from {agent_key}: {e}")
                    responses[agent_key] = f"Error: {str(e)}"
        
        return responses
    
    def get_all_status(self) -> str:
        """
        Ask Chief of Staff for overall status of all projects.
        """
        return self.ask(
            "Дай мне краткий статус по всем проектам. "
            "Что сейчас в работе? Какие приоритеты на эту неделю?"
        ).content
    
    def create_task(self, project: str, task_description: str) -> AgentResponse:
        """
        Create a task through Chief of Staff.
        """
        message = f"Создай задачу для проекта {project}: {task_description}"
        return self.ask(message)
    
    def get_thread_history(self, agent_key: str = "chief_of_staff", 
                          limit: int = 10) -> list:
        """Get conversation history for an agent"""
        if agent_key not in self.threads:
            return []
        
        thread_id = self.threads[agent_key]
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id,
            limit=limit,
            order="asc"
        )
        
        history = []
        for msg in messages.data:
            content = msg.content[0].text.value if msg.content else ""
            history.append({
                "role": msg.role,
                "content": content,
                "created_at": msg.created_at
            })
        
        return history
    
    def reset_thread(self, agent_key: str = "chief_of_staff"):
        """Reset conversation thread for an agent"""
        if agent_key in self.threads:
            del self.threads[agent_key]
            logger.info(f"Reset thread for {agent_key}")
    
    def reset_all_threads(self):
        """Reset all conversation threads"""
        self.threads = {}
        logger.info("Reset all threads")


# Convenience function for quick usage
def chat(message: str) -> str:
    """Quick chat function - sends message to Chief of Staff"""
    orchestrator = Orchestrator()
    response = orchestrator.ask(message)
    return response.content


if __name__ == "__main__":
    # Quick test
    import sys
    
    orchestrator = Orchestrator()
    
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "Привет! Расскажи о текущих проектах."
    
    print(f"\n📤 You: {message}\n")
    response = orchestrator.ask(message)
    print(f"🤖 {response.agent_name}: {response.content}\n")

