import 'dart:io';

import 'package:injectable/injectable.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

class AudioRecordingException implements Exception {
  const AudioRecordingException(this.message);

  final String message;
}

@lazySingleton
class AudioRecorderService {
  AudioRecorder? _recorder;

  String? _activePath;

  AudioRecorder get _client => _recorder ??= AudioRecorder();

  Future<void> start() async {
    if (await _client.isRecording()) {
      return;
    }

    if (!await _client.hasPermission()) {
      throw const AudioRecordingException('Microphone permission not granted.');
    }

    final directory = await getTemporaryDirectory();
    final path =
        '${directory.path}/voice_capture_${DateTime.now().millisecondsSinceEpoch}.m4a';

    await _client.start(
      const RecordConfig(
        encoder: AudioEncoder.aacLc,
        bitRate: 128000,
        sampleRate: 44100,
      ),
      path: path,
    );

    _activePath = path;
  }

  Future<String> stop() async {
    final path = await _client.stop();
    final resolvedPath = path ?? _activePath;
    _activePath = null;

    if (resolvedPath == null || resolvedPath.isEmpty) {
      throw const AudioRecordingException('No audio file was produced.');
    }

    return resolvedPath;
  }

  Future<void> cancel() async {
    if (await _client.isRecording()) {
      await _client.stop();
    }

    final path = _activePath;
    _activePath = null;

    if (path != null) {
      final file = File(path);
      if (await file.exists()) {
        await file.delete();
      }
    }
  }

  Future<void> deleteRecording(String path) async {
    final file = File(path);
    if (await file.exists()) {
      await file.delete();
    }
  }

  Future<void> dispose() async {
    await _recorder?.dispose();
  }
}
