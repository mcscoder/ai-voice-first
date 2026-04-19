final class VoiceLanguage {
  const VoiceLanguage({required this.code, required this.label});

  final String code;
  final String label;

  static const english = VoiceLanguage(code: 'en', label: 'English');
  static const vietnamese = VoiceLanguage(code: 'vi', label: 'Vietnamese');

  static const values = <VoiceLanguage>[english, vietnamese];

  static VoiceLanguage fromCode(String? code) {
    return values.where((language) => language.code == code).firstOrNull ??
        english;
  }
}
