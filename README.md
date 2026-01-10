# ABID - AI Coding Assistant 🤖

A powerful terminal-based AI coding assistant that helps you with coding tasks.

```
     _    ____ ___ ____  
    / \  | __ )_ _|  _ \ 
   / _ \ |  _ \| || | | |
  / ___ \| |_) | || |_| |
 /_/   \_\____/___|____/ 
                         
 Your AI Coding Partner
```

## ⚡ Quick Install (Windows)

### Prerequisites
1. Install [Python](https://python.org) (3.10+)
2. Install [Ollama](https://ollama.ai)

### Installation
```bash
git clone https://github.com/abidraza5594/MY-CLI.git
cd MY-CLI
install.bat
```

That's it! The installer will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Download AI model (glm-4.7:cloud)
- ✅ Add `abid` command to your system

## 🚀 Usage

Open a **new terminal** and use anywhere:

```bash
# Interactive mode
abid

# With prompt
abid "list all files in current directory"

# In any project
cd "D:\your-project"
abid "add dark mode to this React app"
```

## 💡 Example Prompts

| Task | Prompt |
|------|--------|
| Explore Project | `abid "show me the project structure"` |
| Add Feature | `abid "add a search bar to the header"` |
| Fix Bug | `abid "fix the login authentication issue"` |
| Refactor | `abid "refactor this code to use async/await"` |
| Create API | `abid "create REST API for user management"` |

## 🛠️ Features

- 🔍 **Smart Code Analysis** - Understands your entire codebase
- ✏️ **Auto Edit** - Makes changes in correct files
- 🔎 **Code Search** - Finds relevant code quickly
- 💻 **Shell Commands** - Runs build, test commands
- 🌐 **Web Search** - Searches for solutions online
- 💾 **Session Save** - Save and resume conversations

## ⌨️ Commands (Interactive Mode)

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/exit` | Exit |
| `/clear` | Clear conversation |
| `/config` | Show configuration |
| `/model <name>` | Change AI model |
| `/tools` | List available tools |
| `/save` | Save session |

## 🔧 Manual Installation

If `install.bat` doesn't work:

```bash
# 1. Clone repo
git clone https://github.com/abidraza5594/MY-CLI.git
cd MY-CLI

# 2. Create venv
python -m venv venv
venv\Scripts\activate

# 3. Install packages
pip install -r requirements.txt

# 4. Pull model
ollama pull glm-4.7:cloud

# 5. Run
set API_KEY=ollama
set BASE_URL=http://localhost:11434/v1
python main.py
```

## 📁 Project Structure

```
MY-CLI/
├── main.py           # Entry point
├── install.bat       # Auto installer
├── abid.bat          # CLI launcher
├── requirements.txt  # Dependencies
├── agent/            # AI agent logic
├── client/           # LLM client
├── tools/            # Built-in tools
│   └── builtin/      # File, shell, search tools
├── config/           # Configuration
├── context/          # Context management
├── prompts/          # System prompts
├── safety/           # Safety checks
└── ui/               # Terminal UI
```

## 🤝 Contributing

Pull requests welcome! 

## 📄 License

MIT

---

Made with ❤️ by Abid
