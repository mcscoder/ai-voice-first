import '../../../core/error.dart';
import 'personalization_api.dart';
import 'personalization_models.dart';

class PersonalizationRepository {
  PersonalizationRepository(this._api);

  final PersonalizationApi _api;

  Future<({NetworkError? error, PersonalizationModel? personalization})>
  loadPersonalization() {
    return _api.loadPersonalization();
  }

  Future<({NetworkError? error, PersonalizationModel? personalization})>
  updatePersonalization({
    required String nickname,
    required String speakingStyle,
  }) {
    return _api.updatePersonalization(
      nickname: nickname,
      speakingStyle: speakingStyle,
    );
  }

  Future<({NetworkError? error, PersonalizationModel? personalization})>
  updateSetupCompletion({required bool setupCompleted}) {
    return _api.updateSetupCompletion(setupCompleted: setupCompleted);
  }
}
