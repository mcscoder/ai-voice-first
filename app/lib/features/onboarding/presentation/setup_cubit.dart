import 'package:equatable/equatable.dart';
import 'package:hydrated_bloc/hydrated_bloc.dart';

import '../../../core/error.dart';
import '../../profile/data/personalization_repository.dart';
import 'speaking_style.dart';

enum SetupSyncStatus { initial, syncing, synced, failed }

final class SetupState extends Equatable {
  const SetupState({
    this.isComplete = false,
    this.nickname = '',
    this.speakingStyle = SpeakingStyle.shortAnswers,
    this.memoryEnabled = true,
    this.syncStatus = SetupSyncStatus.initial,
    this.errorMessage,
  });

  final bool isComplete;
  final String nickname;
  final SpeakingStyle speakingStyle;
  final bool memoryEnabled;
  final SetupSyncStatus syncStatus;
  final String? errorMessage;

  static const _sentinel = Object();

  SetupState copyWith({
    bool? isComplete,
    String? nickname,
    SpeakingStyle? speakingStyle,
    bool? memoryEnabled,
    SetupSyncStatus? syncStatus,
    Object? errorMessage = _sentinel,
  }) {
    return SetupState(
      isComplete: isComplete ?? this.isComplete,
      nickname: nickname ?? this.nickname,
      speakingStyle: speakingStyle ?? this.speakingStyle,
      memoryEnabled: memoryEnabled ?? this.memoryEnabled,
      syncStatus: syncStatus ?? this.syncStatus,
      errorMessage: errorMessage == _sentinel
          ? this.errorMessage
          : errorMessage as String?,
    );
  }

  @override
  List<Object?> get props => [
    isComplete,
    nickname,
    speakingStyle,
    memoryEnabled,
    syncStatus,
    errorMessage,
  ];
}

final class SetupCubit extends HydratedCubit<SetupState> {
  SetupCubit({Storage? storage, PersonalizationRepository? repository})
    : _repository = repository,
      super(const SetupState(), storage: _resolveStorage(storage));

  final PersonalizationRepository? _repository;

  Future<void> syncFromBackend() async {
    if (state.syncStatus == SetupSyncStatus.syncing || _repository == null) {
      return;
    }

    emit(
      state.copyWith(syncStatus: SetupSyncStatus.syncing, errorMessage: null),
    );

    final result = await _repository.loadPersonalization();
    final personalization = result.personalization;
    if (personalization == null) {
      emit(
        state.copyWith(
          syncStatus: SetupSyncStatus.failed,
          errorMessage: _errorMessage(result.error),
        ),
      );
      return;
    }

    emit(
      state.copyWith(
        isComplete: personalization.setupCompleted,
        nickname: personalization.nickname,
        speakingStyle: personalization.speakingStyle,
        syncStatus: SetupSyncStatus.synced,
        errorMessage: null,
      ),
    );
  }

  Future<bool> savePersonalization({
    required String nickname,
    required SpeakingStyle speakingStyle,
  }) async {
    if (_repository == null) {
      return false;
    }

    final result = await _repository.updatePersonalization(
      nickname: nickname.trim(),
      speakingStyle: speakingStyle.name,
    );
    final personalization = result.personalization;
    if (personalization == null) {
      emit(state.copyWith(errorMessage: _errorMessage(result.error)));
      return false;
    }

    emit(
      state.copyWith(
        nickname: personalization.nickname,
        speakingStyle: personalization.speakingStyle,
        isComplete: personalization.setupCompleted,
        syncStatus: SetupSyncStatus.synced,
        errorMessage: null,
      ),
    );
    return true;
  }

  void setMemoryEnabled(bool enabled) {
    emit(state.copyWith(memoryEnabled: enabled));
  }

  void complete() {
    emit(
      state.copyWith(
        isComplete: true,
        syncStatus: SetupSyncStatus.synced,
        errorMessage: null,
      ),
    );
  }

  Future<bool> markSetupCompleted(bool completed) async {
    if (_repository == null) {
      return false;
    }

    final result = await _repository.updateSetupCompletion(
      setupCompleted: completed,
    );
    final personalization = result.personalization;
    if (personalization == null) {
      emit(state.copyWith(errorMessage: _errorMessage(result.error)));
      return false;
    }

    emit(
      state.copyWith(
        isComplete: personalization.setupCompleted,
        nickname: personalization.nickname,
        speakingStyle: personalization.speakingStyle,
        syncStatus: SetupSyncStatus.synced,
        errorMessage: null,
      ),
    );
    return true;
  }

  void clearLocalStateOnLogout() {
    emit(const SetupState());
  }

  void reset() {
    emit(SetupState(syncStatus: state.syncStatus));
  }

  @override
  SetupState? fromJson(Map<String, dynamic> json) {
    return SetupState(
      isComplete: json['isComplete'] as bool? ?? false,
      nickname: json['nickname'] as String? ?? '',
      speakingStyle: speakingStyleFromName(json['speakingStyle'] as String?),
      memoryEnabled: json['memoryEnabled'] as bool? ?? true,
      syncStatus: _syncStatusFromName(json['syncStatus'] as String?),
    );
  }

  @override
  Map<String, dynamic>? toJson(SetupState state) {
    return {
      'isComplete': state.isComplete,
      'nickname': state.nickname,
      'speakingStyle': state.speakingStyle.name,
      'memoryEnabled': state.memoryEnabled,
      'syncStatus': state.syncStatus.name,
    };
  }

  SetupSyncStatus _syncStatusFromName(String? name) {
    return SetupSyncStatus.values.firstWhere(
      (status) => status.name == name,
      orElse: () => SetupSyncStatus.initial,
    );
  }

  String _errorMessage(NetworkError? error) {
    if (error is Unauthorized) {
      return 'Your session expired. Please sign in again.';
    }
    if (error is Timeout) {
      return 'The request timed out. Try again.';
    }
    if (error is BadRequest) {
      return 'Your personalization could not be saved.';
    }
    return 'Something went wrong. Try again.';
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
