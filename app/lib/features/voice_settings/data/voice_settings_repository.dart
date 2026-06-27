import '../../../core/error.dart';
import 'voice_settings_api.dart';
import 'voice_settings_models.dart';

class VoiceSettingsRepository {
  VoiceSettingsRepository(this._api);

  final VoiceSettingsApi _api;

  Future<({NetworkError? error, VoiceSettingsModel? settings})> loadSettings() {
    return _api.loadSettings();
  }

  Future<({NetworkError? error, VoiceSettingsModel? settings})> saveSettings({
    required String selectedVoice,
  }) {
    return _api.saveSettings(selectedVoice: selectedVoice);
  }
}
