import 'package:equatable/equatable.dart';

final class VoiceOption extends Equatable {
  const VoiceOption({
    required this.id,
    required this.name,
    required this.description,
  });

  final String id;
  final String name;
  final String description;

  factory VoiceOption.fromJson(Map<String, dynamic> json) {
    return VoiceOption(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String? ?? '',
    );
  }

  @override
  List<Object?> get props => [id, name, description];
}

final class VoiceSettingsModel extends Equatable {
  const VoiceSettingsModel({
    required this.selectedVoice,
    required this.defaultVoice,
    required this.voices,
  });

  final String selectedVoice;
  final String defaultVoice;
  final List<VoiceOption> voices;

  factory VoiceSettingsModel.fromJson(Map<String, dynamic> json) {
    final voicesJson = json['voices'];
    final voices = voicesJson is List
        ? voicesJson
              .whereType<Map<String, dynamic>>()
              .map(VoiceOption.fromJson)
              .toList(growable: false)
        : const <VoiceOption>[];

    return VoiceSettingsModel(
      selectedVoice: json['selected_voice'] as String? ?? '',
      defaultVoice: json['default_voice'] as String? ?? '',
      voices: voices,
    );
  }

  @override
  List<Object?> get props => [selectedVoice, defaultVoice, voices];
}
