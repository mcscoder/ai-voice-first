// GENERATED CODE - DO NOT MODIFY BY HAND
// dart format width=80

// **************************************************************************
// InjectableConfigGenerator
// **************************************************************************

// ignore_for_file: type=lint
// coverage:ignore-file

// ignore_for_file: no_leading_underscores_for_library_prefixes
import 'package:dio/dio.dart' as _i361;
import 'package:get_it/get_it.dart' as _i174;
import 'package:injectable/injectable.dart' as _i526;

import '../../features/auth/data/auth_api.dart' as _i936;
import '../../features/auth/data/auth_repository.dart' as _i726;
import '../../features/auth/presentation/auth_cubit.dart' as _i731;
import '../../features/voice/data/audio_recorder_service.dart' as _i495;
import '../../features/voice/data/transcription_api.dart' as _i763;
import '../../features/voice/presentation/voice_capture_cubit.dart' as _i221;
import '../analytics/posthog_analytics_provider.dart' as _i382;
import '../app_bloc_observer.dart' as _i744;
import '../auth/secure_storage_service.dart' as _i921;
import '../auth/session_manager.dart' as _i287;
import '../auth/token_manager.dart' as _i428;
import '../cache/cache_manager.dart' as _i326;
import '../connectivity/connectivity_cubit.dart' as _i690;
import '../connectivity/connectivity_service.dart' as _i528;
import '../connectivity/offline_queue_service.dart' as _i1052;
import '../lifecycle/app_lifecycle_observer.dart' as _i947;
import '../logger/impl/debug_logger.dart' as _i803;
import '../logger/impl/production_logger.dart' as _i67;
import '../logger/logger.dart' as _i512;
import '../network/remote.dart' as _i612;
import '../permissions/permission_cubit.dart' as _i835;
import '../permissions/permission_handler_impl.dart' as _i440;
import '../permissions/permission_service.dart' as _i271;
import '../router/deep_link_handler.dart' as _i605;
import 'get_it.dart' as _i241;

const String _production = 'production';
const String _development = 'development';

extension GetItInjectableX on _i174.GetIt {
  // initializes the registration of main-scope dependencies inside of GetIt
  _i174.GetIt init({
    String? environment,
    _i526.EnvironmentFilter? environmentFilter,
  }) {
    final gh = _i526.GetItHelper(this, environment, environmentFilter);
    final registerModule = _$RegisterModule();
    gh.lazySingleton<_i382.PostHogAnalyticsProvider>(
      () => _i382.PostHogAnalyticsProvider(),
    );
    gh.lazySingleton<_i612.DioClient>(() => registerModule.dioClient);
    gh.lazySingleton<_i528.ConnectivityService>(
      () => registerModule.connectivityService,
    );
    gh.lazySingleton<_i326.CacheManager>(() => registerModule.cacheManager);
    gh.lazySingleton<_i921.SecureStorageService>(
      () => registerModule.secureStorageService,
    );
    gh.lazySingleton<_i287.SessionManager>(() => registerModule.sessionManager);
    gh.lazySingleton<_i605.DeepLinkHandler>(
      () => registerModule.deepLinkHandler,
    );
    gh.lazySingleton<_i947.AppLifecycleObserver>(
      () => _i947.AppLifecycleObserver(),
    );
    gh.lazySingleton<_i495.AudioRecorderService>(
      () => _i495.AudioRecorderService(),
    );
    gh.factory<_i361.Dio>(
      () => registerModule.dioAuth,
      instanceName: 'AuthDio',
    );
    gh.lazySingleton<_i428.TokenManager>(
      () => _i428.TokenManager(gh<_i921.SecureStorageService>()),
    );
    gh.factory<_i361.Dio>(
      () => registerModule.dioNonAuth,
      instanceName: 'NonAuthDio',
    );
    gh.lazySingleton<_i271.PermissionService>(
      () => _i440.PermissionHandlerImpl(),
    );
    gh.lazySingleton<_i690.ConnectivityCubit>(
      () => _i690.ConnectivityCubit(gh<_i528.ConnectivityService>()),
    );
    gh.lazySingleton<_i763.TranscriptionApi>(
      () => _i763.TranscriptionApi(gh<_i361.Dio>(instanceName: 'AuthDio')),
    );
    gh.singleton<_i512.Logger>(
      () => _i67.ProductionLogger(),
      registerFor: {_production},
    );
    gh.lazySingleton<_i936.AuthApi>(
      () => _i936.AuthApi(
        gh<_i361.Dio>(instanceName: 'NonAuthDio'),
        gh<_i361.Dio>(instanceName: 'AuthDio'),
      ),
    );
    gh.singleton<_i512.Logger>(
      () => _i803.DebugLogger(),
      registerFor: {_development},
    );
    gh.lazySingleton<_i726.AuthRepository>(
      () => _i726.AuthRepository(gh<_i936.AuthApi>(), gh<_i428.TokenManager>()),
    );
    gh.factory<_i835.PermissionCubit>(
      () => _i835.PermissionCubit(gh<_i271.PermissionService>()),
    );
    gh.lazySingleton<_i1052.OfflineQueueService>(
      () => _i1052.OfflineQueueService(
        gh<_i428.TokenManager>(),
        gh<_i690.ConnectivityCubit>(),
      ),
    );
    gh.factory<_i221.VoiceCaptureCubit>(
      () => registerModule.voiceCaptureCubit(
        gh<_i271.PermissionService>(),
        gh<_i495.AudioRecorderService>(),
        gh<_i763.TranscriptionApi>(),
      ),
    );
    gh.lazySingleton<_i744.AppBlocObserver>(
      () => _i744.AppBlocObserver(logger: gh<_i512.Logger>()),
    );
    gh.lazySingleton<_i731.AuthCubit>(
      () => _i731.AuthCubit(gh<_i726.AuthRepository>()),
    );
    return this;
  }
}

class _$RegisterModule extends _i241.RegisterModule {}
