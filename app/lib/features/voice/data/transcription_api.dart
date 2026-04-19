import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

import '../../../core/error.dart';
import '../../../core/network/api.dart';
import '../../../core/network/api_path.dart';
import '../../../core/network/dio.dart';
import 'transcription_response.dart';
import 'voice_language.dart';

@lazySingleton
base class TranscriptionApi extends Api {
  TranscriptionApi(@nonAuthDio super.dio);

  Future<({NetworkError? error, TranscriptionResponse? response})> transcribe({
    required String filePath,
    required VoiceLanguage language,
  }) async {
    final result = await withTimeoutRequest(() async {
      final formData = FormData.fromMap({
        'language': language.code,
        'file': await MultipartFile.fromFile(
          filePath,
          filename: filePath.split('/').last,
        ),
      });

      final response = await dio.post<Map<String, dynamic>>(
        ApiPath.transcribe,
        data: formData,
      );

      return TranscriptionResponse.fromJson(response.data ?? const {});
    });

    return result.match(
      (error) => (error: error, response: null),
      (response) => (error: null, response: response),
    );
  }
}
