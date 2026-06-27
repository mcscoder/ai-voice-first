enum SpeakingStyle { shortAnswers, detailedAnswers, casual, professional }

SpeakingStyle speakingStyleFromName(String? name) {
  return SpeakingStyle.values.firstWhere(
    (style) => style.name == name,
    orElse: () => SpeakingStyle.shortAnswers,
  );
}
