const chat = document.getElementById("chat");
const pid = document.getElementById("pid");

async function analyzeText(text) {
    chat.innerHTML += `<div class="user">${text}</div>`;

    console.log("Sending:", pid); 
    const res = await fetch("/doctor/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            patient_id: pid.value,
            symptoms: text
        })
    });

    const data = await res.json();
    chat.innerHTML += `<div class="bot">${data.reply}</div>`;
    chat.scrollTop = chat.scrollHeight;
}

// 🎤 VOICE
let mediaRecorder;
let audioChunks = [];

async function analyze() {
    const pid = document.getElementById("pid").value;
    const symptomsBox = document.getElementById("symptoms");
    const chat = document.getElementById("chat");

    const text = symptomsBox.value.trim();
    if (!text) return;

    chat.innerHTML += `<div class="user">${text}</div>`;
    symptomsBox.value = "";

    const res = await fetch("/doctor/analyze", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            patient_id: pid,
            symptoms: text
        })
    });

    const data = await res.json();
    chat.innerHTML += `<div class="bot">${data.reply}</div>`;
    chat.scrollTop = chat.scrollHeight;
}

async function startVoice() {
    const pid = document.getElementById("pid").value;
    const bars = document.getElementById("micBars");
    if (!pid) {
        alert("Please enter a patient ID first.");
        return;
    }
    audioChunks = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    bars.classList.remove("hidden");

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

    setTimeout(() => mediaRecorder.stop(), 4000);

    mediaRecorder.onstop = async () => {
        bars.classList.add("hidden");

        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        const form = new FormData();
        form.append("audio", audioBlob);
        form.append("patient_id", pid);

        const res = await fetch("/doctor/voice", {
            method: "POST",
            body: form
        });

        if (!res.ok) {
            alert("Error processing voice input.");
            console.error("Backend error:", await res.text());
            return;
        }
        const data = await res.json();
        console.log("Voice RESPONSE:", data);


        if (data.user_spoken) {
            chat.innerHTML += `<div class="user">${data.user_spoken}</div>`;
        }

        if (data.reply_text) {
            chat.innerHTML += `<div class="bot">${data.reply_text}</div>`;
        }

        if (data.reply_audio) {
            new Audio(data.reply_audio).play();
        }

        chat.scrollTop = chat.scrollHeight;
        
        if (data.reply_audio) {
            new Audio(data.reply_audio).play();
        }
    };
}
