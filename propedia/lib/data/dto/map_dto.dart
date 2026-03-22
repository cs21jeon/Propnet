import 'package:freezed_annotation/freezed_annotation.dart';

part 'map_dto.freezed.dart';
part 'map_dto.g.dart';

/// 지도 클릭 → 지번 변환 요청
@freezed
class MapClickJibunRequest with _$MapClickJibunRequest {
  const factory MapClickJibunRequest({
    required double lat,
    required double lng,
  }) = _MapClickJibunRequest;

  factory MapClickJibunRequest.fromJson(Map<String, dynamic> json) =>
      _$MapClickJibunRequestFromJson(json);
}

/// 지번 정보
@freezed
class JibunInfo with _$JibunInfo {
  const factory JibunInfo({
    required String address,
    required String pnu,
    @JsonKey(name: 'bjdong_code') required String bjdongCode,
    required String bun,
    required String ji,
    @JsonKey(name: 'land_type') required String landType,
    @JsonKey(name: 'land_type_name') String? landTypeName,
    @JsonKey(name: 'road_address') String? roadAddress,
    @JsonKey(name: 'main_purpose') String? mainPurpose,
  }) = _JibunInfo;

  factory JibunInfo.fromJson(Map<String, dynamic> json) =>
      _$JibunInfoFromJson(json);
}

/// 지도 클릭 → 지번 변환 응답
@freezed
class MapClickJibunResponse with _$MapClickJibunResponse {
  const factory MapClickJibunResponse({
    required bool success,
    @JsonKey(name: 'jibun_info') JibunInfo? jibunInfo,
    String? error,
  }) = _MapClickJibunResponse;

  factory MapClickJibunResponse.fromJson(Map<String, dynamic> json) =>
      _$MapClickJibunResponseFromJson(json);
}

/// 필지 경계 Geometry (GeoJSON MultiPolygon)
@freezed
class ParcelGeometry with _$ParcelGeometry {
  const factory ParcelGeometry({
    required String type,
    required List<dynamic> coordinates,
  }) = _ParcelGeometry;

  factory ParcelGeometry.fromJson(Map<String, dynamic> json) =>
      _$ParcelGeometryFromJson(json);
}

/// 필지 속성 정보
@freezed
class ParcelProperties with _$ParcelProperties {
  const factory ParcelProperties({
    String? addr,
    String? pnu,
    String? jibun,
    String? jiga,
    @JsonKey(name: 'gosi_year') String? gosiYear,
  }) = _ParcelProperties;

  factory ParcelProperties.fromJson(Map<String, dynamic> json) =>
      _$ParcelPropertiesFromJson(json);
}

/// 필지 경계 응답
@freezed
class ParcelBoundaryResponse with _$ParcelBoundaryResponse {
  const factory ParcelBoundaryResponse({
    required bool success,
    ParcelGeometry? geometry,
    ParcelProperties? properties,
    String? error,
  }) = _ParcelBoundaryResponse;

  factory ParcelBoundaryResponse.fromJson(Map<String, dynamic> json) =>
      _$ParcelBoundaryResponseFromJson(json);
}

/// 지오코딩 응답
@freezed
class GeocodingResponse with _$GeocodingResponse {
  const factory GeocodingResponse({
    required bool success,
    double? lat,
    double? lng,
    String? address,
    String? error,
  }) = _GeocodingResponse;

  factory GeocodingResponse.fromJson(Map<String, dynamic> json) =>
      _$GeocodingResponseFromJson(json);
}
