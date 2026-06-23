# APPENDIX B. DETAILED TEST CASES

## 1. Testing methodology and process
The **VocalMind** system follows a strict testing process that includes Unit Tests for business-logic functions and Integration Tests for the end-to-end Client-Server flow.

*   **Backend:** Uses `pytest` as the test runner. Tests focus on binary audio decoding, ASR and TTS inference calls, and Mem0 memory storage behavior.
*   **Frontend:** Uses `flutter_test` together with BLoC state testing (`bloc_test`) to verify the `VoiceCaptureCubit` state machine when microphone permission is granted/denied or when the network fails.

---

## 2. Backend unit test scenarios (Pytest)

### Scenario TC-B1: Raw audio decoding test
*   **Goal:** Ensure `AsrService.decode_audio_bytes` correctly decodes a binary recording into a NumPy float32 array.
*   **Input data:** A sample `.m4a` audio file containing 5 seconds of speech.
*   **Expected result:**
    *   The function does not raise an exception.
    *   The returned array has dtype `np.float32`.
    *   The sample rate is detected correctly (for example, 16000Hz or 48000Hz).
*   **Test command:** `pytest tests/test_asr.py`

### Scenario TC-B2: TTS input validation test
*   **Goal:** Ensure the system detects and blocks speech synthesis requests with empty text or text that exceeds the allowed configuration limit.
*   **Input data:**
    *   Request 1: Text = `""` (empty).
    *   Request 2: Text containing 5000 words (exceeding `max_text_length = 1000`).
*   **Expected result:**
    *   Request 1: The system returns HTTP 422 or raises `ValueError("Text must not be empty.")`.
    *   Request 2: The system refuses to process the request and reports that the text length exceeds the limit.

---

## 3. Frontend state test scenarios (Flutter App)

The team built automated Flutter tests to check the consistency of `VoiceCaptureCubit` UI responses:

### Scenario TC-F1: User denies microphone permission
*   **Goal:** Ensure the app detects denied microphone permission and shows the correct error to the user.
*   **Procedure:**
    1.  Mock `PermissionService` to return `AppPermissionStatus.denied` when microphone permission is requested.
    2.  Call `cubit.startRecording()`.
*   **Expected result (state stream):**
    *   The Cubit state changes from `VoiceCaptureStatus.idle` to `VoiceCaptureStatus.failure`.
    *   The recorded error is `VoiceCaptureFailure.microphoneDenied`.
    *   The screen shows a prompt asking for microphone permission.

### Scenario TC-F2: Network failure while uploading audio
*   **Goal:** Ensure the app handles connection failures well and does not freeze.
*   **Procedure:**
    1.  Grant microphone permission successfully.
    2.  Mock `TranscriptionApi` to throw a `Timeout` or `NetworkError` when sending data.
    3.  Call `cubit.stopRecording()`.
*   **Expected result (state stream):**
    *   The Cubit emits `VoiceCaptureStatus.uploading`.
    *   When the API fails, the Cubit immediately emits `VoiceCaptureStatus.failure`.
    *   The recorded error is `VoiceCaptureFailure.network`.
    *   The interface shows the mic button with a red network error message so the user can retry.

---

## 4. Running the full automated test suite
To test code reliability before continuous integration (CI/CD), run the following commands:

### Run backend tests:
```bash
cd backend
pytest -v
```

### Run frontend tests:
```bash
cd app
flutter test
```
