import 'package:equatable/equatable.dart';

enum MemoryCategory {
  aboutMe('about_me', 'About me'),
  preferences('preferences', 'Preferences'),
  work('work', 'Work'),
  relationships('relationships', 'Relationships'),
  goals('goals', 'Goals'),
  customNotes('custom_notes', 'Custom notes');

  const MemoryCategory(this.apiKey, this.label);

  final String apiKey;
  final String label;

  static MemoryCategory fromApiKey(String value) {
    return MemoryCategory.values.firstWhere(
      (category) => category.apiKey == value,
      orElse: () => MemoryCategory.customNotes,
    );
  }
}

final class MemoryItem extends Equatable {
  const MemoryItem({
    required this.id,
    required this.memory,
    required this.category,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String memory;
  final MemoryCategory category;
  final String createdAt;
  final String updatedAt;

  factory MemoryItem.fromJson(Map<String, dynamic> json) {
    return MemoryItem(
      id: json['id'] as String? ?? '',
      memory: json['memory'] as String? ?? '',
      category: MemoryCategory.fromApiKey(json['category'] as String? ?? ''),
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }

  @override
  List<Object?> get props => [id, memory, category, createdAt, updatedAt];
}

final class MemoryCollection extends Equatable {
  const MemoryCollection({required this.memoryEnabled, required this.memories});

  final bool memoryEnabled;
  final List<MemoryItem> memories;

  factory MemoryCollection.fromJson(Map<String, dynamic> json) {
    final rawMemories = json['memories'];
    final memories = rawMemories is List
        ? rawMemories
              .whereType<Map<String, dynamic>>()
              .map(MemoryItem.fromJson)
              .toList()
        : <MemoryItem>[];

    return MemoryCollection(
      memoryEnabled: json['memory_enabled'] as bool? ?? true,
      memories: memories,
    );
  }

  @override
  List<Object?> get props => [memoryEnabled, memories];
}
