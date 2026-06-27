import 'dart:typed_data';

import 'package:ai_voice_first/core/error.dart' as app_error;
import 'package:ai_voice_first/features/voice_settings/voice_settings.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('VoiceSettingsCubit', () {
    test('loads voice settings successfully', () async {
      final cubit = VoiceSettingsCubit(
        _VoiceSettingsRepositoryStub(
          loadResult: (
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
          ),
        ),
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {},
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      );

      await cubit.load();

      expect(cubit.state.status, VoiceSettingsStatus.ready);
      expect(cubit.state.selectedVoiceId, 'Ngọc Linh');
      expect(cubit.state.savedVoiceId, 'Ngọc Linh');
      expect(cubit.state.voices.single.name, 'Ngọc Linh');
      await cubit.close();
    });

    test('keeps failure state when load fails', () async {
      final cubit = VoiceSettingsCubit(
        _VoiceSettingsRepositoryStub(
          loadResult: (
            error: app_error.Timeout(exception: Exception('timeout')),
            settings: null,
          ),
        ),
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {},
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      );

      await cubit.load();

      expect(cubit.state.status, VoiceSettingsStatus.failure);
      expect(cubit.state.errorMessage, 'The request timed out. Try again.');
      await cubit.close();
    });

    test('saves only when explicitly requested', () async {
      final repository = _VoiceSettingsRepositoryStub(
        loadResult: (
          error: null,
          settings: const VoiceSettingsModel(
            selectedVoice: 'Mỹ Duyên',
            defaultVoice: 'Mỹ Duyên',
            voices: [
              VoiceOption(
                id: 'Mỹ Duyên',
                name: 'Mỹ Duyên',
                description: 'nữ, giọng nhẹ nhàng',
              ),
              VoiceOption(
                id: 'Ngọc Linh',
                name: 'Ngọc Linh',
                description: 'nữ, giọng tươi sáng',
              ),
            ],
          ),
        ),
        saveResult: (
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
        ),
      );
      final cubit = VoiceSettingsCubit(
        repository,
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {},
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      );

      await cubit.load();
      cubit.selectVoice('Ngọc Linh');

      expect(repository.savedVoiceIds, isEmpty);

      final saved = await cubit.save();

      expect(saved, isTrue);
      expect(repository.savedVoiceIds, ['Ngọc Linh']);
      expect(cubit.state.savedVoiceId, 'Ngọc Linh');
      await cubit.close();
    });

    test('keeps selection on save failure', () async {
      final cubit = VoiceSettingsCubit(
        _VoiceSettingsRepositoryStub(
          loadResult: (
            error: null,
            settings: const VoiceSettingsModel(
              selectedVoice: 'Mỹ Duyên',
              defaultVoice: 'Mỹ Duyên',
              voices: [
                VoiceOption(
                  id: 'Mỹ Duyên',
                  name: 'Mỹ Duyên',
                  description: 'nữ, giọng nhẹ nhàng',
                ),
                VoiceOption(
                  id: 'Ngọc Linh',
                  name: 'Ngọc Linh',
                  description: 'nữ, giọng tươi sáng',
                ),
              ],
            ),
          ),
          saveResult: (
            error: app_error.InternalServerError(
              exception: Exception('server'),
            ),
            settings: null,
          ),
        ),
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {},
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      );

      await cubit.load();
      cubit.selectVoice('Ngọc Linh');
      final saved = await cubit.save();

      expect(saved, isFalse);
      expect(cubit.state.status, VoiceSettingsStatus.ready);
      expect(cubit.state.selectedVoiceId, 'Ngọc Linh');
      expect(cubit.state.savedVoiceId, 'Mỹ Duyên');
      expect(
        cubit.state.errorMessage,
        'The voice service is unavailable right now.',
      );
      await cubit.close();
    });

    test('stops the previous preview before starting another', () async {
      final played = <String>[];
      final stopped = <int>[];
      final loadedVoiceIds = <String>[];
      final repository = _VoiceSettingsRepositoryStub(
        loadResult: (
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
              VoiceOption(
                id: 'Mỹ Duyên',
                name: 'Mỹ Duyên',
                description: 'nữ, giọng nhẹ nhàng',
              ),
            ],
          ),
        ),
      );
      final cubit = VoiceSettingsCubit(
        repository,
        playVoicePreview: (audioBytes) async {
          played.add(audioBytes.first.toString());
        },
        stopVoicePreview: () async {
          stopped.add(stopped.length);
        },
        loadVoicePreviewAsset: (voiceId) async {
          loadedVoiceIds.add(voiceId);
          return Uint8List.fromList(
            voiceId == 'Ngọc Linh' ? const [1] : const [2],
          );
        },
      );

      await cubit.load();
      await cubit.preview('Ngọc Linh');
      await cubit.preview('Mỹ Duyên');

      expect(loadedVoiceIds, ['Ngọc Linh', 'Mỹ Duyên']);
      expect(played, ['1', '2']);
      expect(stopped.length, 2);
      expect(cubit.state.previewingVoiceId, isNull);
      await cubit.close();
    });

    test('stops preview playback on close', () async {
      var stopCalls = 0;
      final cubit = VoiceSettingsCubit(
        _VoiceSettingsRepositoryStub(
          loadResult: (
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
          ),
        ),
        playVoicePreview: (_) async {},
        stopVoicePreview: () async {
          stopCalls += 1;
        },
        loadVoicePreviewAsset: (_) async => Uint8List.fromList(const [1]),
      );

      await cubit.load();
      await cubit.close();

      expect(stopCalls, 1);
    });
  });
}

final class _VoiceSettingsRepositoryStub extends VoiceSettingsRepository {
  _VoiceSettingsRepositoryStub({this.loadResult, this.saveResult})
    : super(VoiceSettingsApi(Dio()));

  final ({app_error.NetworkError? error, VoiceSettingsModel? settings})?
  loadResult;
  final ({app_error.NetworkError? error, VoiceSettingsModel? settings})?
  saveResult;
  final List<String> savedVoiceIds = [];

  @override
  Future<({app_error.NetworkError? error, VoiceSettingsModel? settings})>
  loadSettings() async {
    return loadResult ?? (error: null, settings: null);
  }

  @override
  Future<({app_error.NetworkError? error, VoiceSettingsModel? settings})>
  saveSettings({required String selectedVoice}) async {
    savedVoiceIds.add(selectedVoice);
    return saveResult ?? (error: null, settings: null);
  }
}
