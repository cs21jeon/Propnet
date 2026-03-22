import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/datasources/remote/airtable_api.dart';
import 'package:propedia/data/dto/building_dto.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';

export 'package:propedia/presentation/providers/auth_provider.dart' show canSaveToAirtableProvider;

enum AirtableSaveStatus { idle, saving, success, error }

class AirtableSaveState {
  final AirtableSaveStatus status;
  final String? recordId;
  final String? errorMessage;

  const AirtableSaveState({
    this.status = AirtableSaveStatus.idle,
    this.recordId,
    this.errorMessage,
  });
}

class AirtableSaveNotifier extends StateNotifier<AirtableSaveState> {
  final AirtableApi _api;

  AirtableSaveNotifier(this._api) : super(const AirtableSaveState());

  /// 검색 결과를 Airtable에 저장
  Future<bool> saveToAirtable(
    BuildingSearchResponse result, {
    String? selectedDong,
    String? selectedHo,
    AreaInfo? areaInfo,
  }) async {
    state = const AirtableSaveState(status: AirtableSaveStatus.saving);

    try {
      final building = result.building;
      final buildingType = building?.type;

      // 주소 데이터 구성
      final addressData = <String, dynamic>{};
      if (result.address != null) {
        final addr = result.address!;
        addressData['bjdong_code'] = addr.bjdongCode;
        addressData['full_address'] = addr.fullAddress;
        addressData['sido_name'] = addr.sidoName;
        addressData['sigungu_name'] = addr.sigunguName;
        addressData['eupmyeondong_name'] = addr.eupmyeondongName;
      }
      if (result.codes != null) {
        addressData['pnu'] = result.codes!.pnu;
        addressData['sigungu_cd'] = result.codes!.sigunguCd;
        addressData['bjdong_cd'] = result.codes!.bjdongCd;
      }

      // 건물 데이터 구성
      final buildingData = <String, dynamic>{};
      if (building != null) {
        buildingData['has_data'] = building.hasData;
        buildingData['type'] = building.type;
        if (building.buildingInfo != null) {
          buildingData['building_info'] = building.buildingInfo!.toJson();
        }
        if (building.recapTitleInfo != null) {
          buildingData['recap_title_info'] = building.recapTitleInfo;
        }
      }

      // 토지 데이터 구성
      Map<String, dynamic>? landData;
      if (result.land != null) {
        landData = result.land!.toJson();
      }

      Map<String, dynamic> response;

      if (buildingType == '공동주택' && areaInfo != null) {
        // 공동주택: 동/호 정보 포함
        final areaPayload = <String, dynamic>{
          ...areaInfo.toJson(),
          if (selectedDong != null) 'dong': selectedDong,
          if (selectedHo != null) 'ho': selectedHo,
        };
        response = await _api.saveMultiUnit({
          'address': addressData,
          'building': buildingData,
          'area': areaPayload,
          'land': landData,
        });
      } else if (building?.hasData == true) {
        // 일반 건물
        response = await _api.saveBuilding({
          'address': addressData,
          'building': buildingData,
          'land': landData,
        });
      } else {
        // 건물 데이터 없음 (토지만)
        response = await _api.saveBuilding({
          'address': addressData,
          'building': buildingData,
          'land': landData,
        });
      }

      if (response['success'] == true) {
        final recordId = response['record_id']?.toString();
        debugPrint('[Airtable] 저장 성공: $recordId');
        state = AirtableSaveState(
          status: AirtableSaveStatus.success,
          recordId: recordId,
        );
        return true;
      } else {
        final error = response['error']?.toString() ?? '저장 실패';
        state = AirtableSaveState(
          status: AirtableSaveStatus.error,
          errorMessage: error,
        );
        return false;
      }
    } catch (e) {
      debugPrint('[Airtable] 저장 에러: $e');
      String errorMsg = '저장 중 오류가 발생했습니다';
      if (e.toString().contains('403')) {
        errorMsg = '권한이 없습니다';
      }
      state = AirtableSaveState(
        status: AirtableSaveStatus.error,
        errorMessage: errorMsg,
      );
      return false;
    }
  }

  void reset() {
    state = const AirtableSaveState();
  }
}

// Providers
final airtableApiProvider = Provider<AirtableApi>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AirtableApi(apiClient.dio);
});

final airtableSaveProvider =
    StateNotifierProvider<AirtableSaveNotifier, AirtableSaveState>((ref) {
  final api = ref.watch(airtableApiProvider);
  return AirtableSaveNotifier(api);
});
