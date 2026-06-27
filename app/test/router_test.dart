import 'dart:async';
import 'dart:typed_data';

import 'package:ai_voice_first/core/analytics/analytics_service.dart';
import 'package:ai_voice_first/core/error.dart';
import 'package:ai_voice_first/core/auth/secure_storage_service.dart';
import 'package:ai_voice_first/core/auth/token_manager.dart';
import 'package:ai_voice_first/core/di/get_it.dart';
import 'package:ai_voice_first/core/permissions/permission_service.dart';
import 'package:ai_voice_first/core/router/router.dart';
import 'package:ai_voice_first/features/auth/auth.dart';
import 'package:ai_voice_first/features/memory/memory.dart';
import 'package:ai_voice_first/features/onboarding/onboarding.dart';
import 'package:ai_voice_first/features/voice/data/audio_recorder_service.dart';
import 'package:ai_voice_first/features/voice/data/transcription_api.dart';
import 'package:ai_voice_first/features/voice/presentation/voice_capture_cubit.dart';
import 'package:ai_voice_first/features/voice_settings/voice_settings.dart';
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
          setupState: const SetupState(syncStatus: SetupSyncStatus.synced),
          location: AppRoutes.talk,
        ),
        AppRoutes.setup,
      );
    });

    test('keeps authenticated users on loading until setup sync finishes', () {
      expect(
        AppRouter.redirectFor(
          authState: const AuthState(status: AuthStatus.authenticated),
          setupState: const SetupState(),
          location: AppRoutes.talk,
        ),
        AppRoutes.loading,
      );
    });

    test(
      'sends fully onboarded users from loading, auth, setup, and root to talk',
      () {
        const authState = AuthState(status: AuthStatus.authenticated);
        const setupState = SetupState(
          isComplete: true,
          syncStatus: SetupSyncStatus.synced,
        );

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
      const setupState = SetupState(
        isComplete: true,
        syncStatus: SetupSyncStatus.synced,
      );

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
      expect(
        AppRouter.redirectFor(
          authState: authState,
          setupState: setupState,
          location: AppRoutes.voiceSettings,
        ),
        isNull,
      );
    });
  });

  group('AppRouter stack navigation', () {
    late AuthCubit authCubit;
    late _MemoryRepositoryStub memoryRepository;
    late MemoryCubit memoryCubit;
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
      getIt.registerFactory<VoiceSettingsCubit>(
        () => VoiceSettingsCubit(
          _VoiceSettingsRepositoryStub(),
          playVoicePreview: (_) async {},
          stopVoicePreview: () async {},
          loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
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
      memoryRepository = _MemoryRepositoryStub(
        collection: const MemoryCollection(
          memoryEnabled: false,
          memories: [
            MemoryItem(
              id: 'memory-1',
              memory: 'Prefers short answers.',
              category: MemoryCategory.preferences,
              createdAt: '2026-06-25T04:08:26+00:00',
              updatedAt: '2026-06-25T05:40:29+00:00',
            ),
          ],
        ),
      );
      memoryCubit = MemoryCubit(memoryRepository);
      setupCubit = SetupCubit()..complete();
    });

    tearDown(() async {
      await authCubit.close();
      await memoryCubit.close();
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
        memoryCubit: memoryCubit,
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
        memoryCubit: memoryCubit,
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
      expect(find.text('Memory is disabled'), findsOneWidget);
      expect(find.text('1 item'), findsOneWidget);
      expect(find.byType(FloatingActionButton), findsOneWidget);

      await tester.tap(find.text('Preferences'));
      await _pumpForTransition(tester);

      expect(find.text('Preferences'), findsOneWidget);
      expect(find.text('Prefers short answers.'), findsOneWidget);
      expect(find.byType(FloatingActionButton), findsOneWidget);

      await tester.binding.handlePopRoute();
      await _pumpForTransition(tester);

      expect(find.text('Memory'), findsOneWidget);
      expect(find.text('Memory is disabled'), findsOneWidget);

      await tester.binding.handlePopRoute();
      await _pumpForTransition(tester);

      expect(find.byTooltip('Menu'), findsOneWidget);
      expect(find.text('Memory is disabled'), findsNothing);
    });

    testWidgets('reopens memory and refetches latest items', (tester) async {
      await memoryCubit.close();
      memoryRepository = _MemoryRepositoryStub(
        loadCollections: [
          MemoryCollection(memoryEnabled: true, memories: _memoryItems(10)),
          MemoryCollection(memoryEnabled: true, memories: _memoryItems(12)),
        ],
      );
      memoryCubit = MemoryCubit(memoryRepository);

      final router = await _pumpRouterApp(
        tester,
        authCubit: authCubit,
        memoryCubit: memoryCubit,
        setupCubit: setupCubit,
      );

      router.push(AppRoutes.memory);
      await _pumpForTransition(tester);

      expect(find.text('10 items'), findsOneWidget);
      expect(memoryRepository.loadCallCount, 1);

      await tester.binding.handlePopRoute();
      await _pumpForTransition(tester);

      router.push(AppRoutes.memory);
      await _pumpForTransition(tester);

      expect(find.text('12 items'), findsOneWidget);
      expect(find.text('10 items'), findsNothing);
      expect(memoryRepository.loadCallCount, 2);
    });

    testWidgets('pushes profile from talk and pops back to talk', (
      tester,
    ) async {
      final router = await _pumpRouterApp(
        tester,
        authCubit: authCubit,
        memoryCubit: memoryCubit,
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

    testWidgets('opens voice settings from profile', (tester) async {
      final router = await _pumpRouterApp(
        tester,
        authCubit: authCubit,
        memoryCubit: memoryCubit,
        setupCubit: setupCubit,
      );

      router.push(AppRoutes.profile);
      await _pumpForTransition(tester);

      await tester.tap(find.text('Voice settings'));
      await _pumpForTransition(tester);

      expect(find.byType(VoiceSettingsScreen), findsOneWidget);
      expect(find.byKey(const Key('voice_settings_save')), findsOneWidget);
      expect(find.text('Ngọc Linh'), findsOneWidget);

      await tester.binding.handlePopRoute();
      await _pumpForTransition(tester);

      expect(find.text('Profile'), findsOneWidget);
    });
  });
}

Future<GoRouter> _pumpRouterApp(
  WidgetTester tester, {
  required AuthCubit authCubit,
  required MemoryCubit memoryCubit,
  required SetupCubit setupCubit,
}) async {
  final router = AppRouter.createRouter(
    authCubit: authCubit,
    setupCubit: setupCubit,
  );

  await tester.pumpWidget(
    _RouterTestApp(
      authCubit: authCubit,
      memoryCubit: memoryCubit,
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
    required this.memoryCubit,
    required this.setupCubit,
    required this.router,
  });

  final AuthCubit authCubit;
  final MemoryCubit memoryCubit;
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
        BlocProvider<MemoryCubit>.value(value: widget.memoryCubit),
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

final class _MemoryRepositoryStub extends MemoryRepository {
  _MemoryRepositoryStub({
    MemoryCollection? collection,
    List<MemoryCollection>? loadCollections,
  }) : _loadCollections =
           loadCollections ??
           [
             collection ??
                 const MemoryCollection(memoryEnabled: true, memories: []),
           ],
       super(MemoryApi(Dio()));

  final List<MemoryCollection> _loadCollections;
  int loadCallCount = 0;

  @override
  Future<({NetworkError? error, MemoryCollection? collection})>
  loadMemories() async {
    final index = loadCallCount < _loadCollections.length
        ? loadCallCount
        : _loadCollections.length - 1;
    loadCallCount += 1;
    return (error: null, collection: _loadCollections[index]);
  }

  @override
  Future<({NetworkError? error, MemoryItem? item})> createMemory({
    required String memory,
    required MemoryCategory category,
  }) async {
    return (error: null, item: null);
  }

  @override
  Future<({NetworkError? error, MemoryItem? item})> updateMemory({
    required String id,
    required String memory,
    required MemoryCategory category,
  }) async {
    return (error: null, item: null);
  }

  @override
  Future<NetworkError?> deleteMemory({required String id}) async {
    return null;
  }

  @override
  Future<({NetworkError? error, bool? memoryEnabled})> updateSettings({
    required bool memoryEnabled,
  }) async {
    return (error: null, memoryEnabled: memoryEnabled);
  }
}

final class _VoiceSettingsRepositoryStub extends VoiceSettingsRepository {
  _VoiceSettingsRepositoryStub() : super(VoiceSettingsApi(Dio()));

  @override
  Future<({NetworkError? error, VoiceSettingsModel? settings})>
  loadSettings() async {
    return (
      error: null,
      settings: const VoiceSettingsModel(
        selectedVoice: 'Ngọc Linh',
        defaultVoice: 'Mỹ Duyên',
        voices: [
          VoiceOption(
            id: 'Ngọc Linh',
            name: 'Ngọc Linh',
            description: 'nữ, giọng tươi sáng',
          ),
        ],
      ),
    );
  }

  @override
  Future<({NetworkError? error, VoiceSettingsModel? settings})> saveSettings({
    required String selectedVoice,
  }) async {
    return (
      error: null,
      settings: VoiceSettingsModel(
        selectedVoice: selectedVoice,
        defaultVoice: 'Mỹ Duyên',
        voices: const [
          VoiceOption(
            id: 'Ngọc Linh',
            name: 'Ngọc Linh',
            description: 'nữ, giọng tươi sáng',
          ),
        ],
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

List<MemoryItem> _memoryItems(int count) {
  return List.generate(
    count,
    (index) => MemoryItem(
      id: 'memory-$index',
      memory: 'Preference $index',
      category: MemoryCategory.preferences,
      createdAt: '2026-06-25T04:08:26+00:00',
      updatedAt: '2026-06-25T05:40:29+00:00',
    ),
  );
}
