import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/design_system/design_system.dart';
import '../../home/home.dart';
import '../../onboarding/onboarding.dart';
import 'auth_cubit.dart';
import 'auth_screen.dart';
import 'auth_state.dart';

final class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

final class _AuthGateState extends State<AuthGate> {
  @override
  void initState() {
    super.initState();
    context.read<AuthCubit>().restoreSession();
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthCubit, AuthState>(
      builder: (context, state) {
        switch (state.status) {
          case AuthStatus.authenticated:
            return BlocBuilder<SetupCubit, SetupState>(
              builder: (context, setup) {
                if (!setup.isComplete) {
                  return const SetupFlow();
                }
                return const MainShell();
              },
            );
          case AuthStatus.unknown:
            return const VoxiaScaffold(
              child: Center(child: CircularProgressIndicator()),
            );
          case AuthStatus.unauthenticated:
          case AuthStatus.submitting:
          case AuthStatus.failure:
            return const AuthScreen();
        }
      },
    );
  }
}
