import 'package:injectable/injectable.dart';

import '../../../core/auth/token_manager.dart';
import '../../../core/error.dart';
import '../../../core/analytics/analytics_service.dart';
import '../../../core/di/get_it.dart';
import 'auth_api.dart';
import 'auth_models.dart';

@lazySingleton
final class AuthRepository {
  AuthRepository(this._api, this._tokenManager);

  final AuthApi _api;
  final TokenManager _tokenManager;
  AnalyticsService get _analyticsService => getIt<AnalyticsService>();

  Future<({NetworkError? error, AuthUser? user})> register({
    required String email,
    required String password,
  }) async {
    final result = await _api.register(email: email, password: password);
    return _saveResult(result);
  }

  Future<({NetworkError? error, AuthUser? user})> login({
    required String email,
    required String password,
  }) async {
    final result = await _api.login(email: email, password: password);
    return _saveResult(result);
  }

  Future<bool> restoreSession() async {
    final refreshToken = await _tokenManager.refreshToken;
    if (refreshToken == null) {
      return false;
    }
    if (!await _tokenManager.isTokenExpired) {
      return true;
    }

    final result = await _api.refresh(refreshToken: refreshToken);
    if (result.tokenBundle == null) {
      await _tokenManager.clearTokens();
      await _analyticsService.reset();
      return false;
    }
    await _saveTokenBundle(result.tokenBundle!);
    return true;
  }

  Future<void> logout() async {
    final refreshToken = await _tokenManager.refreshToken;
    if (refreshToken != null) {
      await _api.logout(refreshToken: refreshToken);
    }
    await _tokenManager.clearTokens();
    await _analyticsService.reset();
  }

  Future<({NetworkError? error, AuthUser? user})> _saveResult(
    ({NetworkError? error, AuthTokenBundle? tokenBundle}) result,
  ) async {
    final tokenBundle = result.tokenBundle;
    if (tokenBundle == null) {
      return (error: result.error, user: null);
    }
    await _saveTokenBundle(tokenBundle);
    return (error: null, user: tokenBundle.user);
  }

  Future<void> _saveTokenBundle(AuthTokenBundle tokenBundle) async {
    await _tokenManager.saveTokens(
      access: tokenBundle.accessToken,
      refresh: tokenBundle.refreshToken,
      expiry: tokenBundle.expiresAt,
    );
    await _analyticsService.setUserId(tokenBundle.user.id);
  }
}
