import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/error.dart';
import '../data/memory_models.dart';
import '../data/memory_repository.dart';
import 'memory_state.dart';

final class MemoryCubit extends Cubit<MemoryState> {
  MemoryCubit(this._repository) : super(const MemoryState());

  final MemoryRepository _repository;

  Future<void> load() async {
    emit(state.copyWith(status: MemoryStatus.loading, errorMessage: null));
    final result = await _repository.loadMemories();
    final collection = result.collection;
    if (collection == null) {
      emit(
        state.copyWith(
          status: MemoryStatus.failure,
          errorMessage: _errorMessage(result.error),
        ),
      );
      return;
    }

    emit(
      state.copyWith(
        status: MemoryStatus.ready,
        memoryEnabled: collection.memoryEnabled,
        memories: collection.memories,
        errorMessage: null,
      ),
    );
  }

  Future<bool> setMemoryEnabled(bool enabled) async {
    emit(state.copyWith(status: MemoryStatus.saving, errorMessage: null));
    final result = await _repository.updateSettings(memoryEnabled: enabled);
    if (result.memoryEnabled == null) {
      emit(
        state.copyWith(
          status: MemoryStatus.failure,
          errorMessage: _errorMessage(result.error),
        ),
      );
      return false;
    }

    emit(
      state.copyWith(
        status: MemoryStatus.ready,
        memoryEnabled: result.memoryEnabled,
        errorMessage: null,
      ),
    );
    return true;
  }

  Future<bool> createMemory({
    required String memory,
    required MemoryCategory category,
  }) async {
    emit(state.copyWith(status: MemoryStatus.saving, errorMessage: null));
    final result = await _repository.createMemory(
      memory: memory,
      category: category,
    );
    final item = result.item;
    if (item == null) {
      emit(
        state.copyWith(
          status: MemoryStatus.failure,
          errorMessage: _errorMessage(result.error),
        ),
      );
      return false;
    }

    final memories = [item, ...state.memories];
    emit(
      state.copyWith(
        status: MemoryStatus.ready,
        memories: memories,
        errorMessage: null,
      ),
    );
    return true;
  }

  Future<bool> updateMemory({
    required String id,
    required String memory,
    required MemoryCategory category,
  }) async {
    emit(state.copyWith(status: MemoryStatus.saving, errorMessage: null));
    final result = await _repository.updateMemory(
      id: id,
      memory: memory,
      category: category,
    );
    final item = result.item;
    if (item == null) {
      emit(
        state.copyWith(
          status: MemoryStatus.failure,
          errorMessage: _errorMessage(result.error),
        ),
      );
      return false;
    }

    final memories = state.memories
        .map((existing) => existing.id == id ? item : existing)
        .toList();
    emit(
      state.copyWith(
        status: MemoryStatus.ready,
        memories: memories,
        errorMessage: null,
      ),
    );
    return true;
  }

  Future<bool> deleteMemory(String id) async {
    emit(state.copyWith(status: MemoryStatus.saving, errorMessage: null));
    final error = await _repository.deleteMemory(id: id);
    if (error != null) {
      emit(
        state.copyWith(
          status: MemoryStatus.failure,
          errorMessage: _errorMessage(error),
        ),
      );
      return false;
    }

    emit(
      state.copyWith(
        status: MemoryStatus.ready,
        memories: state.memories.where((item) => item.id != id).toList(),
        errorMessage: null,
      ),
    );
    return true;
  }

  String _errorMessage(NetworkError? error) {
    if (error is Unauthorized) {
      return 'Your session expired.';
    }
    if (error is NotFound) {
      return 'Memory not found.';
    }
    if (error is Forbidden) {
      return 'This action is not allowed.';
    }
    if (error is Timeout) {
      return 'The request timed out.';
    }
    return 'Something went wrong.';
  }
}
