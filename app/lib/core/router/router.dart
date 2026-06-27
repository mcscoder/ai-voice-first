import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../error_screen.dart';
import '../../features/auth/auth.dart';
import '../../features/memory/memory.dart';
import '../../features/onboarding/onboarding.dart';
import '../../features/profile/profile.dart';
import '../../features/voice/voice.dart';
import '../../features/voice_settings/voice_settings.dart';
import '../di/get_it.dart';

abstract class AppRoutes {
  AppRoutes._();
  static const root = '/';
  static const loading = '/loading';
  static const auth = '/auth';
  static const setup = '/setup';
  static const talk = '/talk';
  static const memory = '/memory';
  static const profile = '/profile';
  static const profilePersonalization = '/profile/personalization';
  static const voiceSettings = '/profile/voice-settings';

  static String memoryCategory(String categoryKey) => '$memory/$categoryKey';
}

abstract class AppRouter {
  AppRouter._();

  static GoRouter createRouter({
    required AuthCubit authCubit,
    required SetupCubit setupCubit,
  }) {
    return GoRouter(
      debugLogDiagnostics: true,
      initialLocation: AppRoutes.loading,
      redirect: (_, state) => redirectFor(
        authState: authCubit.state,
        setupState: setupCubit.state,
        location: state.matchedLocation,
      ),
      routes: [
        GoRoute(path: AppRoutes.root, redirect: (_, _) => AppRoutes.talk),
        GoRoute(
          path: AppRoutes.loading,
          builder: (_, _) => const _LoadingScreen(),
        ),
        GoRoute(path: AppRoutes.auth, builder: (_, _) => const AuthScreen()),
        GoRoute(path: AppRoutes.setup, builder: (_, _) => const SetupFlow()),
        GoRoute(path: AppRoutes.talk, builder: (_, _) => const VoiceScreen()),
        GoRoute(
          path: AppRoutes.memory,
          builder: (_, _) => const MemoryScreen(),
        ),
        GoRoute(
          path: '${AppRoutes.memory}/:categoryKey',
          builder: (_, state) => MemoryCategoryScreen(
            categoryKey: state.pathParameters['categoryKey'] ?? '',
          ),
        ),
        GoRoute(
          path: AppRoutes.profile,
          builder: (_, _) => const ProfileScreen(),
        ),
        GoRoute(
          path: AppRoutes.profilePersonalization,
          builder: (_, _) => const ProfilePersonalizationScreen(),
        ),
        GoRoute(
          path: AppRoutes.voiceSettings,
          builder: (_, _) => BlocProvider(
            create: (_) => getIt<VoiceSettingsCubit>()..load(),
            child: const VoiceSettingsScreen(),
          ),
        ),
      ],
      errorBuilder: (_, _) => const ErrorScreen(),
    );
  }

  static String? redirectFor({
    required AuthState authState,
    required SetupState setupState,
    required String location,
  }) {
    if (authState.status == AuthStatus.unknown) {
      return location == AppRoutes.loading ? null : AppRoutes.loading;
    }

    final isAuthenticated = authState.status == AuthStatus.authenticated;
    if (!isAuthenticated) {
      return location == AppRoutes.auth ? null : AppRoutes.auth;
    }

    if (setupState.syncStatus == SetupSyncStatus.initial ||
        setupState.syncStatus == SetupSyncStatus.syncing) {
      return location == AppRoutes.loading ? null : AppRoutes.loading;
    }

    if (!setupState.isComplete) {
      return location == AppRoutes.setup ? null : AppRoutes.setup;
    }

    if (location == AppRoutes.loading ||
        location == AppRoutes.auth ||
        location == AppRoutes.setup ||
        location == AppRoutes.root) {
      return AppRoutes.talk;
    }

    return null;
  }
}

final class _LoadingScreen extends StatelessWidget {
  const _LoadingScreen();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}
