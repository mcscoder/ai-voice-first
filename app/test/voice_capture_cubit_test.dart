import 'package:ai_voice_first/core/error.dart' as app_error;
import 'package:ai_voice_first/core/permissions/permission_service.dart';
import 'package:ai_voice_first/features/voice/data/audio_recorder_service.dart';
import 'package:ai_voice_first/features/voice/data/transcription_api.dart';
import 'package:ai_voice_first/features/voice/data/transcription_response.dart';
import 'package:ai_voice_first/features/voice/data/voice_language.dart';
import 'package:ai_voice_first/features/voice/presentation/voice_capture_cubit.dart';
import 'package:ai_voice_first/features/voice/presentation/voice_capture_state.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hydrated_bloc/hydrated_bloc.dart';

void main() {
  group('VoiceCaptureCubit', () {
    test('starts listening when microphone permission is granted', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(),
        FakeTranscriptionApi.success('ignored'),
      );

      await cubit.startRecording();

      expect(cubit.state.status, VoiceCaptureStatus.listening);
      expect(cubit.state.failure, isNull);
      await cubit.close();
    });

    test('fails when microphone permission is denied', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(
          checkStatus: AppPermissionStatus.denied,
          requestStatus: AppPermissionStatus.denied,
        ),
        FakeAudioRecorderService(),
        FakeTranscriptionApi.success('ignored'),
      );

      await cubit.startRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.microphoneDenied);
      await cubit.close();
    });

    test('fails with permanent-denied state', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(
          checkStatus: AppPermissionStatus.permanentlyDenied,
        ),
        FakeAudioRecorderService(),
        FakeTranscriptionApi.success('ignored'),
      );

      await cubit.startRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(
        cubit.state.failure,
        VoiceCaptureFailure.microphonePermanentlyDenied,
      );
      await cubit.close();
    });

    test('transcribes successfully after stop', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success('Hello from backend'),
      );

      cubit.selectLanguage(VoiceLanguage.vietnamese);
      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.success);
      expect(cubit.state.transcript, 'Hello from backend');
      expect(cubit.state.selectedLanguage, VoiceLanguage.vietnamese);
      await cubit.close();
    });

    test('updates selected language when idle', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success('Hello from backend'),
      );

      cubit.selectLanguage(VoiceLanguage.vietnamese);

      expect(cubit.state.selectedLanguage, VoiceLanguage.vietnamese);
      await cubit.close();
    });

    test('uses selected language when transcribing', () async {
      final api = FakeTranscriptionApi.success('Hello from backend');
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        api,
      );

      cubit.selectLanguage(VoiceLanguage.vietnamese);
      await cubit.startRecording();
      await cubit.stopRecording();

      expect(api.lastLanguageCode, 'vi');
      await cubit.close();
    });

    test('shows empty state when backend returns blank transcript', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success('   '),
      );

      cubit.selectLanguage(VoiceLanguage.vietnamese);
      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.empty);
      expect(cubit.state.transcript, isEmpty);
      expect(cubit.state.selectedLanguage, VoiceLanguage.vietnamese);
      await cubit.close();
    });

    test('maps timeout errors to network failure', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.error(
          app_error.Timeout(exception: Exception('timeout')),
        ),
      );

      cubit.selectLanguage(VoiceLanguage.vietnamese);
      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.network);
      expect(cubit.state.selectedLanguage, VoiceLanguage.vietnamese);
      await cubit.close();
    });

    test('maps bad request errors to bad audio failure', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.error(
          app_error.BadRequest(exception: Exception('bad request')),
        ),
      );

      cubit.selectLanguage(VoiceLanguage.vietnamese);
      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.badAudio);
      expect(cubit.state.selectedLanguage, VoiceLanguage.vietnamese);
      await cubit.close();
    });

    test('maps internal server errors to backend failure', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.error(
          app_error.InternalServerError(exception: Exception('server')),
        ),
      );

      cubit.selectLanguage(VoiceLanguage.vietnamese);
      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.backend);
      expect(cubit.state.selectedLanguage, VoiceLanguage.vietnamese);
      await cubit.close();
    });

    test('keeps selected language on microphone denial', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(
          checkStatus: AppPermissionStatus.denied,
          requestStatus: AppPermissionStatus.denied,
        ),
        FakeAudioRecorderService(),
        FakeTranscriptionApi.success('ignored'),
      );

      cubit.selectLanguage(VoiceLanguage.vietnamese);
      await cubit.startRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.microphoneDenied);
      expect(cubit.state.selectedLanguage, VoiceLanguage.vietnamese);
      await cubit.close();
    });

    test('restores selected language from storage with idle state', () async {
      final storage = FakeStorage();
      final firstCubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success('ignored'),
        storage: storage,
      );

      firstCubit.selectLanguage(VoiceLanguage.vietnamese);
      await firstCubit.close();

      final restoredCubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success('ignored'),
        storage: storage,
      );

      expect(restoredCubit.state.status, VoiceCaptureStatus.idle);
      expect(restoredCubit.state.transcript, isEmpty);
      expect(restoredCubit.state.failure, isNull);
      expect(restoredCubit.state.selectedLanguage, VoiceLanguage.vietnamese);
      await restoredCubit.close();
    });

    test('falls back to english when stored language is unknown', () async {
      final storage = FakeStorage();
      await storage.write('voice_capture_language', {'selectedLanguage': 'jp'});

      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success('ignored'),
        storage: storage,
      );

      expect(cubit.state.selectedLanguage, VoiceLanguage.english);
      await cubit.close();
    });
  });
}

final class FakeStorage implements Storage {
  final Map<String, dynamic> _values = {};

  @override
  Future<void> clear() async {
    _values.clear();
  }

  @override
  Future<void> close() async {}

  @override
  Future<void> delete(String key) async {
    _values.remove(key);
  }

  @override
  dynamic read(String key) => _values[key];

  @override
  Future<void> write(String key, dynamic value) async {
    _values[key] = value;
  }
}

final class FakePermissionService implements PermissionService {
  FakePermissionService({
    required this.checkStatus,
    AppPermissionStatus? requestStatus,
  }) : requestStatus = requestStatus ?? checkStatus;

  final AppPermissionStatus checkStatus;
  final AppPermissionStatus requestStatus;

  @override
  Future<AppPermissionStatus> check(AppPermission permission) async {
    return checkStatus;
  }

  @override
  Future<bool> openSettings() async => true;

  @override
  Future<AppPermissionStatus> request(AppPermission permission) async {
    return requestStatus;
  }
}

final class FakeAudioRecorderService extends AudioRecorderService {
  FakeAudioRecorderService({this.stopPath = '/tmp/audio.m4a'});

  final String stopPath;
  bool started = false;
  bool cancelled = false;
  String? deletedPath;

  @override
  Future<void> start() async {
    started = true;
  }

  @override
  Future<String> stop() async {
    started = false;
    return stopPath;
  }

  @override
  Future<void> cancel() async {
    cancelled = true;
    started = false;
  }

  @override
  Future<void> deleteRecording(String path) async {
    deletedPath = path;
  }
}

final class FakeTranscriptionApi extends TranscriptionApi {
  FakeTranscriptionApi.success(String text)
    : _result = (
        error: null,
        response: TranscriptionResponse(
          text: text,
          language: 'en',
          model: 'base',
        ),
      ),
      super(Dio());

  FakeTranscriptionApi.error(app_error.NetworkError error)
    : _result = (error: error, response: null),
      super(Dio());

  final ({app_error.NetworkError? error, TranscriptionResponse? response})
  _result;
  String? lastLanguageCode;

  @override
  Future<({app_error.NetworkError? error, TranscriptionResponse? response})>
  transcribe({
    required String filePath,
    required VoiceLanguage language,
  }) async {
    lastLanguageCode = language.code;
    return _result;
  }
}
