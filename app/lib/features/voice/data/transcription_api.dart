import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

import '../../../core/error.dart';
import '../../../core/network/api.dart';
import '../../../core/network/api_path.dart';
import '../../../core/network/dio.dart';
import 'voice_language.dart';

sealed class VoiceAssistantStreamEvent {
  const VoiceAssistantStreamEvent();

  factory VoiceAssistantStreamEvent.fromJson(Map<String, dynamic> json) {
    switch (json['type']) {
      case 'asr':
        return VoiceAssistantAsrEvent(
          text: json['text'] as String? ?? '',
          language: json['language'] as String? ?? '',
          model: json['model'] as String? ?? '',
        );
      case 'text_delta':
        return VoiceAssistantTextDeltaEvent(
          text: json['text'] as String? ?? '',
        );
      case 'audio':
        return VoiceAssistantAudioEvent(
          sequence: json['sequence'] as int? ?? 0,
          mediaType: json['media_type'] as String? ?? 'audio/wav',
          audio: base64Decode(json['audio'] as String? ?? ''),
        );
      case 'done':
        return VoiceAssistantDoneEvent(text: json['text'] as String? ?? '');
      case 'error':
        return VoiceAssistantErrorEvent(
          message: json['message'] as String? ?? '',
        );
      default:
        return const VoiceAssistantErrorEvent(message: 'Unknown stream event.');
    }
  }
}

final class VoiceAssistantAsrEvent extends VoiceAssistantStreamEvent {
  const VoiceAssistantAsrEvent({
    required this.text,
    required this.language,
    required this.model,
  });

  final String text;
  final String language;
  final String model;
}

final class VoiceAssistantTextDeltaEvent extends VoiceAssistantStreamEvent {
  const VoiceAssistantTextDeltaEvent({required this.text});

  final String text;
}

final class VoiceAssistantAudioEvent extends VoiceAssistantStreamEvent {
  const VoiceAssistantAudioEvent({
    required this.sequence,
    required this.mediaType,
    required this.audio,
  });

  final int sequence;
  final String mediaType;
  final Uint8List audio;
}

final class VoiceAssistantDoneEvent extends VoiceAssistantStreamEvent {
  const VoiceAssistantDoneEvent({required this.text});

  final String text;
}

final class VoiceAssistantErrorEvent extends VoiceAssistantStreamEvent {
  const VoiceAssistantErrorEvent({required this.message});

  final String message;
}

final class VoiceAssistantRequestErrorEvent extends VoiceAssistantStreamEvent {
  const VoiceAssistantRequestErrorEvent({required this.error});

  final NetworkError error;
}

@lazySingleton
base class TranscriptionApi extends Api {
  TranscriptionApi(@nonAuthDio super.dio);

  Future<({NetworkError? error, Uint8List? audio})> respond({
    required String filePath,
    required VoiceLanguage language,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
  }) async {
    final result = await withTimeoutRequest(() async {
      final formData = FormData.fromMap({
        'language': language.code,
        'file': await MultipartFile.fromFile(
          filePath,
          filename: filePath.split('/').last,
        ),
      });

      final response = await dio.post<List<int>>(
        ApiPath.voiceAssistant,
        data: formData,
        cancelToken: cancelToken,
        options: Options(responseType: ResponseType.bytes),
        onSendProgress: onSendProgress,
      );

      final bytes = response.data;
      return bytes == null ? Uint8List(0) : Uint8List.fromList(bytes);
    });

    return result.match(
      (error) => (error: error, audio: null),
      (audio) => (error: null, audio: audio),
    );
  }

  Stream<VoiceAssistantStreamEvent> respondStream({
    required String filePath,
    required VoiceLanguage language,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
  }) async* {
    try {
      final formData = FormData.fromMap({
        'language': language.code,
        'file': await MultipartFile.fromFile(
          filePath,
          filename: filePath.split('/').last,
        ),
      });

      final response = await dio.post<ResponseBody>(
        ApiPath.voiceAssistantStream,
        data: formData,
        cancelToken: cancelToken,
        options: Options(responseType: ResponseType.stream),
        onSendProgress: onSendProgress,
      );

      final responseBody = response.data;
      if (responseBody == null) {
        yield const VoiceAssistantErrorEvent(message: 'Empty stream response.');
        return;
      }

      await for (final line
          in responseBody.stream
              .cast<List<int>>()
              .transform(utf8.decoder)
              .transform(const LineSplitter())) {
        if (line.trim().isEmpty) {
          continue;
        }
        yield VoiceAssistantStreamEvent.fromJson(
          jsonDecode(line) as Map<String, dynamic>,
        );
      }
    } on DioException catch (error) {
      if (!CancelToken.isCancel(error)) {
        yield VoiceAssistantRequestErrorEvent(
          error: mapErrorToNetworkError(error),
        );
      }
    } on FormatException {
      yield const VoiceAssistantErrorEvent(message: 'Invalid stream response.');
    }
  }
}
