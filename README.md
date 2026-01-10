# MY-CLI - AI Coding Agent

A powerful terminal-based AI coding assistant that helps you with coding tasks using LLM models.

## Features

- 🤖 Interactive CLI chat with AI
- 🛠️ Built-in tools for file operations, shell commands, web search
- 🔌 MCP (Model Context Protocol) support
- 💾 Session persistence and checkpoints
- 🔒 Safety approval system for dangerous operations
- 🪝 Hook system for automation

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/abidraza5594/MY-CLI.git
cd MY-CLI
```

### 2. Create virtual environment
```bash
python -m venv venv
```

### 3. Activate virtual environment

**Windows:**
```powershell
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

## Usage

### With Ollama (Local LLM)

1. Install [Ollama](https://ollama.ai)
2. Pull the model:
```bash
ollama pull glm-4.7:cloud
```

3. Run the agent:

**Windows (PowerShell):**
```powershell
$env:API_KEY="ollama"; $env:BASE_URL="http://localhost:11434/v1"; python main.py
```

**Linux/Mac:**
```bash
API_KEY=ollama BASE_URL=http://localhost:11434/v1 python main.py
```

### With OpenAI or other providers

```bash
API_KEY=your-api-key BASE_URL=https://api.openai.com/v1 python main.py
```

## Commands

Once running, you can use these commands:

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/exit` | Exit the agent |
| `/clear` | Clear conversation |
| `/config` | Show configuration |
| `/model <name>` | Change model |
| `/tools` | List available tools |
| `/save` | Save session |
| `/resume <id>` | Resume saved session |

## Available Tools

- `read_file` - Read file contents
- `write_file` - Create/write files
- `edit` - Edit files with search/replace
- `shell` - Execute shell commands
- `list_dir` - List directory contents
- `grep` - Search in files
- `glob` - Find files by pattern
- `web_search` - Search the web
- `web_fetch` - Fetch web pages
- `todos` - Task management
- `memory` - Store user preferences

## Configuration

Create `.ai-agent/config.toml` in your project:

```toml
[model]
name = "glm-4.7:cloud"
temperature = 0.7

[approval]
policy = "on-request"  # auto, on-request, never
```

## License

MIT
