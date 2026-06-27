import '../../onboarding/presentation/speaking_style.dart';

final class PersonalizationModel {
  const PersonalizationModel({
    required this.nickname,
    required this.speakingStyle,
    required this.setupCompleted,
  });

  factory PersonalizationModel.fromJson(Map<String, dynamic> json) {
    return PersonalizationModel(
      nickname: json['nickname'] as String? ?? '',
      speakingStyle: speakingStyleFromName(json['speaking_style'] as String?),
      setupCompleted: json['setup_completed'] as bool? ?? false,
    );
  }

  final String nickname;
  final SpeakingStyle speakingStyle;
  final bool setupCompleted;
}
