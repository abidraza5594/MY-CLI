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
2. Install [Ollama](https://ollama.ai) (optional - for local models)

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
- ✅ Downloads AI models (if using Ollama)
- ✅ Adds `abid` command to your system

## 🌐 Multiple AI Providers

ABID supports multiple AI providers - use local models OR cloud APIs!

| Provider | Type | Speed | Cost | Best For |
|----------|------|-------|------|----------|
| **Ollama** | Local | Depends on PC | Free | Privacy, Offline |
| **Gemini** | Cloud | Fast | Free tier | General use |
| **Mistral** | Cloud | Very Fast | Paid | Fast coding |
| **OpenAI** | Cloud | Fast | Paid | Best quality |
| **Groq** | Cloud | Ultra Fast | Free tier | Speed |

### Quick Start with Different Providers

```bash
# Local with Ollama (default - free, unlimited)
abid "write a function"

# With Gemini (free tier available)
abid --provider gemini --api-key YOUR_KEY "write a function"

# With Mistral (fast!)
abid --provider mistral -k YOUR_KEY "write a function"

# With OpenAI
abid --provider openai -k YOUR_KEY "write a function"

# With Groq (ultra fast, free tier)
abid --provider groq -k YOUR_KEY "write a function"
```

### Set API Key Once (Environment Variable)

```powershell
# For Gemini
$env:GEMINI_API_KEY = "your-api-key"

# For Mistral
$env:MISTRAL_API_KEY = "your-api-key"

# For OpenAI
$env:OPENAI_API_KEY = "your-api-key"

# For Groq
$env:GROQ_API_KEY = "your-api-key"

# Then just use provider flag
abid --provider gemini "write code"
```

### Interactive Provider Selection

```bash
> /provider           # Show provider menu
> /provider gemini    # Switch to Gemini
> /provider mistral   # Switch to Mistral
> /config             # Show current config
```

## 🚀 Usage

```bash
# Interactive mode
abid

# With prompt
abid "list all files"

# With specific provider
abid --provider gemini -k YOUR_KEY "explain this code"

# With specific model
abid -m llama3 "explain this code"

# With image
abid --paste "fix this error"
abid -i screenshot.png "what's wrong?"

# List Ollama models
abid -l
```

## 🔄 CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--provider` | | AI provider (ollama/gemini/mistral/openai/groq) |
| `--api-key` | `-k` | API key for cloud providers |
| `--model` | `-m` | Specific model to use |
| `--vision-model` | `-v` | Vision model for images |
| `--image` | `-i` | Image file path |
| `--paste` | `-p` | Use clipboard image |
| `--list-models` | `-l` | List Ollama models |

## 🖼️ Image Support

### Copy-Paste (Easiest!)

```bash
# 1. Copy image (Ctrl+C or Win+Shift+S for screenshot)
# 2. Run:
abid --paste "fix this error"
abid -p "what's wrong?"

# In interactive mode:
> /paste
> what's wrong in this code?
```

### Image File

```bash
abid -i screenshot.png "fix this"
abid --image error.png "debug this"
```

## 🤖 Default Models by Provider

| Provider | Coding Model | Vision Model |
|----------|--------------|--------------|
| Ollama | qwen2.5-coder:7b | llava:7b |
| Gemini | gemini-2.0-flash | gemini-2.0-flash |
| Mistral | mistral-small-latest | pixtral-12b-2409 |
| OpenAI | gpt-4o-mini | gpt-4o-mini |
| Groq | llama-3.1-70b-versatile | llama-3.2-11b-vision-preview |

## ⌨️ Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/exit` | Exit |
| `/provider` | Change AI provider |
| `/models` | List Ollama models |
| `/model <name>` | Change model |
| `/vision <name>` | Change vision model |
| `/paste` | Paste clipboard image |
| `/config` | Show configuration |
| `/clear` | Clear conversation |
| `/save` | Save session |

## 💡 Example Prompts

```bash
# Explore project
abid "show me the project structure"

# Add feature
abid "add a search bar to the header"

# Fix bug
abid "fix the authentication issue"

# With image
abid -p "fix the error in this screenshot"

# Fast with Groq
abid --provider groq -k KEY "refactor this code"
```

## 🔧 Manual Installation

```bash
# 1. Clone
git clone https://github.com/abidraza5594/MY-CLI.git
cd MY-CLI

# 2. Create venv
python -m venv venv
.\venv\Scripts\activate

# 3. Install packages
pip install -r requirements.txt

# 4. For Ollama (optional)
ollama pull qwen2.5-coder:7b
ollama pull llava:7b

# 5. Run
python main.py
```

## 🔑 Get API Keys

| Provider | Get Key | Free Tier |
|----------|---------|-----------|
| Gemini | [Google AI Studio](https://makersuite.google.com/app/apikey) | ✅ Yes |
| Mistral | [Mistral Console](https://console.mistral.ai/) | ❌ No |
| OpenAI | [OpenAI Platform](https://platform.openai.com/api-keys) | ❌ No |
| Groq | [Groq Console](https://console.groq.com/) | ✅ Yes |

## 📁 Project Structure

```
MY-CLI/
├── main.py           # Entry point
├── install.bat       # Auto installer
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
