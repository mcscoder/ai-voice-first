import 'dart:io';

import 'package:ai_voice_first/core/error.dart';
import 'package:ai_voice_first/features/voice/data/transcription_api.dart';
import 'package:ai_voice_first/features/voice/data/voice_language.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('TranscriptionApi', () {
    test('sends multipart audio to /transcribe', () async {
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
              Response<Map<String, dynamic>>(
                requestOptions: options,
                data: const {
                  'text': 'hello world',
                  'language': 'en',
                  'model': 'base',
                },
              ),
            );
          },
        ),
      );

      final api = TranscriptionApi(dio);
      final result = await api.transcribe(
        filePath: file.path,
        language: VoiceLanguage.english,
      );

      expect(result.error, isNull);
      expect(result.response?.text, 'hello world');
      expect(capturedPath, '/transcribe');
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
      final result = await api.transcribe(
        filePath: file.path,
        language: VoiceLanguage.vietnamese,
      );

      expect(result.response, isNull);
      expect(result.error, isA<BadRequest>());

      await tempDir.delete(recursive: true);
    });
  });
}
