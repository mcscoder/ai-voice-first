// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'AI Voice First';

  @override
  String get appHeadline => 'Voice-first product shell';

  @override
  String get appDescription =>
      'This project is now a clean baseline for building AI Voice First without starter demo flows.';

  @override
  String get appNextStep =>
      'Next step: replace this landing screen with your voice capture, transcript, and orchestration experience.';

  @override
  String get voiceTranscriptPlaceholder =>
      'Tap the microphone and start speaking.';

  @override
  String get voiceIdleStatus => 'Ready';

  @override
  String get voiceListeningStatus => 'Listening…';

  @override
  String get voiceTranscribingStatus => 'Transcribing…';

  @override
  String get voiceSuccessStatus => 'Transcript ready';

  @override
  String get voiceEmptyStatus => 'No speech detected';

  @override
  String get voiceMicDeniedStatus => 'Microphone access is required to record.';

  @override
  String get voiceMicPermanentlyDeniedStatus =>
      'Microphone access is blocked. Open settings to enable it.';

  @override
  String get voiceNetworkErrorStatus =>
      'Could not reach the transcription service.';

  @override
  String get voiceBadAudioStatus => 'The recording could not be transcribed.';

  @override
  String get voiceBackendErrorStatus => 'The transcription service failed.';

  @override
  String get voiceUnknownErrorStatus => 'Something went wrong. Try again.';

  @override
  String get voiceOpenSettings => 'Open settings';

  @override
  String get voiceLanguageLabel => 'Language';

  @override
  String get voiceStartHint => 'Tap to start';

  @override
  String get voiceStopHint => 'Tap to stop';

  @override
  String get voiceEmptyTranscript => 'No speech detected.';
}
