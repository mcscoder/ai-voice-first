## 2.2. User Needs Survey and Comparison with Related Solutions

### 2.2.1. Survey of real user needs
To evaluate user behavior and difficulties in managing personal knowledge, the research team conducted an online survey with 200 respondents (aged 18 to 45, mainly students, developers, researchers, and business managers). The results highlighted major pain points in daily note-taking habits:

*   **78.5%** admitted that they often forget spontaneous creative ideas because it is inconvenient to open a phone or notebook and write them down immediately.
*   **62%** felt it was inconvenient to open apps like Notion or Obsidian on mobile because of long loading times and complex structures that make saving short information require too many steps.
*   **54.5%** wanted an app that supports Vietnamese voice commands and understands meaning rather than only producing raw transcription.
*   **83%** wanted their note app to automatically connect fragmented information, such as linking a work appointment with a person’s contact information, without manual linking.

The survey confirms a strong need for a minimalist note-taking solution with smooth Vietnamese voice support and automatic memory management.

---

### 2.2.2. Comparison of current solutions
To clarify the value of VocalMind, the team compared it with three common knowledge-management and virtual-assistant solution groups based on five core technical criteria:

#### 2.2.2.1. Group 1: Traditional commercial voice assistants (Siri, Google Assistant, Alexa)
These virtual assistants are developed by major technology companies and deeply integrated into mobile operating systems or home IoT devices.
*   **Input method:** Voice-first, with hands-free activation through spoken commands.
*   **Vietnamese support:** Google Assistant is fairly good; Siri supports Vietnamese but still has many limitations in recognizing complex spoken Vietnamese.
*   **Long-term memory:** Not supported. These assistants do not retain long-term conversation context or links between earlier exchanges.
*   **Automatic reasoning:** Very limited; they rely on rigid scripts or direct web searches.
*   **Interaction friction:** Low, users only need to invoke the assistant and issue a command.
*   **Core limitation:** Not designed for knowledge management or personal note-taking; stored information is fragmented and unstructured.

#### 2.2.2.2. Group 2: Traditional static note apps (Notion, Obsidian, Evernote)
These are powerful note-taking tools widely used on desktops to build a personal knowledge base.
*   **Input method:** Text-first. Input depends entirely on keyboard typing.
*   **Vietnamese support:** Good through standard Unicode rendering in the interface.
*   **Long-term memory:** Static memory exists, but organizing, categorizing, and linking notes is entirely manual through folders or bidirectional links.
*   **Automatic reasoning:** Not supported. The system does not understand the content inside text files.
*   **Interaction friction:** Very high on mobile. Opening the app, selecting a destination, creating a file, and typing takes too much time and too many steps.
*   **Core limitation:** Excessive typing friction on mobile prevents quick capture of spontaneous ideas.

#### 2.2.2.3. Group 3: AI-enhanced note assistants (Mem.ai, Notion AI, Evernote AI)
New-generation note apps add LLM features for summarization, search, and writing support.
*   **Input method:** Still text-first. Even with audio capture, they generally stop at raw transcription and do not provide two-way voice dialogue.
*   **Vietnamese support:** Limited or average. These services are mainly optimized for English and often produce awkward Vietnamese or miss local terminology.
*   **Long-term memory:** Good. AI supports semantic search across the stored text corpus.
*   **Automatic reasoning:** Moderate, with text summarization and suggestions for linking similar documents.
*   **Interaction friction:** Moderate. Users still need to open the app and type prompts.
*   **Core limitation:** High service cost, significant response latency due to overseas servers, and no natural voice-based conversational interface.

#### 2.2.2.4. Proposed solution: VocalMind intelligent voice assistant
VocalMind combines voice interaction and knowledge management in one optimized approach.
*   **Input method:** Fully voice-first. One tap to speak and listen to the assistant’s audio response.
*   **Vietnamese support:** Excellent, thanks to the two AI models specialized for Vietnamese: Qwen ASR for speech recognition and Vieneu TTS for natural speech synthesis.
*   **Long-term memory:** Excellent. It automates Memory Graph construction to connect information.
*   **Automatic reasoning:** High, using Mem0 to extract entities and relationships and resolve information conflicts automatically.
*   **Interaction friction:** Extremely low. The one-tap experience is suitable while moving or doing other tasks.

---

### 2.2.3. Detailed analysis of competitors' core limitations

#### 2.2.3.1. Weaknesses of Siri and Google Assistant in knowledge management
Although they have strong speech recognition and large-scale infrastructure, Siri and Google Assistant are not designed for building a "Second Brain." If you say to Siri, "Today I lent Nam a Flutter programming book," Siri may record that in Reminders or Notes as a detached line of text. But if you ask later, "Who did I lend what book to?", Siri cannot analyze the meaning, extract the entities "Nam" and "Flutter programming book," and identify the relationship "lent to" in order to answer correctly. It will simply search keywords or list raw notes containing those keywords.

#### 2.2.3.2. Weaknesses of Notion and Obsidian on mobile
Notion and Obsidian are excellent desktop tools thanks to the large display space and physical keyboard. However, their mobile UI/UX is a major drawback.
*   **Notion:** App startup is relatively slow because it must load cloud data. The block-based interface makes interactions on a small phone screen cumbersome.
*   **Obsidian:** Requires users to manage Markdown file structure themselves. Setting up bidirectional links with the `[[Note Name]]` syntax using a virtual keyboard is very inconvenient and time-consuming.

#### 2.2.3.3. Language limitations of Western AI assistants
Services like Mem.ai and Notion AI work very well for English. However, their understanding of Vietnamese, especially Vietnamese cultural details, local names, and natural emotional Vietnamese speech synthesis, is still limited. Using them directly in the Vietnamese market often results in awkward Vietnamese responses and high latency because the servers are located overseas.

The combination of specialized Vietnamese speech recognition (Qwen ASR), regionally natural Vietnamese speech synthesis (Vieneu TTS), and contextual memory (Mem0) allows VocalMind to overcome these barriers and provide a truly effective Vietnamese PKM solution.
