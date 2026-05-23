import 'package:equatable/equatable.dart';

import '../data/voice_language.dart';

enum VoiceCaptureStatus {
  idle,
  recording,
  uploading,
  processing,
  speaking,
  success,
  failure,
}

enum VoiceCaptureFailure {
  microphoneDenied,
  microphonePermanentlyDenied,
  network,
  badAudio,
  backend,
  unknown,
}

final class VoiceCaptureState extends Equatable {
  const VoiceCaptureState({
    this.status = VoiceCaptureStatus.idle,
    this.reply = '',
    this.selectedLanguage = VoiceLanguage.english,
    this.failure,
  });

  final VoiceCaptureStatus status;
  final String reply;
  final VoiceLanguage selectedLanguage;
  final VoiceCaptureFailure? failure;

  bool get isBusy =>
      status == VoiceCaptureStatus.recording ||
      status == VoiceCaptureStatus.uploading ||
      status == VoiceCaptureStatus.processing ||
      status == VoiceCaptureStatus.speaking;

  VoiceCaptureState copyWith({
    VoiceCaptureStatus? status,
    String? reply,
    VoiceLanguage? selectedLanguage,
    VoiceCaptureFailure? failure,
    bool clearFailure = false,
  }) {
    return VoiceCaptureState(
      status: status ?? this.status,
      reply: reply ?? this.reply,
      selectedLanguage: selectedLanguage ?? this.selectedLanguage,
      failure: clearFailure && failure == null ? null : failure ?? this.failure,
    );
  }

  @override
  List<Object?> get props => [status, reply, selectedLanguage.code, failure];
}
