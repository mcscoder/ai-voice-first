import 'dart:ui';

import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:hydrated_bloc/hydrated_bloc.dart';
import 'package:path_provider/path_provider.dart';

import 'core/analytics/analytics_service.dart';
import 'core/app_bloc_observer.dart';
import 'core/cache/cache_manager.dart';
import 'core/connectivity/connectivity_cubit.dart';
import 'core/connectivity/connectivity_service.dart';
import 'core/connectivity/offline_queue_service.dart';
import 'core/di/get_it.dart';
import 'core/logger/logger.dart';
import 'core/router/router.dart';
import 'core/theme/theme.dart';
import 'features/auth/auth.dart';
import 'features/onboarding/onboarding.dart';
import 'shared/i18n/generated/app_localizations.dart';

Future<void> initializeFlutterApp() async {
  // 1. Flutter engine must be ready before any platform channel calls.
  WidgetsFlutterBinding.ensureInitialized();

  // 2. Hive — required by DiskCache and OfflineQueueService.
  await Hive.initFlutter();

  // 3. HydratedBloc persistent storage.
  HydratedBloc.storage = await HydratedStorage.build(
    storageDirectory: HydratedStorageDirectory(
      (await getApplicationSupportDirectory()).path,
    ),
  );

  // 4. Dependency injection — all @LazySingleton/@Injectable classes registered.
  configureDependencies();

  // 5. Register CompositeAnalyticsProvider as AnalyticsService after DI is ready.
  registerCompositeAnalytics();

  // 6. Initialise CacheManager disk layer (opens Hive box).
  await getIt<CacheManager>().init();

  // 7. Start connectivity monitoring before any network calls.
  await getIt<ConnectivityService>().init();
  getIt<ConnectivityCubit>().startMonitoring();

  // 8. Initialise OfflineQueueService (opens Hive box, subscribes connectivity).
  await getIt<OfflineQueueService>().initialize();

  // 9. Logger + BLoC observer.
  final logger = getIt<Logger>();
  final observer = getIt<AppBlocObserver>();

  // 10. Wire error handlers to the local logger.
  FlutterError.onError = (FlutterErrorDetails details) {
    logger(details.exceptionAsString(), stackTrace: details.stack);
    FlutterError.presentError(details);
  };
  PlatformDispatcher.instance.onError = (error, stack) {
    logger(error.toString(), error: error, stackTrace: stack);
    return true;
  };

  // 11. Equatable + BLoC observer.
  EquatableConfig.stringify = true;
  Bloc.observer = observer;

  // 12. Analytics.
  await getIt<AnalyticsService>().initialize();

  runApp(const App());
}

final class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => getIt<AuthCubit>()),
        BlocProvider(create: (_) => SetupCubit()),
        BlocProvider(
          // ConnectivityCubit is a lazySingleton — share the same instance.
          create: (_) => getIt<ConnectivityCubit>(),
        ),
      ],
      child: const AppView(),
    );
  }
}

final class AppView extends StatefulWidget {
  const AppView({super.key});

  @override
  State<AppView> createState() => AppViewState();

  static AppViewState of(BuildContext context) =>
      context.findAncestorStateOfType<AppViewState>()!;
}

final class AppViewState extends State<AppView> {
  ThemeMode _themeMode = ThemeMode.dark;

  void setThemeMode(ThemeMode mode) {
    if (!mounted) {
      return;
    }
    setState(() {
      _themeMode = mode;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      routerConfig: AppRouter.routerConfig,
      themeMode: _themeMode,
    );
  }
}
