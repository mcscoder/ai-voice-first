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
        final canCancelRequest =
            state.status == VoiceCaptureStatus.uploading ||
            state.status == VoiceCaptureStatus.processing ||
            state.status == VoiceCaptureStatus.speaking;

        return VoxiaFixedPage(
          title: 'Talk',
          leading: IconButton(
            tooltip: 'Menu',
            onPressed: () {},
            icon: const Icon(Icons.menu),
          ),
          trailing: const _ProChip(),
          body: Column(
            children: [
              const Spacer(),
              _PrimaryVisualizer(status: state.status),
              const SizedBox(height: AppSpacing.md),
              Text(
                _statusTitle(state),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: state.status == VoiceCaptureStatus.failure
                      ? VoxiaColors.red
                      : VoxiaColors.text,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0,
                ),
              ),
              const SizedBox(height: AppSpacing.xs),
              Text(
                _statusSubtitle(context, state),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: VoxiaColors.muted,
                  letterSpacing: 0,
                ),
              ),
              if (canCancelRequest) ...[
                const SizedBox(height: AppSpacing.xs),
                _RequestElapsedTime(state: state),
              ],
              const SizedBox(height: AppSpacing.md),
              _ActionArea(
                state: state,
                isRecording: isRecording,
                onToggleRecording: cubit.toggleRecording,
                onCancelRequest: cubit.cancelRequest,
                onOpenSettings: cubit.openSettings,
              ),
              const Spacer(),
              if (state.status == VoiceCaptureStatus.idle ||
                  state.status == VoiceCaptureStatus.success)
                const _ShortcutGrid(),
              const SizedBox(height: AppSpacing.md),
            ],
          ),
        );
      },
    );
  }

  String _statusTitle(VoiceCaptureState state) {
    return switch (state.status) {
      VoiceCaptureStatus.idle => 'Tap to talk',
      VoiceCaptureStatus.recording => 'Listening...',
      VoiceCaptureStatus.uploading => 'Uploading...',
      VoiceCaptureStatus.processing => 'Processing...',
      VoiceCaptureStatus.speaking => 'Speaking...',
      VoiceCaptureStatus.success => 'Tap to talk',
      VoiceCaptureStatus.failure => 'Try again',
    };
  }

  String _statusSubtitle(BuildContext context, VoiceCaptureState state) {
    return switch (state.status) {
      VoiceCaptureStatus.idle => 'Your assistant is ready',
      VoiceCaptureStatus.recording => 'Speak naturally',
      VoiceCaptureStatus.uploading => context.l10n.voiceUploadingStatus,
      VoiceCaptureStatus.processing => context.l10n.voiceProcessingStatus,
      VoiceCaptureStatus.speaking => 'How can I help?',
      VoiceCaptureStatus.success => context.l10n.voiceSuccessStatus,
      VoiceCaptureStatus.failure => _failureText(context, state),
    };
  }

  String _failureText(BuildContext context, VoiceCaptureState state) {
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

final class _ProChip extends StatelessWidget {
  const _ProChip();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        borderRadius: AppRadius.borderFull,
        border: Border.all(color: VoxiaColors.violet),
        color: VoxiaColors.violet.withValues(alpha: 0.12),
      ),
      child: const Text(
        'Pro',
        style: TextStyle(color: VoxiaColors.text, fontSize: 12),
      ),
    );
  }
}

final class _PrimaryVisualizer extends StatelessWidget {
  const _PrimaryVisualizer({required this.status});

  final VoiceCaptureStatus status;

  @override
  Widget build(BuildContext context) {
    return switch (status) {
      VoiceCaptureStatus.recording => const VoxiaWaveform(
        height: 150,
        mode: VoxiaWaveformMode.listening,
        isAnimated: true,
      ),
      VoiceCaptureStatus.uploading || VoiceCaptureStatus.processing =>
        const VoxiaMark(size: 140, showRing: true),
      VoiceCaptureStatus.speaking => const VoxiaOrb(
        size: 180,
        mode: VoxiaOrbMode.speaking,
        isAnimated: true,
      ),
      VoiceCaptureStatus.failure => const Icon(
        Icons.error_outline,
        color: VoxiaColors.red,
        size: 108,
      ),
      VoiceCaptureStatus.idle ||
      VoiceCaptureStatus.success => const VoxiaOrb(size: 180),
    };
  }
}

final class _ActionArea extends StatelessWidget {
  const _ActionArea({
    required this.state,
    required this.isRecording,
    required this.onToggleRecording,
    required this.onCancelRequest,
    required this.onOpenSettings,
  });

  final VoiceCaptureState state;
  final bool isRecording;
  final VoidCallback onToggleRecording;
  final VoidCallback onCancelRequest;
  final VoidCallback onOpenSettings;

  @override
  Widget build(BuildContext context) {
    if (state.status == VoiceCaptureStatus.speaking) {
      return Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _RoundAction(
            icon: Icons.stop,
            label: 'Stop',
            color: VoxiaColors.red,
            onPressed: onCancelRequest,
          ),
          _RoundAction(icon: Icons.speed, label: 'Slow', onPressed: () {}),
          _RoundAction(icon: Icons.refresh, label: 'Repeat', onPressed: () {}),
          _RoundAction(
            icon: Icons.mic_off_outlined,
            label: 'Mute',
            onPressed: () {},
          ),
        ],
      );
    }

    if (state.failure == VoiceCaptureFailure.microphonePermanentlyDenied) {
      return VoxiaGradientButton(
        label: context.l10n.voiceOpenSettings,
        icon: Icons.settings_outlined,
        onPressed: onOpenSettings,
      );
    }

    if (state.status == VoiceCaptureStatus.uploading ||
        state.status == VoiceCaptureStatus.processing) {
      return _RoundAction(
        icon: Icons.close,
        label: context.l10n.voiceCancelRequest,
        onPressed: onCancelRequest,
      );
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _RoundAction(
          icon: Icons.mic_off_outlined,
          label: 'Mute',
          onPressed: () {},
        ),
        _MicButton(isRecording: isRecording, onPressed: onToggleRecording),
        _RoundAction(
          icon: Icons.call_end,
          label: 'End',
          color: VoxiaColors.red,
          onPressed: () {},
        ),
      ],
    );
  }
}

final class _MicButton extends StatelessWidget {
  const _MicButton({required this.isRecording, required this.onPressed});

  final bool isRecording;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: isRecording
          ? context.l10n.voiceStopHint
          : context.l10n.voiceStartHint,
      child: GestureDetector(
        onTap: onPressed,
        child: Container(
          width: 104,
          height: 104,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: VoxiaColors.accentGradient,
          ),
          padding: const EdgeInsets.all(5),
          child: Container(
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: VoxiaColors.background,
            ),
            child: Icon(
              isRecording ? Icons.stop : Icons.mic,
              color: VoxiaColors.text,
              size: 44,
            ),
          ),
        ),
      ),
    );
  }
}

final class _RoundAction extends StatelessWidget {
  const _RoundAction({
    required this.icon,
    required this.label,
    required this.onPressed,
    this.color = VoxiaColors.text,
  });

  final IconData icon;
  final String label;
  final VoidCallback onPressed;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton.filled(
          tooltip: label,
          onPressed: onPressed,
          style: IconButton.styleFrom(
            backgroundColor: VoxiaColors.panelStrong,
            foregroundColor: color,
            minimumSize: const Size.square(52),
            shape: const CircleBorder(
              side: BorderSide(color: VoxiaColors.border),
            ),
          ),
          icon: Icon(icon, size: 26),
        ),
        const SizedBox(height: AppSpacing.xs),
        Text(
          label,
          style: Theme.of(
            context,
          ).textTheme.bodyMedium?.copyWith(color: color, letterSpacing: 0),
        ),
      ],
    );
  }
}

final class _ShortcutGrid extends StatelessWidget {
  const _ShortcutGrid();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _ShortcutTile(icon: Icons.add, label: 'New session'),
        ),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
          child: _ShortcutTile(
            icon: Icons.psychology_outlined,
            label: 'Memory',
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
          child: _ShortcutTile(
            icon: Icons.settings_outlined,
            label: 'Settings',
          ),
        ),
      ],
    );
  }
}

final class _ShortcutTile extends StatelessWidget {
  const _ShortcutTile({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return VoxiaGlassPanel(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.md,
      ),
      child: Column(
        children: [
          Icon(icon, color: VoxiaColors.text, size: 26),
          const SizedBox(height: AppSpacing.xs),
          Text(
            label,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: VoxiaColors.text,
              fontWeight: FontWeight.w600,
              letterSpacing: 0,
            ),
          ),
        ],
      ),
    );
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

    return StreamBuilder<int>(
      stream: Stream<int>.periodic(const Duration(seconds: 1), (tick) => tick),
      builder: (context, snapshot) {
        final elapsed = DateTime.now().difference(startedAt);
        final minutes = elapsed.inMinutes;
        final seconds = elapsed.inSeconds
            .remainder(60)
            .toString()
            .padLeft(2, '0');
        return Text(
          '$minutes:$seconds',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: VoxiaColors.muted,
            fontWeight: FontWeight.w700,
            letterSpacing: 0,
          ),
        );
      },
    );
  }
}
