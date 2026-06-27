import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/services.dart';

String voicePreviewAssetPath(String voiceId) {
  final fileName =
      '${base64Url.encode(utf8.encode(voiceId)).replaceAll('=', '')}.wav';
  return 'assets/voice_previews/$fileName';
}

Future<Uint8List> loadBundledVoicePreview(String voiceId) async {
  final asset = await rootBundle.load(voicePreviewAssetPath(voiceId));
  return asset.buffer.asUint8List();
}
