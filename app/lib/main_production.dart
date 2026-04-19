import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

import 'app.dart';
import 'core/flavor_configurations.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load();
  ConfigurationProfile.current = ConfigurationProfile.production;
  await initializeFlutterApp();
}
