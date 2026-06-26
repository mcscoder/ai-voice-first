import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/design_system/design_system.dart';
import '../auth/auth.dart';
import '../onboarding/onboarding.dart';

final class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final setup = context.watch<SetupCubit>().state;
    final displayName = setup.nickname.isEmpty ? 'Alex Morgan' : setup.nickname;

    return VoxiaScaffold(
      child: VoxiaScrollPage(
        title: 'Profile',
        leading: _BackToTalkButton(onPressed: context.pop),
        slivers: [
          const SizedBox(height: AppSpacing.sm),
          Row(
            children: [
              Container(
                width: 88,
                height: 88,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: VoxiaColors.accentGradient,
                ),
                padding: const EdgeInsets.all(4),
                child: const CircleAvatar(
                  backgroundColor: VoxiaColors.backgroundAlt,
                  child: Icon(Icons.person, color: VoxiaColors.text, size: 40),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
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
                      'alex.morgan@email.com',
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: VoxiaColors.muted,
                        letterSpacing: 0,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    const _PlanBadge(),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          _SectionLabel('ACCOUNT'),
          const _ProfileTile(
            icon: Icons.person_outline,
            title: 'Personalization',
          ),
          const _ProfileTile(icon: Icons.graphic_eq, title: 'Voice settings'),
          const _ProfileTile(
            icon: Icons.verified_user_outlined,
            title: 'Privacy',
          ),
          const _ProfileTile(
            icon: Icons.notifications_none,
            title: 'Notifications',
          ),
          const _ProfileTile(icon: Icons.help_outline, title: 'Help & Support'),
          const _ProfileTile(icon: Icons.info_outline, title: 'About Voxia'),
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

final class _PlanBadge extends StatelessWidget {
  const _PlanBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        borderRadius: AppRadius.borderSm,
        border: Border.all(color: VoxiaColors.violet),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.workspace_premium, color: VoxiaColors.violet, size: 18),
          SizedBox(width: AppSpacing.xs),
          Text('Pro Plan', style: TextStyle(color: VoxiaColors.violet)),
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
  const _ProfileTile({required this.icon, required this.title});

  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: VoxiaGlassPanel(
        child: Row(
          children: [
            Icon(icon, color: VoxiaColors.cyan, size: 28),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: VoxiaColors.text,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0,
                ),
              ),
            ),
            const Icon(Icons.chevron_right, color: VoxiaColors.muted),
          ],
        ),
      ),
    );
  }
}
