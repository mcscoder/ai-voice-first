import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design_system/design_system.dart';
import 'voice_selection_panel.dart';
import 'voice_settings_cubit.dart';
import 'voice_settings_state.dart';

final class VoiceSettingsScreen extends StatelessWidget {
  const VoiceSettingsScreen({super.key});

  static const _saveBarHeight = 48.0;

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.paddingOf(context).bottom;

    return VoxiaScaffold(
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: BlocBuilder<VoiceSettingsCubit, VoiceSettingsState>(
        builder: (context, state) {
          return Padding(
            padding: EdgeInsets.fromLTRB(
              AppSpacing.md,
              0,
              AppSpacing.md,
              AppSpacing.sm + bottomInset,
            ),
            child: Align(
              alignment: Alignment.bottomCenter,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 430),
                child: SizedBox(
                  width: double.infinity,
                  child: VoxiaGradientButton(
                    key: const Key('voice_settings_save'),
                    label: 'Save',
                    isBusy: state.isSaving,
                    onPressed: state.selectedVoiceId.isEmpty
                        ? null
                        : () async {
                            final saved = await context
                                .read<VoiceSettingsCubit>()
                                .save();
                            if (saved && context.mounted) {
                              context.pop();
                            }
                          },
                  ),
                ),
              ),
            ),
          );
        },
      ),
      child: VoxiaScrollPage(
        title: 'Voice settings',
        leading: IconButton(
          tooltip: 'Back to profile',
          onPressed: context.pop,
          icon: const Icon(Icons.arrow_back),
        ),
        slivers: [
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Choose the voice Voxia uses for previews and future replies.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: VoxiaColors.muted,
              letterSpacing: 0,
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          BlocBuilder<VoiceSettingsCubit, VoiceSettingsState>(
            builder: (context, state) {
              return VoiceSelectionPanel(
                state: state,
                onRetry: () => context.read<VoiceSettingsCubit>().load(),
                onSelectVoice: (voiceId) =>
                    context.read<VoiceSettingsCubit>().selectVoice(voiceId),
                onPreviewVoice: (voiceId) =>
                    context.read<VoiceSettingsCubit>().preview(voiceId),
              );
            },
          ),
          SizedBox(
            height:
                _saveBarHeight +
                (AppSpacing.xxl * 2) +
                AppSpacing.sm +
                bottomInset,
          ),
        ],
      ),
    );
  }
}
