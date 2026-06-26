import 'dart:async';
import 'dart:typed_data';

import 'package:ai_voice_first/core/error.dart' as app_error;
import 'package:ai_voice_first/core/permissions/permission_service.dart';
import 'package:ai_voice_first/features/voice/data/audio_recorder_service.dart';
import 'package:ai_voice_first/features/voice/data/transcription_api.dart';
import 'package:ai_voice_first/features/voice/presentation/voice_capture_cubit.dart';
import 'package:ai_voice_first/features/voice/presentation/voice_capture_state.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hydrated_bloc/hydrated_bloc.dart';

void main() {
  group('VoiceCaptureCubit', () {
    test('starts recording when microphone permission is granted', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(),
        FakeTranscriptionApi.success(const [1, 2, 3]),
        playAssistantSpeech: _noopPlayback,
      );

      await cubit.startRecording();

      expect(cubit.state.status, VoiceCaptureStatus.recording);
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
        FakeTranscriptionApi.success(const [1, 2, 3]),
        playAssistantSpeech: _noopPlayback,
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
        FakeTranscriptionApi.success(const [1, 2, 3]),
        playAssistantSpeech: _noopPlayback,
      );

      await cubit.startRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(
        cubit.state.failure,
        VoiceCaptureFailure.microphonePermanentlyDenied,
      );
      await cubit.close();
    });

    test('plays assistant audio after stop', () async {
      final playedAudio = <Uint8List>[];
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success(const [9, 8, 7]),
        playAssistantSpeech: (audioBytes) async {
          playedAudio.add(audioBytes);
        },
      );

      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.success);
      expect(playedAudio.single, equals(Uint8List.fromList(const [9, 8, 7])));
      await cubit.close();
    });

    test('starts speaking when first streamed audio chunk arrives', () async {
      final api = FakeStreamingTranscriptionApi();
      final playedAudio = <Uint8List>[];
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        api,
        playAssistantSpeech: (audioBytes) async {
          playedAudio.add(audioBytes);
        },
      );

      await cubit.startRecording();
      final stopFuture = cubit.stopRecording();
      await api.firstAudioSent;

      expect(cubit.state.status, VoiceCaptureStatus.speaking);
      expect(playedAudio.single, Uint8List.fromList(const [7, 8, 9]));

      api.complete();
      await stopFuture;

      expect(cubit.state.status, VoiceCaptureStatus.success);
      await cubit.close();
    });

    test('cancels an in-flight voice request', () async {
      final api = FakeTranscriptionApi.pending();
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        api,
        playAssistantSpeech: _noopPlayback,
      );

      await cubit.startRecording();
      final stopFuture = cubit.stopRecording();
      await api.requestStarted;

      expect(cubit.state.status, VoiceCaptureStatus.uploading);
      expect(cubit.state.requestStartedAt, isNotNull);

      cubit.cancelRequest();

      expect(cubit.state.status, VoiceCaptureStatus.idle);
      expect(cubit.state.requestStartedAt, isNull);
      expect(api.lastCancelToken?.isCancelled, isTrue);

      api.complete(const [1, 2, 3]);
      await stopFuture;

      expect(cubit.state.status, VoiceCaptureStatus.idle);
      await cubit.close();
    });

    test(
      'keeps cancelled streaming request idle after late done event',
      () async {
        final api = FakeStreamingTranscriptionApi();
        final cubit = VoiceCaptureCubit(
          FakePermissionService(checkStatus: AppPermissionStatus.granted),
          FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
          api,
          playAssistantSpeech: _noopPlayback,
        );

        await cubit.startRecording();
        final stopFuture = cubit.stopRecording();
        await api.firstAudioSent;

        expect(cubit.state.status, VoiceCaptureStatus.speaking);

        cubit.cancelRequest();

        expect(cubit.state.status, VoiceCaptureStatus.idle);
        expect(api.lastCancelToken?.isCancelled, isTrue);

        api.complete();
        await stopFuture;

        expect(cubit.state.status, VoiceCaptureStatus.idle);
        await cubit.close();
      },
    );

    test('uses vietnamese when responding', () async {
      final api = FakeTranscriptionApi.success(const [4, 5, 6]);
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        api,
        playAssistantSpeech: _noopPlayback,
      );

      await cubit.startRecording();
      await cubit.stopRecording();

      expect(api.lastLanguageCode, 'vi');
      await cubit.close();
    });

    test('maps empty audio responses to bad audio failure', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success(const []),
        playAssistantSpeech: _noopPlayback,
      );

      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.badAudio);
      await cubit.close();
    });

    test('maps timeout errors to network failure', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.error(
          app_error.Timeout(exception: Exception('timeout')),
        ),
        playAssistantSpeech: _noopPlayback,
      );

      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.network);
      await cubit.close();
    });

    test('maps bad request errors to bad audio failure', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.error(
          app_error.BadRequest(exception: Exception('bad request')),
        ),
        playAssistantSpeech: _noopPlayback,
      );

      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.badAudio);
      await cubit.close();
    });

    test('maps internal server errors to backend failure', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.error(
          app_error.InternalServerError(exception: Exception('server')),
        ),
        playAssistantSpeech: _noopPlayback,
      );

      await cubit.startRecording();
      await cubit.stopRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.backend);
      await cubit.close();
    });

    test('keeps microphone denial failure', () async {
      final cubit = VoiceCaptureCubit(
        FakePermissionService(
          checkStatus: AppPermissionStatus.denied,
          requestStatus: AppPermissionStatus.denied,
        ),
        FakeAudioRecorderService(),
        FakeTranscriptionApi.success(const [1, 2, 3]),
        playAssistantSpeech: _noopPlayback,
      );

      await cubit.startRecording();

      expect(cubit.state.status, VoiceCaptureStatus.failure);
      expect(cubit.state.failure, VoiceCaptureFailure.microphoneDenied);
      await cubit.close();
    });

    test('restores idle state from storage', () async {
      final storage = FakeStorage();
      final firstCubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success(const [1, 2, 3]),
        playAssistantSpeech: _noopPlayback,
        storage: storage,
      );

      await firstCubit.close();

      final restoredCubit = VoiceCaptureCubit(
        FakePermissionService(checkStatus: AppPermissionStatus.granted),
        FakeAudioRecorderService(stopPath: '/tmp/audio.m4a'),
        FakeTranscriptionApi.success(const [1, 2, 3]),
        playAssistantSpeech: _noopPlayback,
        storage: storage,
      );

      expect(restoredCubit.state.status, VoiceCaptureStatus.idle);
      expect(restoredCubit.state.reply, isEmpty);
      expect(restoredCubit.state.failure, isNull);
      await restoredCubit.close();
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
  FakeTranscriptionApi.success(List<int> audio)
    : _result = (error: null, audio: Uint8List.fromList(audio)),
      _pending = null,
      super(Dio());

  FakeTranscriptionApi.error(app_error.NetworkError error)
    : _result = (error: error, audio: null),
      _pending = null,
      super(Dio());

  FakeTranscriptionApi.pending()
    : _result = null,
      _pending =
          Completer<({app_error.NetworkError? error, Uint8List? audio})>(),
      super(Dio());

  final ({app_error.NetworkError? error, Uint8List? audio})? _result;
  final Completer<({app_error.NetworkError? error, Uint8List? audio})>?
  _pending;
  final Completer<void> _requestStarted = Completer<void>();
  String? lastLanguageCode;
  CancelToken? lastCancelToken;

  Future<void> get requestStarted => _requestStarted.future;

  void complete(List<int> audio) {
    _pending?.complete((error: null, audio: Uint8List.fromList(audio)));
  }

  @override
  Future<({app_error.NetworkError? error, Uint8List? audio})> respond({
    required String filePath,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
  }) async {
    lastLanguageCode = 'vi';
    lastCancelToken = cancelToken;
    if (!_requestStarted.isCompleted) {
      _requestStarted.complete();
    }
    return _pending?.future ?? _result!;
  }

  @override
  Stream<VoiceAssistantStreamEvent> respondStream({
    required String filePath,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
  }) async* {
    lastLanguageCode = 'vi';
    lastCancelToken = cancelToken;
    if (!_requestStarted.isCompleted) {
      _requestStarted.complete();
    }

    final result = await (_pending?.future ?? Future.value(_result!));
    final error = result.error;
    if (error != null) {
      yield VoiceAssistantRequestErrorEvent(error: error);
      return;
    }

    yield VoiceAssistantAudioEvent(
      sequence: 0,
      mediaType: 'audio/wav',
      audio: result.audio ?? Uint8List(0),
    );
    yield const VoiceAssistantDoneEvent(text: '');
  }
}

final class FakeStreamingTranscriptionApi extends TranscriptionApi {
  FakeStreamingTranscriptionApi() : super(Dio());

  final Completer<void> _firstAudioSent = Completer<void>();
  final Completer<void> _done = Completer<void>();
  CancelToken? lastCancelToken;

  Future<void> get firstAudioSent => _firstAudioSent.future;

  void complete() {
    _done.complete();
  }

  @override
  Future<({app_error.NetworkError? error, Uint8List? audio})> respond({
    required String filePath,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
  }) async {
    return (error: null, audio: Uint8List.fromList(const [7, 8, 9]));
  }

  @override
  Stream<VoiceAssistantStreamEvent> respondStream({
    required String filePath,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
  }) async* {
    lastCancelToken = cancelToken;
    yield VoiceAssistantAudioEvent(
      sequence: 0,
      mediaType: 'audio/wav',
      audio: Uint8List.fromList(const [7, 8, 9]),
    );
    if (!_firstAudioSent.isCompleted) {
      _firstAudioSent.complete();
    }
    await _done.future;
    yield const VoiceAssistantDoneEvent(text: 'done');
  }
}

Future<void> _noopPlayback(Uint8List audioBytes) async {}
