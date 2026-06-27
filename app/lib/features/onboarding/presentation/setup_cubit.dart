import 'package:equatable/equatable.dart';
import 'package:hydrated_bloc/hydrated_bloc.dart';

enum SpeakingStyle { shortAnswers, detailedAnswers, casual, professional }

final class SetupState extends Equatable {
  const SetupState({
    this.isComplete = false,
    this.nickname = '',
    this.speakingStyle = SpeakingStyle.shortAnswers,
    this.memoryEnabled = true,
  });

  final bool isComplete;
  final String nickname;
  final SpeakingStyle speakingStyle;
  final bool memoryEnabled;

  SetupState copyWith({
    bool? isComplete,
    String? nickname,
    SpeakingStyle? speakingStyle,
    bool? memoryEnabled,
  }) {
    return SetupState(
      isComplete: isComplete ?? this.isComplete,
      nickname: nickname ?? this.nickname,
      speakingStyle: speakingStyle ?? this.speakingStyle,
      memoryEnabled: memoryEnabled ?? this.memoryEnabled,
    );
  }

  @override
  List<Object?> get props => [
    isComplete,
    nickname,
    speakingStyle,
    memoryEnabled,
  ];
}

final class SetupCubit extends HydratedCubit<SetupState> {
  SetupCubit({Storage? storage})
    : super(const SetupState(), storage: _resolveStorage(storage));

  void updatePersonalization({
    required String nickname,
    required SpeakingStyle speakingStyle,
  }) {
    emit(
      state.copyWith(nickname: nickname.trim(), speakingStyle: speakingStyle),
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
      speakingStyle: _styleFromName(json['speakingStyle'] as String?),
      memoryEnabled: json['memoryEnabled'] as bool? ?? true,
    );
  }

  @override
  Map<String, dynamic>? toJson(SetupState state) {
    return {
      'isComplete': state.isComplete,
      'nickname': state.nickname,
      'speakingStyle': state.speakingStyle.name,
      'memoryEnabled': state.memoryEnabled,
    };
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
