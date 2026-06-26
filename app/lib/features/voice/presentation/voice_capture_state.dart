import 'package:equatable/equatable.dart';

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
    this.transcript = '',
    this.failure,
    this.requestStartedAt,
    this.requestCompletedAt,
  });

  final VoiceCaptureStatus status;
  final String reply;
  final String transcript;
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
    String? transcript,
    VoiceCaptureFailure? failure,
    DateTime? requestStartedAt,
    DateTime? requestCompletedAt,
    bool clearFailure = false,
    bool clearRequestTiming = false,
  }) {
    return VoiceCaptureState(
      status: status ?? this.status,
      reply: reply ?? this.reply,
      transcript: transcript ?? this.transcript,
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
    transcript,
    failure,
    requestStartedAt,
    requestCompletedAt,
  ];
}
