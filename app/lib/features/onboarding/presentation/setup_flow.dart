import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/design_system/design_system.dart';
import '../../../core/di/get_it.dart';
import '../../memory/memory.dart';
import '../../voice_settings/voice_settings.dart';
import 'speaking_style.dart';
import 'setup_cubit.dart';

final class SetupFlow extends StatefulWidget {
  const SetupFlow({super.key});

  @override
  State<SetupFlow> createState() => _SetupFlowState();
}

final class _SetupFlowState extends State<SetupFlow> {
  final _nicknameController = TextEditingController();
  var _step = 0;
  var _selectedStyle = SpeakingStyle.shortAnswers;
  var _isSavingPersonalization = false;
  var _isFinishingSetup = false;

  @override
  void initState() {
    super.initState();
    final setup = context.read<SetupCubit>().state;
    _nicknameController.text = setup.nickname;
    _selectedStyle = setup.speakingStyle;
  }

  @override
  void dispose() {
    _nicknameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      _PermissionsStep(onContinue: _next),
      const _VoiceSetupStep(),
      _PersonalizationStep(
        nicknameController: _nicknameController,
        selectedStyle: _selectedStyle,
        isBusy: _isSavingPersonalization,
        onStyleChanged: (value) {
          setState(() {
            _selectedStyle = value;
          });
        },
        onContinue: () {
          _savePersonalization();
        },
      ),
      _MemoryConsentStep(
        onFinish: () {
          _finishSetup();
        },
        isBusy: _isFinishingSetup,
      ),
    ];

    final page = VoxiaScaffold(
      floatingActionButtonLocation: _step == 1
          ? FloatingActionButtonLocation.centerFloat
          : null,
      floatingActionButton: _step == 1
          ? _VoiceSetupContinueButton(onContinue: _next)
          : null,
      child: VoxiaFixedPage(
        title: _titleForStep(_step),
        leading: IconButton(
          tooltip: 'Back',
          onPressed: _step == 0 ? null : _back,
          icon: const Icon(Icons.arrow_back),
        ),
        body: AnimatedSwitcher(
          duration: const Duration(milliseconds: 180),
          child: KeyedSubtree(key: ValueKey<int>(_step), child: pages[_step]),
        ),
      ),
    );

    if (_step != 1) {
      return page;
    }

    return BlocProvider(
      create: (_) => getIt<VoiceSettingsCubit>()..load(),
      child: page,
    );
  }

  void _next() {
    setState(() {
      _step = (_step + 1).clamp(0, 3);
    });
  }

  void _back() {
    setState(() {
      _step = (_step - 1).clamp(0, 3);
    });
  }

  Future<void> _savePersonalization() async {
    setState(() {
      _isSavingPersonalization = true;
    });
    final saved = await context.read<SetupCubit>().savePersonalization(
      nickname: _nicknameController.text,
      speakingStyle: _selectedStyle,
    );
    if (!mounted) {
      return;
    }
    setState(() {
      _isSavingPersonalization = false;
    });
    if (!saved) {
      _showError(context.read<SetupCubit>().state.errorMessage);
      return;
    }
    _next();
  }

  Future<void> _finishSetup() async {
    setState(() {
      _isFinishingSetup = true;
    });
    final memorySaved = await context.read<MemoryCubit>().setMemoryEnabled(
      context.read<SetupCubit>().state.memoryEnabled,
    );
    if (!mounted) {
      return;
    }
    if (!memorySaved) {
      setState(() {
        _isFinishingSetup = false;
      });
      _showError(context.read<MemoryCubit>().state.errorMessage);
      return;
    }

    final completed = await context.read<SetupCubit>().markSetupCompleted(true);
    if (!mounted) {
      return;
    }
    setState(() {
      _isFinishingSetup = false;
    });
    if (!completed) {
      _showError(context.read<SetupCubit>().state.errorMessage);
    }
  }

  void _showError(String? message) {
    if (message == null) {
      return;
    }
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  String _titleForStep(int step) {
    return switch (step) {
      0 => 'Permissions',
      1 => 'Voice setup',
      2 => 'Personalization',
      _ => 'Memory',
    };
  }
}

final class _PermissionsStep extends StatelessWidget {
  const _PermissionsStep({required this.onContinue});

  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    return _SetupPage(
      header: const VoxiaScreenHeader(
        title: 'Allow access',
        subtitle:
            'To give you the best voice experience, Voxia needs access to:',
        icon: _ShieldIcon(),
      ),
      children: [
        const _PermissionTile(
          icon: Icons.mic_none,
          title: 'Microphone',
          subtitle: 'For voice conversations',
          isEnabled: true,
        ),
        const _PermissionTile(
          icon: Icons.notifications_none,
          title: 'Notifications',
          subtitle: 'For reminders & updates',
          isEnabled: true,
        ),
        const _PermissionTile(
          icon: Icons.contacts_outlined,
          title: 'Contacts & Calendar',
          subtitle: 'Optional for better help',
          isEnabled: false,
        ),
        VoxiaGradientButton(label: 'Continue', onPressed: onContinue),
        Text(
          'You can change this anytime in Settings.',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: VoxiaColors.muted,
            letterSpacing: 0,
          ),
        ),
      ],
    );
  }
}

final class _VoiceSetupStep extends StatelessWidget {
  const _VoiceSetupStep();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<VoiceSettingsCubit, VoiceSettingsState>(
      builder: (context, state) {
        return _SetupPage(
          header: const VoxiaScreenHeader(
            title: 'Choose your\nAI voice',
            subtitle: 'Preview each VieNeu voice before you continue.',
            icon: VoxiaMark(size: 44),
          ),
          children: [
            VoiceSelectionPanel(
              state: state,
              onRetry: () => context.read<VoiceSettingsCubit>().load(),
              onSelectVoice: (voiceId) =>
                  context.read<VoiceSettingsCubit>().selectVoice(voiceId),
              onPreviewVoice: (voiceId) =>
                  context.read<VoiceSettingsCubit>().preview(voiceId),
            ),
            const SafeArea(
              top: false,
              child: SizedBox(height: AppSpacing.xxxl),
            ),
          ],
        );
      },
    );
  }
}

final class _VoiceSetupContinueButton extends StatelessWidget {
  const _VoiceSetupContinueButton({required this.onContinue});

  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.paddingOf(context).bottom;

    return BlocBuilder<VoiceSettingsCubit, VoiceSettingsState>(
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
                  label: 'Continue',
                  isBusy: state.isSaving,
                  onPressed: state.selectedVoiceId.isEmpty
                      ? null
                      : () async {
                          final saved = await context
                              .read<VoiceSettingsCubit>()
                              .save();
                          if (saved && context.mounted) {
                            await context
                                .read<VoiceSettingsCubit>()
                                .stopPreview();
                            onContinue();
                          }
                        },
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

final class _PersonalizationStep extends StatelessWidget {
  const _PersonalizationStep({
    required this.nicknameController,
    required this.selectedStyle,
    required this.onStyleChanged,
    required this.onContinue,
    this.isBusy = false,
  });

  final TextEditingController nicknameController;
  final SpeakingStyle selectedStyle;
  final ValueChanged<SpeakingStyle> onStyleChanged;
  final VoidCallback onContinue;
  final bool isBusy;

  @override
  Widget build(BuildContext context) {
    return _SetupPage(
      header: const VoxiaScreenHeader(
        title: 'Personalize\nyour assistant',
        icon: VoxiaMark(size: 44),
      ),
      children: [
        _FieldLabel(
          label: 'What should we call you?',
          child: TextField(
            key: const Key('setup_nickname_field'),
            controller: nicknameController,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(hintText: 'Your nickname'),
          ),
        ),
        _FieldLabel(
          label: 'Speaking style',
          child: Wrap(
            spacing: AppSpacing.md,
            runSpacing: AppSpacing.md,
            children: [
              _StyleChip(
                label: 'Short answers',
                style: SpeakingStyle.shortAnswers,
                selectedStyle: selectedStyle,
                onChanged: onStyleChanged,
              ),
              _StyleChip(
                label: 'Detailed answers',
                style: SpeakingStyle.detailedAnswers,
                selectedStyle: selectedStyle,
                onChanged: onStyleChanged,
              ),
              _StyleChip(
                label: 'Casual',
                style: SpeakingStyle.casual,
                selectedStyle: selectedStyle,
                onChanged: onStyleChanged,
              ),
              _StyleChip(
                label: 'Professional',
                style: SpeakingStyle.professional,
                selectedStyle: selectedStyle,
                onChanged: onStyleChanged,
              ),
            ],
          ),
        ),
        VoxiaGradientButton(
          label: 'Continue',
          onPressed: onContinue,
          isBusy: isBusy,
        ),
      ],
    );
  }
}

final class _MemoryConsentStep extends StatelessWidget {
  const _MemoryConsentStep({required this.onFinish, this.isBusy = false});

  final VoidCallback onFinish;
  final bool isBusy;

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<SetupCubit, SetupState>(
      builder: (context, state) {
        return _SetupPage(
          header: const VoxiaScreenHeader(
            title: 'Improve with memory',
            subtitle:
                'Voxia can remember important details across conversations to give you smarter, more personalized help.',
            icon: Icon(
              Icons.psychology_outlined,
              color: VoxiaColors.cyan,
              size: 48,
            ),
          ),
          children: [
            _MemoryChoiceTile(
              isEnabled: true,
              title: 'Enable memory',
              subtitle: 'Remember preferences\nand key details',
              isSelected: state.memoryEnabled,
            ),
            _MemoryChoiceTile(
              isEnabled: false,
              title: 'Disable memory',
              subtitle: 'Keep conversations\ntemporary',
              isSelected: !state.memoryEnabled,
            ),
            VoxiaGradientButton(
              label: 'Finish setup',
              onPressed: onFinish,
              isBusy: isBusy,
            ),
            Text(
              'You can update this anytime in Settings.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: VoxiaColors.muted,
                letterSpacing: 0,
              ),
            ),
          ],
        );
      },
    );
  }
}

final class _SetupPage extends StatelessWidget {
  const _SetupPage({required this.header, required this.children});

  final Widget header;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final pageChildren = <Widget>[
          header,
          const SizedBox(height: AppSpacing.sm),
          ...children.expand(
            (child) => [child, const SizedBox(height: AppSpacing.xs)],
          ),
        ];
        return SingleChildScrollView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight),
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: pageChildren,
              ),
            ),
          ),
        );
      },
    );
  }
}

final class _PermissionTile extends StatelessWidget {
  const _PermissionTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.isEnabled,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final bool isEnabled;

  @override
  Widget build(BuildContext context) {
    return VoxiaGlassPanel(
      child: Row(
        children: [
          _IconSquare(
            icon: icon,
            color: isEnabled ? VoxiaColors.cyan : VoxiaColors.muted,
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: _TileText(title: title, subtitle: subtitle),
          ),
          _SelectionCircle(isSelected: isEnabled),
        ],
      ),
    );
  }
}

final class _MemoryChoiceTile extends StatelessWidget {
  const _MemoryChoiceTile({
    required this.isEnabled,
    required this.title,
    required this.subtitle,
    required this.isSelected,
  });

  final bool isEnabled;
  final String title;
  final String subtitle;
  final bool isSelected;

  @override
  Widget build(BuildContext context) {
    return VoxiaGlassPanel(
      isSelected: isSelected,
      onTap: () => context.read<SetupCubit>().setMemoryEnabled(isEnabled),
      child: Row(
        children: [
          _IconSquare(
            icon: isEnabled ? Icons.memory_outlined : Icons.hide_source,
            color: isSelected ? VoxiaColors.cyan : VoxiaColors.muted,
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: _TileText(title: title, subtitle: subtitle),
          ),
          _SelectionCircle(isSelected: isSelected),
        ],
      ),
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
    return SizedBox(
      width: 150,
      child: VoxiaGlassPanel(
        isSelected: isSelected,
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.sm,
          vertical: AppSpacing.sm,
        ),
        onTap: () => onChanged(style),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Flexible(
              child: Text(
                label,
                textAlign: TextAlign.center,
                overflow: TextOverflow.ellipsis,
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
      ),
    );
  }
}

final class _TileText extends StatelessWidget {
  const _TileText({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            color: VoxiaColors.text,
            fontWeight: FontWeight.w800,
            letterSpacing: 0,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          subtitle,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: VoxiaColors.muted,
            height: 1.32,
            letterSpacing: 0,
          ),
        ),
      ],
    );
  }
}

final class _IconSquare extends StatelessWidget {
  const _IconSquare({required this.icon, required this.color});

  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 38,
      height: 38,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: AppRadius.borderLg,
        border: Border.all(color: color.withValues(alpha: 0.32)),
      ),
      child: Icon(icon, color: color, size: 22),
    );
  }
}

final class _SelectionCircle extends StatelessWidget {
  const _SelectionCircle({required this.isSelected});

  final bool isSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 24,
      height: 24,
      decoration: BoxDecoration(
        gradient: isSelected ? VoxiaColors.accentGradient : null,
        shape: BoxShape.circle,
        border: Border.all(
          color: isSelected ? Colors.transparent : VoxiaColors.muted,
          width: 2,
        ),
      ),
      child: isSelected
          ? const Icon(Icons.check, color: VoxiaColors.text, size: 14)
          : null,
    );
  }
}

final class _ShieldIcon extends StatelessWidget {
  const _ShieldIcon();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: VoxiaColors.cyan.withValues(alpha: 0.09),
      ),
      child: const Icon(
        Icons.shield_outlined,
        color: VoxiaColors.cyan,
        size: 34,
      ),
    );
  }
}
