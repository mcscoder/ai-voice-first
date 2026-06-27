import 'dart:typed_data';

import 'package:ai_voice_first/core/di/get_it.dart';
import 'package:ai_voice_first/core/error.dart';
import 'package:ai_voice_first/features/memory/memory.dart';
import 'package:ai_voice_first/features/onboarding/onboarding.dart';
import 'package:ai_voice_first/features/profile/data/personalization_api.dart';
import 'package:ai_voice_first/features/profile/data/personalization_models.dart';
import 'package:ai_voice_first/features/profile/data/personalization_repository.dart';
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
    final personalizationRepository = _PersonalizationRepositoryStub();
    getIt.registerFactory<VoiceSettingsCubit>(
      () => VoiceSettingsCubit(
        repository,
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {},
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      ),
    );

    await _pumpSetupFlow(
      tester,
      setupCubit: SetupCubit(repository: personalizationRepository),
      memoryCubit: MemoryCubit(_MemoryRepositoryStub()),
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
    final personalizationRepository = _PersonalizationRepositoryStub();
    getIt.registerFactory<VoiceSettingsCubit>(
      () => VoiceSettingsCubit(
        repository,
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {},
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      ),
    );

    await _pumpSetupFlow(
      tester,
      setupCubit: SetupCubit(repository: personalizationRepository),
      memoryCubit: MemoryCubit(_MemoryRepositoryStub()),
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

  testWidgets('personalization step saves to backend before advancing', (
    tester,
  ) async {
    final repository = _SetupVoiceSettingsRepositoryStub();
    final personalizationRepository = _PersonalizationRepositoryStub(
      updatedPersonalization: const PersonalizationModel(
        nickname: 'Alex',
        speakingStyle: SpeakingStyle.casual,
        setupCompleted: false,
      ),
    );
    getIt.registerFactory<VoiceSettingsCubit>(
      () => VoiceSettingsCubit(
        repository,
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {},
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      ),
    );

    final setupCubit = SetupCubit(repository: personalizationRepository);
    final memoryCubit = MemoryCubit(_MemoryRepositoryStub());
    await _pumpSetupFlow(
      tester,
      setupCubit: setupCubit,
      memoryCubit: memoryCubit,
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('setup_nickname_field')),
      'Alex',
    );
    await tester.tap(find.text('Casual'));
    await tester.pump();
    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();

    expect(personalizationRepository.savedNicknames, ['Alex']);
    expect(personalizationRepository.savedSpeakingStyles, ['casual']);
    expect(find.text('Memory'), findsOneWidget);
    expect(setupCubit.state.nickname, 'Alex');
    expect(setupCubit.state.speakingStyle, SpeakingStyle.casual);

    await setupCubit.close();
    await memoryCubit.close();
  });

  testWidgets(
    'finishing onboarding persists memory setting and setup completion',
    (tester) async {
      final repository = _SetupVoiceSettingsRepositoryStub();
      final personalizationRepository = _PersonalizationRepositoryStub(
        updatedPersonalization: const PersonalizationModel(
          nickname: 'Alex',
          speakingStyle: SpeakingStyle.casual,
          setupCompleted: false,
        ),
        setupPersonalization: const PersonalizationModel(
          nickname: 'Alex',
          speakingStyle: SpeakingStyle.casual,
          setupCompleted: true,
        ),
      );
      getIt.registerFactory<VoiceSettingsCubit>(
        () => VoiceSettingsCubit(
          repository,
          playVoicePreview: (_) async {},
          stopVoicePreview: () async {},
          loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
        ),
      );

      final setupCubit = SetupCubit(repository: personalizationRepository);
      final memoryRepository = _MemoryRepositoryStub();
      final memoryCubit = MemoryCubit(memoryRepository);
      await _pumpSetupFlow(
        tester,
        setupCubit: setupCubit,
        memoryCubit: memoryCubit,
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Continue'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Continue'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('setup_nickname_field')),
        'Alex',
      );
      await tester.tap(find.text('Casual'));
      await tester.pump();
      await tester.tap(find.text('Continue'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Finish setup'));
      await tester.pumpAndSettle();

      expect(memoryRepository.updatedMemoryEnabled, [true]);
      expect(personalizationRepository.setupCompletions, [true]);
      expect(setupCubit.state.isComplete, isTrue);

      await setupCubit.close();
      await memoryCubit.close();
    },
  );
}

Future<void> _pumpSetupFlow(
  WidgetTester tester, {
  required SetupCubit setupCubit,
  required MemoryCubit memoryCubit,
}) async {
  await tester.pumpWidget(
    MultiBlocProvider(
      providers: [
        BlocProvider<SetupCubit>.value(value: setupCubit),
        BlocProvider<MemoryCubit>.value(value: memoryCubit),
      ],
      child: const MaterialApp(home: SetupFlow()),
    ),
  );
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

final class _PersonalizationRepositoryStub extends PersonalizationRepository {
  _PersonalizationRepositoryStub({
    this.loadedPersonalization,
    this.updatedPersonalization,
    this.setupPersonalization,
    this.updateError,
    this.setupError,
  }) : super(PersonalizationApi(Dio()));

  final PersonalizationModel? loadedPersonalization;
  PersonalizationModel? updatedPersonalization;
  final PersonalizationModel? setupPersonalization;
  final NetworkError? updateError;
  final NetworkError? setupError;
  final List<String> savedNicknames = [];
  final List<String> savedSpeakingStyles = [];
  final List<bool> setupCompletions = [];

  @override
  Future<({NetworkError? error, PersonalizationModel? personalization})>
  loadPersonalization() async {
    return (error: null, personalization: loadedPersonalization);
  }

  @override
  Future<({NetworkError? error, PersonalizationModel? personalization})>
  updatePersonalization({
    required String nickname,
    required String speakingStyle,
  }) async {
    savedNicknames.add(nickname);
    savedSpeakingStyles.add(speakingStyle);
    return (error: updateError, personalization: updatedPersonalization);
  }

  @override
  Future<({NetworkError? error, PersonalizationModel? personalization})>
  updateSetupCompletion({required bool setupCompleted}) async {
    setupCompletions.add(setupCompleted);
    return (error: setupError, personalization: setupPersonalization);
  }
}

final class _MemoryRepositoryStub extends MemoryRepository {
  _MemoryRepositoryStub() : super(MemoryApi(Dio()));

  final List<bool> updatedMemoryEnabled = [];

  @override
  Future<({NetworkError? error, MemoryCollection? collection})>
  loadMemories() async {
    return (
      error: null,
      collection: const MemoryCollection(memoryEnabled: true, memories: []),
    );
  }

  @override
  Future<({NetworkError? error, bool? memoryEnabled})> updateSettings({
    required bool memoryEnabled,
  }) async {
    updatedMemoryEnabled.add(memoryEnabled);
    return (error: null, memoryEnabled: memoryEnabled);
  }
}
