import 'dart:typed_data';

import 'package:ai_voice_first/core/error.dart';
import 'package:ai_voice_first/core/permissions/permission_service.dart';
import 'package:ai_voice_first/features/voice/data/audio_recorder_service.dart';
import 'package:ai_voice_first/features/voice/data/transcription_api.dart';
import 'package:ai_voice_first/features/voice/data/voice_language.dart';
import 'package:ai_voice_first/features/voice/presentation/voice_capture_cubit.dart';
import 'package:ai_voice_first/features/voice/presentation/voice_capture_state.dart';
import 'package:ai_voice_first/features/voice/presentation/voice_screen.dart';
import 'package:ai_voice_first/shared/i18n/generated/app_localizations.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('voice screen renders idle state', (WidgetTester tester) async {
    final cubit = VoiceCaptureCubit(
      _FakePermissionService(),
      _FakeAudioRecorderService(),
      _FakeTranscriptionApi(),
      playAssistantSpeech: _noopPlayback,
    );

    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: VoiceScreen(cubit: cubit),
      ),
    );

    expect(find.text('Ready'), findsOneWidget);
    expect(find.byIcon(Icons.mic), findsOneWidget);
    expect(find.byKey(const Key('voice_language_dropdown')), findsNothing);
    expect(find.text('Language'), findsNothing);
    expect(find.text('Cancel'), findsNothing);

    await cubit.close();
  });

  testWidgets('voice screen shows request timer and cancel action', (
    WidgetTester tester,
  ) async {
    final cubit = _TestVoiceCaptureCubit();
    cubit.push(
      VoiceCaptureState(
        status: VoiceCaptureStatus.uploading,
        requestStartedAt: DateTime.now(),
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: VoiceScreen(cubit: cubit),
      ),
    );

    await tester.pump();

    expect(find.text('Uploading…'), findsOneWidget);
    expect(find.text('0:00'), findsOneWidget);
    expect(find.text('Cancel'), findsOneWidget);
    expect(find.byIcon(Icons.hourglass_top), findsOneWidget);

    await cubit.close();
  });

  testWidgets('voice screen animates processing orb without layout errors', (
    WidgetTester tester,
  ) async {
    final cubit = _TestVoiceCaptureCubit();
    cubit.push(
      VoiceCaptureState(
        status: VoiceCaptureStatus.processing,
        requestStartedAt: DateTime.now(),
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: VoiceScreen(cubit: cubit),
      ),
    );

    await tester.pump(const Duration(milliseconds: 800));

    expect(find.text('Processing…'), findsOneWidget);
    expect(find.byType(CustomPaint), findsWidgets);
    expect(tester.takeException(), isNull);

    await cubit.close();
  });

  testWidgets('voice screen renders speaking state', (
    WidgetTester tester,
  ) async {
    final cubit = _TestVoiceCaptureCubit();
    cubit.push(const VoiceCaptureState(status: VoiceCaptureStatus.speaking));

    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: VoiceScreen(cubit: cubit),
      ),
    );

    await tester.pump();

    expect(find.text('Speaking…'), findsOneWidget);

    await cubit.close();
  });

  testWidgets('voice screen lets the user stop recording', (
    WidgetTester tester,
  ) async {
    final cubit = _RecordingAwareTestCubit();
    cubit.push(const VoiceCaptureState(status: VoiceCaptureStatus.recording));

    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: VoiceScreen(cubit: cubit),
      ),
    );

    await tester.tap(find.byIcon(Icons.stop));
    await tester.pump();

    expect(cubit.toggleRecordingCalls, 1);

    await cubit.close();
  });

  testWidgets('voice screen renders failure action', (
    WidgetTester tester,
  ) async {
    final cubit = _TestVoiceCaptureCubit();
    cubit.push(
      const VoiceCaptureState(
        status: VoiceCaptureStatus.failure,
        failure: VoiceCaptureFailure.microphonePermanentlyDenied,
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: VoiceScreen(cubit: cubit),
      ),
    );

    await tester.pump();

    expect(
      find.text('Microphone access is blocked. Open settings to enable it.'),
      findsOneWidget,
    );
    expect(find.text('Open settings'), findsOneWidget);

    await cubit.close();
  });
}

final class _FakePermissionService implements PermissionService {
  @override
  Future<AppPermissionStatus> check(AppPermission permission) async {
    return AppPermissionStatus.granted;
  }

  @override
  Future<bool> openSettings() async => true;

  @override
  Future<AppPermissionStatus> request(AppPermission permission) async {
    return AppPermissionStatus.granted;
  }
}

final class _FakeAudioRecorderService extends AudioRecorderService {
  @override
  Future<void> start() async {}

  @override
  Future<String> stop() async => '/tmp/audio.m4a';

  @override
  Future<void> cancel() async {}

  @override
  Future<void> deleteRecording(String path) async {}
}

final class _FakeTranscriptionApi extends TranscriptionApi {
  _FakeTranscriptionApi() : super(Dio());

  @override
  Future<({NetworkError? error, Uint8List? audio})> respond({
    required String filePath,
    required VoiceLanguage language,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
  }) async {
    return (error: null, audio: Uint8List.fromList(const [1, 2, 3]));
  }
}

final class _TestVoiceCaptureCubit extends VoiceCaptureCubit {
  _TestVoiceCaptureCubit()
    : super(
        _FakePermissionService(),
        _FakeAudioRecorderService(),
        _FakeTranscriptionApi(),
        playAssistantSpeech: _noopPlayback,
      );

  void push(VoiceCaptureState state) => emit(state);
}

final class _RecordingAwareTestCubit extends _TestVoiceCaptureCubit {
  int toggleRecordingCalls = 0;

  @override
  Future<void> toggleRecording() async {
    toggleRecordingCalls += 1;
  }
}

Future<void> _noopPlayback(Uint8List audioBytes) async {}
