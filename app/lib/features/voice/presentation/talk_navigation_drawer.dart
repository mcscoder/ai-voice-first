import 'dart:math' as math;
import 'dart:ui';

import 'package:flutter/material.dart';

import '../../../core/design_system/design_system.dart';

final class TalkNavigationDrawer extends StatelessWidget {
  const TalkNavigationDrawer({
    super.key,
    required this.onOpenMemory,
    required this.onOpenProfile,
  });

  final VoidCallback onOpenMemory;
  final VoidCallback onOpenProfile;

  @override
  Widget build(BuildContext context) {
    final drawerWidth = math.min(
      MediaQuery.sizeOf(context).width * 0.76,
      390.0,
    );

    return Drawer(
      width: drawerWidth,
      backgroundColor: Colors.transparent,
      elevation: 0,
      child: ClipRRect(
        borderRadius: const BorderRadius.horizontal(
          left: Radius.circular(AppSpacing.md),
        ),
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
                    _NavigationDrawerItem(
                      icon: Icons.psychology_outlined,
                      label: 'Memory',
                      onTap: () => _closeDrawerThen(context, onOpenMemory),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    _NavigationDrawerItem(
                      icon: Icons.person_outline,
                      label: 'Profile',
                      onTap: () => _closeDrawerThen(context, onOpenProfile),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _closeDrawerThen(BuildContext context, VoidCallback action) {
    Navigator.of(context).pop();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      action();
    });
  }
}

final class TalkMenuButton extends StatelessWidget {
  const TalkMenuButton({super.key});

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

final class _NavigationDrawerItem extends StatelessWidget {
  const _NavigationDrawerItem({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
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
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.md,
            vertical: AppSpacing.md,
          ),
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
              DecoratedBox(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: VoxiaColors.cyan.withValues(alpha: 0.14),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.sm),
                  child: Icon(
                    icon,
                    color: VoxiaColors.cyan.withValues(alpha: 0.95),
                    size: 24,
                  ),
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                child: Text(
                  label,
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
        DecoratedBox(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: VoxiaColors.panel.withValues(alpha: 0.56),
            border: Border.all(color: VoxiaColors.text.withValues(alpha: 0.08)),
          ),
          child: const Padding(
            padding: EdgeInsets.all(AppSpacing.md),
            child: Icon(Icons.graphic_eq, color: VoxiaColors.cyan, size: 28),
          ),
        ),
        const SizedBox(width: AppSpacing.md),
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
