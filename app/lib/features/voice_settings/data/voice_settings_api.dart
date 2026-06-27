import '../../../core/error.dart';
import '../../../core/network/api.dart';
import '../../../core/network/api_path.dart';
import '../../../core/network/dio.dart';
import 'voice_settings_models.dart';

final class VoiceSettingsApi extends Api {
  VoiceSettingsApi(@authDio super.dio);

  Future<({NetworkError? error, VoiceSettingsModel? settings})>
  loadSettings() async {
    final result = await withTimeoutRequest(() async {
      final response = await dio.get<Map<String, dynamic>>(
        ApiPath.voiceSettings,
      );
      return VoiceSettingsModel.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, settings: null),
      (settings) => (error: null, settings: settings),
    );
  }

  Future<({NetworkError? error, VoiceSettingsModel? settings})> saveSettings({
    required String selectedVoice,
  }) async {
    final result = await withTimeoutRequest(() async {
      final response = await dio.put<Map<String, dynamic>>(
        ApiPath.voiceSettings,
        data: {'selected_voice': selectedVoice},
      );
      return VoiceSettingsModel.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, settings: null),
      (settings) => (error: null, settings: settings),
    );
  }
}
