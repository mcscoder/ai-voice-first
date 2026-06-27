import 'dart:typed_data';

import 'package:ai_voice_first/core/di/get_it.dart';
import 'package:ai_voice_first/core/error.dart';
import 'package:ai_voice_first/features/onboarding/onboarding.dart';
import 'package:ai_voice_first/features/voice_settings/voice_settings.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';

void main() {
  setUp(() async {
    await getIt.reset();
  });

  tearDown(() async {
    await getIt.reset();
  });

  testWidgets('voice step saves before advancing', (tester) async {
    final repository = _SetupVoiceSettingsRepositoryStub();
    getIt.registerFactory<VoiceSettingsCubit>(
      () => VoiceSettingsCubit(
        repository,
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {},
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      ),
    );

    await tester.pumpWidget(
      BlocProvider(
        create: (_) => SetupCubit(),
        child: const MaterialApp(home: SetupFlow()),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();

    expect(find.text('Choose your\nAI voice'), findsOneWidget);

    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();

    expect(repository.savedVoiceIds, ['Ngọc Linh']);
    expect(find.text('What should we call you?'), findsOneWidget);
  });

  testWidgets('voice step stays put when save fails', (tester) async {
    final repository = _SetupVoiceSettingsRepositoryStub(
      saveErrorMessage: 'The voice service is unavailable right now.',
    );
    getIt.registerFactory<VoiceSettingsCubit>(
      () => VoiceSettingsCubit(
        repository,
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {},
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      ),
    );

    await tester.pumpWidget(
      BlocProvider(
        create: (_) => SetupCubit(),
        child: const MaterialApp(home: SetupFlow()),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();

    expect(repository.savedVoiceIds, ['Ngọc Linh']);
    expect(find.text('Choose your\nAI voice'), findsOneWidget);
    expect(
      find.text('The voice service is unavailable right now.'),
      findsOneWidget,
    );
  });
}

final class _SetupVoiceSettingsRepositoryStub extends VoiceSettingsRepository {
  _SetupVoiceSettingsRepositoryStub({this.saveErrorMessage})
    : super(VoiceSettingsApi(Dio()));

  final String? saveErrorMessage;
  final List<String> savedVoiceIds = [];

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
    savedVoiceIds.add(selectedVoice);
    if (saveErrorMessage != null) {
      return (
        error: InternalServerError(exception: Exception(saveErrorMessage)),
        settings: null,
      );
    }
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
