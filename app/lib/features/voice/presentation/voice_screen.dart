import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/design_system/design_system.dart';
import '../../../core/di/get_it.dart';
import '../../../shared/i18n/i18n.dart';
import 'voice_capture_cubit.dart';
import 'voice_capture_state.dart';

final class VoiceScreen extends StatelessWidget {
  const VoiceScreen({super.key, this.cubit});

  final VoiceCaptureCubit? cubit;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return BlocProvider(
      create: (_) => cubit ?? getIt<VoiceCaptureCubit>(),
      child: Scaffold(
        backgroundColor: colorScheme.surface,
        body: SafeArea(
          child: BlocBuilder<VoiceCaptureCubit, VoiceCaptureState>(
            builder: (context, state) {
              final cubit = context.read<VoiceCaptureCubit>();
              final isRecording = state.status == VoiceCaptureStatus.recording;
              final isActionLocked =
                  state.status == VoiceCaptureStatus.uploading ||
                  state.status == VoiceCaptureStatus.processing ||
                  state.status == VoiceCaptureStatus.speaking;
              final canCancelRequest =
                  state.status == VoiceCaptureStatus.uploading ||
                  state.status == VoiceCaptureStatus.processing;

              return Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 420),
                  child: Padding(
                    padding: const EdgeInsets.all(AppSpacing.xl),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _VoiceOrbButton(
                          status: state.status,
                          isRecording: isRecording,
                          isDisabled: isActionLocked,
                          onPressed: cubit.toggleRecording,
                        ),
                        const SizedBox(height: AppSpacing.xl),
                        AnimatedSwitcher(
                          duration: const Duration(milliseconds: 180),
                          child: Text(
                            _statusText(context, state),
                            key: ValueKey(state.status),
                            textAlign: TextAlign.center,
                            style: theme.textTheme.titleMedium?.copyWith(
                              color: state.status == VoiceCaptureStatus.failure
                                  ? colorScheme.error
                                  : colorScheme.onSurfaceVariant,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0,
                            ),
                          ),
                        ),
                        if (canCancelRequest) ...[
                          const SizedBox(height: AppSpacing.sm),
                          _RequestElapsedTime(state: state),
                          const SizedBox(height: AppSpacing.md),
                          TextButton.icon(
                            onPressed: cubit.cancelRequest,
                            icon: const Icon(Icons.close),
                            label: Text(context.l10n.voiceCancelRequest),
                          ),
                        ],
                        if (state.failure ==
                            VoiceCaptureFailure
                                .microphonePermanentlyDenied) ...[
                          const SizedBox(height: AppSpacing.md),
                          TextButton.icon(
                            onPressed: cubit.openSettings,
                            icon: const Icon(Icons.settings_outlined),
                            label: Text(context.l10n.voiceOpenSettings),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  String _statusText(BuildContext context, VoiceCaptureState state) {
    switch (state.status) {
      case VoiceCaptureStatus.idle:
        return context.l10n.voiceIdleStatus;
      case VoiceCaptureStatus.recording:
        return context.l10n.voiceRecordingStatus;
      case VoiceCaptureStatus.uploading:
        return context.l10n.voiceUploadingStatus;
      case VoiceCaptureStatus.processing:
        return context.l10n.voiceProcessingStatus;
      case VoiceCaptureStatus.speaking:
        return context.l10n.voiceSpeakingStatus;
      case VoiceCaptureStatus.success:
        return context.l10n.voiceSuccessStatus;
      case VoiceCaptureStatus.failure:
        switch (state.failure) {
          case VoiceCaptureFailure.microphoneDenied:
            return context.l10n.voiceMicDeniedStatus;
          case VoiceCaptureFailure.microphonePermanentlyDenied:
            return context.l10n.voiceMicPermanentlyDeniedStatus;
          case VoiceCaptureFailure.network:
            return context.l10n.voiceNetworkErrorStatus;
          case VoiceCaptureFailure.badAudio:
            return context.l10n.voiceBadAudioStatus;
          case VoiceCaptureFailure.backend:
            return context.l10n.voiceBackendErrorStatus;
          case VoiceCaptureFailure.unknown:
          case null:
            return context.l10n.voiceUnknownErrorStatus;
        }
    }
  }
}

final class _RequestElapsedTime extends StatelessWidget {
  const _RequestElapsedTime({required this.state});

  final VoiceCaptureState state;

  @override
  Widget build(BuildContext context) {
    final startedAt = state.requestStartedAt;
    if (startedAt == null) {
      return const SizedBox.shrink();
    }

    final colorScheme = Theme.of(context).colorScheme;
    final textStyle = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: colorScheme.onSurfaceVariant,
      fontWeight: FontWeight.w600,
      letterSpacing: 0,
    );

    return StreamBuilder<int>(
      stream: Stream<int>.periodic(const Duration(seconds: 1), (tick) => tick),
      builder: (context, snapshot) {
        final elapsed = DateTime.now().difference(startedAt);
        return Text(_formatElapsed(elapsed), style: textStyle);
      },
    );
  }

  String _formatElapsed(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}

final class _VoiceOrbButton extends StatefulWidget {
  const _VoiceOrbButton({
    required this.status,
    required this.isRecording,
    required this.isDisabled,
    required this.onPressed,
  });

  final VoiceCaptureStatus status;
  final bool isRecording;
  final bool isDisabled;
  final VoidCallback onPressed;

  @override
  State<_VoiceOrbButton> createState() => _VoiceOrbButtonState();
}

final class _VoiceOrbButtonState extends State<_VoiceOrbButton>
    with TickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1800),
  );
  late final AnimationController _thinkingController = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1600),
  );

  @override
  void initState() {
    super.initState();
    if (_shouldAnimate) {
      _controller.repeat(reverse: true);
    }
    if (_isThinking) {
      _thinkingController.repeat();
    }
  }

  @override
  void didUpdateWidget(covariant _VoiceOrbButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_shouldAnimate && !_controller.isAnimating) {
      _controller.repeat(reverse: true);
    } else if (!_shouldAnimate && _controller.isAnimating) {
      _controller.stop();
      _controller.value = 0;
    }

    if (_isThinking && !_thinkingController.isAnimating) {
      _thinkingController.repeat();
    } else if (!_isThinking && _thinkingController.isAnimating) {
      _thinkingController.stop();
      _thinkingController.value = 0;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _thinkingController.dispose();
    super.dispose();
  }

  bool get _isThinking =>
      widget.status == VoiceCaptureStatus.uploading ||
      widget.status == VoiceCaptureStatus.processing;

  bool get _shouldAnimate =>
      widget.status == VoiceCaptureStatus.idle ||
      widget.status == VoiceCaptureStatus.recording ||
      widget.status == VoiceCaptureStatus.uploading ||
      widget.status == VoiceCaptureStatus.processing ||
      widget.status == VoiceCaptureStatus.speaking;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final animationsDisabled = MediaQuery.disableAnimationsOf(context);
    final visual = _VoiceOrbVisual.fromStatus(widget.status, colorScheme);
    final buttonColor = widget.isDisabled
        ? colorScheme.surfaceContainerHighest
        : visual.primaryColor;
    final animation = Listenable.merge([_controller, _thinkingController]);
    final semanticLabel = _semanticLabel(context);

    return Semantics(
      button: true,
      enabled: !widget.isDisabled,
      label: semanticLabel,
      child: AnimatedBuilder(
        animation: animation,
        builder: (context, child) {
          final motion = animationsDisabled ? 0.0 : _controller.value;
          final thinking = animationsDisabled ? 0.0 : _thinkingController.value;
          final scale = visual.scaleFor(motion);

          return Transform.scale(
            scale: scale,
            child: SizedBox(
              width: 214,
              height: 214,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Positioned.fill(
                    child: CustomPaint(
                      painter: _VoiceOrbPainter(
                        visual: visual,
                        motion: motion,
                        thinking: thinking,
                        isReducedMotion: animationsDisabled,
                      ),
                    ),
                  ),
                  SizedBox(
                    width: 156,
                    height: 156,
                    child: FilledButton(
                      onPressed: widget.isDisabled ? null : widget.onPressed,
                      style: FilledButton.styleFrom(
                        backgroundColor: buttonColor,
                        disabledBackgroundColor:
                            colorScheme.surfaceContainerHighest,
                        foregroundColor: colorScheme.onPrimary,
                        disabledForegroundColor: colorScheme.onSurfaceVariant,
                        shape: const CircleBorder(),
                        padding: EdgeInsets.zero,
                      ),
                      child: Icon(visual.icon, size: 62),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  String _semanticLabel(BuildContext context) {
    switch (widget.status) {
      case VoiceCaptureStatus.idle:
      case VoiceCaptureStatus.success:
      case VoiceCaptureStatus.failure:
        return context.l10n.voiceStartHint;
      case VoiceCaptureStatus.recording:
        return context.l10n.voiceStopHint;
      case VoiceCaptureStatus.uploading:
        return context.l10n.voiceUploadingStatus;
      case VoiceCaptureStatus.processing:
        return context.l10n.voiceProcessingStatus;
      case VoiceCaptureStatus.speaking:
        return context.l10n.voiceSpeakingStatus;
    }
  }
}

final class _VoiceOrbVisual {
  const _VoiceOrbVisual({
    required this.primaryColor,
    required this.secondaryColor,
    required this.glowColor,
    required this.icon,
    required this.mode,
  });

  final Color primaryColor;
  final Color secondaryColor;
  final Color glowColor;
  final IconData icon;
  final _VoiceOrbMode mode;

  factory _VoiceOrbVisual.fromStatus(
    VoiceCaptureStatus status,
    ColorScheme colorScheme,
  ) {
    switch (status) {
      case VoiceCaptureStatus.recording:
        return _VoiceOrbVisual(
          primaryColor: colorScheme.error,
          secondaryColor: colorScheme.errorContainer,
          glowColor: colorScheme.error,
          icon: Icons.stop,
          mode: _VoiceOrbMode.recording,
        );
      case VoiceCaptureStatus.uploading:
      case VoiceCaptureStatus.processing:
        return _VoiceOrbVisual(
          primaryColor: colorScheme.primary,
          secondaryColor: colorScheme.secondary,
          glowColor: colorScheme.primary,
          icon: Icons.hourglass_top,
          mode: _VoiceOrbMode.thinking,
        );
      case VoiceCaptureStatus.speaking:
        return _VoiceOrbVisual(
          primaryColor: colorScheme.secondary,
          secondaryColor: colorScheme.tertiary,
          glowColor: colorScheme.secondary,
          icon: Icons.graphic_eq,
          mode: _VoiceOrbMode.speaking,
        );
      case VoiceCaptureStatus.failure:
        return _VoiceOrbVisual(
          primaryColor: colorScheme.error,
          secondaryColor: colorScheme.errorContainer,
          glowColor: colorScheme.error,
          icon: Icons.mic,
          mode: _VoiceOrbMode.failure,
        );
      case VoiceCaptureStatus.idle:
      case VoiceCaptureStatus.success:
        return _VoiceOrbVisual(
          primaryColor: colorScheme.primary,
          secondaryColor: colorScheme.secondary,
          glowColor: colorScheme.primary,
          icon: Icons.mic,
          mode: _VoiceOrbMode.idle,
        );
    }
  }

  double scaleFor(double motion) {
    return switch (mode) {
      _VoiceOrbMode.recording => 1 + (motion * 0.08),
      _VoiceOrbMode.thinking => 1 + (math.sin(motion * math.pi) * 0.025),
      _VoiceOrbMode.speaking => 1 + (motion * 0.055),
      _VoiceOrbMode.idle => 1 + (math.sin(motion * math.pi) * 0.018),
      _VoiceOrbMode.failure => 1.0,
    };
  }
}

enum _VoiceOrbMode { idle, recording, thinking, speaking, failure }

final class _VoiceOrbPainter extends CustomPainter {
  const _VoiceOrbPainter({
    required this.visual,
    required this.motion,
    required this.thinking,
    required this.isReducedMotion,
  });

  final _VoiceOrbVisual visual;
  final double motion;
  final double thinking;
  final bool isReducedMotion;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final shortest = math.min(size.width, size.height);
    final baseRadius = shortest * 0.34;
    final pulse = isReducedMotion ? 0.0 : math.sin(motion * math.pi);

    _paintGlow(canvas, center, baseRadius, pulse);
    _paintHalo(canvas, center, baseRadius, pulse);

    switch (visual.mode) {
      case _VoiceOrbMode.recording:
      case _VoiceOrbMode.speaking:
        _paintWaveBars(canvas, center, baseRadius, pulse);
      case _VoiceOrbMode.thinking:
        _paintThinkingArc(canvas, center, baseRadius);
      case _VoiceOrbMode.failure:
        _paintFailureRing(canvas, center, baseRadius);
      case _VoiceOrbMode.idle:
        _paintIdleRing(canvas, center, baseRadius);
    }
  }

  void _paintGlow(
    Canvas canvas,
    Offset center,
    double baseRadius,
    double pulse,
  ) {
    final paint = Paint()
      ..shader =
          RadialGradient(
            colors: [
              visual.glowColor.withValues(alpha: 0.26 + (pulse * 0.08)),
              visual.secondaryColor.withValues(alpha: 0.12),
              visual.glowColor.withValues(alpha: 0),
            ],
          ).createShader(
            Rect.fromCircle(center: center, radius: baseRadius * 1.55),
          );

    canvas.drawCircle(center, baseRadius * (1.42 + (pulse * 0.08)), paint);
  }

  void _paintHalo(
    Canvas canvas,
    Offset center,
    double baseRadius,
    double pulse,
  ) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..color = visual.secondaryColor.withValues(alpha: 0.34 + (pulse * 0.18));

    canvas.drawCircle(center, baseRadius * (1.16 + (pulse * 0.05)), paint);
  }

  void _paintIdleRing(Canvas canvas, Offset center, double baseRadius) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8
      ..strokeCap = StrokeCap.round
      ..color = visual.primaryColor.withValues(alpha: 0.18);

    canvas.drawCircle(center, baseRadius * 0.93, paint);
  }

  void _paintFailureRing(Canvas canvas, Offset center, double baseRadius) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6
      ..strokeCap = StrokeCap.round
      ..color = visual.primaryColor.withValues(alpha: 0.46);

    canvas.drawCircle(center, baseRadius * 1.02, paint);
  }

  void _paintThinkingArc(Canvas canvas, Offset center, double baseRadius) {
    final rect = Rect.fromCircle(center: center, radius: baseRadius * 1.05);
    final start = (thinking * math.pi * 2) - math.pi / 2;
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8
      ..strokeCap = StrokeCap.round
      ..shader = SweepGradient(
        startAngle: start,
        endAngle: start + math.pi * 1.5,
        colors: [
          visual.primaryColor.withValues(alpha: 0.1),
          visual.secondaryColor.withValues(alpha: 0.86),
          visual.primaryColor.withValues(alpha: 0.1),
        ],
      ).createShader(rect);

    canvas.drawArc(rect, start, math.pi * 1.35, false, paint);
  }

  void _paintWaveBars(
    Canvas canvas,
    Offset center,
    double baseRadius,
    double pulse,
  ) {
    const barCount = 9;
    final paint = Paint()
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 5
      ..color = visual.secondaryColor.withValues(alpha: 0.72);
    final startX = center.dx - 44;
    final baseline = center.dy + baseRadius * 1.15;

    for (var i = 0; i < barCount; i += 1) {
      final phase = isReducedMotion ? 0.35 : (motion + (i * 0.13)) % 1;
      final height = 12 + (math.sin(phase * math.pi * 2).abs() * 26);
      final x = startX + (i * 11);
      canvas.drawLine(
        Offset(x, baseline - height / 2),
        Offset(x, baseline + height / 2),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _VoiceOrbPainter oldDelegate) {
    return oldDelegate.visual != visual ||
        oldDelegate.motion != motion ||
        oldDelegate.thinking != thinking ||
        oldDelegate.isReducedMotion != isReducedMotion;
  }
}
