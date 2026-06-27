import 'package:equatable/equatable.dart';

import '../data/voice_settings_models.dart';

enum VoiceSettingsStatus { initial, loading, ready, saving, failure }

final class VoiceSettingsState extends Equatable {
  const VoiceSettingsState({
    this.status = VoiceSettingsStatus.initial,
    this.voices = const [],
    this.selectedVoiceId = '',
    this.savedVoiceId = '',
    this.defaultVoiceId = '',
    this.previewingVoiceId,
    this.previewLoadingVoiceId,
    this.errorMessage,
  });

  final VoiceSettingsStatus status;
  final List<VoiceOption> voices;
  final String selectedVoiceId;
  final String savedVoiceId;
  final String defaultVoiceId;
  final String? previewingVoiceId;
  final String? previewLoadingVoiceId;
  final String? errorMessage;

  bool get isLoading => status == VoiceSettingsStatus.loading;
  bool get isSaving => status == VoiceSettingsStatus.saving;
  bool get hasVoices => voices.isNotEmpty;

  VoiceSettingsState copyWith({
    VoiceSettingsStatus? status,
    List<VoiceOption>? voices,
    String? selectedVoiceId,
    String? savedVoiceId,
    String? defaultVoiceId,
    String? previewingVoiceId,
    String? previewLoadingVoiceId,
    String? errorMessage,
    bool clearPreviewingVoice = false,
    bool clearPreviewLoadingVoice = false,
    bool clearError = false,
  }) {
    return VoiceSettingsState(
      status: status ?? this.status,
      voices: voices ?? this.voices,
      selectedVoiceId: selectedVoiceId ?? this.selectedVoiceId,
      savedVoiceId: savedVoiceId ?? this.savedVoiceId,
      defaultVoiceId: defaultVoiceId ?? this.defaultVoiceId,
      previewingVoiceId: clearPreviewingVoice
          ? null
          : previewingVoiceId ?? this.previewingVoiceId,
      previewLoadingVoiceId: clearPreviewLoadingVoice
          ? null
          : previewLoadingVoiceId ?? this.previewLoadingVoiceId,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
    );
  }

  @override
  List<Object?> get props => [
    status,
    voices,
    selectedVoiceId,
    savedVoiceId,
    defaultVoiceId,
    previewingVoiceId,
    previewLoadingVoiceId,
    errorMessage,
  ];
}
