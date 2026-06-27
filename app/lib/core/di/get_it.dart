import 'package:dio/dio.dart';
import 'package:get_it/get_it.dart';
import 'package:injectable/injectable.dart';

import '../analytics/analytics_service.dart';
import '../analytics/composite_analytics_provider.dart';
import '../analytics/posthog_analytics_provider.dart';
import '../auth/secure_storage_service.dart';
import '../auth/session_manager.dart';
import '../cache/cache_manager.dart';
import '../connectivity/connectivity_service.dart';
import '../flavor_configurations.dart';
import '../network/remote.dart';
import '../permissions/permission_service.dart';
import '../router/deep_link_handler.dart';
import '../../features/memory/data/memory_api.dart';
import '../../features/memory/data/memory_repository.dart';
import '../../features/memory/presentation/memory_cubit.dart';
import '../../features/profile/data/personalization_api.dart';
import '../../features/profile/data/personalization_repository.dart';
import '../../features/voice/data/audio_recorder_service.dart';
import '../../features/voice_settings/data/voice_settings_api.dart';
import '../../features/voice_settings/data/voice_settings_repository.dart';
import '../../features/voice/data/transcription_api.dart';
import '../../features/voice/presentation/voice_capture_cubit.dart';
import '../../features/voice_settings/presentation/voice_settings_cubit.dart';
import 'get_it.config.dart';

final getIt = GetIt.instance;

@InjectableInit(preferRelativeImports: true)
void configureDependencies() {
  getIt.init(environment: ConfigurationProfile.current.name);

  if (!getIt.isRegistered<MemoryApi>()) {
    getIt.registerLazySingleton<MemoryApi>(
      () => MemoryApi(getIt<Dio>(instanceName: 'AuthDio')),
    );
  }
  if (!getIt.isRegistered<MemoryRepository>()) {
    getIt.registerLazySingleton<MemoryRepository>(
      () => MemoryRepository(getIt<MemoryApi>()),
    );
  }
  if (!getIt.isRegistered<MemoryCubit>()) {
    getIt.registerFactory<MemoryCubit>(
      () => MemoryCubit(getIt<MemoryRepository>()),
    );
  }
  if (!getIt.isRegistered<VoiceSettingsApi>()) {
    getIt.registerLazySingleton<VoiceSettingsApi>(
      () => VoiceSettingsApi(getIt<Dio>(instanceName: 'AuthDio')),
    );
  }
  if (!getIt.isRegistered<PersonalizationApi>()) {
    getIt.registerLazySingleton<PersonalizationApi>(
      () => PersonalizationApi(getIt<Dio>(instanceName: 'AuthDio')),
    );
  }
  if (!getIt.isRegistered<PersonalizationRepository>()) {
    getIt.registerLazySingleton<PersonalizationRepository>(
      () => PersonalizationRepository(getIt<PersonalizationApi>()),
    );
  }
  if (!getIt.isRegistered<VoiceSettingsRepository>()) {
    getIt.registerLazySingleton<VoiceSettingsRepository>(
      () => VoiceSettingsRepository(getIt<VoiceSettingsApi>()),
    );
  }
  if (!getIt.isRegistered<VoiceSettingsCubit>()) {
    getIt.registerFactory<VoiceSettingsCubit>(
      () => VoiceSettingsCubit(getIt<VoiceSettingsRepository>()),
    );
  }
}

const development = Environment('development');
const staging = Environment('staging');
const production = Environment('production');

@module
abstract class RegisterModule {
  /// [DioClient] wired with connectivity, cache, and token manager.
  ///
  /// Must be lazySingleton (not singleton) so it is instantiated on first
  /// access — after all other deps are already registered by GetIt.init().
  @lazySingleton
  DioClient get dioClient => DioClient(
    connectivityService: getIt(),
    cacheManager: getIt(),
    tokenManager: getIt(),
  );

  @authDio
  Dio get dioAuth => dioClient.authDio;

  @nonAuthDio
  Dio get dioNonAuth => dioClient.dio;

  /// Override auto-registration to use no-arg constructor (default Connectivity).
  @lazySingleton
  ConnectivityService get connectivityService => ConnectivityService();

  /// Override auto-registration to use no-arg constructor (default MemoryCache + DiskCache).
  @lazySingleton
  CacheManager get cacheManager => CacheManager();

  /// Override auto-registration to use no-arg constructor (default FlutterSecureStorage).
  @lazySingleton
  SecureStorageService get secureStorageService => SecureStorageService();

  /// Override auto-registration to use no-arg constructor (default 30-min timeout).
  @lazySingleton
  SessionManager get sessionManager => SessionManager();

  /// Override auto-registration to use no-arg constructor (default hosts/schemes).
  @lazySingleton
  DeepLinkHandler get deepLinkHandler => DeepLinkHandler();

  VoiceCaptureCubit voiceCaptureCubit(
    PermissionService permissionService,
    AudioRecorderService audioRecorderService,
    TranscriptionApi transcriptionApi,
  ) => VoiceCaptureCubit(
    permissionService,
    audioRecorderService,
    transcriptionApi,
  );
}

/// Registers [CompositeAnalyticsProvider] as the [AnalyticsService] singleton.
///
/// Must be called after [configureDependencies] so analytics providers are
/// already registered as lazySingletons.
void registerCompositeAnalytics() {
  getIt.registerLazySingleton<AnalyticsService>(
    () => CompositeAnalyticsProvider([getIt<PostHogAnalyticsProvider>()]),
  );
}
