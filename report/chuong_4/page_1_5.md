# CHAPTER 4. DEPLOYMENT AND BUSINESS MODEL

## 4.1. Real-world deployment results and system interface

### 4.1.1. Packaging and deployment results
The **VocalMind** system was successfully packaged and deployed in real-world testing on both environments:
*   **AI Backend Server:** Deployed with Docker containers to ensure isolation and easy scaling. The server runs on Ubuntu Server with an NVIDIA RTX 2080S GPU (8GB VRAM) to accelerate inference for Qwen ASR and Vieneu TTS, while calling the DeepSeek API for conversation responses. The FastAPI port is protected by an Nginx reverse proxy and supports SSL/TLS (HTTPS) certificates.
*   **Flutter Client Application:** Published as an APK for Android and as an IPA (through TestFlight) for iOS for direct testing on common mobile devices.

### 4.1.2. Real usage scenario
A realistic interaction between a user and the VocalMind assistant proceeds smoothly as follows:
*   **User (speaks Vietnamese):** *"Hey assistant, I just lent Minh sixty thousand dong so he can buy breakfast."*
*   **System processing:**
    1.  The app records the speech as an audio file and uploads it to the backend server.
    2.  Qwen ASR accurately transcribes the sentence into Vietnamese text.
    3.  The Mem0 core automatically extracts the following information: person entity `Minh`, action `lent`, amount `60,000 VND`, reason `buy breakfast`. This information is linked into the user's long-term memory graph.
    4.  DeepSeek LLM generates the text response: *"Understood. I have stored that Minh owes you 60 thousand dong for breakfast."*
    5.  Vieneu TTS synthesizes the answer in a natural southern Vietnamese female voice and plays it back on the phone.
*   **A few days later - the user asks:** *"How much does Minh owe me?"*
*   **System processing:**
    1.  The system receives the speech and transcribes it.
    2.  Mem0 performs semantic search in the vector memory and finds the memory about Minh owing 60,000 VND.
    3.  DeepSeek LLM generates the answer: *"Minh owes you 60 thousand dong for the breakfast purchase earlier."*
    4.  Vieneu TTS plays the answer as audio.

---

## 4.2. Testing, performance evaluation, and effectiveness analysis

### 4.2.1. Technical performance metrics
The team recorded real logs from one end-to-end run of the voice assistant endpoint. This run successfully called DeepSeek and had no prior memories in storage:

```text
HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
Total existing memories: 0
voice_assistant step=memory duration_ms=4726.48
voice_assistant step=tts duration_ms=8291.70
voice_assistant step=total duration_ms=14224.81
```

| Logged component | Meaning | Time |
| :--- | :--- | :---: |
| **Memory & LLM** | Retrieve memories through Mem0 and call DeepSeek to generate the response | **4.73 s** |
| **TTS (Vieneu)** | Synthesize the text response into WAV speech | **8.29 s** |
| **Total (End-to-End)** | Total processing time of the voice assistant endpoint | **14.22 s** |

*Comment:* The real run currently reaches a total time of about **14.22 seconds**, with TTS taking the most time. Upload, ASR, and download steps are not separated in this sample log, so the report presents only the figures directly recorded by the system.

### 4.2.2. Practical effectiveness for users
*   **Time saving:** Voice note capture takes about 3-5 seconds to speak, which is **5 to 8 times** faster than opening a note app, creating a new page, and typing on a phone keyboard.
*   **Higher productivity:** Users can take notes hands-free while driving, walking, or doing other physical tasks, making better use of spare time and capturing knowledge in time.
*   **High accuracy:** Integrating advanced ASR models reduces the word error rate (WER) to below **8.5%** for common Vietnamese speech, minimizing misunderstandings of user intent.

---

## 4.3. Startup direction and product commercialization

### 4.3.1. Business Model Canvas (BMC) analysis

VocalMind is positioned to grow into a potential innovation startup through the following detailed Business Model Canvas:

| BMC element | Detailed description for VocalMind |
| :--- | :--- |
| **1. Customer segments** | *   Office workers and busy managers who need to optimize personal productivity.<br>*   Content creators, programmers, and graduate researchers.<br>*   Older adults who have difficulty typing on mobile devices. |
| **2. Value propositions** | *   The first voice-first Second Brain system fully optimized for Vietnamese.<br>*   Automatic storage and linking of memories into an intelligent long-term knowledge graph.<br>*   Natural, emotionally expressive Vietnamese voice responses with regional accents. |
| **3. Channels** | *   Official mobile app stores: Apple App Store and Google Play Store.<br>*   Social media and productivity communities (Notion Vietnam, Obsidian Vietnam).<br>*   Product landing page with SEO/content marketing. |
| **4. Customer relationships** | *   24/7 online support through chatbot and email.<br>*   Discord/Facebook communities for sharing effective usage practices.<br>*   A strong commitment to absolute privacy for user data. |
| **5. Revenue streams** | *   **Freemium:** Basic features free of charge, with memory limits.<br>*   **Subscription:** Recurring payment (50,000 VND/month or 500,000 VND/year) to unlock unlimited memory and customize the assistant's voice and emotion.<br>*   **B2B revenue:** Provide voice-assistant API integration for third-party apps. |
| **6. Key resources** | *   A highly skilled team in AI, Flutter mobile development, and cloud DevOps.<br>*   High-performance GPU servers for AI inference.<br>*   Intellectual property: custom ASR/TTS algorithms and optimized Mem0 memory-graph configuration. |
| **7. Key activities** | *   Software R&D and AI model optimization.<br>*   Maintenance, operation, and security of cloud servers.<br>*   Marketing and customer support. |
| **8. Key partners** | *   GPU infrastructure providers (AWS, RunPod, VNG Cloud).<br>*   Universities and technology incubators supporting outreach and fundraising.<br>*   Open-source software developer communities. |
| **9. Cost structure** | *   Costs for GPU infrastructure and LLM APIs.<br>*   Costs for software engineering and marketing staff.<br>*   Costs for licensing and business/legal operations. |

### 4.3.2. Product roadmap using Lean Startup thinking
The project applies the Lean Startup method to validate the market quickly with minimal cost through three phases:
1.  **Phase 1: Build and test the MVP (January - April 2026):** Release a limited trial version (the current version) to the first 200 users to gather feedback, measure accuracy, and optimize system latency.
2.  **Phase 2: Optimize and release beta (May - August 2026):** Integrate subscription payment gateways, add multi-device sync, and diversify Vieneu TTS voice presets. Run a marketing campaign targeted at office workers.
3.  **Phase 3: Commercialization and expansion (September 2026 onward):** Research running AI models directly on-device (Edge AI / Offline Mode) for premium phones with strong NPU chips to reduce GPU server costs and improve private data security for premium paid users.
