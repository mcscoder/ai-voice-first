import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/di/get_it.dart';
import '../../../shared/i18n/i18n.dart';
import '../data/voice_language.dart';
import 'voice_capture_cubit.dart';
import 'voice_capture_state.dart';

final class VoiceScreen extends StatelessWidget {
  const VoiceScreen({super.key, this.cubit});

  final VoiceCaptureCubit? cubit;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return BlocProvider(
      create: (_) => cubit ?? getIt<VoiceCaptureCubit>(),
      child: Scaffold(
        backgroundColor: theme.colorScheme.surface,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: BlocBuilder<VoiceCaptureCubit, VoiceCaptureState>(
              builder: (context, state) {
                final cubit = context.read<VoiceCaptureCubit>();
                final isListening =
                    state.status == VoiceCaptureStatus.listening;
                final isTranscribing =
                    state.status == VoiceCaptureStatus.transcribing;

                return Column(
                  children: [
                    Align(
                      alignment: Alignment.centerLeft,
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 240),
                        child: InputDecorator(
                          decoration: InputDecoration(
                            labelText: context.l10n.voiceLanguageLabel,
                            filled: true,
                            fillColor:
                                theme.colorScheme.surfaceContainerHighest,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(18),
                              borderSide: BorderSide.none,
                            ),
                          ),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              key: const Key('voice_language_dropdown'),
                              isExpanded: true,
                              value: state.selectedLanguage.code,
                              items: VoiceLanguage.values
                                  .map(
                                    (language) => DropdownMenuItem<String>(
                                      value: language.code,
                                      child: Text(language.label),
                                    ),
                                  )
                                  .toList(),
                              onChanged: isListening || isTranscribing
                                  ? null
                                  : (value) {
                                      if (value == null) {
                                        return;
                                      }
                                      cubit.selectLanguage(
                                        VoiceLanguage.values.firstWhere(
                                          (language) => language.code == value,
                                        ),
                                      );
                                    },
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    Expanded(
                      child: Center(
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 560),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                _transcriptText(context, state),
                                textAlign: TextAlign.center,
                                style: theme.textTheme.headlineMedium?.copyWith(
                                  height: 1.35,
                                  color: state.transcript.isEmpty
                                      ? theme.colorScheme.onSurfaceVariant
                                      : theme.colorScheme.onSurface,
                                ),
                              ),
                              const SizedBox(height: 20),
                              Text(
                                _statusText(context, state),
                                textAlign: TextAlign.center,
                                style: theme.textTheme.bodyLarge?.copyWith(
                                  color:
                                      state.status == VoiceCaptureStatus.failure
                                      ? theme.colorScheme.error
                                      : theme.colorScheme.onSurfaceVariant,
                                ),
                              ),
                              if (state.failure ==
                                  VoiceCaptureFailure
                                      .microphonePermanentlyDenied) ...[
                                const SizedBox(height: 16),
                                TextButton(
                                  onPressed: cubit.openSettings,
                                  child: Text(context.l10n.voiceOpenSettings),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    _PulseMicButton(
                      isListening: isListening,
                      isDisabled: isTranscribing,
                      onPressed: cubit.toggleRecording,
                    ),
                    const SizedBox(height: 20),
                    Text(
                      isListening
                          ? context.l10n.voiceStopHint
                          : context.l10n.voiceStartHint,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }

  String _transcriptText(BuildContext context, VoiceCaptureState state) {
    switch (state.status) {
      case VoiceCaptureStatus.success:
        return state.transcript;
      case VoiceCaptureStatus.empty:
        return context.l10n.voiceEmptyTranscript;
      case VoiceCaptureStatus.failure:
      case VoiceCaptureStatus.idle:
      case VoiceCaptureStatus.listening:
      case VoiceCaptureStatus.transcribing:
        return state.transcript.isEmpty
            ? context.l10n.voiceTranscriptPlaceholder
            : state.transcript;
    }
  }

  String _statusText(BuildContext context, VoiceCaptureState state) {
    switch (state.status) {
      case VoiceCaptureStatus.idle:
        return context.l10n.voiceIdleStatus;
      case VoiceCaptureStatus.listening:
        return context.l10n.voiceListeningStatus;
      case VoiceCaptureStatus.transcribing:
        return context.l10n.voiceTranscribingStatus;
      case VoiceCaptureStatus.success:
        return context.l10n.voiceSuccessStatus;
      case VoiceCaptureStatus.empty:
        return context.l10n.voiceEmptyStatus;
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

final class _PulseMicButton extends StatefulWidget {
  const _PulseMicButton({
    required this.isListening,
    required this.isDisabled,
    required this.onPressed,
  });

  final bool isListening;
  final bool isDisabled;
  final VoidCallback onPressed;

  @override
  State<_PulseMicButton> createState() => _PulseMicButtonState();
}

final class _PulseMicButtonState extends State<_PulseMicButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1400),
  );

  @override
  void initState() {
    super.initState();
    if (widget.isListening) {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(covariant _PulseMicButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isListening && !_controller.isAnimating) {
      _controller.repeat(reverse: true);
    } else if (!widget.isListening && _controller.isAnimating) {
      _controller.stop();
      _controller.value = 0;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDisabled = widget.isDisabled;
    final baseColor = widget.isListening
        ? theme.colorScheme.error
        : theme.colorScheme.primary;

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final scale = widget.isListening ? 1 + (_controller.value * 0.1) : 1.0;
        final glowOpacity = widget.isListening
            ? 0.18 + (_controller.value * 0.12)
            : 0.0;

        return Transform.scale(
          scale: scale,
          child: Container(
            width: 150,
            height: 150,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: baseColor.withValues(alpha: glowOpacity),
                  blurRadius: 36,
                  spreadRadius: 12,
                ),
              ],
            ),
            child: FilledButton(
              onPressed: isDisabled ? null : widget.onPressed,
              style: FilledButton.styleFrom(
                backgroundColor: baseColor,
                disabledBackgroundColor:
                    theme.colorScheme.surfaceContainerHighest,
                foregroundColor: theme.colorScheme.onPrimary,
                shape: const CircleBorder(),
              ),
              child: Icon(
                widget.isDisabled ? Icons.hourglass_top : Icons.mic,
                size: 54,
              ),
            ),
          ),
        );
      },
    );
  }
}
