# Agent Orchestrator

Personal Project Management System powered by OpenAI Assistants

## Overview

Yana's AI-powered project orchestration system that manages multiple creative and technical projects using a team of specialized AI agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        YOU (Yana)                           │
│                    Telegram / CLI                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                             │
│                   (orchestrator.py)                         │
│                                                             │
│  Routes messages, manages threads, handles function calls   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               👑 CHIEF OF STAFF                             │
│            (iana-chief-of-staff)                            │
│                                                             │
│  Main coordinator - understands all projects,               │
│  delegates tasks to specialists                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┬───────────┐
        ▼             ▼             ▼             ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│  🎧 Deep  │ │  💻 LSRC  │ │  🎬 Docu- │ │ 🎨 Bill-  │ │ 🌐 Digital│
│ Listening │ │   Tech    │ │  mentary  │ │  boards   │ │ Presence  │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
```

## Agents

| Agent | ID | Role |
|-------|-------|------|
| Chief of Staff | `asst_YNkTp9OaRExKr2wiOfEddC9Y` | Main coordinator |
| Deep Listening | `asst_8KgaIluAcNi8H6KtPr7VWes1` | DL projects |
| LSRC Tech | `asst_VhubS5qiL248WeCTqADu4yBZ` | App development |
| Documentary | `asst_wASgEj7SQEDuLkCsQy5voGVL` | Film production |
| Billboards & Experiments | `asst_P4bSUVW1kAY3keK3Gt2Jk3Yf` | Creative experiments |
| Digital Presence | `asst_6Y5LPMYw9guLDgOB7lYr3B4O` | Website & social |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up environment

Create a `.env` file:

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key

# Optional (for Telegram)
TELEGRAM_BOT_TOKEN=your-bot-token

# Optional (for persistence)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### 3. Run the orchestrator

**CLI mode:**
```bash
python interfaces/cli.py
```

**One-shot command:**
```bash
python interfaces/cli.py "Какие задачи на сегодня?"
```

**Telegram bot:**
```bash
python interfaces/telegram_bot.py
```

**Direct Python:**
```python
from orchestrator import Orchestrator

orch = Orchestrator()
response = orch.ask("Какой статус по LSRC?")
print(response.content)
```

## Usage Examples

### Via CLI

```
💬 You: Привет! Какие проекты сейчас в работе?

🤖 Chief of Staff: [response about projects]

💬 You: /ask lsrc_tech Какой следующий релиз планируется?

🤖 pm-lsrc-tech: [technical response]

💬 You: /status

📊 Status: [overview of all projects]
```

### Via Telegram

Just message the bot! Commands:
- `/status` - Get all projects status
- `/agents` - List available agents
- `/ask <agent> <message>` - Talk to specific agent
- `/reset` - Reset conversation

### Via Python

```python
from orchestrator import Orchestrator

orch = Orchestrator()

# Talk to Chief of Staff
response = orch.ask("Что нужно сделать на этой неделе?")

# Talk directly to a specialist
tech_response = orch.ask_specialist("lsrc_tech", "Какие баги в приоритете?")

# Auto-route based on topic
response = orch.ask_with_auto_routing("Нужно смонтировать трейлер")
# -> Automatically routes to documentary agent

# Get status from all specialists
all_responses = orch.broadcast("Краткий статус?")
```

## Project Structure

```
agent-orchestrator/
├── orchestrator.py          # Main orchestration logic
├── assistants_config.py     # Agent IDs and configuration
├── supabase_manager.py      # Database operations (optional)
├── requirements.txt         # Python dependencies
├── config/
│   ├── projects.yaml        # Project definitions
│   └── supabase_schema.sql  # Database schema
├── interfaces/
│   ├── cli.py               # Command-line interface
│   └── telegram_bot.py      # Telegram bot
├── functions/
│   ├── project_functions.py # Project management tools
│   └── task_functions.py    # Task management tools
└── scripts/
    └── setup_database.py    # Database initialization
```

## How It Works

1. **You send a message** via CLI or Telegram
2. **Orchestrator receives it** and creates/uses a thread
3. **Chief of Staff processes** the message:
   - For general questions: answers directly
   - For specific projects: may delegate to specialists
4. **Response is returned** to you
5. **Conversation continues** in the same thread (context preserved)

## Development

### Adding new agents

1. Create the assistant in OpenAI Platform
2. Add the ID to `assistants_config.py`
3. Update `PROJECT_TO_SPECIALIST` mapping if needed

### Extending function tools

Add new functions in `functions/` and register them in the assistant's tool configuration on OpenAI Platform.

---

Built with ❤️ for parallel creative work
