# EXECUTIVE SUMMARY

## 1. Project Summary
**VocalMind** is a voice-first intelligent memory assistant that acts as a user's "Second Brain." Unlike traditional text-based note-taking apps that require keyboard input, VocalMind lets users interact entirely through natural speech via a Flutter mobile app. The backend is built with FastAPI (Python) and integrates advanced deep learning models: **Qwen ASR** for speech recognition, **Vieneu** for natural Vietnamese speech synthesis, **Mem0** as the graph-based conversational memory layer, and **DeepSeek** as the LLM provider for conversational responses. The system can automatically extract information, organize and connect memories by time and context, and support proactive reminders and intelligent dialogue.

## 2. Methodology
The study followed an Agile/Scrum product-development process combined with Lean Startup thinking. The main methods included:
*   **Survey and requirements analysis:** Identifying friction in current personal knowledge management (PKM) workflows and mapping the customer journey.
*   **System architecture design:** Applying a lightweight service-oriented Client-Server model with asynchronous RESTful APIs.
*   **AI integration:** Using transfer learning and LLMs through Mem0 to build contextual memory.
*   **Testing and evaluation:** Measuring latency, ASR accuracy (Word Error Rate - WER), and end-user satisfaction.

## 3. Key Findings
*   **Mobile app:** Successfully developed a Flutter app with a minimal interface optimized for voice interaction, using Cubit for smooth state management.
*   **Backend system:** Built a FastAPI backend capable of handling multimedia audio streams via PyAV, integrating Qwen ASR, DeepSeek LLM, and Vieneu TTS; a real execution recorded a total response time of about **14.22 seconds**.
*   **Intelligent memory:** Successfully used Mem0 to store user memories consistently, with automatic inference and linking of related events (debts, plans, relationships).

## 4. Recommendations and Startup Direction
*   **Commercialization:** Launch the product as SaaS with two tiers: Free (limited memory storage) and Paid (unlimited memory, assistant personality customization, multi-device sync).
*   **Development plan:** Optimize the AI models for offline execution (Edge AI) to strengthen privacy, and integrate smart wearables.
