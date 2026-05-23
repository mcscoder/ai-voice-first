import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

import '../../../core/error.dart';
import '../../../core/network/api.dart';
import '../../../core/network/api_path.dart';
import '../../../core/network/dio.dart';
import 'voice_language.dart';

@lazySingleton
base class TranscriptionApi extends Api {
  TranscriptionApi(@nonAuthDio super.dio);

  Future<({NetworkError? error, Uint8List? audio})> respond({
    required String filePath,
    required VoiceLanguage language,
    ProgressCallback? onSendProgress,
  }) async {
    final result = await withTimeoutRequest(() async {
      final formData = FormData.fromMap({
        'language': language.code,
        'file': await MultipartFile.fromFile(
          filePath,
          filename: filePath.split('/').last,
        ),
      });

      final response = await dio.post<List<int>>(
        ApiPath.voiceAssistant,
        data: formData,
        options: Options(responseType: ResponseType.bytes),
        onSendProgress: onSendProgress,
      );

      final bytes = response.data;
      return bytes == null ? Uint8List(0) : Uint8List.fromList(bytes);
    });

    return result.match(
      (error) => (error: error, audio: null),
      (audio) => (error: null, audio: audio),
    );
  }
}
