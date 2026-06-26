import 'package:equatable/equatable.dart';

enum AuthStatus { unknown, unauthenticated, authenticated, submitting, failure }

final class AuthState extends Equatable {
  const AuthState({
    this.status = AuthStatus.unknown,
    this.isRegisterMode = false,
    this.failureMessage,
  });

  final AuthStatus status;
  final bool isRegisterMode;
  final String? failureMessage;

  bool get isBusy =>
      status == AuthStatus.unknown || status == AuthStatus.submitting;

  AuthState copyWith({
    AuthStatus? status,
    bool? isRegisterMode,
    String? failureMessage,
    bool clearFailure = false,
  }) {
    return AuthState(
      status: status ?? this.status,
      isRegisterMode: isRegisterMode ?? this.isRegisterMode,
      failureMessage: clearFailure
          ? null
          : failureMessage ?? this.failureMessage,
    );
  }

  @override
  List<Object?> get props => [status, isRegisterMode, failureMessage];
}
