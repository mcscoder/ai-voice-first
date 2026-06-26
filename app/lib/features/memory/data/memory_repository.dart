import '../../../core/error.dart';
import 'memory_api.dart';
import 'memory_models.dart';

class MemoryRepository {
  MemoryRepository(this._api);

  final MemoryApi _api;

  Future<({NetworkError? error, MemoryCollection? collection})> loadMemories() {
    return _api.loadMemories();
  }

  Future<({NetworkError? error, MemoryItem? item})> createMemory({
    required String memory,
    required MemoryCategory category,
  }) {
    return _api.createMemory(memory: memory, category: category);
  }

  Future<({NetworkError? error, MemoryItem? item})> updateMemory({
    required String id,
    required String memory,
    required MemoryCategory category,
  }) {
    return _api.updateMemory(id: id, memory: memory, category: category);
  }

  Future<NetworkError?> deleteMemory({required String id}) {
    return _api.deleteMemory(id: id);
  }

  Future<({NetworkError? error, bool? memoryEnabled})> updateSettings({
    required bool memoryEnabled,
  }) {
    return _api.updateSettings(memoryEnabled: memoryEnabled);
  }
}
