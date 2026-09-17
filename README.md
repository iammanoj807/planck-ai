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

**Planck AI** is an advanced agentic search interface that combines the reasoning power of **Google Gemini 3.6 Flash** and **Gemini 2.5 Pro** with real-time web access. Unlike traditional chatbots, Planck AI thinks before it speaks—breaking down complex queries into steps, searching multiple sources, reading deep into documents, and verifying facts before giving you an answer.
## 🚀 Features

- **🧠 Agentic Reasoning**: Uses a multi-step "Thinking" process to plan, execute, and verify tasks.
- **🌐 Deep Web Search**: Integated with Google & DuckDuckGo to find real-time information.
- **🌍 Multi-Language Support**: Talk to Planck in **20+ Languages** (e.g., Nepali, Spanish, Hindi, French). The UI adapts, and the agent responds natively while maintaining its reasoning capabilities.
- **💻 Code Execution**: Writes and runs code in **7+ Languages** (Python, Java, JS/TS, C/C++, Go) to solve logic/math problems.
- **📄 Document Analysis**: Upload PDFs or paste URLs—Planck reads and analyzes them (up to 10k chars/page).
- **👁️ Vision Capabilities**: Analyze uploaded images using Gemini's multimodal vision.
- **⚡ Reactive UI**: A beautiful, dark-mode interface built with React & TailwindCSS.
- **🔒 Privacy First**: All sessions are isolated. No data is stored permanently.

## 🛠️ Tech Stack

- **Frontend**: React (Vite), TailwindCSS, Lucide Icons
- **Backend**: FastAPI (Python 3.11), LangGraph (Agent Logic)
- **AI Models**: Google Gemini 3.6 Flash / Gemini 2.5 Pro (via Google AI Studio)
- **Vector Store**: ChromaDB (In-memory for session context)
- **Deployment**: Docker, Hugging Face Spaces

## ⚡ AI Engine

This project is powered by **Google Gemini 3.6 Flash** and **Gemini 2.5 Pro**, offering fast multimodal inference, high throughput, and deep agentic tool reasoning.
- **Context Window**: Supports large context and reasoning.
- **Multimodal**: Handles image analysis, document transcription, and real-time tool execution seamlessly.

## 📦 Installation (Local)

1. **Clone the repository**
   ```bash
   git clone https://github.com/iammanoj807/planck-ai.git
   cd planck-ai
   ```

2. **Set up Environment Variables**
   Create a `.env` file in `backend/`:
   ```bash
   GEMINI_API_KEY=your_key_here   # From Google AI Studio (aistudio.google.com/app/apikey)
   GOOGLE_API_KEY=optional_key     # For Google Search
   GOOGLE_CSE_ID=optional_id       # For Google Search
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
4. Add your `GEMINI_API_KEY` in the Space's **Settings > Variables and secrets**.
5. The specific `Dockerfile` at the root will build the React frontend and serve it via FastAPI on port `7860`.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

Made with ❤️ by Manoj Kumar Thapa