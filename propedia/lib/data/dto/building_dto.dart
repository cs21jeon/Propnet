import 'package:freezed_annotation/freezed_annotation.dart';

part 'building_dto.freezed.dart';
part 'building_dto.g.dart';

/// 숫자 또는 "-" 문자열을 int로 변환 ("-"는 0으로 처리)
int? _intFromDynamic(dynamic value) {
  if (value == null) return null;
  if (value is int) return value;
  if (value is String) {
    if (value == '-' || value.trim().isEmpty) return 0;
    return int.tryParse(value) ?? 0;
  }
  return 0;
}

/// 숫자 또는 "-" 문자열을 String으로 변환 ("-"는 null로 처리)
String? _stringFromDynamic(dynamic value) {
  if (value == null) return null;
  if (value is String && (value == '-' || value.trim().isEmpty)) return null;
  return value.toString();
}

/// 도로명 검색 요청
@freezed
class RoadSearchRequest with _$RoadSearchRequest {
  const factory RoadSearchRequest({
    @JsonKey(name: 'road_name') required String roadName,
  }) = _RoadSearchRequest;

  factory RoadSearchRequest.fromJson(Map<String, dynamic> json) =>
      _$RoadSearchRequestFromJson(json);
}

/// 도로명 검색 결과 아이템
@freezed
class RoadSearchResultItem with _$RoadSearchResultItem {
  const factory RoadSearchResultItem({
    required String roadAddr,
    required String jibunAddr,
    required String bdMgtSn,
    String? bdNm,
    String? zipNo,
    String? lnbrMnnm,  // 지번 본번 (토지 지번)
    String? lnbrSlno,  // 지번 부번 (토지 지번)
    String? admCd,     // 법정동코드 (juso.go.kr)
  }) = _RoadSearchResultItem;

  factory RoadSearchResultItem.fromJson(Map<String, dynamic> json) =>
      _$RoadSearchResultItemFromJson(json);
}

/// 도로명 검색 응답
@freezed
class RoadSearchResponse with _$RoadSearchResponse {
  const factory RoadSearchResponse({
    required bool success,
    @Default(0) int count,
    @Default([]) List<RoadSearchResultItem> results,
    String? message,
    String? error,
  }) = _RoadSearchResponse;

  factory RoadSearchResponse.fromJson(Map<String, dynamic> json) =>
      _$RoadSearchResponseFromJson(json);
}

/// 지번 검색 요청
@freezed
class JibunSearchRequest with _$JibunSearchRequest {
  const factory JibunSearchRequest({
    @JsonKey(name: 'bjdong_code') required String bjdongCode,
    required String bun,
    @Default('0000') String ji,
    @JsonKey(name: 'land_type') @Default('1') String landType,
  }) = _JibunSearchRequest;

  factory JibunSearchRequest.fromJson(Map<String, dynamic> json) =>
      _$JibunSearchRequestFromJson(json);
}

/// 건물관리번호 검색 요청
@freezed
class BdMgtSnSearchRequest with _$BdMgtSnSearchRequest {
  const factory BdMgtSnSearchRequest({
    required String bdMgtSn,
    String? lnbrMnnm,  // 지번 본번 (토지 지번)
    String? lnbrSlno,  // 지번 부번 (토지 지번)
    String? admCd,     // 법정동코드 (juso.go.kr)
  }) = _BdMgtSnSearchRequest;

  factory BdMgtSnSearchRequest.fromJson(Map<String, dynamic> json) =>
      _$BdMgtSnSearchRequestFromJson(json);
}

/// 코드 정보
@freezed
class CodeInfo with _$CodeInfo {
  const factory CodeInfo({
    @JsonKey(name: 'sigungu_cd') String? sigunguCd,
    @JsonKey(name: 'bjdong_cd') String? bjdongCd,
    String? pnu,
  }) = _CodeInfo;

  factory CodeInfo.fromJson(Map<String, dynamic> json) =>
      _$CodeInfoFromJson(json);
}

/// 주소 정보
@freezed
class AddressInfo with _$AddressInfo {
  const factory AddressInfo({
    @JsonKey(name: 'bjdong_code') String? bjdongCode,
    @JsonKey(name: 'full_address') String? fullAddress,
    @JsonKey(name: 'sido_name') String? sidoName,
    @JsonKey(name: 'sigungu_name') String? sigunguName,
    @JsonKey(name: 'eupmyeondong_name') String? eupmyeondongName,
  }) = _AddressInfo;

  factory AddressInfo.fromJson(Map<String, dynamic> json) =>
      _$AddressInfoFromJson(json);
}

/// 건축물 기본 정보
@freezed
class BuildingBasicInfo with _$BuildingBasicInfo {
  const factory BuildingBasicInfo({
    // 기본 정보
    @JsonKey(name: 'building_name') String? buildingName,
    @JsonKey(name: 'dong_nm') String? dongNm,
    @JsonKey(name: 'plat_plc') String? platPlc,
    @JsonKey(name: 'new_plat_plc') String? newPlatPlc,

    // 용도
    @JsonKey(name: 'main_purpose') String? mainPurpose,
    @JsonKey(name: 'etc_purpose') String? etcPurpose,

    // 구조
    @JsonKey(name: 'main_structure') String? mainStructure,
    String? roof,
    @JsonKey(name: 'etc_roof') String? etcRoof,

    // 층수
    @JsonKey(name: 'total_floors') int? totalFloors,
    @JsonKey(name: 'basement_floors') int? basementFloors,
    double? height,

    // 면적
    @JsonKey(name: 'land_area') double? landArea,
    @JsonKey(name: 'building_area') double? buildingArea,
    @JsonKey(name: 'total_area') double? totalArea,
    @JsonKey(name: 'vl_rat_estm_tot_area') double? vlRatEstmTotArea,

    // 비율
    @JsonKey(name: 'building_coverage') double? buildingCoverage,
    @JsonKey(name: 'floor_area_ratio') double? floorAreaRatio,

    // 세대/호수 정보
    @JsonKey(name: 'family_cnt', fromJson: _intFromDynamic) int? familyCnt,
    @JsonKey(name: 'hhld_cnt', fromJson: _intFromDynamic) int? hhldCnt,
    @JsonKey(name: 'ho_cnt', fromJson: _intFromDynamic) int? hoCnt,

    // 설비
    @JsonKey(name: 'elevator_count', fromJson: _intFromDynamic) int? elevatorCount,
    @JsonKey(name: 'emergency_elevator_count', fromJson: _intFromDynamic) int? emergencyElevatorCount,
    @JsonKey(name: 'total_parking', fromJson: _stringFromDynamic) String? totalParking,

    // 일자
    @JsonKey(name: 'permit_date') String? permitDate,
    @JsonKey(name: 'use_approval_date') String? useApprovalDate,
    @JsonKey(name: 'permit_date_raw') String? permitDateRaw,
    @JsonKey(name: 'use_approval_date_raw') String? useApprovalDateRaw,

    // 가격 (개별주택/공동주택)
    @JsonKey(name: 'house_price') int? housePrice,
    @JsonKey(name: 'house_price_year') String? housePriceYear,
    @JsonKey(name: 'house_price_month') String? housePriceMonth,
  }) = _BuildingBasicInfo;

  factory BuildingBasicInfo.fromJson(Map<String, dynamic> json) =>
      _$BuildingBasicInfoFromJson(json);
}

/// 층별 정보
@freezed
class FloorInfo with _$FloorInfo {
  const factory FloorInfo({
    @JsonKey(name: 'floor_no') int? floorNo,
    @JsonKey(name: 'floor_name') String? floorName,
    @JsonKey(name: 'floor_gb') String? floorGb,
    double? area,
    String? purpose,
    @JsonKey(name: 'etc_purpose') String? etcPurpose,
    String? structure,
  }) = _FloorInfo;

  factory FloorInfo.fromJson(Map<String, dynamic> json) =>
      _$FloorInfoFromJson(json);
}

/// 건축물 정보 (검색 결과)
@freezed
class BuildingInfo with _$BuildingInfo {
  const factory BuildingInfo({
    @JsonKey(name: 'has_data') @Default(false) bool hasData,
    String? type,
    @JsonKey(name: 'building_info') BuildingBasicInfo? buildingInfo,
    @JsonKey(name: 'recap_title_info') Map<String, dynamic>? recapTitleInfo,
    @JsonKey(name: 'dong_ho_dict') Map<String, dynamic>? dongHoDict,
    @JsonKey(name: 'floor_info') List<FloorInfo>? floorInfo,
  }) = _BuildingInfo;

  factory BuildingInfo.fromJson(Map<String, dynamic> json) =>
      _$BuildingInfoFromJson(json);
}

/// 토지 정보
@freezed
class LandInfo with _$LandInfo {
  const factory LandInfo({
    @JsonKey(name: 'land_area') double? landArea,
    @JsonKey(name: 'parcel_count') int? parcelCount,
    @JsonKey(name: 'land_category') String? landCategory,
    @JsonKey(name: 'land_category_name') String? landCategoryName,
    @JsonKey(name: 'public_land_price') int? publicLandPrice,
    @JsonKey(name: 'price_year') String? priceYear,
    @JsonKey(name: 'zone_classification') String? zoneClassification,
    @JsonKey(name: 'land_use_situation_name') String? landUseSituationName,
    @JsonKey(name: 'topography_height_name') String? topographyHeightName,
    @JsonKey(name: 'topography_form_name') String? topographyFormName,
    @JsonKey(name: 'road_side_name') String? roadSideName,
    List<Map<String, dynamic>>? details,
  }) = _LandInfo;

  factory LandInfo.fromJson(Map<String, dynamic> json) =>
      _$LandInfoFromJson(json);
}

/// 건축물 검색 응답 (지번/건물관리번호)
@freezed
class BuildingSearchResponse with _$BuildingSearchResponse {
  const factory BuildingSearchResponse({
    required bool success,
    CodeInfo? codes,
    AddressInfo? address,
    BuildingInfo? building,
    LandInfo? land,
    String? error,
  }) = _BuildingSearchResponse;

  factory BuildingSearchResponse.fromJson(Map<String, dynamic> json) =>
      _$BuildingSearchResponseFromJson(json);
}

/// 법정동 검색 결과 아이템
@freezed
class BjdongSearchItem with _$BjdongSearchItem {
  const factory BjdongSearchItem({
    @JsonKey(name: 'bjdong_code') required String code,
    @JsonKey(name: 'full_address') String? fullAddress,
    @JsonKey(name: 'sido_name') String? sidoName,
    @JsonKey(name: 'sigungu_name') String? sigunguName,
    @JsonKey(name: 'eupmyeondong_name') String? eupmyeondongName,
    @JsonKey(name: 'ri_name') String? riName,
  }) = _BjdongSearchItem;

  factory BjdongSearchItem.fromJson(Map<String, dynamic> json) =>
      _$BjdongSearchItemFromJson(json);
}

/// 법정동 검색 응답
@freezed
class BjdongSearchResponse with _$BjdongSearchResponse {
  const factory BjdongSearchResponse({
    required bool success,
    @Default(0) int count,
    @Default([]) List<BjdongSearchItem> results,
    String? error,
  }) = _BjdongSearchResponse;

  factory BjdongSearchResponse.fromJson(Map<String, dynamic> json) =>
      _$BjdongSearchResponseFromJson(json);
}

/// 공동주택 동/호별 상세 정보 요청
@freezed
class AreaInfoRequest with _$AreaInfoRequest {
  const factory AreaInfoRequest({
    @JsonKey(name: 'bjdong_code') required String bjdongCode,
    required String bun,
    @Default('0000') String ji,
    @JsonKey(name: 'dong_nm') required String dongNm,
    @JsonKey(name: 'ho_nm') required String hoNm,
  }) = _AreaInfoRequest;

  factory AreaInfoRequest.fromJson(Map<String, dynamic> json) =>
      _$AreaInfoRequestFromJson(json);
}

/// 면적 정보
@freezed
class AreaInfo with _$AreaInfo {
  const factory AreaInfo({
    @JsonKey(name: 'dong_nm') String? dongNm,
    @JsonKey(name: 'ho_nm') String? hoNm,
    @JsonKey(name: 'bld_nm') String? bldNm,
    @JsonKey(name: 'floor_no') int? floorNo,
    @JsonKey(name: 'floor_gb') String? floorGb,
    @JsonKey(name: 'exclusive_area') double? exclusiveArea,
    @JsonKey(name: 'supply_area') double? supplyArea,
    @JsonKey(name: 'sale_area') double? saleArea,
    @JsonKey(name: 'land_share') double? landShare,
    @JsonKey(name: 'land_share_ratio') String? landShareRatio,
    @JsonKey(name: 'house_price') int? housePrice,
    @JsonKey(name: 'house_price_year') String? housePriceYear,
    @JsonKey(name: 'house_price_month') String? housePriceMonth,
    @JsonKey(name: 'main_purpose') String? mainPurpose,
    @JsonKey(name: 'etc_purpose') String? etcPurpose,
    @JsonKey(name: 'dong_title_info') Map<String, dynamic>? dongTitleInfo,
  }) = _AreaInfo;

  factory AreaInfo.fromJson(Map<String, dynamic> json) =>
      _$AreaInfoFromJson(json);
}

/// 면적 정보 응답
@freezed
class AreaInfoResponse with _$AreaInfoResponse {
  const factory AreaInfoResponse({
    required bool success,
    @JsonKey(name: 'area_info') AreaInfo? areaInfo,
    String? error,
  }) = _AreaInfoResponse;

  factory AreaInfoResponse.fromJson(Map<String, dynamic> json) =>
      _$AreaInfoResponseFromJson(json);
}
