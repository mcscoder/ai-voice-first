import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/design_system/design_system.dart';
import '../../core/router/router.dart';
import '../onboarding/onboarding.dart';
import 'data/memory_models.dart';
import 'presentation/memory_cubit.dart';
import 'presentation/memory_state.dart';

final class MemoryScreen extends StatefulWidget {
  const MemoryScreen({super.key});

  @override
  State<MemoryScreen> createState() => _MemoryScreenState();
}

final class _MemoryScreenState extends State<MemoryScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      context.read<MemoryCubit>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    return _MemoryStateListener(
      child: BlocBuilder<MemoryCubit, MemoryState>(
        builder: (context, state) {
          final cubit = context.read<MemoryCubit>();
          final subtitle = state.memoryEnabled
              ? 'Memory is enabled'
              : 'Memory is disabled';

          return VoxiaScaffold(
            child: Stack(
              children: [
                VoxiaScrollPage(
                  title: 'Memory',
                  subtitle: subtitle,
                  leading: _BackToTalkButton(onPressed: context.pop),
                  trailing: _MemoryHeaderActions(
                    memoryEnabled: state.memoryEnabled,
                    isBusy: state.status == MemoryStatus.saving,
                    onToggle: cubit.setMemoryEnabled,
                  ),
                  slivers: [
                    const SizedBox(height: AppSpacing.sm),
                    if (state.status == MemoryStatus.loading &&
                        state.memories.isEmpty)
                      const _LoadingPanel()
                    else if (state.status == MemoryStatus.failure &&
                        state.memories.isEmpty)
                      _RetryPanel(onRetry: cubit.load)
                    else
                      ...MemoryCategory.values.map(
                        (category) => _MemoryCategoryTile(
                          category: category,
                          count: state.memories
                              .where((item) => item.category == category)
                              .length,
                          onTap: () => context.push(
                            AppRoutes.memoryCategory(category.apiKey),
                          ),
                        ),
                      ),
                    const SizedBox(height: AppSpacing.xxxl + AppSpacing.md),
                  ],
                ),
                Positioned(
                  right: AppSpacing.md,
                  bottom: AppSpacing.md,
                  child: _MemoryFloatingActionButton(
                    onPressed: () => _showMemoryEditorSheet(context),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

final class MemoryCategoryScreen extends StatefulWidget {
  const MemoryCategoryScreen({required this.categoryKey, super.key});

  final String categoryKey;

  @override
  State<MemoryCategoryScreen> createState() => _MemoryCategoryScreenState();
}

final class _MemoryCategoryScreenState extends State<MemoryCategoryScreen> {
  late final MemoryCategory _category = MemoryCategory.fromApiKey(
    widget.categoryKey,
  );

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      context.read<MemoryCubit>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    return _MemoryStateListener(
      child: BlocBuilder<MemoryCubit, MemoryState>(
        builder: (context, state) {
          final cubit = context.read<MemoryCubit>();
          final items = state.memories
              .where((item) => item.category == _category)
              .toList();

          return VoxiaScaffold(
            child: Stack(
              children: [
                VoxiaScrollPage(
                  title: _category.label,
                  subtitle:
                      '${items.length} item${items.length == 1 ? '' : 's'}',
                  leading: _BackToTalkButton(onPressed: context.pop),
                  slivers: [
                    const SizedBox(height: AppSpacing.sm),
                    if (state.status == MemoryStatus.loading &&
                        state.memories.isEmpty)
                      const _LoadingPanel()
                    else if (items.isEmpty)
                      VoxiaGlassPanel(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'No memories here yet.',
                              style: Theme.of(context).textTheme.titleMedium
                                  ?.copyWith(
                                    color: VoxiaColors.text,
                                    fontWeight: FontWeight.w700,
                                  ),
                            ),
                            const SizedBox(height: AppSpacing.sm),
                            VoxiaOutlineButton(
                              label: 'Add memory',
                              onPressed: () => _showMemoryEditorSheet(
                                context,
                                initialCategory: _category,
                              ),
                              icon: Icons.add_rounded,
                            ),
                          ],
                        ),
                      )
                    else
                      ...items.map(
                        (item) => _MemoryItemTile(
                          item: item,
                          onEdit: () => _showMemoryEditorSheet(
                            context,
                            initialItem: item,
                          ),
                          onDelete: () => _confirmDeleteMemory(context, item),
                        ),
                      ),
                    if (state.status == MemoryStatus.failure &&
                        state.errorMessage != null)
                      _RetryPanel(onRetry: cubit.load),
                    const SizedBox(height: AppSpacing.xxxl + AppSpacing.md),
                  ],
                ),
                Positioned(
                  right: AppSpacing.md,
                  bottom: AppSpacing.md,
                  child: _MemoryFloatingActionButton(
                    onPressed: () => _showMemoryEditorSheet(
                      context,
                      initialCategory: _category,
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

final class _MemoryStateListener extends StatelessWidget {
  const _MemoryStateListener({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return BlocListener<MemoryCubit, MemoryState>(
      listenWhen: (previous, current) =>
          previous.memoryEnabled != current.memoryEnabled ||
          previous.errorMessage != current.errorMessage ||
          previous.status != current.status,
      listener: (context, state) {
        if (state.status == MemoryStatus.ready) {
          context.read<SetupCubit>().setMemoryEnabled(state.memoryEnabled);
        }
        final errorMessage = state.errorMessage;
        if (state.status == MemoryStatus.failure && errorMessage != null) {
          ScaffoldMessenger.of(context)
            ..hideCurrentSnackBar()
            ..showSnackBar(SnackBar(content: Text(errorMessage)));
        }
      },
      child: child,
    );
  }
}

final class _MemoryHeaderActions extends StatelessWidget {
  const _MemoryHeaderActions({
    required this.memoryEnabled,
    required this.isBusy,
    required this.onToggle,
  });

  final bool memoryEnabled;
  final bool isBusy;
  final ValueChanged<bool> onToggle;

  @override
  Widget build(BuildContext context) {
    return Switch(value: memoryEnabled, onChanged: isBusy ? null : onToggle);
  }
}

final class _MemoryFloatingActionButton extends StatelessWidget {
  const _MemoryFloatingActionButton({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return SafeArea(
      child: FloatingActionButton(
        tooltip: 'Add memory',
        onPressed: onPressed,
        backgroundColor: colorScheme.primary,
        foregroundColor: colorScheme.onPrimary,
        child: const Icon(Icons.add_rounded),
      ),
    );
  }
}

final class _BackToTalkButton extends StatelessWidget {
  const _BackToTalkButton({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Back to talk',
      onPressed: onPressed,
      style: IconButton.styleFrom(
        backgroundColor: Colors.transparent,
        foregroundColor: VoxiaColors.text,
        minimumSize: const Size.square(44),
        shape: const CircleBorder(),
      ),
      icon: const Icon(Icons.arrow_back_rounded, size: 26),
    );
  }
}

final class _MemoryCategoryTile extends StatelessWidget {
  const _MemoryCategoryTile({
    required this.category,
    required this.count,
    required this.onTap,
  });

  final MemoryCategory category;
  final int count;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: VoxiaGlassPanel(
        onTap: onTap,
        child: Row(
          children: [
            Icon(_iconForCategory(category), color: VoxiaColors.cyan, size: 30),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Text(
                category.label,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: VoxiaColors.text,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0,
                ),
              ),
            ),
            Text(
              '$count item${count == 1 ? '' : 's'}',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: VoxiaColors.muted,
                letterSpacing: 0,
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            const Icon(Icons.chevron_right, color: VoxiaColors.muted),
          ],
        ),
      ),
    );
  }
}

final class _MemoryItemTile extends StatelessWidget {
  const _MemoryItemTile({
    required this.item,
    required this.onEdit,
    required this.onDelete,
  });

  final MemoryItem item;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final timestamp = item.updatedAt.isNotEmpty
        ? item.updatedAt
        : item.createdAt;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: VoxiaGlassPanel(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    item.memory,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: VoxiaColors.text,
                      letterSpacing: 0,
                    ),
                  ),
                ),
                Wrap(
                  spacing: AppSpacing.xs,
                  children: [
                    IconButton(
                      tooltip: 'Edit memory',
                      onPressed: onEdit,
                      style: IconButton.styleFrom(
                        foregroundColor: VoxiaColors.text,
                        backgroundColor: Colors.transparent,
                      ),
                      icon: const Icon(Icons.edit_outlined),
                    ),
                    IconButton(
                      tooltip: 'Delete memory',
                      onPressed: onDelete,
                      style: IconButton.styleFrom(
                        foregroundColor: VoxiaColors.red,
                        backgroundColor: Colors.transparent,
                      ),
                      icon: const Icon(Icons.delete_outline),
                    ),
                  ],
                ),
              ],
            ),
            if (timestamp.isNotEmpty) ...[
              const SizedBox(height: AppSpacing.sm),
              Text(
                timestamp,
                style: Theme.of(
                  context,
                ).textTheme.bodySmall?.copyWith(color: VoxiaColors.muted),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

final class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: AppSpacing.lg),
      child: Center(child: CircularProgressIndicator()),
    );
  }
}

final class _RetryPanel extends StatelessWidget {
  const _RetryPanel({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return VoxiaGlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Could not load memories.',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: VoxiaColors.text,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          VoxiaOutlineButton(
            label: 'Retry',
            onPressed: onRetry,
            icon: Icons.refresh_rounded,
          ),
        ],
      ),
    );
  }
}

Future<void> _showMemoryEditorSheet(
  BuildContext context, {
  MemoryItem? initialItem,
  MemoryCategory? initialCategory,
}) async {
  final cubit = context.read<MemoryCubit>();
  final controller = TextEditingController(text: initialItem?.memory ?? '');
  var selectedCategory =
      initialItem?.category ?? initialCategory ?? MemoryCategory.customNotes;
  var isSaving = false;

  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (context) {
      return StatefulBuilder(
        builder: (context, setModalState) {
          Future<void> save() async {
            final memoryText = controller.text.trim();
            if (memoryText.isEmpty || isSaving) {
              return;
            }

            setModalState(() {
              isSaving = true;
            });

            final success = initialItem == null
                ? await cubit.createMemory(
                    memory: memoryText,
                    category: selectedCategory,
                  )
                : await cubit.updateMemory(
                    id: initialItem.id,
                    memory: memoryText,
                    category: selectedCategory,
                  );

            if (!context.mounted) {
              return;
            }
            if (success) {
              Navigator.of(context).pop();
              return;
            }

            setModalState(() {
              isSaving = false;
            });
          }

          return SafeArea(
            child: Padding(
              padding: EdgeInsets.only(
                left: AppSpacing.md,
                right: AppSpacing.md,
                bottom: MediaQuery.viewInsetsOf(context).bottom + AppSpacing.md,
                top: AppSpacing.md,
              ),
              child: VoxiaGlassPanel(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        initialItem == null ? 'New memory' : 'Edit memory',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: VoxiaColors.text,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      TextField(
                        controller: controller,
                        minLines: 4,
                        maxLines: 6,
                        style: const TextStyle(color: VoxiaColors.text),
                        decoration: const InputDecoration(
                          hintText: 'Write the memory',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      DropdownButtonFormField<MemoryCategory>(
                        value: selectedCategory,
                        decoration: const InputDecoration(
                          labelText: 'Category',
                          border: OutlineInputBorder(),
                        ),
                        items: MemoryCategory.values
                            .map(
                              (category) => DropdownMenuItem(
                                value: category,
                                child: Text(category.label),
                              ),
                            )
                            .toList(),
                        onChanged: (value) {
                          if (value == null) {
                            return;
                          }
                          setModalState(() {
                            selectedCategory = value;
                          });
                        },
                      ),
                      const SizedBox(height: AppSpacing.md),
                      Row(
                        children: [
                          Expanded(
                            child: VoxiaOutlineButton(
                              label: 'Cancel',
                              onPressed: () => Navigator.of(context).pop(),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            child: VoxiaGradientButton(
                              label: 'Save',
                              onPressed: save,
                              isBusy: isSaving,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      );
    },
  );
}

Future<void> _confirmDeleteMemory(BuildContext context, MemoryItem item) async {
  final shouldDelete = await showDialog<bool>(
    context: context,
    builder: (context) {
      return AlertDialog(
        title: const Text('Delete memory?'),
        content: Text(item.memory),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Delete'),
          ),
        ],
      );
    },
  );

  if (shouldDelete != true || !context.mounted) {
    return;
  }
  await context.read<MemoryCubit>().deleteMemory(item.id);
}

IconData _iconForCategory(MemoryCategory category) {
  return switch (category) {
    MemoryCategory.aboutMe => Icons.person_outline,
    MemoryCategory.preferences => Icons.star_border,
    MemoryCategory.work => Icons.business_center_outlined,
    MemoryCategory.relationships => Icons.groups_outlined,
    MemoryCategory.goals => Icons.track_changes,
    MemoryCategory.customNotes => Icons.description_outlined,
  };
}
