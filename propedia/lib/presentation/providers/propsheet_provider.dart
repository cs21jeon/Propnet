import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/datasources/remote/propsheet_api.dart';
import 'package:propedia/data/dto/building_dto.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';

// 권한 Provider
final canSaveToPropSheetProvider = Provider<bool>((ref) {
  final authState = ref.watch(authProvider);
  return authState.user?.canSaveToPropSheet ?? false;
});

enum PropSheetSaveStatus { idle, saving, success, error, duplicate }

enum PropSheetPropertyType { danil, bubun, jibhap }

class PropSheetSaveState {
  final PropSheetSaveStatus status;
  final String? recordId;
  final String? errorMessage;
  final String? duplicateMessage;

  const PropSheetSaveState({
    this.status = PropSheetSaveStatus.idle,
    this.recordId,
    this.errorMessage,
    this.duplicateMessage,
  });
}

class PropSheetSaveNotifier extends StateNotifier<PropSheetSaveState> {
  final PropSheetApi _api;

  PropSheetSaveNotifier(this._api) : super(const PropSheetSaveState());

  Map<String, dynamic> _buildPayload(
    BuildingSearchResponse result, {
    required PropSheetPropertyType propertyType,
    String? selectedDong,
    String? selectedHo,
    AreaInfo? areaInfo,
    bool forceNew = false,
  }) {
    final building = result.building;

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

    Map<String, dynamic>? landData;
    if (result.land != null) {
      landData = result.land!.toJson();
    }

    final payload = <String, dynamic>{
      'property_type': propertyType.name,
      'address': addressData,
      'building': buildingData,
      'land': landData,
    };

    if (forceNew) payload['force_new'] = true;

    if (propertyType == PropSheetPropertyType.jibhap && areaInfo != null) {
      final areaPayload = <String, dynamic>{
        ...areaInfo.toJson(),
        if (selectedDong != null) 'dong': selectedDong,
        if (selectedHo != null) 'ho': selectedHo,
      };
      payload['area'] = areaPayload;
    }

    return payload;
  }

  /// 검색 결과를 PropSheet에 저장
  Future<bool> saveToPropSheet(
    BuildingSearchResponse result, {
    required PropSheetPropertyType propertyType,
    String? selectedDong,
    String? selectedHo,
    AreaInfo? areaInfo,
    bool forceNew = false,
  }) async {
    state = const PropSheetSaveState(status: PropSheetSaveStatus.saving);

    try {
      final payload = _buildPayload(
        result,
        propertyType: propertyType,
        selectedDong: selectedDong,
        selectedHo: selectedHo,
        areaInfo: areaInfo,
        forceNew: forceNew,
      );

      final response = await _api.saveProperty(payload);

      if (response['success'] == true) {
        final recordId = response['record_id']?.toString();
        debugPrint('[PropSheet] 저장 성공: $recordId');
        state = PropSheetSaveState(
          status: PropSheetSaveStatus.success,
          recordId: recordId,
        );
        return true;
      } else if (response['duplicate'] == true) {
        final msg = response['message']?.toString() ?? '이미 등록된 주소입니다';
        state = PropSheetSaveState(
          status: PropSheetSaveStatus.duplicate,
          duplicateMessage: msg,
        );
        return false;
      } else {
        final error = response['error']?.toString() ?? '저장 실패';
        state = PropSheetSaveState(
          status: PropSheetSaveStatus.error,
          errorMessage: error,
        );
        return false;
      }
    } on DioException catch (e) {
      // 409 Conflict = 중복
      if (e.response?.statusCode == 409) {
        final data = e.response?.data;
        final msg = data is Map ? data['message']?.toString() ?? '이미 등록된 주소입니다' : '이미 등록된 주소입니다';
        state = PropSheetSaveState(
          status: PropSheetSaveStatus.duplicate,
          duplicateMessage: msg,
        );
        return false;
      }
      debugPrint('[PropSheet] 저장 에러: $e');
      String errorMsg = '저장 중 오류가 발생했습니다';
      if (e.response?.statusCode == 403) {
        errorMsg = '권한이 없습니다';
      }
      state = PropSheetSaveState(
        status: PropSheetSaveStatus.error,
        errorMessage: errorMsg,
      );
      return false;
    } catch (e) {
      debugPrint('[PropSheet] 저장 에러: $e');
      state = PropSheetSaveState(
        status: PropSheetSaveStatus.error,
        errorMessage: '저장 중 오류가 발생했습니다',
      );
      return false;
    }
  }

  void reset() {
    state = const PropSheetSaveState();
  }
}

// Providers
final propSheetApiProvider = Provider<PropSheetApi>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return PropSheetApi(apiClient.dio);
});

final propSheetSaveProvider =
    StateNotifierProvider<PropSheetSaveNotifier, PropSheetSaveState>((ref) {
  final api = ref.watch(propSheetApiProvider);
  return PropSheetSaveNotifier(api);
});
