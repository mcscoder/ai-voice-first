import 'package:ai_voice_first/features/profile/data/personalization_api.dart';
import 'package:ai_voice_first/features/onboarding/onboarding.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('PersonalizationApi', () {
    test('loads personalization from the expected path', () async {
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
                  'nickname': 'Alex',
                  'speaking_style': 'casual',
                  'setup_completed': true,
                },
              ),
            );
          },
        ),
      );

      final api = PersonalizationApi(dio);
      final result = await api.loadPersonalization();

      expect(result.error, isNull);
      expect(capturedPath, '/v1/profile/personalization');
      expect(result.personalization?.nickname, 'Alex');
      expect(result.personalization?.speakingStyle, SpeakingStyle.casual);
      expect(result.personalization?.setupCompleted, isTrue);
    });

    test('saves personalization on the expected path', () async {
      String? capturedPath;
      Map<String, dynamic>? capturedBody;

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPath = options.path;
            capturedBody = Map<String, dynamic>.from(options.data as Map);
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                data: {
                  'nickname': 'Alex',
                  'speaking_style': 'professional',
                  'setup_completed': false,
                },
              ),
            );
          },
        ),
      );

      final api = PersonalizationApi(dio);
      final result = await api.updatePersonalization(
        nickname: 'Alex',
        speakingStyle: 'professional',
      );

      expect(result.error, isNull);
      expect(capturedPath, '/v1/profile/personalization');
      expect(capturedBody, {
        'nickname': 'Alex',
        'speaking_style': 'professional',
      });
      expect(result.personalization?.speakingStyle, SpeakingStyle.professional);
    });

    test('updates setup completion on the expected path', () async {
      String? capturedPath;
      Map<String, dynamic>? capturedBody;

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPath = options.path;
            capturedBody = Map<String, dynamic>.from(options.data as Map);
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                data: {
                  'nickname': 'Alex',
                  'speaking_style': 'casual',
                  'setup_completed': true,
                },
              ),
            );
          },
        ),
      );

      final api = PersonalizationApi(dio);
      final result = await api.updateSetupCompletion(setupCompleted: true);

      expect(result.error, isNull);
      expect(capturedPath, '/v1/profile/setup');
      expect(capturedBody, {'setup_completed': true});
      expect(result.personalization?.setupCompleted, isTrue);
    });
  });
}
