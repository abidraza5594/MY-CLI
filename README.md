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

## ⚡ One-Click Install (Windows)

### Prerequisites
1. Install [Python](https://python.org) (3.10+)
2. Install [Ollama](https://ollama.ai)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/abidraza5594/MY-CLI.git
cd MY-CLI

# 2. Run installer (does everything automatically!)
install.bat
```

**That's it!** The installer automatically:
- ✅ Creates virtual environment
- ✅ Installs all dependencies  
- ✅ Downloads AI model (glm-4.7:cloud)
- ✅ Adds `abid` command to your system

### After Installation

1. **Close the terminal**
2. **Open a NEW PowerShell window**
3. **Type `abid` anywhere!**

```bash
# Go to any project
cd "D:\your-project"

# Start coding with AI
abid
```

## 🚀 Usage

```bash
# Interactive mode
abid

# With prompt
abid "list all files"

# In any project folder
cd "C:\Projects\my-app"
abid "add dark mode to this React app"
abid "fix the login bug"
abid "create a REST API for users"
```

## 💡 Example Prompts

| Task | Command |
|------|---------|
| Explore | `abid "show me the project structure"` |
| Add Feature | `abid "add a search bar to the header"` |
| Fix Bug | `abid "fix the authentication issue"` |
| Refactor | `abid "refactor to use async/await"` |
| Create API | `abid "create REST API for products"` |
| Add Tests | `abid "add unit tests for utils"` |

## 🛠️ Features

- 🔍 **Smart Code Analysis** - Understands your entire codebase
- ✏️ **Auto Edit** - Makes changes in correct files automatically
- 🔎 **Code Search** - Finds relevant code with grep/glob
- 💻 **Shell Commands** - Runs build, test, lint commands
- 🌐 **Web Search** - Searches for solutions online
- 💾 **Session Save** - Save and resume conversations

## ⌨️ Interactive Commands

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
# 1. Clone
git clone https://github.com/abidraza5594/MY-CLI.git
cd MY-CLI

# 2. Create venv
python -m venv venv
.\venv\Scripts\activate

# 3. Install packages
pip install -r requirements.txt

# 4. Pull model
ollama pull glm-4.7:cloud

# 5. Run manually
$env:API_KEY="ollama"
$env:BASE_URL="http://localhost:11434/v1"
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
├── config/           # Configuration
└── ui/               # Terminal UI
```

## 🤝 Contributing

Pull requests welcome!

## 📄 License

MIT

---

Made with ❤️ by Abid
