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

enum _AuthView { welcome, login, forgotPassword }

final class _AuthScreenState extends State<AuthScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  var _view = _AuthView.welcome;
  bool _submitted = false;
  bool _passwordVisible = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return VoxiaScaffold(
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 180),
        child: switch (_view) {
          _AuthView.welcome => _WelcomeView(
            key: const ValueKey('welcome'),
            onLogin: () => _showLogin(register: false),
            onSignUp: () => _showLogin(register: true),
          ),
          _AuthView.login => _LoginView(
            key: const ValueKey('login'),
            emailController: _emailController,
            passwordController: _passwordController,
            submitted: _submitted,
            passwordVisible: _passwordVisible,
            emailErrorText: _emailErrorText,
            passwordErrorText: _passwordErrorText,
            onBack: _showWelcome,
            onForgotPassword: () => setState(() {
              _view = _AuthView.forgotPassword;
            }),
            onTogglePasswordVisibility: () => setState(() {
              _passwordVisible = !_passwordVisible;
            }),
            onChanged: _clearSubmitted,
            onSubmit: () => _submit(context),
          ),
          _AuthView.forgotPassword => _ForgotPasswordView(
            key: const ValueKey('forgot'),
            emailController: _emailController,
            submitted: _submitted,
            emailErrorText: _emailErrorText,
            onBack: _showLoginFromForgot,
            onChanged: _clearSubmitted,
            onSubmit: _sendResetLink,
          ),
        },
      ),
    );
  }

  void _showWelcome() {
    setState(() {
      _submitted = false;
      _view = _AuthView.welcome;
    });
  }

  void _showLogin({required bool register}) {
    final cubit = context.read<AuthCubit>();
    if (cubit.state.isRegisterMode != register) {
      cubit.toggleMode();
    }
    setState(() {
      _submitted = false;
      _view = _AuthView.login;
    });
  }

  void _showLoginFromForgot() {
    setState(() {
      _submitted = false;
      _view = _AuthView.login;
    });
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

  void _sendResetLink() {
    setState(() {
      _submitted = true;
    });
    final email = EmailInput.dirty(_emailController.text.trim());
    if (!email.isValid) {
      return;
    }
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Reset link sent.')));
  }
}

final class _WelcomeView extends StatelessWidget {
  const _WelcomeView({
    required this.onLogin,
    required this.onSignUp,
    super.key,
  });

  final VoidCallback onLogin;
  final VoidCallback onSignUp;

  @override
  Widget build(BuildContext context) {
    return VoxiaFixedPage(
      body: Column(
        children: [
          const Spacer(),
          const VoxiaOrb(size: 150),
          const SizedBox(height: AppSpacing.lg),
          Text(
            'Talk naturally\nwith your AI',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: VoxiaColors.text,
              fontWeight: FontWeight.w800,
              height: 1.14,
              letterSpacing: 0,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Your voice. Your assistant.\nAlways here.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: VoxiaColors.muted,
              height: 1.35,
              letterSpacing: 0,
            ),
          ),
          const Spacer(),
          VoxiaGradientButton(label: 'Sign up', onPressed: onSignUp),
          const SizedBox(height: AppSpacing.sm),
          VoxiaOutlineButton(label: 'Log in', onPressed: onLogin),
          const SizedBox(height: AppSpacing.lg),
          const _PagerDots(),
          const SizedBox(height: AppSpacing.md),
        ],
      ),
    );
  }
}

final class _LoginView extends StatelessWidget {
  const _LoginView({
    required this.emailController,
    required this.passwordController,
    required this.submitted,
    required this.passwordVisible,
    required this.emailErrorText,
    required this.passwordErrorText,
    required this.onBack,
    required this.onForgotPassword,
    required this.onTogglePasswordVisibility,
    required this.onChanged,
    required this.onSubmit,
    super.key,
  });

  final TextEditingController emailController;
  final TextEditingController passwordController;
  final bool submitted;
  final bool passwordVisible;
  final String? emailErrorText;
  final String? passwordErrorText;
  final VoidCallback onBack;
  final VoidCallback onForgotPassword;
  final VoidCallback onTogglePasswordVisibility;
  final VoidCallback onChanged;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthCubit, AuthState>(
      builder: (context, state) {
        final isBusy = state.status == AuthStatus.submitting;
        final isRegister = state.isRegisterMode;
        return VoxiaFixedPage(
          leading: IconButton(
            tooltip: 'Back',
            onPressed: isBusy ? null : onBack,
            icon: const Icon(Icons.arrow_back),
          ),
          body: CustomScrollView(
            slivers: [
              SliverFillRemaining(
                hasScrollBody: false,
                child: Column(
                  children: [
                    const Spacer(),
                    ..._formChildren(
                      context,
                      state,
                      isBusy: isBusy,
                      isRegister: isRegister,
                      includeBrand: true,
                      includeSocial: true,
                    ),
                    const Spacer(flex: 2),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  List<Widget> _formChildren(
    BuildContext context,
    AuthState state, {
    required bool isBusy,
    required bool isRegister,
    required bool includeBrand,
    required bool includeSocial,
  }) {
    return [
      if (includeBrand) ...[
        const Center(child: VoxiaMark(size: 96)),
        const SizedBox(height: AppSpacing.md),
      ],
      TextField(
        controller: emailController,
        enabled: !isBusy,
        keyboardType: TextInputType.emailAddress,
        autofillHints: const [AutofillHints.email],
        decoration: InputDecoration(
          hintText: 'Email or phone',
          errorText: emailErrorText,
          prefixIcon: const Icon(Icons.mail_outline),
        ),
        onChanged: (_) => onChanged(),
      ),
      const SizedBox(height: AppSpacing.sm),
      TextField(
        controller: passwordController,
        enabled: !isBusy,
        obscureText: !passwordVisible,
        autofillHints: const [AutofillHints.password],
        decoration: InputDecoration(
          hintText: 'Password',
          errorText: passwordErrorText,
          prefixIcon: const Icon(Icons.lock_outline),
          suffixIcon: IconButton(
            tooltip: passwordVisible ? 'Hide password' : 'Show password',
            onPressed: onTogglePasswordVisibility,
            icon: Icon(
              passwordVisible
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined,
            ),
          ),
        ),
        onChanged: (_) => onChanged(),
        onSubmitted: (_) => onSubmit(),
      ),
      if (!isRegister)
        Align(
          alignment: Alignment.centerRight,
          child: TextButton(
            onPressed: isBusy ? null : onForgotPassword,
            child: const Text('Forgot password?'),
          ),
        ),
      if (state.failureMessage != null) ...[
        const SizedBox(height: AppSpacing.sm),
        Text(
          state.failureMessage!,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.error,
            fontWeight: FontWeight.w700,
            letterSpacing: 0,
          ),
        ),
      ],
      if (includeSocial) ...[
        const SizedBox(height: AppSpacing.md),
        const _SocialButton(
          icon: Icons.g_mobiledata,
          label: 'Continue with Google',
        ),
        const SizedBox(height: AppSpacing.sm),
        const _SocialButton(icon: Icons.apple, label: 'Continue with Apple'),
        const SizedBox(height: AppSpacing.sm),
        const _DividerLabel(label: 'or'),
      ],
      const SizedBox(height: AppSpacing.sm),
      VoxiaGradientButton(
        label: isRegister ? 'Sign up' : 'Log in',
        isBusy: isBusy,
        onPressed: onSubmit,
      ),
      TextButton(
        onPressed: isBusy ? null : context.read<AuthCubit>().toggleMode,
        child: Text(
          isRegister ? 'Use an existing account' : 'Create a new account',
        ),
      ),
    ];
  }
}

final class _ForgotPasswordView extends StatelessWidget {
  const _ForgotPasswordView({
    required this.emailController,
    required this.submitted,
    required this.emailErrorText,
    required this.onBack,
    required this.onChanged,
    required this.onSubmit,
    super.key,
  });

  final TextEditingController emailController;
  final bool submitted;
  final String? emailErrorText;
  final VoidCallback onBack;
  final VoidCallback onChanged;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return VoxiaFixedPage(
      leading: IconButton(
        tooltip: 'Back',
        onPressed: onBack,
        icon: const Icon(Icons.arrow_back),
      ),
      body: CustomScrollView(
        slivers: [
          SliverFillRemaining(
            hasScrollBody: false,
            child: Column(
              children: [
                const Spacer(),
                ..._children(context, includeBrand: true),
                const Spacer(flex: 2),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _children(BuildContext context, {required bool includeBrand}) {
    return [
      if (includeBrand) ...[
        const Center(child: VoxiaMark(size: 96)),
        const SizedBox(height: AppSpacing.md),
        const VoxiaScreenHeader(
          title: 'Reset your password',
          subtitle:
              "Enter your email or phone number and we'll send you a link to reset it.",
        ),
        const SizedBox(height: AppSpacing.md),
      ],
      TextField(
        controller: emailController,
        keyboardType: TextInputType.emailAddress,
        decoration: InputDecoration(
          hintText: 'Email or phone',
          errorText: emailErrorText,
          prefixIcon: const Icon(Icons.mark_email_unread_outlined),
        ),
        onChanged: (_) => onChanged(),
        onSubmitted: (_) => onSubmit(),
      ),
      const SizedBox(height: AppSpacing.sm),
      VoxiaGradientButton(label: 'Send reset link', onPressed: onSubmit),
      TextButton(onPressed: onBack, child: const Text('Back to login')),
    ];
  }
}

final class _SocialButton extends StatelessWidget {
  const _SocialButton({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return VoxiaGlassPanel(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: VoxiaColors.text, size: 24),
          const SizedBox(width: AppSpacing.sm),
          Text(
            label,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: VoxiaColors.text,
              fontWeight: FontWeight.w700,
              letterSpacing: 0,
            ),
          ),
        ],
      ),
    );
  }
}

final class _DividerLabel extends StatelessWidget {
  const _DividerLabel({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(child: Divider(color: VoxiaColors.border)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
          child: Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: VoxiaColors.muted,
              letterSpacing: 0,
            ),
          ),
        ),
        const Expanded(child: Divider(color: VoxiaColors.border)),
      ],
    );
  }
}

final class _PagerDots extends StatelessWidget {
  const _PagerDots();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        for (var i = 0; i < 5; i += 1)
          Container(
            width: 10,
            height: 10,
            margin: const EdgeInsets.symmetric(horizontal: AppSpacing.xs),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: i == 0
                  ? VoxiaColors.cyan
                  : VoxiaColors.muted.withValues(alpha: 0.24),
            ),
          ),
      ],
    );
  }
}
