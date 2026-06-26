import 'dart:ui';

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
      _MemoryScreen(onBack: _returnHome),
      _ProfileScreen(onBack: _returnHome),
    ];

    return VoxiaScaffold(
      safeArea: false,
      endDrawer: _currentIndex == 0
          ? _NavigationSidebar(onChanged: _selectScreen)
          : null,
      child: Stack(
        children: [
          IndexedStack(
            index: _currentIndex,
            children: [
              for (var index = 0; index < pages.length; index += 1)
                TickerMode(
                  enabled: index == _currentIndex,
                  child: pages[index],
                ),
            ],
          ),
          if (_currentIndex == 0)
            const Positioned(
              top: AppSpacing.sm,
              right: AppSpacing.md,
              child: SafeArea(child: _MenuButton()),
            ),
        ],
      ),
    );
  }

  void _selectScreen(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  void _returnHome() {
    _selectScreen(0);
  }
}

final class _MenuButton extends StatelessWidget {
  const _MenuButton();

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Menu',
      onPressed: Scaffold.of(context).openEndDrawer,
      style: IconButton.styleFrom(
        backgroundColor: Colors.transparent,
        foregroundColor: VoxiaColors.text.withValues(alpha: 0.86),
        minimumSize: const Size.square(44),
        shape: const CircleBorder(),
      ),
      icon: const Icon(Icons.menu_rounded, size: 28),
    );
  }
}

final class _NavigationSidebar extends StatelessWidget {
  const _NavigationSidebar({required this.onChanged});

  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final drawerWidth = width * 0.76 > 390 ? 390.0 : width * 0.76;

    return Drawer(
      width: drawerWidth,
      backgroundColor: Colors.transparent,
      elevation: 0,
      child: ClipRRect(
        borderRadius: const BorderRadius.horizontal(left: Radius.circular(16)),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 22, sigmaY: 22),
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  VoxiaColors.backgroundAlt.withValues(alpha: 0.96),
                  VoxiaColors.background.withValues(alpha: 0.98),
                ],
              ),
              border: Border(
                left: BorderSide(
                  color: VoxiaColors.text.withValues(alpha: 0.12),
                ),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.42),
                  blurRadius: 42,
                  offset: const Offset(-18, 0),
                ),
              ],
            ),
            child: SafeArea(
              child: Column(
                children: [
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(
                        AppSpacing.md,
                        0,
                        AppSpacing.md,
                        AppSpacing.sm,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Padding(
                            padding: const EdgeInsets.only(top: AppSpacing.sm),
                            child: Align(
                              alignment: Alignment.centerRight,
                              child: _DrawerCloseButton(
                                onPressed: Navigator.of(context).pop,
                              ),
                            ),
                          ),
                          const SizedBox(height: AppSpacing.lg),
                          const _DrawerHeader(),
                          const SizedBox(height: AppSpacing.lg),
                          for (
                            var index = 1;
                            index < _navigationItems.length;
                            index += 1
                          ) ...[
                            _NavigationSidebarItem(
                              item: _navigationItems[index],
                              onTap: () {
                                Navigator.of(context).pop();
                                onChanged(index);
                              },
                            ),
                            if (index < _navigationItems.length - 1)
                              const SizedBox(height: AppSpacing.sm),
                          ],
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

final class _NavigationSidebarItem extends StatelessWidget {
  const _NavigationSidebarItem({required this.item, required this.onTap});

  final _NavigationItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      borderRadius: AppRadius.borderMd,
      child: InkWell(
        onTap: onTap,
        borderRadius: AppRadius.borderMd,
        child: Container(
          height: 70,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(
            borderRadius: AppRadius.borderMd,
            color: VoxiaColors.panelStrong.withValues(alpha: 0.74),
            border: Border.all(color: VoxiaColors.text.withValues(alpha: 0.06)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.18),
                blurRadius: 22,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                height: 46,
                width: 46,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: VoxiaColors.cyan.withValues(alpha: 0.14),
                ),
                child: Icon(
                  item.icon,
                  color: VoxiaColors.cyan.withValues(alpha: 0.95),
                  size: 24,
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                child: Text(
                  item.label,
                  style: TextStyle(
                    fontSize: 18,
                    height: 1,
                    color: VoxiaColors.text.withValues(alpha: 0.95),
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0,
                  ),
                ),
              ),
              Icon(
                Icons.chevron_right_rounded,
                color: VoxiaColors.muted.withValues(alpha: 0.82),
                size: 28,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

final class _DrawerHeader extends StatelessWidget {
  const _DrawerHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          height: 58,
          width: 58,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: VoxiaColors.panel.withValues(alpha: 0.56),
            border: Border.all(color: VoxiaColors.text.withValues(alpha: 0.08)),
          ),
          child: const Icon(
            Icons.graphic_eq,
            color: VoxiaColors.cyan,
            size: 28,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Hello!',
                style: const TextStyle(
                  fontSize: 19,
                  height: 1.05,
                  color: VoxiaColors.text,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0,
                ),
              ),
              const SizedBox(height: AppSpacing.xs),
              Text(
                'Welcome back',
                style: const TextStyle(
                  fontSize: 13,
                  height: 1.15,
                  color: VoxiaColors.muted,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

final class _DrawerCloseButton extends StatelessWidget {
  const _DrawerCloseButton({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Close',
      onPressed: onPressed,
      style: IconButton.styleFrom(
        backgroundColor: VoxiaColors.panelStrong.withValues(alpha: 0.82),
        foregroundColor: VoxiaColors.muted,
        minimumSize: const Size.square(44),
        shape: RoundedRectangleBorder(borderRadius: AppRadius.borderLg),
      ),
      icon: const Icon(Icons.close_rounded, size: 28),
    );
  }
}

const _navigationItems = <_NavigationItem>[
  _NavigationItem(Icons.mic_none, 'Talk'),
  _NavigationItem(Icons.psychology_outlined, 'Memory'),
  _NavigationItem(Icons.person_outline, 'Profile'),
];

final class _NavigationItem {
  const _NavigationItem(this.icon, this.label);

  final IconData icon;
  final String label;
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

final class _MemoryScreen extends StatelessWidget {
  const _MemoryScreen({required this.onBack});

  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<SetupCubit, SetupState>(
      builder: (context, setup) {
        return VoxiaScrollPage(
          title: 'Memory',
          subtitle: setup.memoryEnabled
              ? 'Memory is enabled'
              : 'Memory is disabled',
          leading: _BackToTalkButton(onPressed: onBack),
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
  const _ProfileScreen({required this.onBack});

  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final setup = context.watch<SetupCubit>().state;
    final displayName = setup.nickname.isEmpty ? 'Alex Morgan' : setup.nickname;

    return VoxiaScrollPage(
      title: 'Profile',
      leading: _BackToTalkButton(onPressed: onBack),
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
