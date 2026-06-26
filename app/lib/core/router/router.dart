import 'package:go_router/go_router.dart';

import '../error_screen.dart';
import '../../features/auth/auth.dart';

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
      GoRoute(path: AppRoutes.home, builder: (_, _) => const AuthGate()),
    ],
    errorBuilder: (_, _) => const ErrorScreen(),
  );
}
