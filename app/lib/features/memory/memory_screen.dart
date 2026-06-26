import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/design_system/design_system.dart';
import '../onboarding/onboarding.dart';

final class MemoryScreen extends StatelessWidget {
  const MemoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<SetupCubit, SetupState>(
      builder: (context, setup) {
        return VoxiaScaffold(
          child: VoxiaScrollPage(
            title: 'Memory',
            subtitle: setup.memoryEnabled
                ? 'Memory is enabled'
                : 'Memory is disabled',
            leading: _BackToTalkButton(onPressed: context.pop),
            trailing: Switch(
              value: setup.memoryEnabled,
              onChanged: context.read<SetupCubit>().setMemoryEnabled,
            ),
            slivers: const [
              SizedBox(height: AppSpacing.sm),
              _MemoryCategory(
                icon: Icons.person_outline,
                title: 'About me',
                count: '12 items',
              ),
              _MemoryCategory(
                icon: Icons.star_border,
                title: 'Preferences',
                count: '8 items',
              ),
              _MemoryCategory(
                icon: Icons.business_center_outlined,
                title: 'Work',
                count: '15 items',
              ),
              _MemoryCategory(
                icon: Icons.groups_outlined,
                title: 'Relationships',
                count: '6 items',
              ),
              _MemoryCategory(
                icon: Icons.track_changes,
                title: 'Goals',
                count: '7 items',
              ),
              _MemoryCategory(
                icon: Icons.description_outlined,
                title: 'Custom notes',
                count: '9 items',
              ),
            ],
          ),
        );
      },
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

final class _MemoryCategory extends StatelessWidget {
  const _MemoryCategory({
    required this.icon,
    required this.title,
    required this.count,
  });

  final IconData icon;
  final String title;
  final String count;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: VoxiaGlassPanel(
        child: Row(
          children: [
            Icon(icon, color: VoxiaColors.cyan, size: 30),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: VoxiaColors.text,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0,
                ),
              ),
            ),
            Text(
              count,
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
