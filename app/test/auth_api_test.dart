import 'package:ai_voice_first/features/auth/auth.dart';
import 'package:ai_voice_first/core/error.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('AuthApi', () {
    test('logs in and parses token bundle', () async {
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
                  'access_token': 'access',
                  'refresh_token': 'refresh',
                  'expires_at': '2026-06-26T12:00:00Z',
                  'user': {'id': 'user-1', 'email': 'test@example.com'},
                },
              ),
            );
          },
        ),
      );

      final api = AuthApi(
        dio,
        Dio(BaseOptions(baseUrl: 'http://localhost:8000')),
      );
      final result = await api.login(
        email: 'test@example.com',
        password: 'Password1!',
      );

      expect(result.error, isNull);
      expect(result.tokenBundle?.accessToken, 'access');
      expect(result.tokenBundle?.refreshToken, 'refresh');
      expect(result.tokenBundle?.user.id, 'user-1');
      expect(capturedPath, '/auth/login');
      expect(capturedBody, {
        'email': 'test@example.com',
        'password': 'Password1!',
      });
    });

    test('maps unauthorized login responses', () async {
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

      final api = AuthApi(
        dio,
        Dio(BaseOptions(baseUrl: 'http://localhost:8000')),
      );
      final result = await api.login(
        email: 'test@example.com',
        password: 'Password1!',
      );

      expect(result.tokenBundle, isNull);
      expect(result.error, isA<Unauthorized>());
    });
  });
}
