import 'package:equatable/equatable.dart';

final class AuthUser extends Equatable {
  const AuthUser({required this.id, required this.email});

  factory AuthUser.fromJson(Map<String, dynamic> json) => AuthUser(
    id: json['id'] as String? ?? '',
    email: json['email'] as String? ?? '',
  );

  final String id;
  final String email;

  @override
  List<Object?> get props => [id, email];
}

final class AuthTokenBundle extends Equatable {
  const AuthTokenBundle({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresAt,
    required this.user,
  });

  factory AuthTokenBundle.fromJson(Map<String, dynamic> json) {
    final userJson = json['user'];
    return AuthTokenBundle(
      accessToken: json['access_token'] as String? ?? '',
      refreshToken: json['refresh_token'] as String? ?? '',
      expiresAt:
          DateTime.tryParse(json['expires_at'] as String? ?? '') ??
          DateTime.now(),
      user: userJson is Map<String, dynamic>
          ? AuthUser.fromJson(userJson)
          : const AuthUser(id: '', email: ''),
    );
  }

  final String accessToken;
  final String refreshToken;
  final DateTime expiresAt;
  final AuthUser user;

  @override
  List<Object?> get props => [accessToken, refreshToken, expiresAt, user];
}
