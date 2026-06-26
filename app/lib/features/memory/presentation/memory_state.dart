import 'package:equatable/equatable.dart';

import '../data/memory_models.dart';

enum MemoryStatus { initial, loading, ready, saving, failure }

final class MemoryState extends Equatable {
  const MemoryState({
    this.status = MemoryStatus.initial,
    this.memoryEnabled = true,
    this.memories = const [],
    this.errorMessage,
  });

  final MemoryStatus status;
  final bool memoryEnabled;
  final List<MemoryItem> memories;
  final String? errorMessage;

  static const _sentinel = Object();

  MemoryState copyWith({
    MemoryStatus? status,
    bool? memoryEnabled,
    List<MemoryItem>? memories,
    Object? errorMessage = _sentinel,
  }) {
    return MemoryState(
      status: status ?? this.status,
      memoryEnabled: memoryEnabled ?? this.memoryEnabled,
      memories: memories ?? this.memories,
      errorMessage: errorMessage == _sentinel
          ? this.errorMessage
          : errorMessage as String?,
    );
  }

  @override
  List<Object?> get props => [status, memoryEnabled, memories, errorMessage];
}
