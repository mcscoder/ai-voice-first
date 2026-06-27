import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/error.dart';
import '../data/voice_preview_asset.dart';
import '../data/voice_settings_models.dart';
import '../data/voice_settings_repository.dart';
import 'voice_settings_state.dart';

typedef PlayVoicePreview = Future<void> Function(Uint8List audioBytes);
typedef StopVoicePreview = Future<void> Function();
typedef LoadVoicePreviewAsset = Future<Uint8List> Function(String voiceId);

final class VoiceSettingsCubit extends Cubit<VoiceSettingsState> {
  VoiceSettingsCubit(
    this._repository, {
    PlayVoicePreview? playVoicePreview,
    StopVoicePreview? stopVoicePreview,
    LoadVoicePreviewAsset? loadVoicePreviewAsset,
  }) : super(const VoiceSettingsState()) {
    if (playVoicePreview != null && stopVoicePreview != null) {
      _audioPlayer = null;
      _playVoicePreview = playVoicePreview;
      _stopVoicePreview = stopVoicePreview;
      _loadVoicePreviewAsset = loadVoicePreviewAsset ?? loadBundledVoicePreview;
      return;
    }

    final player = AudioPlayer();
    _audioPlayer = player;
    _playVoicePreview = (audioBytes) async {
      final completed = player.onPlayerComplete.first;
      final stopped = player.onPlayerStateChanged.firstWhere(
        (state) => state == PlayerState.stopped,
      );
      await player.play(BytesSource(audioBytes, mimeType: 'audio/wav'));
      await Future.any([completed, stopped]);
    };
    _stopVoicePreview = player.stop;
    _loadVoicePreviewAsset = loadVoicePreviewAsset ?? loadBundledVoicePreview;
  }

  final VoiceSettingsRepository _repository;
  late final AudioPlayer? _audioPlayer;
  late final PlayVoicePreview _playVoicePreview;
  late final StopVoicePreview _stopVoicePreview;
  late final LoadVoicePreviewAsset _loadVoicePreviewAsset;
  final Map<String, Uint8List> _previewAudioByVoice = {};
  int _previewToken = 0;

  Future<void> load() async {
    emit(state.copyWith(status: VoiceSettingsStatus.loading, clearError: true));

    final result = await _repository.loadSettings();
    if (result.error != null || result.settings == null) {
      emit(
        state.copyWith(
          status: VoiceSettingsStatus.failure,
          errorMessage: _messageForError(result.error),
        ),
      );
      return;
    }

    await _preloadVoicePreviews(result.settings!.voices);
    _applySettings(result.settings!);
  }

  void selectVoice(String voiceId) {
    emit(
      state.copyWith(
        status: VoiceSettingsStatus.ready,
        selectedVoiceId: voiceId,
        clearError: true,
      ),
    );
  }

  Future<bool> save() async {
    if (state.selectedVoiceId.isEmpty) {
      return false;
    }

    emit(state.copyWith(status: VoiceSettingsStatus.saving, clearError: true));

    final result = await _repository.saveSettings(
      selectedVoice: state.selectedVoiceId,
    );
    if (result.error != null || result.settings == null) {
      emit(
        state.copyWith(
          status: VoiceSettingsStatus.ready,
          errorMessage: _messageForError(result.error),
        ),
      );
      return false;
    }

    _applySettings(result.settings!);
    return true;
  }

  Future<void> preview(String voiceId) async {
    if (state.previewingVoiceId == voiceId &&
        state.previewLoadingVoiceId == null) {
      await stopPreview();
      return;
    }

    final token = ++_previewToken;
    await _stopVoicePreview();
    if (token != _previewToken) {
      return;
    }

    final audioBytes = _previewAudioByVoice[voiceId];
    if (audioBytes == null) {
      emit(
        state.copyWith(
          status: VoiceSettingsStatus.ready,
          errorMessage: 'The voice preview is not available.',
        ),
      );
      return;
    }

    emit(
      state.copyWith(
        status: VoiceSettingsStatus.ready,
        previewingVoiceId: voiceId,
        clearError: true,
      ),
    );

    try {
      await _playVoicePreview(audioBytes);
    } on Exception {
      if (token != _previewToken) {
        return;
      }
      emit(
        state.copyWith(
          status: VoiceSettingsStatus.ready,
          clearPreviewingVoice: true,
          errorMessage: 'Could not play the voice preview.',
        ),
      );
      return;
    }

    if (token != _previewToken) {
      return;
    }
    emit(
      state.copyWith(
        status: VoiceSettingsStatus.ready,
        clearPreviewingVoice: true,
      ),
    );
  }

  Future<void> stopPreview() async {
    _previewToken += 1;
    await _stopVoicePreview();
    emit(
      state.copyWith(
        status: VoiceSettingsStatus.ready,
        clearPreviewingVoice: true,
        clearPreviewLoadingVoice: true,
      ),
    );
  }

  @override
  Future<void> close() async {
    _previewToken += 1;
    await _stopVoicePreview();
    await _audioPlayer?.dispose();
    return super.close();
  }

  void _applySettings(VoiceSettingsModel settings) {
    emit(
      state.copyWith(
        status: VoiceSettingsStatus.ready,
        voices: settings.voices,
        selectedVoiceId: settings.selectedVoice,
        savedVoiceId: settings.selectedVoice,
        defaultVoiceId: settings.defaultVoice,
        clearPreviewingVoice: true,
        clearPreviewLoadingVoice: true,
        clearError: true,
      ),
    );
  }

  Future<void> _preloadVoicePreviews(List<VoiceOption> voices) async {
    _previewAudioByVoice
      ..clear()
      ..addEntries(
        await Future.wait(
          voices.map((voice) async {
            final audioBytes = await _loadVoicePreviewAsset(voice.id);
            return MapEntry(voice.id, audioBytes);
          }),
        ),
      );
  }

  String _messageForError(NetworkError? error) {
    if (error is Unauthorized) {
      return 'Your session expired. Please sign in again.';
    }
    if (error is Timeout) {
      return 'The request timed out. Try again.';
    }
    if (error is BadRequest) {
      return 'The selected voice could not be saved.';
    }
    if (error is InternalServerError) {
      return 'The voice service is unavailable right now.';
    }
    return 'Something went wrong. Try again.';
  }
}
