import 'package:ai_voice_first/core/error.dart';
import 'package:ai_voice_first/features/memory/memory.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('MemoryCubit', () {
    test('loads memories and becomes ready', () async {
      final cubit = MemoryCubit(
        _MemoryRepositoryStub(
          loadResult: (
            error: null,
            collection: const MemoryCollection(
              memoryEnabled: false,
              memories: [
                MemoryItem(
                  id: 'memory-1',
                  memory: 'Prefers tea.',
                  category: MemoryCategory.preferences,
                  createdAt: '2026-06-25T04:08:26+00:00',
                  updatedAt: '2026-06-25T05:40:29+00:00',
                ),
              ],
            ),
          ),
        ),
      );

      final states = <MemoryState>[];
      final subscription = cubit.stream.listen(states.add);

      await cubit.load();
      await Future<void>.delayed(Duration.zero);

      expect(states.map((state) => state.status), [
        MemoryStatus.loading,
        MemoryStatus.ready,
      ]);
      expect(cubit.state.memoryEnabled, isFalse);
      expect(cubit.state.memories.single.memory, 'Prefers tea.');

      await subscription.cancel();
      await cubit.close();
    });

    test('updates memory settings and keeps server state', () async {
      final cubit = MemoryCubit(
        _MemoryRepositoryStub(
          settingsResult: (error: null, memoryEnabled: false),
        ),
      );

      final success = await cubit.setMemoryEnabled(false);

      expect(success, isTrue);
      expect(cubit.state.status, MemoryStatus.ready);
      expect(cubit.state.memoryEnabled, isFalse);
      await cubit.close();
    });

    test('creates a memory and prepends it', () async {
      final cubit = MemoryCubit(
        _MemoryRepositoryStub(
          createResult: (
            error: null,
            item: const MemoryItem(
              id: 'created-id',
              memory: 'New memory.',
              category: MemoryCategory.goals,
              createdAt: '2026-06-25T04:08:26+00:00',
              updatedAt: '2026-06-25T05:40:29+00:00',
            ),
          ),
        ),
      );

      final success = await cubit.createMemory(
        memory: 'New memory.',
        category: MemoryCategory.goals,
      );

      expect(success, isTrue);
      expect(cubit.state.status, MemoryStatus.ready);
      expect(cubit.state.memories.single.id, 'created-id');
      await cubit.close();
    });

    test('updates a memory in place', () async {
      final cubit = MemoryCubit(
        _MemoryRepositoryStub(
          updateResult: (
            error: null,
            item: const MemoryItem(
              id: 'memory-1',
              memory: 'Updated memory.',
              category: MemoryCategory.work,
              createdAt: '2026-06-25T04:08:26+00:00',
              updatedAt: '2026-06-26T05:40:29+00:00',
            ),
          ),
        ),
      );
      cubit.emit(
        const MemoryState(
          status: MemoryStatus.ready,
          memories: [
            MemoryItem(
              id: 'memory-1',
              memory: 'Old memory.',
              category: MemoryCategory.preferences,
              createdAt: '2026-06-25T04:08:26+00:00',
              updatedAt: '2026-06-25T05:40:29+00:00',
            ),
          ],
        ),
      );

      final success = await cubit.updateMemory(
        id: 'memory-1',
        memory: 'Updated memory.',
        category: MemoryCategory.work,
      );

      expect(success, isTrue);
      expect(cubit.state.status, MemoryStatus.ready);
      expect(cubit.state.memories.single.memory, 'Updated memory.');
      expect(cubit.state.memories.single.category, MemoryCategory.work);
      await cubit.close();
    });

    test('deletes a memory and removes it from state', () async {
      final cubit = MemoryCubit(_MemoryRepositoryStub());
      cubit.emit(
        const MemoryState(
          status: MemoryStatus.ready,
          memories: [
            MemoryItem(
              id: 'memory-1',
              memory: 'Old memory.',
              category: MemoryCategory.preferences,
              createdAt: '2026-06-25T04:08:26+00:00',
              updatedAt: '2026-06-25T05:40:29+00:00',
            ),
          ],
        ),
      );

      final success = await cubit.deleteMemory('memory-1');

      expect(success, isTrue);
      expect(cubit.state.status, MemoryStatus.ready);
      expect(cubit.state.memories, isEmpty);
      await cubit.close();
    });
  });
}

final class _MemoryRepositoryStub extends MemoryRepository {
  _MemoryRepositoryStub({
    this.loadResult,
    this.createResult,
    this.updateResult,
    this.settingsResult,
    this.deleteError,
  }) : super(MemoryApi(Dio()));

  final ({NetworkError? error, MemoryCollection? collection})? loadResult;
  final ({NetworkError? error, MemoryItem? item})? createResult;
  final ({NetworkError? error, MemoryItem? item})? updateResult;
  final ({NetworkError? error, bool? memoryEnabled})? settingsResult;
  final NetworkError? deleteError;

  @override
  Future<({NetworkError? error, MemoryCollection? collection})>
  loadMemories() async {
    return loadResult ??
        (
          error: null,
          collection: const MemoryCollection(memoryEnabled: true, memories: []),
        );
  }

  @override
  Future<({NetworkError? error, MemoryItem? item})> createMemory({
    required String memory,
    required MemoryCategory category,
  }) async {
    return createResult ?? (error: null, item: null);
  }

  @override
  Future<({NetworkError? error, MemoryItem? item})> updateMemory({
    required String id,
    required String memory,
    required MemoryCategory category,
  }) async {
    return updateResult ?? (error: null, item: null);
  }

  @override
  Future<NetworkError?> deleteMemory({required String id}) async {
    return deleteError;
  }

  @override
  Future<({NetworkError? error, bool? memoryEnabled})> updateSettings({
    required bool memoryEnabled,
  }) async {
    return settingsResult ?? (error: null, memoryEnabled: memoryEnabled);
  }
}
