import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/design_system/design_system.dart';
import '../onboarding/onboarding.dart';

final class ProfilePersonalizationScreen extends StatefulWidget {
  const ProfilePersonalizationScreen({super.key});

  @override
  State<ProfilePersonalizationScreen> createState() =>
      _ProfilePersonalizationScreenState();
}

final class _ProfilePersonalizationScreenState
    extends State<ProfilePersonalizationScreen> {
  late final TextEditingController _nicknameController;
  late SpeakingStyle _selectedStyle;
  var _isSaving = false;

  @override
  void initState() {
    super.initState();
    final setup = context.read<SetupCubit>().state;
    _nicknameController = TextEditingController(text: setup.nickname);
    _selectedStyle = setup.speakingStyle;
  }

  @override
  void dispose() {
    _nicknameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return VoxiaScaffold(
      child: VoxiaScrollPage(
        title: 'Personalization',
        leading: _BackButton(onPressed: context.pop),
        slivers: [
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Adjust how Voxia addresses you and how detailed replies should feel.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: VoxiaColors.muted,
              letterSpacing: 0,
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          _FieldLabel(
            label: 'Nickname',
            child: TextField(
              key: const Key('profile_nickname_field'),
              controller: _nicknameController,
              textInputAction: TextInputAction.done,
              decoration: const InputDecoration(hintText: 'Your nickname'),
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          _FieldLabel(
            label: 'Speaking style',
            child: Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              children: [
                _StyleChip(
                  label: 'Short answers',
                  style: SpeakingStyle.shortAnswers,
                  selectedStyle: _selectedStyle,
                  onChanged: _updateStyle,
                ),
                _StyleChip(
                  label: 'Detailed answers',
                  style: SpeakingStyle.detailedAnswers,
                  selectedStyle: _selectedStyle,
                  onChanged: _updateStyle,
                ),
                _StyleChip(
                  label: 'Casual',
                  style: SpeakingStyle.casual,
                  selectedStyle: _selectedStyle,
                  onChanged: _updateStyle,
                ),
                _StyleChip(
                  label: 'Professional',
                  style: SpeakingStyle.professional,
                  selectedStyle: _selectedStyle,
                  onChanged: _updateStyle,
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          VoxiaGradientButton(
            label: 'Save',
            onPressed: () {
              _save();
            },
            isBusy: _isSaving,
          ),
        ],
      ),
    );
  }

  void _updateStyle(SpeakingStyle style) {
    setState(() {
      _selectedStyle = style;
    });
  }

  Future<void> _save() async {
    setState(() {
      _isSaving = true;
    });
    final saved = await context.read<SetupCubit>().savePersonalization(
      nickname: _nicknameController.text,
      speakingStyle: _selectedStyle,
    );
    if (!mounted) {
      return;
    }
    setState(() {
      _isSaving = false;
    });
    if (saved) {
      context.pop();
      return;
    }
    final error = context.read<SetupCubit>().state.errorMessage;
    if (error != null) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(error)));
    }
  }
}

final class _BackButton extends StatelessWidget {
  const _BackButton({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Back to profile',
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

final class _FieldLabel extends StatelessWidget {
  const _FieldLabel({required this.label, required this.child});

  final String label;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            color: VoxiaColors.muted,
            fontWeight: FontWeight.w600,
            letterSpacing: 0,
          ),
        ),
        const SizedBox(height: AppSpacing.sm),
        child,
      ],
    );
  }
}

final class _StyleChip extends StatelessWidget {
  const _StyleChip({
    required this.label,
    required this.style,
    required this.selectedStyle,
    required this.onChanged,
  });

  final String label;
  final SpeakingStyle style;
  final SpeakingStyle selectedStyle;
  final ValueChanged<SpeakingStyle> onChanged;

  @override
  Widget build(BuildContext context) {
    final isSelected = style == selectedStyle;

    return VoxiaGlassPanel(
      isSelected: isSelected,
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      onTap: () => onChanged(style),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Flexible(
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                color: VoxiaColors.text,
                fontWeight: FontWeight.w700,
                letterSpacing: 0,
              ),
            ),
          ),
          if (isSelected) ...[
            const SizedBox(width: AppSpacing.sm),
            const Icon(Icons.check_circle, color: VoxiaColors.cyan, size: 22),
          ],
        ],
      ),
    );
  }
}
