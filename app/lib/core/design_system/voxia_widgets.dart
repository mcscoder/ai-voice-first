import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'app_radius.dart';
import 'app_spacing.dart';

abstract final class VoxiaColors {
  static const Color background = Color(0xFF020714);
  static const Color backgroundAlt = Color(0xFF061225);
  static const Color panel = Color(0x99101B2D);
  static const Color panelStrong = Color(0xCC101B2D);
  static const Color border = Color(0xFF253148);
  static const Color text = Color(0xFFF7F8FF);
  static const Color muted = Color(0xFFB4B8C3);
  static const Color cyan = Color(0xFF20B8FF);
  static const Color blue = Color(0xFF2477FF);
  static const Color violet = Color(0xFFA33DFF);
  static const Color red = Color(0xFFFF4D5D);

  static const LinearGradient accentGradient = LinearGradient(
    colors: [cyan, blue, violet],
  );
}

final class VoxiaScaffold extends StatelessWidget {
  const VoxiaScaffold({
    required this.child,
    super.key,
    this.bottomNavigationBar,
    this.endDrawer,
    this.safeArea = true,
  });

  final Widget child;
  final Widget? bottomNavigationBar;
  final Widget? endDrawer;
  final bool safeArea;

  @override
  Widget build(BuildContext context) {
    final content = ColoredBox(
      color: VoxiaColors.background,
      child: safeArea ? SafeArea(child: child) : child,
    );

    return Scaffold(
      backgroundColor: VoxiaColors.background,
      body: content,
      bottomNavigationBar: bottomNavigationBar,
      endDrawer: endDrawer,
    );
  }
}

final class VoxiaGradientButton extends StatelessWidget {
  const VoxiaGradientButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.icon,
    this.isBusy = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isBusy;

  @override
  Widget build(BuildContext context) {
    final textStyle = Theme.of(context).textTheme.titleMedium?.copyWith(
      color: VoxiaColors.text,
      fontWeight: FontWeight.w700,
      letterSpacing: 0,
    );

    return DecoratedBox(
      decoration: const BoxDecoration(
        color: VoxiaColors.cyan,
        borderRadius: AppRadius.borderFull,
      ),
      child: FilledButton(
        onPressed: isBusy ? null : onPressed,
        style: FilledButton.styleFrom(
          backgroundColor: Colors.transparent,
          disabledBackgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          minimumSize: const Size.fromHeight(48),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.borderFull,
          ),
        ),
        child: isBusy
            ? const SizedBox.square(
                dimension: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (icon != null) ...[
                    Icon(icon, color: VoxiaColors.text),
                    const SizedBox(width: AppSpacing.sm),
                  ],
                  Text(label, style: textStyle),
                ],
              ),
      ),
    );
  }
}

final class VoxiaOutlineButton extends StatelessWidget {
  const VoxiaOutlineButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.icon,
    this.foregroundColor = VoxiaColors.text,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final Color foregroundColor;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: onPressed,
      style: OutlinedButton.styleFrom(
        foregroundColor: foregroundColor,
        side: BorderSide(color: foregroundColor.withValues(alpha: 0.28)),
        minimumSize: const Size.fromHeight(48),
        shape: const RoundedRectangleBorder(borderRadius: AppRadius.borderFull),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon),
            const SizedBox(width: AppSpacing.sm),
          ],
          Text(label),
        ],
      ),
    );
  }
}

final class VoxiaGlassPanel extends StatelessWidget {
  const VoxiaGlassPanel({
    required this.child,
    super.key,
    this.padding = const EdgeInsets.all(AppSpacing.md),
    this.isSelected = false,
    this.onTap,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final bool isSelected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final panel = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: isSelected ? VoxiaColors.panelStrong : VoxiaColors.panel,
        borderRadius: AppRadius.borderXl,
        border: Border.all(
          color: isSelected ? VoxiaColors.cyan : VoxiaColors.border,
        ),
      ),
      child: child,
    );

    if (onTap == null) {
      return panel;
    }

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: AppRadius.borderXl,
        child: panel,
      ),
    );
  }
}

final class VoxiaMark extends StatelessWidget {
  const VoxiaMark({super.key, this.size = 64, this.showRing = false});

  final double size;
  final bool showRing;

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: SizedBox.square(
        dimension: size,
        child: CustomPaint(painter: _VoxiaMarkPainter(showRing: showRing)),
      ),
    );
  }
}

final class VoxiaOrb extends StatefulWidget {
  const VoxiaOrb({
    super.key,
    this.size = 230,
    this.mode = VoxiaOrbMode.idle,
    this.isAnimated = false,
  });

  final double size;
  final VoxiaOrbMode mode;
  final bool isAnimated;

  @override
  State<VoxiaOrb> createState() => _VoxiaOrbState();
}

enum VoxiaOrbMode { idle, listening, speaking }

final class _VoxiaOrbState extends State<VoxiaOrb>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1800),
  );

  @override
  void initState() {
    super.initState();
    _syncAnimation();
  }

  @override
  void didUpdateWidget(covariant VoxiaOrb oldWidget) {
    super.didUpdateWidget(oldWidget);
    _syncAnimation();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final disabled = MediaQuery.disableAnimationsOf(context);
    final shouldAnimate = widget.isAnimated && !disabled;
    return RepaintBoundary(
      child: SizedBox.square(
        dimension: widget.size,
        child: shouldAnimate
            ? AnimatedBuilder(
                animation: _controller,
                builder: (context, child) {
                  return CustomPaint(
                    painter: _VoxiaOrbPainter(
                      progress: _controller.value,
                      mode: widget.mode,
                      isAnimated: true,
                    ),
                  );
                },
              )
            : CustomPaint(
                painter: _VoxiaOrbPainter(
                  progress: 0.2,
                  mode: widget.mode,
                  isAnimated: false,
                ),
              ),
      ),
    );
  }

  void _syncAnimation() {
    if (widget.isAnimated && !_controller.isAnimating) {
      _controller.repeat();
      return;
    }
    if (!widget.isAnimated && _controller.isAnimating) {
      _controller.stop();
    }
  }
}

final class VoxiaWaveform extends StatefulWidget {
  const VoxiaWaveform({
    super.key,
    this.height = 180,
    this.mode = VoxiaWaveformMode.compact,
    this.isAnimated = false,
  });

  final double height;
  final VoxiaWaveformMode mode;
  final bool isAnimated;

  @override
  State<VoxiaWaveform> createState() => _VoxiaWaveformState();
}

enum VoxiaWaveformMode { compact, listening }

final class _VoxiaWaveformState extends State<VoxiaWaveform>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1100),
  );

  @override
  void initState() {
    super.initState();
    _syncAnimation();
  }

  @override
  void didUpdateWidget(covariant VoxiaWaveform oldWidget) {
    super.didUpdateWidget(oldWidget);
    _syncAnimation();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final disabled = MediaQuery.disableAnimationsOf(context);
    final shouldAnimate = widget.isAnimated && !disabled;
    return RepaintBoundary(
      child: SizedBox(
        height: widget.height,
        width: double.infinity,
        child: shouldAnimate
            ? AnimatedBuilder(
                animation: _controller,
                builder: (context, child) {
                  return CustomPaint(
                    painter: _VoxiaWaveformPainter(
                      progress: _controller.value,
                      mode: widget.mode,
                    ),
                  );
                },
              )
            : CustomPaint(
                painter: _VoxiaWaveformPainter(
                  progress: 0.4,
                  mode: widget.mode,
                ),
              ),
      ),
    );
  }

  void _syncAnimation() {
    if (widget.isAnimated && !_controller.isAnimating) {
      _controller.repeat();
      return;
    }
    if (!widget.isAnimated && _controller.isAnimating) {
      _controller.stop();
    }
  }
}

final class VoxiaScreenHeader extends StatelessWidget {
  const VoxiaScreenHeader({
    required this.title,
    super.key,
    this.subtitle,
    this.icon,
  });

  final String title;
  final String? subtitle;
  final Widget? icon;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        if (icon != null) ...[icon!, const SizedBox(height: AppSpacing.sm)],
        Text(
          title,
          textAlign: TextAlign.center,
          style: theme.textTheme.headlineSmall?.copyWith(
            color: VoxiaColors.text,
            fontWeight: FontWeight.w800,
            letterSpacing: 0,
            height: 1.08,
          ),
        ),
        if (subtitle != null) ...[
          const SizedBox(height: AppSpacing.sm),
          Text(
            subtitle!,
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: VoxiaColors.muted,
              height: 1.45,
              letterSpacing: 0,
            ),
          ),
        ],
      ],
    );
  }
}

final class VoxiaFixedPage extends StatelessWidget {
  const VoxiaFixedPage({
    required this.body,
    super.key,
    this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.padding = const EdgeInsets.symmetric(horizontal: AppSpacing.md),
    this.maxWidth = 430,
  });

  final Widget body;
  final String? title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final EdgeInsetsGeometry padding;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: SafeArea(
          child: Padding(
            padding: padding,
            child: Column(
              children: [
                if (_hasHeader)
                  VoxiaPageHeader(
                    title: title,
                    subtitle: subtitle,
                    leading: leading,
                    trailing: trailing,
                  ),
                Expanded(child: body),
              ],
            ),
          ),
        ),
      ),
    );
  }

  bool get _hasHeader =>
      title != null || subtitle != null || leading != null || trailing != null;
}

final class VoxiaScrollPage extends StatelessWidget {
  const VoxiaScrollPage({
    required this.slivers,
    super.key,
    this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.padding = const EdgeInsets.symmetric(horizontal: AppSpacing.md),
    this.maxWidth = 430,
  });

  final List<Widget> slivers;
  final String? title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final EdgeInsetsGeometry padding;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: SafeArea(
          child: Padding(
            padding: padding,
            child: Column(
              children: [
                if (_hasHeader)
                  VoxiaPageHeader(
                    title: title,
                    subtitle: subtitle,
                    leading: leading,
                    trailing: trailing,
                  ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                    children: slivers,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  bool get _hasHeader =>
      title != null || subtitle != null || leading != null || trailing != null;
}

final class VoxiaPageHeader extends StatelessWidget {
  const VoxiaPageHeader({
    super.key,
    this.title,
    this.subtitle,
    this.leading,
    this.trailing,
  });

  final String? title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final hasTitle = title != null || subtitle != null;
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: hasTitle
          ? Stack(
              alignment: Alignment.center,
              children: [
                Center(
                  child: _PageHeaderTitle(title: title, subtitle: subtitle),
                ),
                ?_alignedHeaderAction(Alignment.centerLeft, leading),
                ?_alignedHeaderAction(Alignment.centerRight, trailing),
              ],
            )
          : Row(children: [?leading, const Spacer(), ?trailing]),
    );
  }
}

Widget? _alignedHeaderAction(Alignment alignment, Widget? child) {
  if (child == null) {
    return null;
  }
  return Align(alignment: alignment, child: child);
}

final class _PageHeaderTitle extends StatelessWidget {
  const _PageHeaderTitle({required this.title, required this.subtitle});

  final String? title;
  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (title != null)
            Text(
              title!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: theme.textTheme.titleLarge?.copyWith(
                color: VoxiaColors.text,
                fontWeight: FontWeight.w800,
                letterSpacing: 0,
              ),
            ),
          if (subtitle != null)
            Text(
              subtitle!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall?.copyWith(
                color: VoxiaColors.muted,
                letterSpacing: 0,
              ),
            ),
        ],
      ),
    );
  }
}

final class VoxiaTabBar extends StatelessWidget {
  const VoxiaTabBar({
    required this.currentIndex,
    required this.onChanged,
    super.key,
  });

  final int currentIndex;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    final items = <_VoxiaTabItem>[
      const _VoxiaTabItem(Icons.mic_none, 'Talk'),
      const _VoxiaTabItem(Icons.psychology_outlined, 'Memory'),
      const _VoxiaTabItem(Icons.person_outline, 'Profile'),
    ];

    return DecoratedBox(
      decoration: BoxDecoration(
        color: VoxiaColors.background.withValues(alpha: 0.96),
        border: Border(
          top: BorderSide(color: VoxiaColors.border.withValues(alpha: 0.62)),
        ),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 78,
          child: Row(
            children: [
              for (var i = 0; i < items.length; i += 1)
                Expanded(
                  child: _VoxiaTabButton(
                    item: items[i],
                    isSelected: i == currentIndex,
                    onTap: () => onChanged(i),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

final class _VoxiaTabItem {
  const _VoxiaTabItem(this.icon, this.label);

  final IconData icon;
  final String label;
}

final class _VoxiaTabButton extends StatelessWidget {
  const _VoxiaTabButton({
    required this.item,
    required this.isSelected,
    required this.onTap,
  });

  final _VoxiaTabItem item;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = isSelected ? VoxiaColors.cyan : VoxiaColors.muted;
    return InkWell(
      onTap: onTap,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(item.icon, color: color, size: 28),
          const SizedBox(height: AppSpacing.xs),
          Text(
            item.label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.w600,
              letterSpacing: 0,
            ),
          ),
          const SizedBox(height: AppSpacing.xs),
          AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            width: isSelected ? 6 : 0,
            height: 6,
            decoration: const BoxDecoration(
              color: VoxiaColors.cyan,
              shape: BoxShape.circle,
            ),
          ),
        ],
      ),
    );
  }
}

final class _VoxiaMarkPainter extends CustomPainter {
  const _VoxiaMarkPainter({required this.showRing});

  final bool showRing;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final gradient = VoxiaColors.accentGradient.createShader(
      Rect.fromLTWH(0, 0, size.width, size.height),
    );
    if (showRing) {
      final ringPaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = size.width * 0.035
        ..shader = gradient;
      canvas.drawCircle(center, size.width * 0.42, ringPaint);
    }

    final paint = Paint()
      ..strokeCap = StrokeCap.round
      ..strokeWidth = math.max(size.width * 0.06, 3)
      ..shader = gradient;
    const values = <double>[0.22, 0.42, 0.62, 0.88, 0.62, 0.42, 0.22];
    final spacing = size.width / (values.length + 1);
    for (var i = 0; i < values.length; i += 1) {
      final x = spacing * (i + 1);
      final height = size.height * values[i];
      canvas.drawLine(
        Offset(x, center.dy - height / 2),
        Offset(x, center.dy + height / 2),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _VoxiaMarkPainter oldDelegate) {
    return oldDelegate.showRing != showRing;
  }
}

final class _VoxiaOrbPainter extends CustomPainter {
  const _VoxiaOrbPainter({
    required this.progress,
    required this.mode,
    required this.isAnimated,
  });

  final double progress;
  final VoxiaOrbMode mode;
  final bool isAnimated;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = size.shortestSide * 0.34;
    final pulse = math.sin(progress * math.pi * 2);
    final rect = Rect.fromCircle(center: center, radius: radius);
    final glowPaint = Paint()..color = VoxiaColors.cyan.withValues(alpha: 0.12);
    canvas.drawCircle(center, radius * (1.55 + pulse.abs() * 0.03), glowPaint);

    final ringPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4
      ..shader = isAnimated
          ? SweepGradient(
              colors: const [
                VoxiaColors.cyan,
                VoxiaColors.blue,
                VoxiaColors.violet,
                VoxiaColors.cyan,
              ],
              transform: GradientRotation(progress * math.pi * 2),
            ).createShader(rect)
          : VoxiaColors.accentGradient.createShader(rect);
    canvas.drawCircle(center, radius, ringPaint);

    final dotCount = isAnimated ? 18 : 24;
    for (var i = 0; i < dotCount; i += 1) {
      final angle = (math.pi * 2 / dotCount) * i;
      final dotRadius = radius * 1.32;
      final dotCenter = Offset(
        center.dx + math.cos(angle) * dotRadius,
        center.dy + math.sin(angle) * dotRadius,
      );
      final dotPaint = Paint()
        ..color = Color.lerp(
          VoxiaColors.cyan,
          VoxiaColors.violet,
          i / (dotCount - 1),
        )!.withValues(alpha: 0.52);
      canvas.drawCircle(dotCenter, 1.4, dotPaint);
    }

    if (mode == VoxiaOrbMode.speaking ||
        (!isAnimated && mode == VoxiaOrbMode.idle)) {
      final wavePaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5
        ..strokeCap = StrokeCap.round
        ..shader = VoxiaColors.accentGradient.createShader(
          Rect.fromLTWH(0, center.dy - 40, size.width, 80),
        );
      final path = Path();
      for (var x = 0.0; x <= size.width; x += 4) {
        final normalized = x / size.width;
        final y =
            center.dy +
            math.sin((normalized * math.pi * 4) + (progress * math.pi * 2)) *
                radius *
                0.16;
        if (x == 0) {
          path.moveTo(x, y);
        } else {
          path.lineTo(x, y);
        }
      }
      canvas.drawPath(path, wavePaint);
    }
  }

  @override
  bool shouldRepaint(covariant _VoxiaOrbPainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.mode != mode ||
        oldDelegate.isAnimated != isAnimated;
  }
}

final class _VoxiaWaveformPainter extends CustomPainter {
  const _VoxiaWaveformPainter({required this.progress, required this.mode});

  final double progress;
  final VoxiaWaveformMode mode;

  @override
  void paint(Canvas canvas, Size size) {
    final centerY = size.height / 2;
    final barCount = mode == VoxiaWaveformMode.listening ? 35 : 17;
    final maxHeight = mode == VoxiaWaveformMode.listening
        ? size.height * 0.82
        : size.height * 0.44;
    final paint = Paint()
      ..strokeCap = StrokeCap.round
      ..strokeWidth = mode == VoxiaWaveformMode.listening ? 5 : 4
      ..shader = VoxiaColors.accentGradient.createShader(
        Rect.fromLTWH(0, 0, size.width, size.height),
      );
    final spacing = size.width / (barCount + 1);

    for (var i = 0; i < barCount; i += 1) {
      final phase = (progress + i * 0.071) % 1;
      final falloff = 1 - ((i - (barCount - 1) / 2).abs() / (barCount / 2));
      final height =
          10 +
          (math.sin(phase * math.pi * 2).abs() * maxHeight * 0.34) +
          (maxHeight * falloff * 0.56);
      final x = spacing * (i + 1);
      canvas.drawLine(
        Offset(x, centerY - height / 2),
        Offset(x, centerY + height / 2),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _VoxiaWaveformPainter oldDelegate) {
    return oldDelegate.progress != progress || oldDelegate.mode != mode;
  }
}
