import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:hydrated_bloc/hydrated_bloc.dart';
import 'package:injectable/injectable.dart';

import '../../../core/error.dart';
import '../../../core/network/request_cancellation_mixin.dart';
import '../../../core/permissions/permission_service.dart';
import '../data/audio_recorder_service.dart';
import '../data/transcription_api.dart';
import '../data/voice_language.dart';
import 'voice_capture_state.dart';

@injectable
class VoiceCaptureCubit extends HydratedCubit<VoiceCaptureState>
    with RequestCancellationMixin<VoiceCaptureState> {
  VoiceCaptureCubit(
    this._permissionService,
    this._audioRecorderService,
    this._transcriptionApi, {
    Future<void> Function(Uint8List audioBytes)? playAssistantSpeech,
    Storage? storage,
  }) : super(const VoiceCaptureState(), storage: _resolveStorage(storage)) {
    if (playAssistantSpeech != null) {
      _audioPlayer = null;
      _playAssistantSpeech = playAssistantSpeech;
      return;
    }

    final player = AudioPlayer();
    _audioPlayer = player;
    _playAssistantSpeech = (audioBytes) async {
      await player.play(BytesSource(audioBytes, mimeType: 'audio/mpeg'));
    };
  }

  final PermissionService _permissionService;
  final AudioRecorderService _audioRecorderService;
  final TranscriptionApi _transcriptionApi;
  late final AudioPlayer? _audioPlayer;
  late final Future<void> Function(Uint8List audioBytes) _playAssistantSpeech;
  int _requestGeneration = 0;

  void selectLanguage(VoiceLanguage language) {
    if (state.isBusy || language.code == state.selectedLanguage.code) {
      return;
    }

    emit(state.copyWith(selectedLanguage: language, clearFailure: true));
  }

  Future<void> toggleRecording() async {
    switch (state.status) {
      case VoiceCaptureStatus.idle:
      case VoiceCaptureStatus.success:
      case VoiceCaptureStatus.failure:
        await startRecording();
        return;
      case VoiceCaptureStatus.recording:
        await stopRecording();
        return;
      case VoiceCaptureStatus.uploading:
      case VoiceCaptureStatus.processing:
      case VoiceCaptureStatus.speaking:
        return;
    }
  }

  Future<void> startRecording() async {
    final status = await _permissionService.check(AppPermission.microphone);

    if (status == AppPermissionStatus.denied) {
      final requested = await _permissionService.request(
        AppPermission.microphone,
      );
      if (!_isGranted(requested)) {
        emit(
          state.copyWith(
            status: VoiceCaptureStatus.failure,
            failure: requested == AppPermissionStatus.permanentlyDenied
                ? VoiceCaptureFailure.microphonePermanentlyDenied
                : VoiceCaptureFailure.microphoneDenied,
          ),
        );
        return;
      }
    } else if (!_isGranted(status)) {
      emit(
        state.copyWith(
          status: VoiceCaptureStatus.failure,
          failure: status == AppPermissionStatus.permanentlyDenied
              ? VoiceCaptureFailure.microphonePermanentlyDenied
              : VoiceCaptureFailure.microphoneDenied,
        ),
      );
      return;
    }

    try {
      await _audioRecorderService.start();
      emit(
        state.copyWith(
          status: VoiceCaptureStatus.recording,
          reply: '',
          clearFailure: true,
          clearRequestTiming: true,
        ),
      );
    } on AudioRecordingException {
      emit(
        state.copyWith(
          status: VoiceCaptureStatus.failure,
          failure: VoiceCaptureFailure.microphoneDenied,
        ),
      );
    } on Exception {
      emit(
        state.copyWith(
          status: VoiceCaptureStatus.failure,
          failure: VoiceCaptureFailure.unknown,
        ),
      );
    }
  }

  Future<void> stopRecording() async {
    final requestGeneration = ++_requestGeneration;
    emit(
      state.copyWith(
        status: VoiceCaptureStatus.uploading,
        clearFailure: true,
        requestStartedAt: DateTime.now(),
        requestCompletedAt: null,
      ),
    );

    String? filePath;

    try {
      filePath = await _audioRecorderService.stop();
      if (_isStaleRequest(requestGeneration)) {
        return;
      }

      final result = await _transcriptionApi.respond(
        filePath: filePath,
        language: state.selectedLanguage,
        cancelToken: cancelToken,
        onSendProgress: (sent, total) {
          if (_isStaleRequest(requestGeneration)) {
            return;
          }
          if (total > 0 &&
              sent >= total &&
              state.status == VoiceCaptureStatus.uploading) {
            emit(
              state.copyWith(
                status: VoiceCaptureStatus.processing,
                clearFailure: true,
              ),
            );
          }
        },
      );
      if (_isStaleRequest(requestGeneration)) {
        return;
      }
      final error = result.error;
      final audio = result.audio;

      if (error != null) {
        if (cancelToken.isCancelled) {
          return;
        }
        emit(
          state.copyWith(
            status: VoiceCaptureStatus.failure,
            failure: _mapNetworkError(error),
            reply: state.reply,
            requestCompletedAt: DateTime.now(),
          ),
        );
        return;
      }

      final audioBytes = audio ?? Uint8List(0);
      if (audioBytes.isEmpty) {
        emit(
          state.copyWith(
            status: VoiceCaptureStatus.failure,
            failure: VoiceCaptureFailure.badAudio,
            clearFailure: true,
            requestCompletedAt: DateTime.now(),
          ),
        );
        return;
      }

      emit(
        state.copyWith(
          status: VoiceCaptureStatus.speaking,
          clearFailure: true,
          requestCompletedAt: DateTime.now(),
        ),
      );

      try {
        await _playAssistantSpeech(audioBytes);
      } on Exception {
        emit(
          state.copyWith(
            status: VoiceCaptureStatus.failure,
            failure: VoiceCaptureFailure.unknown,
            clearFailure: true,
            requestCompletedAt: DateTime.now(),
          ),
        );
        return;
      }

      emit(
        state.copyWith(status: VoiceCaptureStatus.success, clearFailure: true),
      );
    } on AudioRecordingException {
      if (_isStaleRequest(requestGeneration)) {
        return;
      }
      emit(
        state.copyWith(
          status: VoiceCaptureStatus.failure,
          failure: VoiceCaptureFailure.badAudio,
          requestCompletedAt: DateTime.now(),
        ),
      );
    } on Exception {
      if (cancelToken.isCancelled || _isStaleRequest(requestGeneration)) {
        return;
      }
      emit(
        state.copyWith(
          status: VoiceCaptureStatus.failure,
          failure: VoiceCaptureFailure.unknown,
          requestCompletedAt: DateTime.now(),
        ),
      );
    } finally {
      if (filePath != null) {
        await _audioRecorderService.deleteRecording(filePath);
      }
    }
  }

  Future<void> openSettings() async {
    await _permissionService.openSettings();
  }

  void cancelRequest() {
    if (state.status != VoiceCaptureStatus.uploading &&
        state.status != VoiceCaptureStatus.processing) {
      return;
    }

    _requestGeneration += 1;
    cancelRequests('Voice request cancelled');
    emit(
      state.copyWith(
        status: VoiceCaptureStatus.idle,
        clearFailure: true,
        clearRequestTiming: true,
      ),
    );
  }

  bool _isGranted(AppPermissionStatus status) {
    return status == AppPermissionStatus.granted ||
        status == AppPermissionStatus.limited;
  }

  VoiceCaptureFailure _mapNetworkError(NetworkError error) {
    if (error is Timeout) {
      return VoiceCaptureFailure.network;
    }
    if (error is BadRequest) {
      return VoiceCaptureFailure.badAudio;
    }
    if (error is InternalServerError) {
      return VoiceCaptureFailure.backend;
    }
    return VoiceCaptureFailure.network;
  }

  bool _isStaleRequest(int requestGeneration) {
    return requestGeneration != _requestGeneration || isClosed;
  }

  @override
  Future<void> close() async {
    cancelRequests();
    await _audioRecorderService.cancel();
    await _audioPlayer?.dispose();
    return super.close();
  }

  @override
  String get storagePrefix => 'voice_capture_language';

  @override
  VoiceCaptureState? fromJson(Map<String, dynamic> json) {
    return VoiceCaptureState(
      selectedLanguage: VoiceLanguage.fromCode(
        json['selectedLanguage'] as String?,
      ),
    );
  }

  @override
  Map<String, dynamic>? toJson(VoiceCaptureState state) {
    return {'selectedLanguage': state.selectedLanguage.code};
  }

  static Storage _resolveStorage(Storage? storage) {
    if (storage != null) {
      return storage;
    }

    try {
      return HydratedBloc.storage;
    } on StorageNotFound {
      return _InMemoryStorage();
    }
  }
}

final class _InMemoryStorage implements Storage {
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
