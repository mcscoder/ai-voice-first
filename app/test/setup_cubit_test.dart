import 'dart:async';

import 'package:ai_voice_first/core/error.dart' as app_error;
import 'package:ai_voice_first/features/onboarding/onboarding.dart';
import 'package:ai_voice_first/features/profile/data/personalization_api.dart';
import 'package:ai_voice_first/features/profile/data/personalization_models.dart';
import 'package:ai_voice_first/features/profile/data/personalization_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('keeps local setup values when initial sync fails', () async {
    final cubit = SetupCubit(
      repository: _PersonalizationRepositoryStub(
        loadError: app_error.Timeout(exception: TimeoutException('timed out')),
      ),
    );
    cubit.setMemoryEnabled(false);
    cubit.complete();

    await cubit.syncFromBackend();

    expect(cubit.state.isComplete, isTrue);
    expect(cubit.state.memoryEnabled, isFalse);
    expect(cubit.state.syncStatus, SetupSyncStatus.failed);
    expect(cubit.state.errorMessage, 'The request timed out. Try again.');
    await cubit.close();
  });

  test('syncs backend personalization into setup state', () async {
    final cubit = SetupCubit(
      repository: _PersonalizationRepositoryStub(
        loadedPersonalization: const PersonalizationModel(
          nickname: 'Alex',
          speakingStyle: SpeakingStyle.professional,
          setupCompleted: true,
        ),
      ),
    );

    await cubit.syncFromBackend();

    expect(cubit.state.nickname, 'Alex');
    expect(cubit.state.speakingStyle, SpeakingStyle.professional);
    expect(cubit.state.isComplete, isTrue);
    expect(cubit.state.syncStatus, SetupSyncStatus.synced);
    await cubit.close();
  });

  test(
    'updates setup state only after personalization save succeeds',
    () async {
      final repository = _PersonalizationRepositoryStub(
        updateError: const app_error.InternalServerError(
          exception: FormatException(),
        ),
      );
      final cubit = SetupCubit(repository: repository);

      final failed = await cubit.savePersonalization(
        nickname: 'Alex',
        speakingStyle: SpeakingStyle.casual,
      );

      expect(failed, isFalse);
      expect(cubit.state.nickname, '');
      expect(cubit.state.speakingStyle, SpeakingStyle.shortAnswers);

      repository.updatedPersonalization = const PersonalizationModel(
        nickname: 'Alex',
        speakingStyle: SpeakingStyle.casual,
        setupCompleted: false,
      );
      repository.updateError = null;

      final saved = await cubit.savePersonalization(
        nickname: 'Alex',
        speakingStyle: SpeakingStyle.casual,
      );

      expect(saved, isTrue);
      expect(cubit.state.nickname, 'Alex');
      expect(cubit.state.speakingStyle, SpeakingStyle.casual);
      await cubit.close();
    },
  );
}

final class _PersonalizationRepositoryStub extends PersonalizationRepository {
  _PersonalizationRepositoryStub({
    this.loadedPersonalization,
    this.updatedPersonalization,
    this.setupPersonalization,
    this.loadError,
    this.updateError,
    this.setupError,
  }) : super(PersonalizationApi(Dio()));

  PersonalizationModel? loadedPersonalization;
  PersonalizationModel? updatedPersonalization;
  PersonalizationModel? setupPersonalization;
  app_error.NetworkError? loadError;
  app_error.NetworkError? updateError;
  app_error.NetworkError? setupError;

  @override
  Future<
    ({app_error.NetworkError? error, PersonalizationModel? personalization})
  >
  loadPersonalization() async {
    return (error: loadError, personalization: loadedPersonalization);
  }

  @override
  Future<
    ({app_error.NetworkError? error, PersonalizationModel? personalization})
  >
  updatePersonalization({
    required String nickname,
    required String speakingStyle,
  }) async {
    return (error: updateError, personalization: updatedPersonalization);
  }

  @override
  Future<
    ({app_error.NetworkError? error, PersonalizationModel? personalization})
  >
  updateSetupCompletion({required bool setupCompleted}) async {
    return (error: setupError, personalization: setupPersonalization);
  }
}
