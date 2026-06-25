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
    this.requestStartedAt,
    this.requestCompletedAt,
  });

  final VoiceCaptureStatus status;
  final String reply;
  final VoiceLanguage selectedLanguage;
  final VoiceCaptureFailure? failure;
  final DateTime? requestStartedAt;
  final DateTime? requestCompletedAt;

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
    DateTime? requestStartedAt,
    DateTime? requestCompletedAt,
    bool clearFailure = false,
    bool clearRequestTiming = false,
  }) {
    return VoiceCaptureState(
      status: status ?? this.status,
      reply: reply ?? this.reply,
      selectedLanguage: selectedLanguage ?? this.selectedLanguage,
      failure: clearFailure && failure == null ? null : failure ?? this.failure,
      requestStartedAt: clearRequestTiming
          ? null
          : requestStartedAt ?? this.requestStartedAt,
      requestCompletedAt: clearRequestTiming
          ? null
          : requestCompletedAt ?? this.requestCompletedAt,
    );
  }

  @override
  List<Object?> get props => [
    status,
    reply,
    selectedLanguage.code,
    failure,
    requestStartedAt,
    requestCompletedAt,
  ];
}
