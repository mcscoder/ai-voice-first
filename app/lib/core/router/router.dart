import 'package:go_router/go_router.dart';

import '../error_screen.dart';
import '../../features/home/home.dart';

abstract class AppRoutes {
  AppRoutes._();
  static const home = '/';
}

abstract class AppRouter {
  AppRouter._();

  static final routerConfig = GoRouter(
    debugLogDiagnostics: true,
    initialLocation: AppRoutes.home,
    routes: [
      GoRoute(path: AppRoutes.home, builder: (_, _) => const HomeScreen()),
    ],
    errorBuilder: (_, _) => const ErrorScreen(),
  );
}
