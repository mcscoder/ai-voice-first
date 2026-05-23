import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[Locale('en')];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'AI Voice First'**
  String get appTitle;

  /// No description provided for @appHeadline.
  ///
  /// In en, this message translates to:
  /// **'Voice-first product shell'**
  String get appHeadline;

  /// No description provided for @appDescription.
  ///
  /// In en, this message translates to:
  /// **'This project is now a clean baseline for building AI Voice First without starter demo flows.'**
  String get appDescription;

  /// No description provided for @appNextStep.
  ///
  /// In en, this message translates to:
  /// **'Next step: replace this landing screen with your voice capture, assistant speech, and orchestration experience.'**
  String get appNextStep;

  /// No description provided for @voiceTranscriptPlaceholder.
  ///
  /// In en, this message translates to:
  /// **'Your assistant speech will play here.'**
  String get voiceTranscriptPlaceholder;

  /// No description provided for @voiceIdleStatus.
  ///
  /// In en, this message translates to:
  /// **'Ready'**
  String get voiceIdleStatus;

  /// No description provided for @voiceListeningStatus.
  ///
  /// In en, this message translates to:
  /// **'Recording…'**
  String get voiceListeningStatus;

  /// No description provided for @voiceRecordingStatus.
  ///
  /// In en, this message translates to:
  /// **'Recording…'**
  String get voiceRecordingStatus;

  /// No description provided for @voiceTranscribingStatus.
  ///
  /// In en, this message translates to:
  /// **'Uploading…'**
  String get voiceTranscribingStatus;

  /// No description provided for @voiceUploadingStatus.
  ///
  /// In en, this message translates to:
  /// **'Uploading…'**
  String get voiceUploadingStatus;

  /// No description provided for @voiceProcessingStatus.
  ///
  /// In en, this message translates to:
  /// **'Processing…'**
  String get voiceProcessingStatus;

  /// No description provided for @voiceSpeakingStatus.
  ///
  /// In en, this message translates to:
  /// **'Speaking…'**
  String get voiceSpeakingStatus;

  /// No description provided for @voiceSuccessStatus.
  ///
  /// In en, this message translates to:
  /// **'Speech played'**
  String get voiceSuccessStatus;

  /// No description provided for @voiceEmptyStatus.
  ///
  /// In en, this message translates to:
  /// **'No speech detected'**
  String get voiceEmptyStatus;

  /// No description provided for @voiceMicDeniedStatus.
  ///
  /// In en, this message translates to:
  /// **'Microphone access is required to record.'**
  String get voiceMicDeniedStatus;

  /// No description provided for @voiceMicPermanentlyDeniedStatus.
  ///
  /// In en, this message translates to:
  /// **'Microphone access is blocked. Open settings to enable it.'**
  String get voiceMicPermanentlyDeniedStatus;

  /// No description provided for @voiceNetworkErrorStatus.
  ///
  /// In en, this message translates to:
  /// **'Could not reach the assistant service.'**
  String get voiceNetworkErrorStatus;

  /// No description provided for @voiceBadAudioStatus.
  ///
  /// In en, this message translates to:
  /// **'The recording could not be understood.'**
  String get voiceBadAudioStatus;

  /// No description provided for @voiceBackendErrorStatus.
  ///
  /// In en, this message translates to:
  /// **'The assistant service failed.'**
  String get voiceBackendErrorStatus;

  /// No description provided for @voiceUnknownErrorStatus.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Try again.'**
  String get voiceUnknownErrorStatus;

  /// No description provided for @voiceOpenSettings.
  ///
  /// In en, this message translates to:
  /// **'Open settings'**
  String get voiceOpenSettings;

  /// No description provided for @voiceLanguageLabel.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get voiceLanguageLabel;

  /// No description provided for @voiceStartHint.
  ///
  /// In en, this message translates to:
  /// **'Tap to start'**
  String get voiceStartHint;

  /// No description provided for @voiceStopHint.
  ///
  /// In en, this message translates to:
  /// **'Tap to stop'**
  String get voiceStopHint;

  /// No description provided for @voiceEmptyTranscript.
  ///
  /// In en, this message translates to:
  /// **'No speech detected.'**
  String get voiceEmptyTranscript;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
