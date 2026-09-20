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

**Planck AI** is an advanced agentic search interface that combines the reasoning power of **Groq 120B** (powered by `openai/gpt-oss-120b`) with real-time web access, and automatically falls back to **Google Gemini** and **NVIDIA** models when Groq is rate limited. Unlike traditional chatbots, Planck AI thinks before it speaks—breaking down complex queries into steps, searching multiple sources, reading deep into documents, and verifying facts before giving you an answer.

## 🚀 Features

- **🧠 Agentic Reasoning**: Plans, executes, and verifies tasks step by step—view the model's reasoning in the "Thinking Process" panel.
- **🔁 Automatic Fallback**: If Groq is rate limited or errors, Gemini (then NVIDIA) takes over instantly—even mid-answer.
- **🌐 Deep Web Search**: Integrated with Google & DuckDuckGo to find real-time information.
- **🌍 Multi-Language Support**: Talk to Planck in **20+ Languages** (e.g., Nepali, Spanish, Hindi, French). The UI adapts, and the agent responds natively while maintaining its reasoning capabilities.
- **💻 Code Execution**: Writes and runs code in **7+ Languages** (Python, Java, JS/TS, C/C++, Go) to solve logic/math problems.
- **📄 Document Analysis**: Upload PDFs or paste URLs—Planck reads and analyzes them (up to 10k chars/page).
- **👁️ Vision Capabilities**: Analyze uploaded images using multimodal vision.
- **⚡ Reactive UI**: A beautiful, dark-mode interface built with React & TailwindCSS, with rich Markdown answers (tables, syntax-highlighted code).
- **🔒 Privacy First**: All sessions are isolated. No data is stored permanently.

## 🛠️ Tech Stack

- **Frontend**: React (Vite), TailwindCSS, Lucide Icons
- **Backend**: FastAPI (Python 3.11), LangGraph (Agent Logic)
- **AI Models**: Groq `openai/gpt-oss-120b` (primary), Gemini `gemini-3.5-flash-lite` and NVIDIA `openai/gpt-oss-20b` (fallbacks)
- **Vector Store**: ChromaDB (In-memory for session context)
- **Deployment**: Docker, Hugging Face Spaces

## ⚡ AI Engine

Planck AI talks to every provider through the same OpenAI-compatible API and tries them in order:

| Priority | Provider | Default model | Get a free key |
|----------|----------|---------------|----------------|
| 1 | **Groq** | `openai/gpt-oss-120b` | [console.groq.com](https://console.groq.com) |
| 2 | **Google Gemini** | `gemini-3.5-flash-lite` | [aistudio.google.com](https://aistudio.google.com/apikey) |
| 3 | **NVIDIA** | `openai/gpt-oss-20b` | [build.nvidia.com](https://build.nvidia.com) |

- **Speed**: Groq's LPU hardware delivers sub-second token generation.
- **Instant failover**: A rate-limited or failing provider is skipped immediately (no retry sleeps); the conversation, including tool calls, carries over to the next one.
- **Tool Calling**: Native function calling for web search, code execution, and document analysis.
- **One key is enough.** Providers without an API key are skipped (Groq is recommended as the primary). Override any default model with `GROQ_MODEL`, `GEMINI_MODEL` or `NVIDIA_MODEL`.

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
   GEMINI_API_KEY=your_key_here    # Optional fallback: https://aistudio.google.com/apikey
   NVIDIA_API_KEY=your_key_here    # Optional fallback: https://build.nvidia.com
   GOOGLE_API_KEY=your_key_here     # For Google Search (Google Cloud Console)
   GOOGLE_CSE_ID=your_cse_id       # For Google Search (Programmable Search Engine)
   ```
   See [`backend/.env.example`](backend/.env.example) for all options.

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
4. Add your `GROQ_API_KEY` in the Space's **Settings > Variables and secrets**. Also add `GEMINI_API_KEY` and `NVIDIA_API_KEY` to enable fallback, and `GOOGLE_API_KEY` / `GOOGLE_CSE_ID` for Google Search.
5. The specific `Dockerfile` at the root will build the React frontend and serve it via FastAPI on port `7860`.

## 📊 Evaluation

The agent is measured, not asserted. `eval/` holds a 30-question golden set, the
harness that runs it and the scorer that grades it. The rubric was **committed
before the first API call** (`eval/RUBRIC.md`), so no metric could be shaped
after seeing results.

```bash
python eval/run_eval.py --out eval/results/baseline.jsonl          # record
python eval/run_eval.py --out eval/results/faulted.jsonl --fault-injection
python eval/score.py eval/results/baseline.jsonl eval/results/faulted.jsonl
```

Recording and grading are separate on purpose: re-scoring never re-spends API
quota, and the raw trajectories in `eval/results/` stay auditable.

### Results

| Metric | Baseline | Primary provider disabled |
|---|---|---|
| Correct tool selection | 24/30 (80.0%) | 23/30 (76.7%) |
| Task success | 20/20 | 20/20 |
| Completed | **30/30** | **30/30** |
| Median latency | 2.67 s | 2.16 s |

Fault injection patches the primary provider to fail on **every** call, so the
agent falls through mid-run at each step. Groq served **0 calls** in that run;
Gemini served 62 and NVIDIA 7.

### What the numbers do and do not say

- **Task success is 20 of 30, not 30 of 30.** Six questions have no stable
  target ("current population of Birmingham"). Four more have targets a pass
  would not demonstrate — `code_07` asks for the median of a list containing the
  answer; `doc_04` and `doc_06` have targets appearing in the papers' own
  titles; `doc_05`'s target is just the ONNX acronym expansion. All ten were
  answered correctly; the test cannot prove four of them, so `score.py` excludes
  them automatically and prints why.
- **Failover costs tail latency, not correctness.** The 5 of 30 requests that
  reached the third provider took 15–24.5 s while the median held at 2.2 s.
- **The failover path is not an emergency path.** Provider instrumentation shows
  the primary was rate-limited on 35 of its 82 call attempts even in the
  baseline run.
- **The tool-selection gap is a routing preference, not an error.** Every miss is
  the agent answering easy arithmetic (GCD, median of 7 numbers) from reasoning
  instead of executing code — and getting it right. The fallback model does this
  more: 7 of 30 questions with no tool call against the primary's 4.
- **n = 30.** Differences of a few points are noise, and latency is a property of
  free-tier endpoints on home broadband.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

Made with ❤️ by Manoj Kumar Thapa