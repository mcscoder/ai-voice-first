import 'package:ai_voice_first/features/home/home_screen.dart';
import 'package:ai_voice_first/shared/i18n/generated/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('home shell renders', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: HomeScreen(),
      ),
    );

    expect(find.text('AI Voice First'), findsOneWidget);
    expect(find.text('Voice-first product shell'), findsOneWidget);
  });
}
