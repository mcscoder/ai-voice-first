import 'dart:async';

import 'package:ai_voice_first/core/analytics/analytics_service.dart';
import 'package:ai_voice_first/core/auth/secure_storage_service.dart';
import 'package:ai_voice_first/core/auth/token_manager.dart';
import 'package:ai_voice_first/core/di/get_it.dart';
import 'package:ai_voice_first/core/permissions/permission_service.dart';
import 'package:ai_voice_first/core/router/router.dart';
import 'package:ai_voice_first/features/auth/auth.dart';
import 'package:ai_voice_first/features/onboarding/onboarding.dart';
import 'package:ai_voice_first/features/voice/data/audio_recorder_service.dart';
import 'package:ai_voice_first/features/voice/data/transcription_api.dart';
import 'package:ai_voice_first/features/voice/presentation/voice_capture_cubit.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'package:ai_voice_first/shared/i18n/generated/app_localizations.dart';

void main() {
  group('AppRouter.redirectFor', () {
    test('keeps unknown auth state on loading route', () {
      expect(
        AppRouter.redirectFor(
          authState: const AuthState(status: AuthStatus.unknown),
          setupState: const SetupState(),
          location: AppRoutes.loading,
        ),
        isNull,
      );
    });

    test('sends unknown auth state to loading from other routes', () {
      expect(
        AppRouter.redirectFor(
          authState: const AuthState(status: AuthStatus.unknown),
          setupState: const SetupState(),
          location: AppRoutes.talk,
        ),
        AppRoutes.loading,
      );
    });

    test('sends unauthenticated users to auth', () {
      expect(
        AppRouter.redirectFor(
          authState: const AuthState(status: AuthStatus.unauthenticated),
          setupState: const SetupState(),
          location: AppRoutes.memory,
        ),
        AppRoutes.auth,
      );
    });

    test('keeps unauthenticated users on auth route', () {
      expect(
        AppRouter.redirectFor(
          authState: const AuthState(status: AuthStatus.unauthenticated),
          setupState: const SetupState(),
          location: AppRoutes.auth,
        ),
        isNull,
      );
    });

    test('sends authenticated users with incomplete setup to setup', () {
      expect(
        AppRouter.redirectFor(
          authState: const AuthState(status: AuthStatus.authenticated),
          setupState: const SetupState(isComplete: false),
          location: AppRoutes.talk,
        ),
        AppRoutes.setup,
      );
    });

    test(
      'sends fully onboarded users from loading, auth, setup, and root to talk',
      () {
        const authState = AuthState(status: AuthStatus.authenticated);
        const setupState = SetupState(isComplete: true);

        expect(
          AppRouter.redirectFor(
            authState: authState,
            setupState: setupState,
            location: AppRoutes.loading,
          ),
          AppRoutes.talk,
        );
        expect(
          AppRouter.redirectFor(
            authState: authState,
            setupState: setupState,
            location: AppRoutes.auth,
          ),
          AppRoutes.talk,
        );
        expect(
          AppRouter.redirectFor(
            authState: authState,
            setupState: setupState,
            location: AppRoutes.setup,
          ),
          AppRoutes.talk,
        );
        expect(
          AppRouter.redirectFor(
            authState: authState,
            setupState: setupState,
            location: AppRoutes.root,
          ),
          AppRoutes.talk,
        );
      },
    );

    test('keeps fully onboarded users on talk, memory, and profile routes', () {
      const authState = AuthState(status: AuthStatus.authenticated);
      const setupState = SetupState(isComplete: true);

      expect(
        AppRouter.redirectFor(
          authState: authState,
          setupState: setupState,
          location: AppRoutes.talk,
        ),
        isNull,
      );
      expect(
        AppRouter.redirectFor(
          authState: authState,
          setupState: setupState,
          location: AppRoutes.memory,
        ),
        isNull,
      );
      expect(
        AppRouter.redirectFor(
          authState: authState,
          setupState: setupState,
          location: AppRoutes.profile,
        ),
        isNull,
      );
    });
  });

  group('AppRouter stack navigation', () {
    late AuthCubit authCubit;
    late SetupCubit setupCubit;

    setUpAll(() {
      getIt.registerFactory<VoiceCaptureCubit>(
        () => VoiceCaptureCubit(
          const _GrantedPermissionService(),
          AudioRecorderService(),
          TranscriptionApi(Dio()),
          playAssistantSpeech: (_) async {},
        ),
      );
      getIt.registerLazySingleton<AnalyticsService>(() => _NoopAnalytics());
    });

    setUp(() {
      authCubit = AuthCubit(
        AuthRepository(
          AuthApi(Dio(), Dio()),
          _TestTokenManager(
            refreshTokenValue: 'refresh-token',
            isExpiredValue: false,
          ),
        ),
      );
      setupCubit = SetupCubit()..complete();
    });

    tearDown(() async {
      await authCubit.close();
      await setupCubit.close();
    });

    tearDownAll(() async {
      await getIt.reset();
    });

    testWidgets('starts at talk when auth and setup are complete', (
      tester,
    ) async {
      final router = await _pumpRouterApp(
        tester,
        authCubit: authCubit,
        setupCubit: setupCubit,
      );

      expect(_currentPath(router), AppRoutes.talk);
      expect(find.byTooltip('Menu'), findsOneWidget);
      expect(find.text('Memory'), findsNothing);
      expect(find.text('Profile'), findsNothing);
    });

    testWidgets('pushes memory from talk and pops back to talk', (
      tester,
    ) async {
      final router = await _pumpRouterApp(
        tester,
        authCubit: authCubit,
        setupCubit: setupCubit,
      );

      await tester.tap(find.byTooltip('Menu'));
      await _pumpForTransition(tester);
      expect(find.byTooltip('Close'), findsOneWidget);
      await tester.tap(find.byTooltip('Close'));
      await _pumpForTransition(tester);
      router.push(AppRoutes.memory);
      await _pumpForTransition(tester);

      expect(find.byTooltip('Back to talk'), findsOneWidget);
      expect(find.text('Memory'), findsOneWidget);
      expect(find.text('Memory is enabled'), findsOneWidget);

      await tester.binding.handlePopRoute();
      await _pumpForTransition(tester);

      expect(find.byTooltip('Menu'), findsOneWidget);
      expect(find.text('Memory is enabled'), findsNothing);
    });

    testWidgets('pushes profile from talk and pops back to talk', (
      tester,
    ) async {
      final router = await _pumpRouterApp(
        tester,
        authCubit: authCubit,
        setupCubit: setupCubit,
      );

      await tester.tap(find.byTooltip('Menu'));
      await _pumpForTransition(tester);
      expect(find.byTooltip('Close'), findsOneWidget);
      await tester.tap(find.byTooltip('Close'));
      await _pumpForTransition(tester);
      router.push(AppRoutes.profile);
      await _pumpForTransition(tester);

      expect(find.byTooltip('Back to talk'), findsOneWidget);
      expect(find.text('Profile'), findsOneWidget);
      expect(find.text('ACCOUNT'), findsOneWidget);
      expect(find.text('Voice settings'), findsOneWidget);

      await tester.binding.handlePopRoute();
      await _pumpForTransition(tester);

      expect(find.byTooltip('Menu'), findsOneWidget);
      expect(find.text('Voice settings'), findsNothing);
    });
  });
}

Future<GoRouter> _pumpRouterApp(
  WidgetTester tester, {
  required AuthCubit authCubit,
  required SetupCubit setupCubit,
}) async {
  final router = AppRouter.createRouter(
    authCubit: authCubit,
    setupCubit: setupCubit,
  );

  await tester.pumpWidget(
    _RouterTestApp(
      authCubit: authCubit,
      setupCubit: setupCubit,
      router: router,
    ),
  );
  await tester.pump();
  await _pumpForTransition(tester);
  return router;
}

String _currentPath(GoRouter router) {
  return router.routeInformationProvider.value.uri.path;
}

Future<void> _pumpForTransition(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(seconds: 1));
}

final class _RouterTestApp extends StatefulWidget {
  const _RouterTestApp({
    required this.authCubit,
    required this.setupCubit,
    required this.router,
  });

  final AuthCubit authCubit;
  final SetupCubit setupCubit;
  final GoRouter router;

  @override
  State<_RouterTestApp> createState() => _RouterTestAppState();
}

final class _RouterTestAppState extends State<_RouterTestApp> {
  StreamSubscription<AuthState>? _authSubscription;
  StreamSubscription<SetupState>? _setupSubscription;

  @override
  void initState() {
    super.initState();
    _authSubscription = widget.authCubit.stream.listen((_) {
      widget.router.refresh();
    });
    _setupSubscription = widget.setupCubit.stream.listen((_) {
      widget.router.refresh();
    });
    unawaited(widget.authCubit.restoreSession());
  }

  @override
  void dispose() {
    _authSubscription?.cancel();
    _setupSubscription?.cancel();
    widget.router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<AuthCubit>.value(value: widget.authCubit),
        BlocProvider<SetupCubit>.value(value: widget.setupCubit),
      ],
      child: MaterialApp.router(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        routerConfig: widget.router,
      ),
    );
  }
}

final class _GrantedPermissionService implements PermissionService {
  const _GrantedPermissionService();

  @override
  Future<AppPermissionStatus> check(AppPermission permission) async {
    return AppPermissionStatus.granted;
  }

  @override
  Future<bool> openSettings() async {
    return true;
  }

  @override
  Future<AppPermissionStatus> request(AppPermission permission) async {
    return AppPermissionStatus.granted;
  }
}

final class _TestTokenManager extends TokenManager {
  _TestTokenManager({
    required this.refreshTokenValue,
    required this.isExpiredValue,
  }) : super(_InMemorySecureStorageService());

  final String? refreshTokenValue;
  final bool isExpiredValue;

  @override
  Future<String?> get refreshToken async => refreshTokenValue;

  @override
  Future<bool> get isTokenExpired async => isExpiredValue;
}

final class _InMemorySecureStorageService extends SecureStorageService {
  _InMemorySecureStorageService();

  final Map<String, String> _values = <String, String>{};

  @override
  Future<void> delete(String key) async {
    _values.remove(key);
  }

  @override
  Future<void> deleteAll() async {
    _values.clear();
  }

  @override
  Future<String?> read(String key) async {
    return _values[key];
  }

  @override
  Future<void> write(String key, String value) async {
    _values[key] = value;
  }
}

final class _NoopAnalytics implements AnalyticsService {
  @override
  Future<void> initialize() async {}

  @override
  Future<void> reset() async {}

  @override
  Future<void> setUserId(String? userId) async {}

  @override
  Future<void> setUserProperty(String key, String value) async {}

  @override
  Future<void> trackEvent(
    String name, {
    Map<String, dynamic>? properties,
  }) async {}

  @override
  Future<void> trackScreen(
    String screenName, {
    Map<String, dynamic>? properties,
  }) async {}
}
