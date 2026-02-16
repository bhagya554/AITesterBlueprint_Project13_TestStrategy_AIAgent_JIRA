# TestStrategy Agent

> AI-Powered Enterprise Test Strategy Document Generator

A production-grade, locally-hosted web application that automatically generates comprehensive, enterprise-level test strategy documents by pulling context from JIRA tickets and populating a user-provided test strategy template using an LLM.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![React](https://img.shields.io/badge/react-18-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)

## 🎯 Key Difference from Test Plan Agents

A **Test Strategy** is a **higher-level, project-wide** document that defines the overall testing approach, methodology, tools, environments, risk management, and governance. It typically covers an entire project or release, whereas a Test Plan is per-feature/sprint. The AI understands this distinction and generates strategic, architectural-level content — not just test cases.

## ✨ Features

- 🔗 **JIRA Integration**: Fetch tickets, epics, and linked issues from JIRA Cloud
- 🤖 **Dual LLM Support**: Groq (cloud) and Ollama (local) providers
- 📝 **Template-Based**: Uses your PDF template structure
- 🌊 **Streaming Generation**: Real-time SSE streaming of generated content
- 📊 **Context Optimization**: Intelligent token budget management
- 📄 **Export Options**: PDF and DOCX export with professional formatting
- 💾 **History**: Save and retrieve generated strategies
- ⚙️ **Full Settings**: Configure JIRA, LLM, and generation preferences

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI |
| Frontend | React 18, Vite, Tailwind CSS |
| Database | SQLite via SQLAlchemy |
| PDF Parsing | pdfplumber |
| PDF/DOCX Export | ReportLab, python-docx |
| LLM | Groq SDK, Ollama |

## 📋 Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- (Optional) Ollama for local LLM support

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd teststrategy-agent
```

### 2. Configure Environment

Copy the template and fill in your credentials:

```bash
cp .env.template .env
```

Edit `.env` with your settings:

```env
# JIRA Configuration
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Groq Configuration (for cloud LLM)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Ollama Configuration (for local LLM - optional)
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Run

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```batch
start.bat
```

### 4. Open in Browser

Navigate to: http://localhost:8000

## 📚 Getting API Keys

### JIRA API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "TestStrategy Agent")
4. Copy the token and paste it in `.env`

### Groq API Key

1. Sign up at https://console.groq.com
2. Go to API Keys
3. Create a new key
4. Copy and paste it in `.env`

### Ollama (Optional - Local LLM)

1. Install Ollama from https://ollama.com/download
2. Pull a model: `ollama pull llama3.1`
3. Start Ollama: `ollama serve`

## 📖 Usage

### 1. Configure Settings
- Go to **Settings** page
- Enter your JIRA credentials and test the connection
- Configure your preferred LLM provider
- Upload your test strategy template PDF (or use default)

### 2. Generate Strategy
- Go to **Generator** page
- Enter JIRA ticket IDs (e.g., `VMO-1, VMO-2, VMO-15`)
- Select LLM provider and model
- Choose strategy depth and focus areas
- Click "Fetch & Generate"

### 3. Export and Save
- Copy to clipboard, or
- Download as PDF/DOCX, or
- Save to history for later access

## 🛠️ Development

### Backend Development

```bash
cd teststrategy-agent/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend Development

```bash
cd teststrategy-agent/frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

## 🧪 Testing Connectivity

Run the connectivity check tools:

```bash
# Test all connections
python tools/check_all.py

# Or test individually
python tools/check_jira.py
python tools/check_groq.py
python tools/check_ollama.py
python tools/check_template.py
```

## 🐛 Troubleshooting

### JIRA Connection Issues
- Verify your JIRA base URL (should end with `.atlassian.net` for cloud)
- Check that your API token is correct (not your password)
- Ensure you have access to the JIRA project

### Groq Rate Limits
- Free tier has rate limits (30 requests/minute)
- If rate limited, wait a moment and try again
- Consider upgrading to paid tier for production use

### Ollama Not Found
- Ensure Ollama is running: `ollama serve`
- Check the Ollama URL in settings (default: http://localhost:11434)
- Verify the model is pulled: `ollama list`

### Template Not Found
- Place `teststrategy.pdf` in the project root
- Or upload via Settings page

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review the logs in the terminal
- Open an issue on GitHub

---

Built with ❤️ for QA Architects and Test Strategists
