import 'package:dio/dio.dart';

import '../../../core/error.dart';
import '../../../core/network/api.dart';
import '../../../core/network/api_path.dart';
import '../../../core/network/dio.dart';
import 'personalization_models.dart';

final class PersonalizationApi extends Api {
  PersonalizationApi(@authDio super.dio);

  Future<({NetworkError? error, PersonalizationModel? personalization})>
  loadPersonalization() async {
    final result = await withTimeoutRequest(() async {
      final response = await dio.get<Map<String, dynamic>>(
        ApiPath.profilePersonalization,
      );
      return PersonalizationModel.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, personalization: null),
      (personalization) => (error: null, personalization: personalization),
    );
  }

  Future<({NetworkError? error, PersonalizationModel? personalization})>
  updatePersonalization({
    required String nickname,
    required String speakingStyle,
  }) async {
    final result = await withTimeoutRequest(() async {
      final response = await dio.put<Map<String, dynamic>>(
        ApiPath.profilePersonalization,
        data: {'nickname': nickname, 'speaking_style': speakingStyle},
      );
      return PersonalizationModel.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, personalization: null),
      (personalization) => (error: null, personalization: personalization),
    );
  }

  Future<({NetworkError? error, PersonalizationModel? personalization})>
  updateSetupCompletion({required bool setupCompleted}) async {
    final result = await withTimeoutRequest(() async {
      final response = await dio.put<Map<String, dynamic>>(
        ApiPath.profileSetup,
        data: {'setup_completed': setupCompleted},
      );
      return PersonalizationModel.fromJson(response.data ?? {});
    });

    return result.match(
      (error) => (error: error, personalization: null),
      (personalization) => (error: null, personalization: personalization),
    );
  }
}
