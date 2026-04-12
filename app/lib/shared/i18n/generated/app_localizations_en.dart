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
}
