# AI Doctor v3: Complete Codebase Walkthrough

This guide breaks down every major file in your project, explaining what the code does section by section. While reading actual code line-by-line is helpful, interviewers care more about **understanding the logic blocks** (e.g., "Lines 100-150 connect to the database, lines 151-200 handle user input"). Use this guide to deeply understand how your project works.

---

## 1. The Core API: [enhanced_api.py](file:///d:/ai-doctor-v3/enhanced_api.py)
This is the brain of your backend. It uses **FastAPI** to expose URLs (endpoints) that your frontend can talk to.

### Lines 1 - 50: Setup and Imports
- **What it does:** Imports everything needed (FastAPI modules, Pydantic for validation, and all your custom services like [VoiceProcessor](file:///d:/ai-doctor-v3/services/services_voice_processor.py#20-307), [MedicalLLMEngine](file:///d:/ai-doctor-v3/services/services_llm_engine.py#18-608), etc.).
- **Line 46-55 (Initialization):** This is where you create instances of all your service classes. `db = HealthDatabase()`, `llm_engine = MedicalLLMEngine()`, etc. This makes these tools available to all the API routes below.
- **Lines 57-61 (CORS):** `CORSMiddleware` is added so your frontend (which might run on a different port) is allowed to securely request data from this backend API without the browser blocking it.

### Lines 100 - 250: The Chat Stream (`/api/chat/stream`)
- **What it does:** This is the most complex point. It handles real-time streaming chat.
- It receives a [ChatRequest](file:///d:/ai-doctor-v3/enhanced_api.py#70-76) (which includes the `patient_id` and the [message](file:///d:/ai-doctor-v3/services/database.py#320-331)).
- It fetches the patient's database history and active medications.
- It decides the "Generation Mode" (detailed, balanced, fast). If it's detailed, it tells the LLM to write long medical notes.
- It calls `llm_engine.stream_chat(...)`, which opens a connection to your local Llama-3 model and pulls words one-by-one, yielding them back to the frontend immediately so the UI feels fast.

### Lines 250 - 890: Health Tools and Reference APIs
- **`/api/specialists`**: Returns the list of specialized AI personas (Cardiologist, Dermatologist, etc.).
- **`/api/medical-library/search`**: Searches your offline medicine database.
- **`/api/symptom-triage`**: Takes patient symptoms, calls `triage.analyze_symptoms`, and returns a color-coded urgency (Red/Yellow/Green).
- **`/api/patient/{id}/health-timeline`**: Fetches all historical events and lab results from the database, formats them into a timeline, and returns them for the Overview dashboard.

### Lines 890 - 980: Health Score and Trajectory (Novel Feature)
- **`/api/patient/{id}/health-score`**: Calculates an A-F grade based on abnormal lab results, missed medications, and emergency events.
- **`/api/patient/{id}/health-trajectory`**: The new patentable feature. It calls `predictive_engine.generate_health_forecast` to run linear regression on past labs and predict future health trends.

### Lines 1800+ : File Uploads (OCR/Vision/Audio)
- **`/api/upload/lab-report`**: Saves the `PDF/Image` to the server, applies OCR (`ocr_engine.extract_text`), uses the LLM to extract meaning, and saves structured lab values out of unstructured text directly to the DB.
- **`/api/upload/medical-image`**: Saves an X-ray/skin photo, calls `vision_analyzer.analyze()` to check for abnormalities, and links it to the patient's body map.

---

## 2. Artificial Intelligence: [services/services_llm_engine.py](file:///d:/ai-doctor-v3/services/services_llm_engine.py)
This file connects your Python code to the local `llama-server.exe` running your Llama 3 model.

### Lines 14 - 110: System Prompts
- **`SYSTEM_PROMPT`**: The massive block of text that tells the LLM how to act. "You are MedAssist, a highly capable clinical AI assistant... Format differential diagnoses using ## headers". This is how you control the AI's behavior and formatting.
- **`COMPACT_SYSTEM_PROMPT`**: The backup plan. If the conversation history is too huge and exceeds 4096 tokens, it uses this shorter prompt to save space.

### Lines 112 - 275: Memory and Trimming
- **[_trim_messages_to_fit()](file:///d:/ai-doctor-v3/services/services_llm_engine.py#153-219)**: A crucial function. Because AI models have a memory limit (Context Window), this function calculates how many "tokens" (roughly words) are in the chat history. If there are too many, it starts cutting off the oldest messages to ensure the server doesn't crash.

### Lines 276 - 365: `stream_chat()` Output
- **What it does:** Sends an HTTP POST to `http://127.0.0.1:8080/v1/chat/completions` with the prompt.
- **The Loop:** It reads the response piece by piece (`chunk`), decodes the JSON, and pulls out the newly generated word. It handles errors if the llama-server is offline.

---

## 3. Database Management: [services/database.py](file:///d:/ai-doctor-v3/services/database.py)
This handles standard SQLite data storage, but with added security.

### Lines 20 - 61: Field-Level Encryption
- **[encrypt_field()](file:///d:/ai-doctor-v3/services/database.py#44-49) and [decrypt_field()](file:///d:/ai-doctor-v3/services/database.py#51-60)**: For HIPAA-compliance emulation. Sensitive fields like a patient's name, allergies, or family history are run through `Fernet` (base64 encryption) before being saved to the database. Even if someone steals [health_records.db](file:///d:/ai-doctor-v3/data/health_records.db), they can't read patient names without the secret [.encryption_key](file:///d:/ai-doctor-v3/data/.encryption_key) file.

### Lines 85 - 225: The Schema ([_init_schema](file:///d:/ai-doctor-v3/services/database.py#85-225))
- **What it does:** This block uses SQL strings (`CREATE TABLE IF NOT EXISTS`) to define the structure for 8 tables: [patients](file:///d:/ai-doctor-v3/enhanced_api.py#647-650), [sessions](file:///d:/ai-doctor-v3/enhanced_api.py#663-666), [messages](file:///d:/ai-doctor-v3/services/services_llm_engine.py#153-219), `health_events`, [lab_results](file:///d:/ai-doctor-v3/enhanced_api.py#695-698), `medical_images`, [medications](file:///d:/ai-doctor-v3/enhanced_api.py#1461-1480), and `medication_logs`. 

### Lines 226 - 650: CRUD Methods (Create, Read, Update, Delete)
- Functions like [get_patient()](file:///d:/ai-doctor-v3/enhanced_api.py#651-657), [save_message()](file:///d:/ai-doctor-v3/services/database.py#320-331), and [get_lab_results()](file:///d:/ai-doctor-v3/enhanced_api.py#695-698) abstract away the SQL commands. When the API needs a lab result, it calls `db.get_lab_results()`, and this file executes `SELECT * FROM lab_results WHERE patient_id=?`.

---

## 4. Speech and Vision: [services/services_voice_processor.py](file:///d:/ai-doctor-v3/services/services_voice_processor.py) & [services_all_remaining.py](file:///d:/ai-doctor-v3/services/services_all_remaining.py)

### [services_voice_processor.py](file:///d:/ai-doctor-v3/services/services_voice_processor.py)
- Setup uses **faster-whisper** (a highly optimized version of OpenAI's Whisper model).
- **[transcribe()](file:///d:/ai-doctor-v3/services/services_voice_processor.py#99-194)**: Takes a raw audio file path, runs `self.model.transcribe(audio_file)`, and extracts the exact text. Crucially, it handles Hindi and Punjabi translation logic if `target_lang="hi"`.

### [services_all_remaining.py](file:///d:/ai-doctor-v3/services/services_all_remaining.py) (TTS, Translation, Vision)
- **[TTSEngine](file:///d:/ai-doctor-v3/services/services_all_remaining.py#16-112) (Text-to-Speech)**: Uses `edge-tts` (Microsoft's cloud neural voices). It takes text from the LLM, maps Hindi/Punjabi context to the `hi-IN-SwaraNeural` voice, and generates a [.mp3](file:///d:/ai-doctor-v3/static/audio/patient_1769786212819_83667244-f209-497e-bbf5-0089d6dc09ef_20260130_204820.mp3) file that the frontend plays.
- **[VisionAnalyzer](file:///d:/ai-doctor-v3/services/services_all_remaining.py#158-325) (Image AI)**: Connects to a secondary LLM pipeline (like LLaVA if active) to analyze skin rashes or X-rays and return structured JSON descriptions of what it sees.

---

## 5. Patent Feature: [services/predictive_health.py](file:///d:/ai-doctor-v3/services/predictive_health.py)
This is your custom-built logic engine for detecting anomalies in lab trends over time.

### The Algorithm: [_linear_regression()](file:///d:/ai-doctor-v3/services/predictive_health.py#88-117) (Line 86)
- This is raw math. It takes a bunch of plot points (X = days passed, Y = lab test value). It calculates the trajectory line. If the line is pointing sharply up (positive slope), a value is accelerating. 

### Core Logic: [analyze_lab_trajectory()](file:///d:/ai-doctor-v3/services/predictive_health.py#138-277)
- Fetches all historical data for a specific lab (e.g., Blood Sugar).
- Calculates the `percent_change`.
- Compares the first half of the timeline to the second half to check if the disease is **accelerating** or **decelerating**.
- **`intervention_window`**: Calculates literally how many days remain before the mathematical line crosses the "Critical Threshold". 

### Medication Correlation: [detect_medication_correlations()](file:///d:/ai-doctor-v3/services/predictive_health.py#278-363)
- Grabs the date the patient started a specific medicine. Grabs the lab results from 30 days before, and 30-120 days after. If the After average is significantly better than the Before average, it concludes the medication is mathematically effective.

---

## 6. The User Interface: [frontend_EnhancedMedicalChat.jsx](file:///d:/ai-doctor-v3/frontend/components/frontend_EnhancedMedicalChat.jsx)
This single massive file is a React application that controls the entire browser interface.

### State Hooks (`useState`)
- Lines 850-950 declare all the memory variables. `patientId` remembers who is logged in. [messages](file:///d:/ai-doctor-v3/services/services_llm_engine.py#153-219) holds the chat history. `isRecording` knows if the microphone icon should be red.

### `useEffect` Loaders
- Line 1055: `useEffect(() => { loadSessions(); ... }, [patientId])`. Whenever the `patientId` changes, this tells React to instantly fetch the chat history, lab results, and dashboard stats for that specific patient from the backend API.

### Rendering: The Giant `return ( ... )` Statement (Line ~1600+)
The interface is split into chunks:
1. **The Left Sidebar**: Shows the list of patients under the doctor's care.
2. **The Main Chat Area (tab === "chat")**: Maps through the [messages](file:///d:/ai-doctor-v3/services/services_llm_engine.py#153-219) array and draws bubbles. If the message is from the "user", it draws it aligned to the right. If from "medassist", aligned left. It also renders the [input](file:///d:/ai-doctor-v3/enhanced_api.py#1816-1865) box where you type.
3. **The Overview Dashboard (tab === "dashboard")**: This renders the new `Predictive Health Trajectory` cards, throwing up red/yellow alert banners if the backend's `predictive_engine` flagged a dangerous trend. It displays the `Health Score` ring.
4. **The Tools Panel (tab === "tools")**: Renders forms to upload images, check symptoms, or add medications.
