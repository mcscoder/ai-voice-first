import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../core/design_system/design_system.dart';
import '../auth/auth.dart';
import '../onboarding/onboarding.dart';
import '../voice/voice.dart';

final class MainShell extends StatefulWidget {
  const MainShell({super.key, this.voiceCubit});

  final VoiceCaptureCubit? voiceCubit;

  @override
  State<MainShell> createState() => _MainShellState();
}

final class _MainShellState extends State<MainShell> {
  var _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      VoiceScreen(cubit: widget.voiceCubit, isShellMode: true),
      const _HistoryScreen(),
      const _MemoryScreen(),
      const _ProfileScreen(),
    ];

    return VoxiaScaffold(
      safeArea: false,
      bottomNavigationBar: VoxiaTabBar(
        currentIndex: _currentIndex,
        onChanged: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
      ),
      child: IndexedStack(
        index: _currentIndex,
        children: [
          for (var index = 0; index < pages.length; index += 1)
            TickerMode(enabled: index == _currentIndex, child: pages[index]),
        ],
      ),
    );
  }
}

final class _HistoryScreen extends StatelessWidget {
  const _HistoryScreen();

  @override
  Widget build(BuildContext context) {
    return VoxiaScrollPage(
      title: 'History',
      subtitle: 'Recent conversations',
      slivers: [
        const SizedBox(height: AppSpacing.sm),
        const _SummaryCard(
          icon: Icons.track_changes,
          title: 'Main topic',
          subtitle: 'Project planning and next steps',
        ),
        const SizedBox(height: AppSpacing.sm),
        const _SummaryCard(
          icon: Icons.star_border,
          title: 'Key takeaways',
          subtitle: '3 key points discussed',
        ),
        const SizedBox(height: AppSpacing.sm),
        const _SummaryCard(
          icon: Icons.arrow_forward,
          title: 'Suggested next action',
          subtitle: 'Review timeline and assign tasks',
        ),
        const SizedBox(height: AppSpacing.sm),
        VoxiaGradientButton(label: 'Continue talking', onPressed: () {}),
        const SizedBox(height: AppSpacing.sm),
        VoxiaOutlineButton(label: 'Save summary', onPressed: () {}),
        const SizedBox(height: AppSpacing.sm),
        VoxiaOutlineButton(
          label: 'Delete session',
          foregroundColor: VoxiaColors.red,
          onPressed: () {},
        ),
      ],
    );
  }
}

final class _MemoryScreen extends StatelessWidget {
  const _MemoryScreen();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<SetupCubit, SetupState>(
      builder: (context, setup) {
        return VoxiaScrollPage(
          title: 'Memory',
          subtitle: setup.memoryEnabled
              ? 'Memory is enabled'
              : 'Memory is disabled',
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
        );
      },
    );
  }
}

final class _ProfileScreen extends StatelessWidget {
  const _ProfileScreen();

  @override
  Widget build(BuildContext context) {
    final setup = context.watch<SetupCubit>().state;
    final displayName = setup.nickname.isEmpty ? 'Alex Morgan' : setup.nickname;

    return VoxiaScrollPage(
      title: 'Profile',
      leading: IconButton(
        tooltip: 'Menu',
        onPressed: () {},
        icon: const Icon(Icons.menu),
      ),
      trailing: const _ProChip(),
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
    );
  }
}

final class _SummaryCard extends StatelessWidget {
  const _SummaryCard({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return VoxiaGlassPanel(
      child: Row(
        children: [
          _CircleIcon(icon: icon),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: _TitleSubtitle(title: title, subtitle: subtitle),
          ),
        ],
      ),
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

final class _TitleSubtitle extends StatelessWidget {
  const _TitleSubtitle({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            color: VoxiaColors.text,
            fontWeight: FontWeight.w800,
            letterSpacing: 0,
          ),
        ),
        const SizedBox(height: AppSpacing.xs),
        Text(
          subtitle,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: VoxiaColors.muted,
            letterSpacing: 0,
          ),
        ),
      ],
    );
  }
}

final class _CircleIcon extends StatelessWidget {
  const _CircleIcon({required this.icon});

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 52,
      height: 52,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: VoxiaColors.violet.withValues(alpha: 0.14),
        border: Border.all(color: VoxiaColors.blue.withValues(alpha: 0.42)),
      ),
      child: Icon(icon, color: VoxiaColors.violet, size: 28),
    );
  }
}

final class _ProChip extends StatelessWidget {
  const _ProChip();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        borderRadius: AppRadius.borderFull,
        border: Border.all(color: VoxiaColors.violet),
        color: VoxiaColors.violet.withValues(alpha: 0.12),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.star, color: VoxiaColors.violet, size: 18),
          SizedBox(width: AppSpacing.xs),
          Text('Pro', style: TextStyle(color: VoxiaColors.text)),
        ],
      ),
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
