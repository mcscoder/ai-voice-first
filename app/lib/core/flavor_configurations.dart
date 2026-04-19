import 'package:flutter_dotenv/flutter_dotenv.dart';

enum ConfigurationProfile {
  development(name: 'development'),
  staging(name: 'staging'),
  production(name: 'production');

  final int connectTimeout = _defaultConnectTimeout;
  final int receiveTimeout = _defaultReceiveTimeout;
  final int sendTimeout = _defaultSendTimeout;
  final String name;

  // Flavor things...

  const ConfigurationProfile({required this.name});

  static const _defaultConnectTimeout = 30000;
  static const _defaultReceiveTimeout = 30000;
  static const _defaultSendTimeout = 30000;

  static ConfigurationProfile _current = ConfigurationProfile.development;

  static ConfigurationProfile get current {
    return _current;
  }

  static set current(ConfigurationProfile flavor) {
    _current = flavor;
  }

  static String get baseUrl {
    final url = dotenv.maybeGet('API_BASE_URL')?.trim() ?? '';
    if (url.isEmpty) {
      throw StateError('API_BASE_URL is missing from .env');
    }
    return url;
  }
}
