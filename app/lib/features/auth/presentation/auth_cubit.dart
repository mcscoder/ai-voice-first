import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:injectable/injectable.dart';

import '../../../core/error.dart';
import '../data/auth_repository.dart';
import 'auth_state.dart';

@lazySingleton
final class AuthCubit extends Cubit<AuthState> {
  AuthCubit(this._repository) : super(const AuthState());

  final AuthRepository _repository;

  Future<void> restoreSession() async {
    emit(state.copyWith(status: AuthStatus.unknown, clearFailure: true));
    final restored = await _repository.restoreSession();
    emit(
      state.copyWith(
        status: restored
            ? AuthStatus.authenticated
            : AuthStatus.unauthenticated,
        clearFailure: true,
      ),
    );
  }

  void toggleMode() {
    if (state.isBusy) {
      return;
    }
    emit(
      state.copyWith(
        isRegisterMode: !state.isRegisterMode,
        status: AuthStatus.unauthenticated,
        clearFailure: true,
      ),
    );
  }

  Future<void> submit({required String email, required String password}) async {
    if (state.status == AuthStatus.submitting) {
      return;
    }
    emit(state.copyWith(status: AuthStatus.submitting, clearFailure: true));
    final result = state.isRegisterMode
        ? await _repository.register(email: email, password: password)
        : await _repository.login(email: email, password: password);
    if (result.user != null) {
      emit(
        state.copyWith(status: AuthStatus.authenticated, clearFailure: true),
      );
      return;
    }
    emit(
      state.copyWith(
        status: AuthStatus.failure,
        failureMessage: _messageFor(result.error),
      ),
    );
  }

  Future<void> logout() async {
    await _repository.logout();
    emit(
      state.copyWith(status: AuthStatus.unauthenticated, clearFailure: true),
    );
  }

  String _messageFor(NetworkError? error) {
    if (error is Unauthorized) {
      return 'Email or password is incorrect.';
    }
    if (error is BadRequest) {
      return 'Check your email and password.';
    }
    if (error is Timeout) {
      return 'The request timed out.';
    }
    return 'Authentication failed.';
  }
}
