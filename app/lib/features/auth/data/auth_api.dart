import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

import '../../../core/error.dart';
import '../../../core/network/api.dart';
import '../../../core/network/api_path.dart';
import '../../../core/network/dio.dart';
import 'auth_models.dart';

@lazySingleton
final class AuthApi extends Api {
  AuthApi(@nonAuthDio super.dio, @authDio this._authDio);

  final Dio _authDio;

  Future<({NetworkError? error, AuthTokenBundle? tokenBundle})> register({
    required String email,
    required String password,
  }) async {
    return _submitCredentials(ApiPath.authRegister, email, password);
  }

  Future<({NetworkError? error, AuthTokenBundle? tokenBundle})> login({
    required String email,
    required String password,
  }) async {
    return _submitCredentials(ApiPath.authLogin, email, password);
  }

  Future<({NetworkError? error, AuthTokenBundle? tokenBundle})> refresh({
    required String refreshToken,
  }) async {
    final result = await withTimeoutRequest(() async {
      final response = await dio.post<Map<String, dynamic>>(
        ApiPath.authRefresh,
        data: {'refresh_token': refreshToken},
      );
      return AuthTokenBundle.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, tokenBundle: null),
      (tokenBundle) => (error: null, tokenBundle: tokenBundle),
    );
  }

  Future<NetworkError?> logout({required String refreshToken}) async {
    final result = await withTimeoutRequest(() async {
      await _authDio.post<Map<String, dynamic>>(
        ApiPath.authLogout,
        data: {'refresh_token': refreshToken},
      );
    });
    return result.match((error) => error, (_) => null);
  }

  Future<({NetworkError? error, AuthUser? user})> me() async {
    final result = await withTimeoutRequest(() async {
      final response = await _authDio.get<Map<String, dynamic>>(ApiPath.authMe);
      return AuthUser.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, user: null),
      (user) => (error: null, user: user),
    );
  }

  Future<({NetworkError? error, AuthTokenBundle? tokenBundle})>
  _submitCredentials(String path, String email, String password) async {
    final result = await withTimeoutRequest(() async {
      final response = await dio.post<Map<String, dynamic>>(
        path,
        data: {'email': email, 'password': password},
      );
      return AuthTokenBundle.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, tokenBundle: null),
      (tokenBundle) => (error: null, tokenBundle: tokenBundle),
    );
  }
}
