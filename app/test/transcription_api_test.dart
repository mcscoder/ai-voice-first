import 'dart:convert';
import 'dart:typed_data';
import 'dart:io';

import 'package:ai_voice_first/core/error.dart';
import 'package:ai_voice_first/features/voice/data/transcription_api.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('TranscriptionApi', () {
    test('sends multipart audio to /v1/voice/assistant', () async {
      final tempDir = await Directory.systemTemp.createTemp('voice_api_test');
      final file = File('${tempDir.path}/sample.m4a');
      await file.writeAsString('audio');

      FormData? capturedFormData;
      String? capturedPath;
      CancelToken? capturedCancelToken;
      final cancelToken = CancelToken();

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPath = options.path;
            capturedFormData = options.data as FormData;
            capturedCancelToken = options.cancelToken;
            handler.resolve(
              Response<List<int>>(
                requestOptions: options,
                data: const [1, 2, 3, 4],
              ),
            );
          },
        ),
      );

      final api = TranscriptionApi(dio);
      final result = await api.respond(
        filePath: file.path,
        cancelToken: cancelToken,
      );

      expect(result.error, isNull);
      expect(result.audio, equals(Uint8List.fromList(const [1, 2, 3, 4])));
      expect(capturedPath, '/v1/voice/assistant');
      expect(capturedCancelToken, same(cancelToken));
      expect(capturedFormData, isNotNull);
      expect(capturedFormData!.fields.single.key, 'language');
      expect(capturedFormData!.fields.single.value, 'vi');
      expect(capturedFormData!.files.single.key, 'file');

      await tempDir.delete(recursive: true);
    });

    test('maps Dio bad request responses to NetworkError', () async {
      final tempDir = await Directory.systemTemp.createTemp('voice_api_test');
      final file = File('${tempDir.path}/sample.m4a');
      await file.writeAsString('audio');

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            handler.reject(
              DioException(
                requestOptions: options,
                response: Response(requestOptions: options, statusCode: 400),
              ),
            );
          },
        ),
      );

      final api = TranscriptionApi(dio);
      final result = await api.respond(filePath: file.path);

      expect(result.audio, isNull);
      expect(result.error, isA<BadRequest>());

      await tempDir.delete(recursive: true);
    });

    test('streams multipart audio from /v1/voice/assistant/stream', () async {
      final tempDir = await Directory.systemTemp.createTemp('voice_api_test');
      final file = File('${tempDir.path}/sample.m4a');
      await file.writeAsString('audio');

      FormData? capturedFormData;
      String? capturedPath;
      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPath = options.path;
            capturedFormData = options.data as FormData;
            handler.resolve(
              Response<ResponseBody>(
                requestOptions: options,
                data: ResponseBody.fromString(
                  [
                    '{"type":"text_delta","text":"Hello"}',
                    '{"type":"audio","sequence":0,"media_type":"audio/wav","audio":"${base64Encode([1, 2, 3])}"}',
                    '{"type":"done","text":"Hello"}',
                  ].join('\n'),
                  200,
                  headers: {
                    Headers.contentTypeHeader: ['application/x-ndjson'],
                  },
                ),
              ),
            );
          },
        ),
      );

      final api = TranscriptionApi(dio);
      final events = await api.respondStream(filePath: file.path).toList();

      expect(capturedPath, '/v1/voice/assistant/stream');
      expect(capturedFormData, isNotNull);
      expect(capturedFormData!.fields.single.key, 'language');
      expect(capturedFormData!.fields.single.value, 'vi');
      expect(events[0], isA<VoiceAssistantTextDeltaEvent>());
      expect((events[0] as VoiceAssistantTextDeltaEvent).text, 'Hello');
      expect(events[1], isA<VoiceAssistantAudioEvent>());
      expect(
        (events[1] as VoiceAssistantAudioEvent).audio,
        Uint8List.fromList(const [1, 2, 3]),
      );
      expect(events[2], isA<VoiceAssistantDoneEvent>());

      await tempDir.delete(recursive: true);
    });
  });
}
