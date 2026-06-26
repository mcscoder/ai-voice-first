import 'package:equatable/equatable.dart';
import 'package:hydrated_bloc/hydrated_bloc.dart';

enum AssistantVoice { friendly, calm, professional, energetic }

enum SpeakingStyle { shortAnswers, detailedAnswers, casual, professional }

final class SetupState extends Equatable {
  const SetupState({
    this.isComplete = false,
    this.nickname = '',
    this.language = 'English',
    this.voice = AssistantVoice.friendly,
    this.speakingStyle = SpeakingStyle.shortAnswers,
    this.memoryEnabled = true,
  });

  final bool isComplete;
  final String nickname;
  final String language;
  final AssistantVoice voice;
  final SpeakingStyle speakingStyle;
  final bool memoryEnabled;

  SetupState copyWith({
    bool? isComplete,
    String? nickname,
    String? language,
    AssistantVoice? voice,
    SpeakingStyle? speakingStyle,
    bool? memoryEnabled,
  }) {
    return SetupState(
      isComplete: isComplete ?? this.isComplete,
      nickname: nickname ?? this.nickname,
      language: language ?? this.language,
      voice: voice ?? this.voice,
      speakingStyle: speakingStyle ?? this.speakingStyle,
      memoryEnabled: memoryEnabled ?? this.memoryEnabled,
    );
  }

  @override
  List<Object?> get props => [
    isComplete,
    nickname,
    language,
    voice,
    speakingStyle,
    memoryEnabled,
  ];
}

final class SetupCubit extends HydratedCubit<SetupState> {
  SetupCubit({Storage? storage})
    : super(const SetupState(), storage: _resolveStorage(storage));

  void selectVoice(AssistantVoice voice) {
    emit(state.copyWith(voice: voice));
  }

  void updatePersonalization({
    required String nickname,
    required String language,
    required SpeakingStyle speakingStyle,
  }) {
    emit(
      state.copyWith(
        nickname: nickname.trim(),
        language: language,
        speakingStyle: speakingStyle,
      ),
    );
  }

  void setMemoryEnabled(bool enabled) {
    emit(state.copyWith(memoryEnabled: enabled));
  }

  void complete() {
    emit(state.copyWith(isComplete: true));
  }

  void reset() {
    emit(const SetupState());
  }

  @override
  SetupState? fromJson(Map<String, dynamic> json) {
    return SetupState(
      isComplete: json['isComplete'] as bool? ?? false,
      nickname: json['nickname'] as String? ?? '',
      language: json['language'] as String? ?? 'English',
      voice: _voiceFromName(json['voice'] as String?),
      speakingStyle: _styleFromName(json['speakingStyle'] as String?),
      memoryEnabled: json['memoryEnabled'] as bool? ?? true,
    );
  }

  @override
  Map<String, dynamic>? toJson(SetupState state) {
    return {
      'isComplete': state.isComplete,
      'nickname': state.nickname,
      'language': state.language,
      'voice': state.voice.name,
      'speakingStyle': state.speakingStyle.name,
      'memoryEnabled': state.memoryEnabled,
    };
  }

  AssistantVoice _voiceFromName(String? name) {
    return AssistantVoice.values.firstWhere(
      (voice) => voice.name == name,
      orElse: () => AssistantVoice.friendly,
    );
  }

  SpeakingStyle _styleFromName(String? name) {
    return SpeakingStyle.values.firstWhere(
      (style) => style.name == name,
      orElse: () => SpeakingStyle.shortAnswers,
    );
  }

  static Storage _resolveStorage(Storage? storage) {
    if (storage != null) {
      return storage;
    }

    try {
      return HydratedBloc.storage;
    } on StorageNotFound {
      return _InMemoryStorage();
    }
  }
}

final class _InMemoryStorage implements Storage {
  final Map<String, dynamic> _values = {};

  @override
  Future<void> clear() async {
    _values.clear();
  }

  @override
  Future<void> close() async {}

  @override
  Future<void> delete(String key) async {
    _values.remove(key);
  }

  @override
  dynamic read(String key) => _values[key];

  @override
  Future<void> write(String key, dynamic value) async {
    _values[key] = value;
  }
}
