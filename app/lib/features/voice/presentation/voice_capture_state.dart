import 'package:equatable/equatable.dart';

import '../data/voice_language.dart';

enum VoiceCaptureStatus {
  idle,
  listening,
  transcribing,
  success,
  empty,
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
    this.transcript = '',
    this.selectedLanguage = VoiceLanguage.english,
    this.failure,
  });

  final VoiceCaptureStatus status;
  final String transcript;
  final VoiceLanguage selectedLanguage;
  final VoiceCaptureFailure? failure;

  bool get isBusy =>
      status == VoiceCaptureStatus.listening ||
      status == VoiceCaptureStatus.transcribing;

  VoiceCaptureState copyWith({
    VoiceCaptureStatus? status,
    String? transcript,
    VoiceLanguage? selectedLanguage,
    VoiceCaptureFailure? failure,
    bool clearFailure = false,
  }) {
    return VoiceCaptureState(
      status: status ?? this.status,
      transcript: transcript ?? this.transcript,
      selectedLanguage: selectedLanguage ?? this.selectedLanguage,
      failure: clearFailure ? null : failure ?? this.failure,
    );
  }

  @override
  List<Object?> get props => [
    status,
    transcript,
    selectedLanguage.code,
    failure,
  ];
}
