import 'package:ai_voice_first/core/error.dart';
import 'package:ai_voice_first/features/voice_settings/voice_settings.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('VoiceSettingsApi', () {
    test('loads voice settings', () async {
      String? capturedPath;

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPath = options.path;
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                data: {
                  'selected_voice': 'Ngọc Linh',
                  'default_voice': 'Mỹ Duyên',
                  'voices': [
                    {
                      'id': 'Ngọc Linh',
                      'name': 'Ngọc Linh',
                      'description': 'nữ, giọng tươi sáng',
                    },
                  ],
                },
              ),
            );
          },
        ),
      );

      final api = VoiceSettingsApi(dio);
      final result = await api.loadSettings();

      expect(result.error, isNull);
      expect(result.settings?.selectedVoice, 'Ngọc Linh');
      expect(result.settings?.defaultVoice, 'Mỹ Duyên');
      expect(result.settings?.voices.single.description, 'nữ, giọng tươi sáng');
      expect(capturedPath, '/v1/voice/settings');
    });

    test('saves selected voice', () async {
      String? capturedPath;
      Map<String, dynamic>? capturedBody;

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPath = options.path;
            capturedBody = options.data as Map<String, dynamic>;
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                data: {
                  'selected_voice': 'Ngọc Linh',
                  'default_voice': 'Mỹ Duyên',
                  'voices': const [],
                },
              ),
            );
          },
        ),
      );

      final api = VoiceSettingsApi(dio);
      final result = await api.saveSettings(selectedVoice: 'Ngọc Linh');

      expect(result.error, isNull);
      expect(result.settings?.selectedVoice, 'Ngọc Linh');
      expect(capturedPath, '/v1/voice/settings');
      expect(capturedBody, {'selected_voice': 'Ngọc Linh'});
    });

    test('maps unauthorized load failures', () async {
      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            handler.reject(
              DioException(
                requestOptions: options,
                response: Response(requestOptions: options, statusCode: 401),
              ),
            );
          },
        ),
      );

      final api = VoiceSettingsApi(dio);
      final result = await api.loadSettings();

      expect(result.settings, isNull);
      expect(result.error, isA<Unauthorized>());
    });
  });
}
