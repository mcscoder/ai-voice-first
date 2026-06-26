import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/design_system/design_system.dart';
import '../../../shared/forms/email_input.dart';
import '../../../shared/forms/password_input.dart';
import 'auth_cubit.dart';
import 'auth_state.dart';

final class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

final class _AuthScreenState extends State<AuthScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _submitted = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      backgroundColor: colorScheme.surface,
      body: SafeArea(
        child: BlocBuilder<AuthCubit, AuthState>(
          builder: (context, state) {
            final isBusy = state.status == AuthStatus.submitting;
            final isRegister = state.isRegisterMode;
            return Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.xl),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        isRegister ? 'Create account' : 'Sign in',
                        style: theme.textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      TextField(
                        controller: _emailController,
                        enabled: !isBusy,
                        keyboardType: TextInputType.emailAddress,
                        autofillHints: const [AutofillHints.email],
                        decoration: InputDecoration(
                          labelText: 'Email',
                          errorText: _emailErrorText,
                          border: const OutlineInputBorder(
                            borderRadius: AppRadius.borderSm,
                          ),
                        ),
                        onChanged: (_) => _clearSubmitted(),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      TextField(
                        controller: _passwordController,
                        enabled: !isBusy,
                        obscureText: true,
                        autofillHints: const [AutofillHints.password],
                        decoration: InputDecoration(
                          labelText: 'Password',
                          errorText: _passwordErrorText,
                          border: const OutlineInputBorder(
                            borderRadius: AppRadius.borderSm,
                          ),
                        ),
                        onChanged: (_) => _clearSubmitted(),
                        onSubmitted: (_) => _submit(context),
                      ),
                      if (state.failureMessage != null) ...[
                        const SizedBox(height: AppSpacing.md),
                        Text(
                          state.failureMessage!,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: colorScheme.error,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 0,
                          ),
                        ),
                      ],
                      const SizedBox(height: AppSpacing.lg),
                      FilledButton(
                        onPressed: isBusy ? null : () => _submit(context),
                        child: isBusy
                            ? const SizedBox.square(
                                dimension: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : Text(isRegister ? 'Create account' : 'Sign in'),
                      ),
                      TextButton(
                        onPressed: isBusy
                            ? null
                            : context.read<AuthCubit>().toggleMode,
                        child: Text(
                          isRegister
                              ? 'Use an existing account'
                              : 'Create a new account',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  String? get _emailErrorText {
    if (!_submitted) {
      return null;
    }
    final email = EmailInput.dirty(_emailController.text.trim());
    if (email.error == EmailValidationError.empty) {
      return 'Email is required.';
    }
    if (email.error == EmailValidationError.invalid) {
      return 'Enter a valid email.';
    }
    return null;
  }

  String? get _passwordErrorText {
    if (!_submitted) {
      return null;
    }
    final password = PasswordInput.dirty(_passwordController.text);
    switch (password.error) {
      case PasswordValidationError.empty:
        return 'Password is required.';
      case PasswordValidationError.tooShort:
        return 'Use at least 8 characters.';
      case PasswordValidationError.noUppercase:
        return 'Add an uppercase letter.';
      case PasswordValidationError.noDigit:
        return 'Add a number.';
      case PasswordValidationError.noSpecial:
        return 'Add a special character.';
      case null:
        return null;
    }
  }

  void _clearSubmitted() {
    if (_submitted) {
      setState(() {
        _submitted = false;
      });
    }
  }

  void _submit(BuildContext context) {
    setState(() {
      _submitted = true;
    });
    final email = EmailInput.dirty(_emailController.text.trim());
    final password = PasswordInput.dirty(_passwordController.text);
    if (!email.isValid || !password.isValid) {
      return;
    }
    context.read<AuthCubit>().submit(
      email: email.value,
      password: password.value,
    );
  }
}
