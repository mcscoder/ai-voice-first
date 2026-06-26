final class VoiceLanguage {
  const VoiceLanguage({required this.code, required this.label});

  final String code;
  final String label;

  static const vietnamese = VoiceLanguage(code: 'vi', label: 'Vietnamese');
}
