# 🦥 SlothSort — Slow and Steady File Organization

**Organize smarter, not faster.**

SlothSort is a local AI-powered file organizer built with Python, Streamlit, and Ollama. It helps users understand their cluttered folders, categorize files, identify duplicates, and review organization suggestions before moving files.

Inspired by the idea of *Slow and Steady*, SlothSort prioritizes deliberate, transparent, and user-controlled file organization over risky automation.

## ✨ Features

- 📂 **File Categorization** — Group files by their extensions and file types.
- 🤖 **Local AI Suggestions** — Use an Ollama-hosted language model to suggest meaningful filenames.
- 🔍 **Duplicate Detection** — Compare SHA-256 file hashes to identify files with identical content.
- 👀 **Preview Before Action** — Review proposed file moves before applying them.
- 🛡️ **User-Controlled Organization** — Keep control over which file moves are approved.
- 🖥️ **Simple Web Interface** — Interact with the organizer through a Streamlit application.
- 🔓 **Open-Source Friendly** — Built with tools that support local development and experimentation.

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web interface |
| Ollama | Run a language model locally |
| Qwen 2.5 1.5B | Local model for AI suggestions |
| Requests | Communicate with the Ollama API |
| SHA-256 | Duplicate-content detection |
| Git & GitHub | Version control and collaboration |

## ⚙️ How It Works

1. **Scan** — Select a folder and inspect its files.
2. **Categorize** — Group files according to their extensions.
3. **Analyze** — Check file hashes to identify potential duplicates.
4. **Suggest** — Ask the locally running AI model for filename suggestions.
5. **Review** — Inspect the proposed changes.
6. **Organize** — Approve the file moves you want to perform.

SlothSort is designed to keep the user involved in the organization process rather than silently changing files.

## 🚀 Getting Started

### Prerequisites

Install the following:

- Python 3.10 or newer
- Git
- [Ollama](https://ollama.com/download)

### 1. Clone the repository

```bash
git clone https://github.com/padmalochini27-del/SlothSort.git
cd SlothSort
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the local AI model

```bash
ollama pull qwen2.5:1.5b
```

Ensure Ollama is running before launching the application. If it is not already running, start it
