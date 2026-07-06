# 🏥 AI Doctor Pro — Run From Scratch Guide

Complete step-by-step guide to run the entire project on a fresh Windows machine.

---

## Prerequisites

| Software | Version | Download |
|----------|---------|----------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| Git | Latest | https://git-scm.com/ |
| llama.cpp (llama-server) | Latest | https://github.com/ggerganov/llama.cpp/releases |

You also need a GGUF model file:
- **Recommended:** `Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`
- Download from HuggingFace: search for "Meta-Llama-3.1-8B-Instruct-GGUF"

---

## Step 1: Clone / Copy the Project

```bash
cd D:\
# If from Git:
git clone <your-repo-url> ai-doctor-v3
# Or just copy the folder
```

---

## Step 2: Set Up Python Virtual Environment

Open PowerShell / Terminal in the project root:

```powershell
cd D:\ai-doctor-v3

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate

# Install all Python dependencies
pip install -r requirements_enterprise.txt
```

> **Note:** `torch` may take a while to download (~2 GB). For GPU support, install the CUDA version of PyTorch from https://pytorch.org/get-started/locally/ before running pip install.

### First-time model downloads (automatic)

On first run, these models will auto-download:
- **Whisper "base"** (~140 MB) — for speech-to-text
- **BLIP** (~1 GB) — for medical image analysis
- **all-MiniLM-L6-v2** (~90 MB) — for RAG embeddings
- **EasyOCR** (~150 MB) — for lab report OCR

---

## Step 3: Start the LLM Server (llama-server)

In a **separate terminal**, start llama-server with your GGUF model:

```powershell
# Adjust the path to your llama-server.exe and model file
llama-server.exe -m "D:\path\to\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" -c 4096 --host 0.0.0.0 --port 8080
```

Options:
- `-c 4096` — context window size (increase for longer conversations)
- `-ngl 35` — offload layers to GPU (if you have CUDA-capable GPU)
- `--threads 8` — CPU threads to use

Wait until you see `server listening` in the output.

**Verify:** Open http://localhost:8080/health in your browser — should show `{"status":"ok"}`.

---

## Step 4: Start the Backend API Server

In a **new terminal**:

```powershell
cd D:\ai-doctor-v3
.\venv\Scripts\Activate
python -m uvicorn enhanced_api:app --host 0.0.0.0 --port 8000
```

Wait for the startup — first run downloads AI models (Whisper, BLIP, etc.).

**Verify:** Open http://localhost:8000/api/health in your browser — should show:
```json
{"status": "healthy", "services": {"llm": true, "voice": true, ...}}
```

---

## Step 5: Set Up & Start the Frontend

In a **new terminal**:

```powershell
cd D:\ai-doctor-v3\frontend

# Install Node.js dependencies (first time only)
npm install

# Start development server
npx next dev --port 3001
```

**Verify:** Open http://localhost:3001 in your browser — you should see the AI Doctor Pro interface.

---

## Step 6: Use the Application

Open **http://localhost:3001** in Chrome or Edge.

### Features Available:
1. **Chat** — Type symptoms in English, Hindi, or Punjabi
2. **Voice Input** — Click mic icon, select language (Globe icon), speak
3. **X-ray / Photo Upload** — Click image icon or upload via body map
4. **Lab Report Upload** — Click document icon to auto-parse lab values
5. **Body Map** — Click body regions → upload X-rays per region
6. **Symptom Checker** — Tools tab → enter symptoms → AI differential diagnosis
7. **Drug Interactions** — Tools tab → enter 2+ medications → check interactions
8. **Mental Health** — Tools tab → PHQ-9 (depression) or GAD-7 (anxiety) screening
9. **Health Report** — Reports tab → generate AI summary of all health data
10. **Dark Mode** — Toggle via moon/sun icon in sidebar

---

## Architecture Summary

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  LLM Server  │
│   Next.js    │     │   FastAPI    │     │ llama-server  │
│  :3001       │◀────│  :8000       │◀────│  :8080        │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                     ┌──────┴──────┐
                     │  AI Models  │
                     │• Whisper STT│
                     │• BLIP Vision│
                     │• EasyOCR    │
                     │• FAISS RAG  │
                     │• pyttsx3 TTS│
                     │• SQLite DB  │
                     └─────────────┘
```

---

## Ports Used

| Port | Service |
|------|---------|
| 3001 | Frontend (Next.js) |
| 8000 | Backend API (FastAPI) |
| 8080 | LLM Server (llama-server) |

---

## Troubleshooting

### "llm": false in health check
→ llama-server is not running or not on port 8080. Start it first.

### Voice/mic not working
→ Allow microphone permissions in Chrome. Use HTTPS or localhost only.
→ Select the correct language using the Globe icon before recording.

### Whisper model download fails
→ Check internet connection. Whisper downloads models to `~/.cache/whisper/`.

### Frontend shows blank page
→ Check terminal for Next.js errors. Run `npm install` if dependencies are missing.

### Image analysis is slow
→ BLIP runs on CPU by default. First analysis is slow (model loading). Subsequent ones are faster.

### CUDA out of memory
→ Reduce llama-server `-ngl` value or use CPU-only mode (remove `-ngl` flag).
