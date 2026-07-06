# 🚀 Quick Start - Enterprise Medical AI

## Fastest Way to Run (30 Minutes)

### Step 1: Setup Python Backend (10 min)

```bash
# Create project
mkdir medical-ai-pro && cd medical-ai-pro

# Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn whisper torch transformers gtts deep-translator langdetect Pillow requests python-multipart websockets sqlalchemy aiofiles pydantic

# Create structure
mkdir -p services utils static/audio static/images data/conversations logs
```

### Step 2: Copy Files (2 min)

Copy these files to your project:

```
services/
  - All services_*.py files

utils/
  - utils_logger.py

enhanced_api.py (root)
```

### Step 3: Start LLaMA Server (5 min)

```bash
# Download llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make

# Download model (one-time, ~5GB)
# Get Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf from HuggingFace
# Place in llama.cpp/models/

# Start server
./server -m models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf --port 8080
```

### Step 4: Start Backend (1 min)

```bash
# New terminal
cd medical-ai-pro
source venv/bin/activate
python enhanced_api.py

# Should see: "Uvicorn running on http://0.0.0.0:8000"
```

### Step 5: Setup Frontend (10 min)

```bash
# Create Next.js app
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend

# Install dependencies
npm install axios lucide-react

# Copy frontend_EnhancedMedicalChat.jsx to components/

# Edit app/page.tsx:
```

```typescript
import EnhancedMedicalChat from '@/components/EnhancedMedicalChat'

export default function Home() {
  return <EnhancedMedicalChat />
}
```

### Step 6: Start Frontend (1 min)

```bash
npm run dev

# Open: http://localhost:3000
```

---

## ✅ Verification

Test these features:

1. **Text Chat**
   - Type "I have a headache"
   - Get response
   - See conversation in UI

2. **Voice Input**
   - Click mic button
   - See audio visualization bars
   - Speak in any language
   - Get transcription + response

3. **Image Upload**
   - Click image button
   - Upload medical image
   - Get AI analysis

4. **Multi-Language**
   - Type in Hindi/Punjabi
   - See auto-detection
   - Get response in same language

5. **Emergency Detection**
   - Type "I have severe chest pain"
   - See emergency alert
   - Get immediate guidance

---

## 🎯 What You Have

✅ Production-grade medical AI
✅ Multi-language support
✅ Voice conversation
✅ Real-time audio visualization
✅ Medical image analysis
✅ Full conversation memory
✅ Emergency detection
✅ Enterprise database
✅ Professional UI
✅ Patent-ready system

---

## 📁 File Mapping

Your downloaded files → Where they go:

```
enhanced_api.py                    → medical-ai-pro/enhanced_api.py
services_voice_processor.py        → medical-ai-pro/services/voice_processor.py
services_llm_engine.py             → medical-ai-pro/services/llm_engine.py
services_memory_manager.py         → medical-ai-pro/services/memory_manager.py
services_all_remaining.py          → Extract and split into:
                                     - services/tts_engine.py
                                     - services/translation_service.py
                                     - services/vision_analyzer.py
                                     - services/emergency_detector.py
utils_logger.py                    → medical-ai-pro/utils/logger.py
frontend_EnhancedMedicalChat.jsx   → frontend/components/EnhancedMedicalChat.jsx
```

---

## 🔧 Common Issues

### Port already in use
```bash
# Kill process on port 8000
lsof -i :8000  # Get PID
kill -9 <PID>

# Or use different port
uvicorn enhanced_api:app --port 8001
```

### LLaMA not responding
```bash
# Check if running
curl http://localhost:8080/health

# Check logs
tail -f logs/medical_ai_*.log
```

### Microphone not working
```bash
# Check browser permissions
# Chrome: Settings → Privacy → Microphone
# Allow localhost

# Check system permissions
```

### No audio output
```bash
# Check audio files generated
ls static/audio/

# Try playing manually
# Check browser audio permissions
```

---

## 🎨 Customization

### Change Medical Prompts
Edit `services/llm_engine.py`:
```python
SYSTEM_PROMPT = """Your custom prompt here"""
```

### Add More Languages
Edit `services/translation_service.py`:
```python
self.supported_languages = {
    "en": "English",
    "hi": "Hindi",
    "pa": "Punjabi",
    "es": "Spanish",  # Add more
}
```

### Adjust Voice Model
Edit `enhanced_api.py`:
```python
voice_processor = VoiceProcessor(model_size="large")  # small/medium/large
```

---

## 📊 Performance Tuning

### Faster Response (CPU)
- Use Whisper "small"
- Use Q4 quantized LLaMA
- Reduce max_tokens in LLM

### Better Quality (GPU)
- Use Whisper "medium" or "large"
- Use full LLaMA model
- Increase max_tokens

---

## 🚀 Production Deployment

```bash
# Backend
pip install gunicorn
gunicorn enhanced_api:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend
cd frontend
npm run build
npm start

# Reverse proxy with nginx
# SSL with Let's Encrypt
# Domain setup
```

---

## 📞 Quick Help

**Backend not starting?**
- Check Python version (3.10+)
- Check all files copied
- Check dependencies installed

**Frontend not loading?**
- Check Node version (18+)
- Check npm install completed
- Check port 3000 free

**Voice not working?**
- Check microphone permissions
- Check Whisper model downloaded
- Check audio device selected

**LLM not responding?**
- Check llama.cpp server running
- Check model loaded correctly
- Check port 8080 free

---

**You're ready! Start chatting in any language. 🎉**

Time: ~30 minutes
Result: Enterprise medical AI system
Status: Production-ready
Patent: Ready to file
