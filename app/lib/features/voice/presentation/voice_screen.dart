import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/design_system/design_system.dart';
import '../../../core/di/get_it.dart';
import '../../../shared/i18n/i18n.dart';
import 'voice_capture_cubit.dart';
import 'voice_capture_state.dart';

final class VoiceScreen extends StatelessWidget {
  const VoiceScreen({super.key, this.cubit, this.isShellMode = false});

  final VoiceCaptureCubit? cubit;
  final bool isShellMode;

  @override
  Widget build(BuildContext context) {
    final content = BlocProvider(
      create: (_) => cubit ?? getIt<VoiceCaptureCubit>(),
      child: const _TalkContent(),
    );

    if (isShellMode) {
      return content;
    }

    return VoxiaScaffold(child: content);
  }
}

final class _TalkContent extends StatelessWidget {
  const _TalkContent();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<VoiceCaptureCubit, VoiceCaptureState>(
      builder: (context, state) {
        final cubit = context.read<VoiceCaptureCubit>();
        final isRecording = state.status == VoiceCaptureStatus.recording;
        final isBusy =
            state.status == VoiceCaptureStatus.uploading ||
            state.status == VoiceCaptureStatus.processing ||
            state.status == VoiceCaptureStatus.speaking;

        return VoxiaFixedPage(
          body: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(),
              _PrimaryVisualizer(status: state.status),
              const SizedBox(height: AppSpacing.xl),
              _MicButton(
                isRecording: isRecording,
                isBusy: isBusy,
                hasPermanentMicFailure:
                    state.failure ==
                    VoiceCaptureFailure.microphonePermanentlyDenied,
                onPressed: () {
                  if (state.failure ==
                      VoiceCaptureFailure.microphonePermanentlyDenied) {
                    cubit.openSettings();
                    return;
                  }
                  if (isBusy) {
                    cubit.cancelRequest();
                    return;
                  }
                  cubit.toggleRecording();
                },
              ),
              const Spacer(),
            ],
          ),
        );
      },
    );
  }
}

final class _PrimaryVisualizer extends StatelessWidget {
  const _PrimaryVisualizer({required this.status});

  final VoiceCaptureStatus status;

  @override
  Widget build(BuildContext context) {
    return _BreathingOrb(status: status);
  }
}

final class _MicButton extends StatelessWidget {
  const _MicButton({
    required this.isRecording,
    required this.isBusy,
    required this.hasPermanentMicFailure,
    required this.onPressed,
  });

  final bool isRecording;
  final bool isBusy;
  final bool hasPermanentMicFailure;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final icon = switch ((isRecording, isBusy, hasPermanentMicFailure)) {
      (_, _, true) => Icons.settings_outlined,
      (true, _, _) => Icons.stop,
      (_, true, _) => Icons.close,
      _ => Icons.mic,
    };

    return Semantics(
      button: true,
      label: _semanticLabel(context),
      child: GestureDetector(
        onTap: onPressed,
        child: Container(
          width: 116,
          height: 116,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const SweepGradient(
              colors: [
                Color(0xFF4285F4),
                Color(0xFF34A853),
                Color(0xFFFBBC05),
                Color(0xFFEA4335),
                Color(0xFF4285F4),
              ],
            ),
            boxShadow: [
              BoxShadow(
                color: VoxiaColors.cyan.withValues(alpha: 0.24),
                blurRadius: 28,
                spreadRadius: 2,
              ),
            ],
          ),
          padding: const EdgeInsets.all(6),
          child: Container(
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: VoxiaColors.background,
            ),
            child: Icon(icon, color: VoxiaColors.text, size: 46),
          ),
        ),
      ),
    );
  }

  String _semanticLabel(BuildContext context) {
    if (hasPermanentMicFailure) {
      return context.l10n.voiceOpenSettings;
    }
    if (isBusy) {
      return context.l10n.voiceCancelRequest;
    }
    return isRecording
        ? context.l10n.voiceStopHint
        : context.l10n.voiceStartHint;
  }
}

final class _BreathingOrb extends StatefulWidget {
  const _BreathingOrb({required this.status});

  final VoiceCaptureStatus status;

  @override
  State<_BreathingOrb> createState() => _BreathingOrbState();
}

final class _BreathingOrbState extends State<_BreathingOrb>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: _durationFor(widget.status),
  )..repeat();

  @override
  void didUpdateWidget(covariant _BreathingOrb oldWidget) {
    super.didUpdateWidget(oldWidget);
    final duration = _durationFor(widget.status);
    if (_controller.duration != duration) {
      _controller.duration = duration;
      _controller.repeat();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final disabled = MediaQuery.disableAnimationsOf(context);
    return RepaintBoundary(
      child: SizedBox.square(
        dimension: 230,
        child: disabled
            ? CustomPaint(
                painter: _BreathingOrbPainter(
                  progress: 0.25,
                  status: widget.status,
                ),
              )
            : AnimatedBuilder(
                animation: _controller,
                builder: (context, child) {
                  return CustomPaint(
                    painter: _BreathingOrbPainter(
                      progress: _controller.value,
                      status: widget.status,
                    ),
                  );
                },
              ),
      ),
    );
  }

  Duration _durationFor(VoiceCaptureStatus status) {
    return switch (status) {
      VoiceCaptureStatus.recording => const Duration(milliseconds: 1350),
      VoiceCaptureStatus.uploading ||
      VoiceCaptureStatus.processing ||
      VoiceCaptureStatus.speaking => const Duration(milliseconds: 1100),
      _ => const Duration(milliseconds: 2400),
    };
  }
}

final class _BreathingOrbPainter extends CustomPainter {
  const _BreathingOrbPainter({required this.progress, required this.status});

  final double progress;
  final VoiceCaptureStatus status;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final pulse = (math.sin(progress * math.pi * 2) + 1) / 2;
    final active =
        status == VoiceCaptureStatus.recording ||
        status == VoiceCaptureStatus.uploading ||
        status == VoiceCaptureStatus.processing ||
        status == VoiceCaptureStatus.speaking;
    final failure = status == VoiceCaptureStatus.failure;
    final baseRadius = size.shortestSide * (active ? 0.25 : 0.23);
    final radius = baseRadius + (active ? pulse * 9 : pulse * 6);
    final palette = failure
        ? const [Color(0xFFEA4335), Color(0xFFFF7A70), Color(0xFFEA4335)]
        : const [
            Color(0xFF4285F4),
            Color(0xFF34A853),
            Color(0xFFFBBC05),
            Color(0xFFEA4335),
            Color(0xFF4285F4),
          ];
    final rect = Rect.fromCircle(center: center, radius: radius * 1.35);

    for (var i = 3; i >= 1; i -= 1) {
      final glowRadius = radius * (1.25 + i * 0.26 + pulse * 0.08);
      final glowPaint = Paint()
        ..color = (failure ? VoxiaColors.red : VoxiaColors.cyan).withValues(
          alpha: 0.035 * i,
        );
      canvas.drawCircle(center, glowRadius, glowPaint);
    }

    for (var i = 0; i < 4; i += 1) {
      final angle = progress * math.pi * 2 + i * math.pi / 2;
      final offset = Offset(math.cos(angle), math.sin(angle)) * radius * 0.38;
      final paint = Paint()
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 16)
        ..shader =
            RadialGradient(
              colors: [
                palette[i % palette.length].withValues(alpha: 0.9),
                palette[(i + 1) % palette.length].withValues(alpha: 0.2),
              ],
            ).createShader(
              Rect.fromCircle(center: center + offset, radius: radius * 0.9),
            );
      canvas.drawCircle(center + offset, radius * (0.62 + pulse * 0.05), paint);
    }

    final fillPaint = Paint()
      ..shader = RadialGradient(
        colors: [
          Colors.white.withValues(alpha: 0.94),
          palette[0].withValues(alpha: 0.72),
          palette[1].withValues(alpha: 0.42),
        ],
      ).createShader(Rect.fromCircle(center: center, radius: radius * 1.1));
    canvas.drawCircle(center, radius * 0.82, fillPaint);

    final ringPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = active ? 5 : 4
      ..shader = SweepGradient(
        colors: palette,
        transform: GradientRotation(progress * math.pi * 2),
      ).createShader(rect);
    canvas.drawCircle(center, radius * 1.12, ringPaint);

    final innerPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..color = Colors.white.withValues(alpha: 0.42);
    canvas.drawCircle(center, radius * 0.55, innerPaint);
  }

  @override
  bool shouldRepaint(covariant _BreathingOrbPainter oldDelegate) {
    return oldDelegate.progress != progress || oldDelegate.status != status;
  }
}
