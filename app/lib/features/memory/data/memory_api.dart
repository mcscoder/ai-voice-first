import 'package:dio/dio.dart';

import '../../../core/error.dart';
import '../../../core/network/api.dart';
import '../../../core/network/api_path.dart';
import '../../../core/network/dio.dart';
import 'memory_models.dart';

final class MemoryApi extends Api {
  MemoryApi(@authDio super.dio);

  Future<({NetworkError? error, MemoryCollection? collection})>
  loadMemories() async {
    final result = await withTimeoutRequest(() async {
      final response = await dio.get<Map<String, dynamic>>(ApiPath.memories);
      return MemoryCollection.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, collection: null),
      (collection) => (error: null, collection: collection),
    );
  }

  Future<({NetworkError? error, MemoryItem? item})> createMemory({
    required String memory,
    required MemoryCategory category,
  }) async {
    return _submitMemory(ApiPath.memories, memory: memory, category: category);
  }

  Future<({NetworkError? error, MemoryItem? item})> updateMemory({
    required String id,
    required String memory,
    required MemoryCategory category,
  }) async {
    return _submitMemory(
      '${ApiPath.memories}/$id',
      memory: memory,
      category: category,
      patch: true,
    );
  }

  Future<NetworkError?> deleteMemory({required String id}) async {
    final result = await withTimeoutRequest(() async {
      await dio.delete<Map<String, dynamic>>('${ApiPath.memories}/$id');
    });
    return result.match((error) => error, (_) => null);
  }

  Future<({NetworkError? error, bool? memoryEnabled})> updateSettings({
    required bool memoryEnabled,
  }) async {
    final result = await withTimeoutRequest(() async {
      final response = await dio.put<Map<String, dynamic>>(
        ApiPath.memorySettings,
        data: {'memory_enabled': memoryEnabled},
      );
      return response.data?['memory_enabled'] as bool? ?? true;
    });

    return result.match(
      (error) => (error: error, memoryEnabled: null),
      (memoryEnabled) => (error: null, memoryEnabled: memoryEnabled),
    );
  }

  Future<({NetworkError? error, MemoryItem? item})> _submitMemory(
    String path, {
    required String memory,
    required MemoryCategory category,
    bool patch = false,
  }) async {
    final result = await withTimeoutRequest(() async {
      final response = patch
          ? await dio.patch<Map<String, dynamic>>(
              path,
              data: {'memory': memory, 'category': category.apiKey},
            )
          : await dio.post<Map<String, dynamic>>(
              path,
              data: {'memory': memory, 'category': category.apiKey},
            );
      return MemoryItem.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, item: null),
      (item) => (error: null, item: item),
    );
  }
}
