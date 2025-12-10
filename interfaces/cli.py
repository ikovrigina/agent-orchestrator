#!/usr/bin/env python3
"""
CLI Interface for Agent Orchestrator
Interactive command-line chat with your AI assistants
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator
from assistants_config import ASSISTANTS
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="WARNING")


def print_help():
    """Print available commands"""
    print("""
╭─────────────────────────────────────────────────────────╮
│  🎯 Agent Orchestrator CLI                              │
╰─────────────────────────────────────────────────────────╯

Commands:
  /help          - Show this help
  /status        - Get status of all projects
  /agents        - List all available agents
  /ask <agent>   - Talk directly to a specialist
  /reset         - Reset conversation
  /quit          - Exit

Examples:
  "Какие задачи на сегодня?"
  "Статус по LSRC?"
  /ask lsrc_tech Какой стек используется?
  
Just type your message to talk to Chief of Staff.
""")


def print_agents():
    """Print list of available agents"""
    print("\n📋 Available Agents:\n")
    for key, info in ASSISTANTS.items():
        role_emoji = "👑" if info["role"] == "coordinator" else "🔧"
        print(f"  {role_emoji} {key}")
        print(f"     Name: {info['name']}")
        print(f"     {info['description']}\n")


def main():
    """Main CLI loop"""
    print("""
╭─────────────────────────────────────────────────────────╮
│  🎯 Agent Orchestrator                                  │
│  Your AI-powered project management system              │
╰─────────────────────────────────────────────────────────╯
    """)
    
    # Check for command-line argument
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        orchestrator = Orchestrator()
        response = orchestrator.ask(message)
        print(f"\n🤖 {response.agent_name}:\n{response.content}\n")
        return
    
    print("Type /help for commands, or just start chatting!\n")
    
    try:
        orchestrator = Orchestrator()
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        print("Make sure OPENAI_API_KEY is set in your .env file")
        return
    
    current_agent = "chief_of_staff"
    
    while True:
        try:
            user_input = input(f"\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd_parts = user_input.split()
                cmd = cmd_parts[0].lower()
                
                if cmd == "/quit" or cmd == "/exit" or cmd == "/q":
                    print("\n👋 До встречи!\n")
                    break
                
                elif cmd == "/help" or cmd == "/?":
                    print_help()
                
                elif cmd == "/status":
                    print("\n⏳ Getting status...")
                    status = orchestrator.get_all_status()
                    print(f"\n📊 Status:\n{status}")
                
                elif cmd == "/agents":
                    print_agents()
                
                elif cmd == "/ask":
                    if len(cmd_parts) < 3:
                        print("Usage: /ask <agent_key> <message>")
                        print("Example: /ask lsrc_tech What's the current status?")
                        continue
                    
                    agent_key = cmd_parts[1]
                    message = " ".join(cmd_parts[2:])
                    
                    if agent_key not in ASSISTANTS:
                        print(f"❌ Unknown agent: {agent_key}")
                        print_agents()
                        continue
                    
                    print(f"\n⏳ Asking {ASSISTANTS[agent_key]['name']}...")
                    response = orchestrator.ask_specialist(agent_key, message)
                    print(f"\n🤖 {ASSISTANTS[agent_key]['name']}:\n{response}")
                
                elif cmd == "/reset":
                    orchestrator.reset_all_threads()
                    print("🔄 Conversation reset!")
                
                elif cmd == "/auto":
                    if len(cmd_parts) < 2:
                        print("Usage: /auto <message>")
                        continue
                    message = " ".join(cmd_parts[1:])
                    print("\n⏳ Auto-routing...")
                    response = orchestrator.ask_with_auto_routing(message)
                    if response.delegated_to:
                        print(f"📍 Routed to: {response.delegated_to}")
                    print(f"\n🤖 {response.agent_name}:\n{response.content}")
                
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type /help for available commands")
            
            else:
                # Regular message - send to Chief of Staff
                print("\n⏳ Thinking...")
                response = orchestrator.ask(user_input)
                print(f"\n🤖 {response.agent_name}:\n{response.content}")
        
        except KeyboardInterrupt:
            print("\n\n👋 До встречи!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.exception("CLI error")


if __name__ == "__main__":
    main()

