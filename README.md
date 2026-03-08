# ⚡ ReqCraft

**An interactive API testing client for your terminal** — like Postman, but in your terminal.

Built with [Textual](https://textual.textualize.io/) for a beautiful, modern TUI that works on **macOS, Linux, and Windows**.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey" alt="Platform">
</p>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔧 **Request Builder** | Compose HTTP requests (GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS) with URL bar, headers, query params, body (JSON/form/raw), and auth |
| 📊 **Response Viewer** | Syntax-highlighted JSON/XML/HTML responses, headers, cookies, timing breakdown, with color-coded status badges |
| 📁 **Collections** | Save requests into named collections, browse them in the sidebar tree, and re-run with one click |
| 🌍 **Environments** | Define variable sets (dev/staging/prod), use `{{variable}}` syntax in URLs, headers, and body |
| 🕐 **Request History** | Searchable log of all requests with timestamps, status codes, and response times |
| 📋 **cURL Import/Export** | Paste a cURL command to import it, or export any request as a cURL one-liner |
| 🔐 **Authentication** | Basic Auth, Bearer Token, API Key (header or query) — all built in |
| ⌨️ **Keyboard-Driven** | Full keyboard navigation with shortcuts for every action |
| 🎨 **Themes** | Dark and light themes |
| 🌐 **Web Shareable** | Serve via `textual serve reqcraft` for browser access |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** — [Download Python](https://python.org/downloads/)
- **pip** — comes with Python

### Install from source

```bash
# Clone the repository
git clone https://github.com/terminal-fun/reqcraft.git
cd reqcraft

# Install in development mode
pip install -e .

# Run ReqCraft
reqcraft
```

### Install from PyPI (when published)

```bash
pip install reqcraft
reqcraft
```

### Run without installing

```bash
python -m reqcraft
```

---

## 🎮 Usage

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` | Send the current request |
| `Ctrl+S` | Save request to a collection |
| `Ctrl+I` | Import a cURL command |
| `Ctrl+X` | Export as cURL command |
| `Ctrl+E` | Manage environments |
| `Ctrl+N` | New empty request |
| `Ctrl+L` | Clear response panel |
| `Ctrl+Q` | Quit |

### Sending Your First Request

1. Launch ReqCraft: `reqcraft`
2. Type a URL in the URL bar (e.g., `https://httpbin.org/get`)
3. Press **Ctrl+Enter** or click **Send**
4. View the syntax-highlighted response in the right panel

### Working with Environments

1. Press **Ctrl+E** to open the environment manager
2. Click **+ New Environment**
3. Name it (e.g., "Development") and add variables:
   ```
   base_url=http://localhost:8000
   api_key=your-dev-key
   ```
4. Click **Use** to activate it
5. Now use `{{base_url}}/api/users` as your URL — variables will be substituted automatically

### Importing cURL Commands

1. Press **Ctrl+I**
2. Paste your cURL command:
   ```bash
   curl -X POST https://api.example.com/users \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer mytoken" \
     -d '{"name": "Alice", "email": "alice@example.com"}'
   ```
3. Click **Import** — the method, URL, headers, body, and auth will all populate automatically

### Saving to Collections

1. Build your request and send it
2. Press **Ctrl+S**
3. Enter a name and collection — it will appear in the sidebar tree
4. Click any saved request to reload it instantly

---

## 🏗️ Building from Source

### All Platforms (macOS, Linux, Windows)

```bash
# 1. Ensure Python 3.10+ is installed
python --version  # Should be 3.10 or higher

# 2. Clone the repository
git clone https://github.com/terminal-fun/reqcraft.git
cd reqcraft

# 3. (Optional) Create a virtual environment
python -m venv .venv
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 4. Install dependencies
pip install -e .

# 5. Run the application
reqcraft
# Or: python -m reqcraft
```

### Running Tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

### Serving via Web Browser

```bash
pip install textual-serve
textual serve "python -m reqcraft"
```

---

## 🗂️ Project Structure

```
reqcraft/
├── pyproject.toml          # Project config & dependencies
├── LICENSE                 # MIT License
├── README.md               # This file
├── src/reqcraft/
│   ├── __init__.py         # Package metadata
│   ├── __main__.py         # CLI entry point (Click)
│   ├── app.py              # Main Textual App
│   ├── models.py           # Data models (Request, Response, etc.)
│   ├── http_client.py      # Async HTTP client (httpx)
│   ├── storage.py          # JSON persistence layer
│   ├── curl_parser.py      # cURL import/export
│   ├── config.py           # App configuration
│   ├── widgets/            # TUI widgets
│   │   ├── url_bar.py      # Method + URL + Send
│   │   ├── request_panel.py # Params/Headers/Body/Auth tabs
│   │   ├── response_panel.py # Response viewer with syntax hl
│   │   ├── sidebar.py      # Collections tree + history
│   │   └── environment_modal.py # Modals for save/cURL/envs
│   └── styles/
│       └── app.tcss        # Textual CSS stylesheet
└── tests/
    ├── test_models.py      # 16 tests
    ├── test_curl_parser.py # 16 tests
    ├── test_storage.py     # 12 tests
    └── test_http_client.py # 8 tests
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **TUI Framework** | [Textual](https://textual.textualize.io/) |
| **HTTP Client** | [httpx](https://www.python-httpx.org/) (async) |
| **Text Formatting** | [Rich](https://rich.readthedocs.io/) |
| **CLI** | [Click](https://click.palletsprojects.com/) |
| **Testing** | pytest + pytest-asyncio |

---

## 📦 Data Storage

ReqCraft stores your data locally:

| Platform | Location |
|---|---|
| **Linux** | `~/.local/share/reqcraft/` |
| **macOS** | `~/.local/share/reqcraft/` |
| **Windows** | `%APPDATA%\reqcraft\` |

Files stored:
- `collections.json` — Saved request collections
- `environments.json` — Environment variable sets
- `history.json` — Request history (last 500 entries)
- `config.json` — App preferences

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest tests/ -v`
5. Submit a pull request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.