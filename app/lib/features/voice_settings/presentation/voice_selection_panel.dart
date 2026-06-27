import 'package:flutter/material.dart';

import '../../../core/design_system/design_system.dart';
import 'voice_settings_state.dart';

final class VoiceSelectionPanel extends StatelessWidget {
  const VoiceSelectionPanel({
    required this.state,
    required this.onSelectVoice,
    required this.onPreviewVoice,
    super.key,
    this.onRetry,
  });

  final VoiceSettingsState state;
  final ValueChanged<String> onSelectVoice;
  final ValueChanged<String> onPreviewVoice;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    if (state.isLoading && !state.hasVoices) {
      return const Center(child: CircularProgressIndicator());
    }

    if (!state.hasVoices) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            state.errorMessage ?? 'No voices are available right now.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: VoxiaColors.muted,
              letterSpacing: 0,
            ),
          ),
          if (onRetry != null) ...[
            const SizedBox(height: AppSpacing.md),
            VoxiaOutlineButton(label: 'Try again', onPressed: onRetry),
          ],
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (state.errorMessage != null) ...[
          Text(
            state.errorMessage!,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: VoxiaColors.red,
              letterSpacing: 0,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
        ],
        for (final voice in state.voices) ...[
          _VoiceOptionTile(
            key: Key('voice_option_${voice.id}'),
            voiceId: voice.id,
            title: voice.name,
            description: voice.description,
            isSelected: state.selectedVoiceId == voice.id,
            isPreviewing: state.previewingVoiceId == voice.id,
            isPreviewLoading: state.previewLoadingVoiceId == voice.id,
            onSelect: () => onSelectVoice(voice.id),
            onPreview: () => onPreviewVoice(voice.id),
          ),
          const SizedBox(height: AppSpacing.sm),
        ],
      ],
    );
  }
}

final class _VoiceOptionTile extends StatelessWidget {
  const _VoiceOptionTile({
    required this.voiceId,
    required this.title,
    required this.description,
    required this.isSelected,
    required this.isPreviewing,
    required this.isPreviewLoading,
    required this.onSelect,
    required this.onPreview,
    super.key,
  });

  final String voiceId;
  final String title;
  final String description;
  final bool isSelected;
  final bool isPreviewing;
  final bool isPreviewLoading;
  final VoidCallback onSelect;
  final VoidCallback onPreview;

  @override
  Widget build(BuildContext context) {
    final previewIcon = isPreviewLoading
        ? null
        : isPreviewing
        ? Icons.stop_circle_outlined
        : Icons.play_circle_outline;
    final previewLabel = isPreviewing ? 'Stop' : 'Preview';

    return VoxiaGlassPanel(
      isSelected: isSelected,
      onTap: onSelect,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Icon(
            isSelected ? Icons.check_circle : Icons.radio_button_unchecked,
            color: isSelected ? VoxiaColors.cyan : VoxiaColors.muted,
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: VoxiaColors.text,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  description,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: VoxiaColors.muted,
                    letterSpacing: 0,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              TextButton.icon(
                key: Key('voice_preview_$voiceId'),
                onPressed: isPreviewLoading ? null : onPreview,
                icon: isPreviewLoading
                    ? const SizedBox.square(
                        dimension: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Icon(previewIcon, size: 20),
                label: Text(previewLabel),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
