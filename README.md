---
title: Planck AI
emoji: 🪐
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
short_description: 'Planck AI: Agentic search with reasoning and web access.'
---

<div align="center">
  <img src="frontend/public/planck-logo.svg" alt="Logo" width="100" />
  <h1>Planck AI</h1>
  <h3>Your Autonomous Reasoning Engine for the Web.</h3>
  <p><strong>Think -> Search -> Solve</strong></p>
</div>

---

## ✨ Overview

**Planck AI** is an advanced agentic search interface that combines the reasoning power of **Groq 120B** (powered by `openai/gpt-oss-120b`) with real-time web access. Unlike traditional chatbots, Planck AI thinks before it speaks—breaking down complex queries into steps, searching multiple sources, reading deep into documents, and verifying facts before giving you an answer.
## 🚀 Features

- **🧠 Agentic Reasoning**: Uses a multi-step "Thinking" process to plan, execute, and verify tasks.
- **🌐 Deep Web Search**: Integated with Google & DuckDuckGo to find real-time information.
- **🌍 Multi-Language Support**: Talk to Planck in **20+ Languages** (e.g., Nepali, Spanish, Hindi, French). The UI adapts, and the agent responds natively while maintaining its reasoning capabilities.
- **💻 Code Execution**: Writes and runs code in **7+ Languages** (Python, Java, JS/TS, C/C++, Go) to solve logic/math problems.
- **📄 Document Analysis**: Upload PDFs or paste URLs—Planck reads and analyzes them (up to 10k chars/page).
- **👁️ Vision Capabilities**: Analyze uploaded images using multimodal vision.
- **⚡ Reactive UI**: A beautiful, dark-mode interface built with React & TailwindCSS.
- **🔒 Privacy First**: All sessions are isolated. No data is stored permanently.

## 🛠️ Tech Stack

- **Frontend**: React (Vite), TailwindCSS, Lucide Icons
- **Backend**: FastAPI (Python 3.11), LangGraph (Agent Logic)
- **AI Models**: Groq `openai/gpt-oss-120b` / `openai/gpt-oss-20b` (via [Groq API](https://console.groq.com))
- **Vector Store**: ChromaDB (In-memory for session context)
- **Deployment**: Docker, Hugging Face Spaces

## ⚡ AI Engine

This project is powered by **Groq** (`openai/gpt-oss-120b` and `openai/gpt-oss-20b`), offering ultra-fast inference, tool calling, and deep agentic reasoning.
- **Speed**: Groq's LPU hardware delivers sub-second token generation.
- **Tool Calling**: Native function calling for web search, code execution, and document analysis.

## 📦 Installation (Local)

1. **Clone the repository**
   ```bash
   git clone https://github.com/iammanoj807/planck-ai.git
   cd planck-ai
   ```

2. **Set up Environment Variables**
   Create a `.env` file in `backend/`:
   ```bash
   GROQ_API_KEY=your_key_here      # From https://console.groq.com
   GOOGLE_API_KEY=your_key_here     # For Google Search (Google Cloud Console)
   GOOGLE_CSE_ID=your_cse_id       # For Google Search (Programmable Search Engine)
   ```

3. **Run the Application**
   Use the provided start script:
   ```bash
   ./run.sh
   ```
   - Frontend: `http://localhost:5173`
   - Backend: `http://localhost:8000`

## ☁️ Deployment (Hugging Face Spaces)

This project is configured for **Hugging Face Spaces (Docker)**.

1. Create a new Space on Hugging Face.
2. Select **Docker** as the SDK.
3. Upload this entire repository.
4. Add your `GROQ_API_KEY` (and optionally `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`) in the Space's **Settings > Variables and secrets**.
5. The specific `Dockerfile` at the root will build the React frontend and serve it via FastAPI on port `7860`.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

Made with ❤️ by Manoj Kumar Thapa