final class TranscriptionResponse {
  const TranscriptionResponse({
    required this.text,
    required this.language,
    required this.model,
  });

  final String text;
  final String? language;
  final String? model;

  factory TranscriptionResponse.fromJson(Map<String, dynamic> json) {
    return TranscriptionResponse(
      text: (json['text'] as String? ?? '').trim(),
      language: json['language'] as String?,
      model: json['model'] as String?,
    );
  }
}
