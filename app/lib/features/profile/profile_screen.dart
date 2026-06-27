import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/design_system/design_system.dart';
import '../../core/router/router.dart';
import '../auth/auth.dart';
import '../onboarding/onboarding.dart';

final class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final setup = context.watch<SetupCubit>().state;
    final displayName = setup.nickname.isEmpty
        ? 'Your profile'
        : setup.nickname;
    final speakingStyle = _labelForStyle(setup.speakingStyle);
    final memorySummary = setup.memoryEnabled ? 'Enabled' : 'Disabled';

    return VoxiaScaffold(
      child: VoxiaScrollPage(
        title: 'Profile',
        leading: _BackToTalkButton(onPressed: context.pop),
        slivers: [
          const SizedBox(height: AppSpacing.sm),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Flexible(
                flex: 2,
                child: AspectRatio(
                  aspectRatio: 1,
                  child: Container(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: VoxiaColors.accentGradient,
                    ),
                    padding: const EdgeInsets.all(4),
                    child: const CircleAvatar(
                      backgroundColor: VoxiaColors.backgroundAlt,
                      child: Icon(
                        Icons.person,
                        color: VoxiaColors.text,
                        size: 40,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                flex: 5,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      displayName,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: VoxiaColors.text,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      'Voice-first assistant profile',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: VoxiaColors.muted,
                        letterSpacing: 0,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Wrap(
                      spacing: AppSpacing.sm,
                      runSpacing: AppSpacing.xs,
                      children: [
                        _StatusBadge(
                          icon: Icons.tune_rounded,
                          label: speakingStyle,
                          color: VoxiaColors.cyan,
                        ),
                        _StatusBadge(
                          icon: setup.memoryEnabled
                              ? Icons.psychology_outlined
                              : Icons.hide_source,
                          label: 'Memory $memorySummary',
                          color: setup.memoryEnabled
                              ? VoxiaColors.violet
                              : VoxiaColors.muted,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          _SectionLabel('ACCOUNT'),
          _ProfileTile(
            icon: Icons.person_outline,
            title: 'Personalization',
            subtitle: speakingStyle,
            onTap: () => context.push(AppRoutes.profilePersonalization),
          ),
          _ProfileTile(
            icon: Icons.graphic_eq,
            title: 'Voice settings',
            subtitle: 'Choose how Voxia sounds',
            onTap: () => context.push(AppRoutes.voiceSettings),
          ),
          _ProfileTile(
            icon: Icons.psychology_outlined,
            title: 'Memory',
            subtitle: memorySummary,
            onTap: () => context.push(AppRoutes.memory),
          ),
          const SizedBox(height: AppSpacing.md),
          _SectionLabel('APP'),
          const _InfoPanel(),
          const SizedBox(height: AppSpacing.md),
          VoxiaOutlineButton(
            icon: Icons.logout,
            label: 'Sign out',
            onPressed: () => context.read<AuthCubit>().logout(),
          ),
          const SizedBox(height: AppSpacing.sm),
          TextButton(
            onPressed: context.read<SetupCubit>().reset,
            child: const Text('Reset setup'),
          ),
        ],
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

final class _StatusBadge extends StatelessWidget {
  const _StatusBadge({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        borderRadius: AppRadius.borderSm,
        border: Border.all(color: color),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: AppSpacing.xs),
          Text(label, style: TextStyle(color: color)),
        ],
      ),
    );
  }
}

final class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
          color: VoxiaColors.muted,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.8,
        ),
      ),
    );
  }
}

final class _ProfileTile extends StatelessWidget {
  const _ProfileTile({
    required this.icon,
    required this.title,
    this.subtitle,
    this.onTap,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: VoxiaGlassPanel(
        onTap: onTap,
        child: Row(
          children: [
            Icon(icon, color: VoxiaColors.cyan, size: 28),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: VoxiaColors.text,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0,
                    ),
                  ),
                  if (subtitle != null) ...[
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      subtitle!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: VoxiaColors.muted,
                        letterSpacing: 0,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: VoxiaColors.muted),
          ],
        ),
      ),
    );
  }
}

final class _InfoPanel extends StatelessWidget {
  const _InfoPanel();

  @override
  Widget build(BuildContext context) {
    return VoxiaGlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'About Voxia',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: VoxiaColors.text,
              fontWeight: FontWeight.w700,
              letterSpacing: 0,
            ),
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'A voice-first assistant focused on quick setup, memory-aware conversations, and customizable replies.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: VoxiaColors.muted,
              letterSpacing: 0,
            ),
          ),
        ],
      ),
    );
  }
}

String _labelForStyle(SpeakingStyle style) {
  return switch (style) {
    SpeakingStyle.shortAnswers => 'Short answers',
    SpeakingStyle.detailedAnswers => 'Detailed answers',
    SpeakingStyle.casual => 'Casual',
    SpeakingStyle.professional => 'Professional',
  };
}
