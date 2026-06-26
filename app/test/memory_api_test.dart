import 'package:ai_voice_first/features/memory/memory.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('MemoryApi', () {
    test('loads memories and parses backend state', () async {
      String? capturedPath;

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPath = options.path;
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                data: {
                  'memory_enabled': false,
                  'memories': [
                    {
                      'id': 'memory-1',
                      'memory': 'Prefers tea.',
                      'category': 'preferences',
                      'created_at': '2026-06-25T04:08:26+00:00',
                      'updated_at': '2026-06-25T05:40:29+00:00',
                    },
                  ],
                },
              ),
            );
          },
        ),
      );

      final api = MemoryApi(dio);
      final result = await api.loadMemories();

      expect(result.error, isNull);
      expect(capturedPath, '/v1/memories');
      expect(result.collection?.memoryEnabled, isFalse);
      expect(
        result.collection?.memories.single.category,
        MemoryCategory.preferences,
      );
    });

    test('creates and updates memories on the expected paths', () async {
      final capturedPaths = <String>[];
      final capturedBodies = <Map<String, dynamic>>[];

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPaths.add(options.path);
            capturedBodies.add(Map<String, dynamic>.from(options.data as Map));
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                data: {
                  'id': 'memory-1',
                  'memory': 'Prefers tea.',
                  'category': 'preferences',
                  'created_at': '2026-06-25T04:08:26+00:00',
                  'updated_at': '2026-06-25T05:40:29+00:00',
                },
              ),
            );
          },
        ),
      );

      final api = MemoryApi(dio);
      await api.createMemory(
        memory: 'Prefers tea.',
        category: MemoryCategory.preferences,
      );
      await api.updateMemory(
        id: 'memory-1',
        memory: 'Prefers coffee.',
        category: MemoryCategory.preferences,
      );

      expect(capturedPaths, ['/v1/memories', '/v1/memories/memory-1']);
      expect(capturedBodies, [
        {'memory': 'Prefers tea.', 'category': 'preferences'},
        {'memory': 'Prefers coffee.', 'category': 'preferences'},
      ]);
    });

    test('deletes memories on the expected path', () async {
      String? capturedPath;

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPath = options.path;
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                data: const {'status': 'ok'},
              ),
            );
          },
        ),
      );

      final api = MemoryApi(dio);
      final error = await api.deleteMemory(id: 'memory-1');

      expect(error, isNull);
      expect(capturedPath, '/v1/memories/memory-1');
    });

    test('updates memory settings from the backend response', () async {
      String? capturedPath;
      Map<String, dynamic>? capturedBody;

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedPath = options.path;
            capturedBody = Map<String, dynamic>.from(options.data as Map);
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                data: {'memory_enabled': false},
              ),
            );
          },
        ),
      );

      final api = MemoryApi(dio);
      final result = await api.updateSettings(memoryEnabled: false);

      expect(result.error, isNull);
      expect(result.memoryEnabled, isFalse);
      expect(capturedPath, '/v1/memories/settings');
      expect(capturedBody, {'memory_enabled': false});
    });
  });
}
