---
title: Planck AI
emoji: 🪐
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Planck AI <img src="frontend/public/planck-logo.svg" width="40" height="40" align="center" />

> **Your Autonomous Reasoning Engine for the Web.**
> *Think. Search. Solve.*

Planck AI is an advanced agentic search interface that combines the reasoning power of **GPT-4o** and **GPT-4o Mini** with real-time web access. Unlike traditional chatbots, Planck AI thinks before it speaks—breaking down complex queries into steps, searching multiple sources, reading deep into documents, and verifying facts before giving you an answer.

## 🚀 Features

- **🧠 Agentic Reasoning**: Uses a multi-step "Thinking" process to plan, execute, and verify tasks.
- **💻 Code Execution**: Writes and runs code in **7+ Languages** (Python, Java, JS/TS, C/C++, Go) to solve logic/math problems.
- **🌐 Deep Web Search**: Integated with Google & DuckDuckGo to find real-time information.
- **📄 Document Analysis**: Upload PDFs or paste URLs—Planck reads and analyzes them (up to 10k chars/page).
- **️ Vision Capabilities**: Analyze uploaded images using GPT-4o's vision model.
- **⚡ Reactive UI**: A beautiful, dark-mode interface built with React & TailwindCSS.
- **🔒 Privacy First**: All sessions are isolated. No data is stored permanently.

## 🛠️ Tech Stack

- **Frontend**: React (Vite), TailwindCSS, Lucide Icons
- **Backend**: FastAPI (Python 3.11), LangGraph (Agent Logic)
- **AI Models**: GPT-4o / GPT-4o-mini (via Azure/GitHub Models)
- **Vector Store**: ChromaDB (In-memory for session context)
- **Deployment**: Docker, Hugging Face Spaces

## ⚠️ API Limitations (Free Tier)

This project uses the **GitHub Models API (Free Tier)** for AI inference.
- **Token Limit**: Both GPT-4o and GPT-4o Mini are capped at a strict **8k token context window** ~~(standard is 128k)~~.
- **Handling**: The application automatically manages this by truncating conversation history to ~30k characters to prevent overflow errors.
- **Upgrade**: To unlock full 128k context, configure a paid OpenAI/Azure API key in the backend.

## 📦 Installation (Local)

1. **Clone the repository**
   ```bash
   git clone https://github.com/iammanoj807/planck-ai.git
   cd planck-ai
   ```

2. **Set up Environment Variables**
   Create a `.env` file in `backend/`:
   ```bash
   GITHUB_TOKEN=your_token_here    # For GPT-4o access
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
4. Add your `GITHUB_TOKEN` in the Space's **Settings > Variables**.
5. The specific `Dockerfile` at the root will build the React frontend and serve it via FastAPI on port `7860`.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

Made with ❤️ by Manoj Kumar Thapa