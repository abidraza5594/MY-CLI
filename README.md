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
- ✅ Downloads AI models (qwen2.5-coder:14b + llava:13b)
- ✅ Adds `abid` command to your system

### After Installation

1. **Close the terminal**
2. **Open a NEW PowerShell window**
3. **Type `abid` anywhere!**

## 🚀 Usage

```bash
# Interactive mode
abid

# With prompt
abid "list all files"

# With specific model
abid --model llama3 "explain this code"
abid -m codellama "refactor this function"

# With image (uses vision model automatically)
abid --image screenshot.png "fix the error shown here"
abid -i error.png "what's wrong in this code?"

# With custom vision model
abid -i screenshot.png -v bakllava "analyze this UI"

# List all available models
abid --list-models
abid -l
```

## 🔄 Model Management

### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--model` | `-m` | Use specific coding model |
| `--vision-model` | `-v` | Use specific vision model |
| `--image` | `-i` | Provide image file |
| `--list-models` | `-l` | List all Ollama models |

### Examples

```bash
# List all your downloaded models
abid -l

# Use different coding model
abid -m llama3 "write a function"
abid -m codellama:13b "optimize this code"
abid -m mistral "explain async/await"
abid -m deepseek-coder "create REST API"

# Use different vision model
abid -i error.png -v bakllava "fix this error"
abid -i ui.png -v llava:34b "improve this design"

# Combine options
abid -m codellama -i screenshot.png "fix the bug shown"
```

### Interactive Commands

Change models during a session:

```bash
> /models              # List all available Ollama models
> /model llama3        # Switch to llama3
> /model codellama:13b # Switch to codellama 13b
> /vision bakllava     # Switch vision model to bakllava
> /config              # Show current configuration
```

## 🖼️ Image Support

### How to Use Images

```bash
# Method 1: CLI flag (recommended)
abid --image path/to/image.png "describe this"
abid -i screenshot.png "fix the error"

# Method 2: Full path
abid -i "C:\Users\you\Desktop\error.png" "what's wrong?"

# Method 3: Relative path
abid -i ./screenshots/bug.png "debug this"
```

### Supported Formats
- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- WebP (.webp)

### Use Cases

| Scenario | Command |
|----------|---------|
| Debug error screenshot | `abid -i error.png "fix this error"` |
| Analyze UI design | `abid -i ui.png "improve this layout"` |
| Understand code screenshot | `abid -i code.png "explain this code"` |
| Fix console error | `abid -i console.png "what's causing this?"` |

## 🤖 Dual Model System

| Task | Default Model | Description |
|------|---------------|-------------|
| **Coding** | `qwen2.5-coder:14b` | Fast, accurate code generation |
| **Vision** | `llava:13b` | Image analysis, screenshot debugging |

The correct model is selected automatically based on your input!

### Popular Alternative Models

**Coding Models:**
- `codellama` - Meta's code-focused model
- `deepseek-coder` - Great for code generation
- `llama3` - General purpose, good at coding
- `mistral` - Fast and efficient

**Vision Models:**
- `llava` - Default vision model
- `bakllava` - Alternative vision model
- `llava:34b` - Larger, more accurate

## 💡 Example Prompts

| Task | Command |
|------|---------|
| Explore | `abid "show me the project structure"` |
| Add Feature | `abid "add a search bar to the header"` |
| Fix Bug | `abid "fix the authentication issue"` |
| Refactor | `abid "refactor to use async/await"` |
| Create API | `abid "create REST API for products"` |
| Debug Image | `abid -i error.png "fix this"` |

## ⌨️ Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/exit` | Exit |
| `/clear` | Clear conversation |
| `/config` | Show configuration |
| `/models` | List available Ollama models |
| `/model <name>` | Change coding model |
| `/vision <name>` | Change vision model |
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

# 4. Pull models
ollama pull qwen2.5-coder:14b
ollama pull llava:13b

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
