import 'dart:typed_data';
import 'dart:io';

import 'package:ai_voice_first/core/error.dart';
import 'package:ai_voice_first/features/voice/data/transcription_api.dart';
import 'package:ai_voice_first/features/voice/data/voice_language.dart';
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
        language: VoiceLanguage.english,
        cancelToken: cancelToken,
      );

      expect(result.error, isNull);
      expect(result.audio, equals(Uint8List.fromList(const [1, 2, 3, 4])));
      expect(capturedPath, '/v1/voice/assistant');
      expect(capturedCancelToken, same(cancelToken));
      expect(capturedFormData, isNotNull);
      expect(capturedFormData!.fields.single.key, 'language');
      expect(capturedFormData!.fields.single.value, 'en');
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
      final result = await api.respond(
        filePath: file.path,
        language: VoiceLanguage.vietnamese,
      );

      expect(result.audio, isNull);
      expect(result.error, isA<BadRequest>());

      await tempDir.delete(recursive: true);
    });
  });
}
