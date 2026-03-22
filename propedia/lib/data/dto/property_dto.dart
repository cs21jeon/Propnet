import 'package:freezed_annotation/freezed_annotation.dart';

part 'property_dto.freezed.dart';
part 'property_dto.g.dart';

/// 가격(만원)을 억 형식으로 변환 (예: 17.8억)
String formatPrice(int? priceInManwon) {
  if (priceInManwon == null || priceInManwon == 0) return '-';

  // 억 단위로 변환 (소수점 1자리)
  final eokValue = priceInManwon / 10000;

  if (eokValue >= 1) {
    // 1억 이상: 소수점 있으면 표시, 없으면 정수로
    if (eokValue == eokValue.truncate()) {
      return '${eokValue.toInt()}억';
    } else {
      return '${eokValue.toStringAsFixed(1)}억';
    }
  } else {
    // 1억 미만: 만원 단위로 표시
    return '${priceInManwon}만';
  }
}

/// 면적(㎡)을 평으로 변환
int sqmToPyung(double? sqm) {
  if (sqm == null || sqm == 0) return 0;
  return (sqm / 3.3058).round();
}

/// dynamic 값을 int로 변환
int? _intFromDynamic(dynamic value) {
  if (value == null) return null;
  if (value is int) return value;
  if (value is double) return value.toInt();
  if (value is String) {
    final cleaned = value.replaceAll(',', '');
    return int.tryParse(cleaned);
  }
  return null;
}

/// dynamic 값을 double로 변환
double? _doubleFromDynamic(dynamic value) {
  if (value == null) return null;
  if (value is double) return value;
  if (value is int) return value.toDouble();
  if (value is String) {
    final cleaned = value.replaceAll(',', '').replaceAll('%', '');
    return double.tryParse(cleaned);
  }
  return null;
}

/// 현황 필드를 List<String>으로 변환
List<String> _statusFromDynamic(dynamic value) {
  if (value == null) return [];
  if (value is List) {
    return value.map((e) => e.toString()).toList();
  }
  if (value is String) {
    return [value];
  }
  return [];
}

// =============================================================================
// 매물 목록 아이템 (Airtable fields 직접 매핑)
// =============================================================================
@freezed
class PropertyRecord with _$PropertyRecord {
  const PropertyRecord._();

  const factory PropertyRecord({
    required String id,
    required PropertyFields fields,
  }) = _PropertyRecord;

  factory PropertyRecord.fromJson(Map<String, dynamic> json) =>
      _$PropertyRecordFromJson(json);

  /// 비공개 매물인지 확인
  bool get isPrivate {
    final status = fields.status;
    if (status == null) return false;
    return status.contains('비공개');
  }

  /// 표시용 가격
  String get priceDisplay => formatPrice(fields.price);

  /// 토지면적(평)
  int get landAreaPyung => sqmToPyung(fields.landArea);
}

/// 매물 필드 (Airtable fields 매핑)
@freezed
class PropertyFields with _$PropertyFields {
  const factory PropertyFields({
    // 주소
    @JsonKey(name: '지번 주소') String? address,
    @JsonKey(name: '도로명주소') String? roadAddress,

    // 가격 정보
    @JsonKey(name: '매가(만원)', fromJson: _intFromDynamic) int? price,
    @JsonKey(name: '보증금(만원)', fromJson: _intFromDynamic) int? deposit,
    @JsonKey(name: '월세(만원)', fromJson: _intFromDynamic) int? monthlyRent,
    @JsonKey(name: '융자(만원)', fromJson: _intFromDynamic) int? loan,
    @JsonKey(name: '실투자금', fromJson: _intFromDynamic) int? investment,
    @JsonKey(name: '융자제외수익률(%)', fromJson: _doubleFromDynamic) double? yieldRate,
    @JsonKey(name: '감정가(만원,랜드북)', fromJson: _intFromDynamic) int? appraisedValue,
    @JsonKey(name: '감정가율(%)', fromJson: _doubleFromDynamic) double? appraisalRate,

    // 면적 정보
    @JsonKey(name: '토지면적(㎡)', fromJson: _doubleFromDynamic) double? landArea,
    @JsonKey(name: '연면적(㎡)', fromJson: _doubleFromDynamic) double? totalFloorArea,
    @JsonKey(name: '건축면적(㎡)', fromJson: _doubleFromDynamic) double? buildingArea,
    @JsonKey(name: '용적률산정용연면적(㎡)', fromJson: _doubleFromDynamic) double? farArea,

    // 건물 정보
    @JsonKey(name: '층수') String? floors,
    @JsonKey(name: '주용도') String? mainUsage,
    @JsonKey(name: '기타용도') String? etcUsage,
    @JsonKey(name: '주구조') String? structure,
    @JsonKey(name: '지붕') String? roof,
    @JsonKey(name: '사용승인일') String? approvalDate,
    @JsonKey(name: '건물명') String? buildingName,
    @JsonKey(name: '건물구성') String? buildingComposition,
    @JsonKey(name: '건폐율(%)', fromJson: _doubleFromDynamic) double? buildingCoverageRatio,
    @JsonKey(name: '용적률(%)', fromJson: _doubleFromDynamic) double? floorAreaRatio,
    @JsonKey(name: '높이(m)', fromJson: _doubleFromDynamic) double? height,

    // 설비
    @JsonKey(name: '주차대수', fromJson: _intFromDynamic) int? parkingCount,
    @JsonKey(name: '승강기수', fromJson: _intFromDynamic) int? elevatorCount,
    @JsonKey(name: '세대/가구/호') String? householdInfo,

    // 위치 정보
    @JsonKey(name: '용도지역') String? zoning,
    @JsonKey(name: '공시지가(원/㎡)', fromJson: _intFromDynamic) int? landPrice,
    @JsonKey(name: '인접역') String? nearStation,
    @JsonKey(name: '거리(m)', fromJson: _intFromDynamic) int? stationDistance,

    // 상태 및 링크
    @JsonKey(name: '현황', fromJson: _statusFromDynamic) List<String>? status,
    @JsonKey(name: '광고(자동완성)') String? description,
    @JsonKey(name: '지도') String? mapLink,
    @JsonKey(name: '사진링크') String? photoLink,
    @JsonKey(name: '디스코광고') String? discoLink,

    // 이미지 (Airtable attachment)
    @JsonKey(name: '대표사진') List<AirtableAttachment>? representativePhoto,
  }) = _PropertyFields;

  factory PropertyFields.fromJson(Map<String, dynamic> json) =>
      _$PropertyFieldsFromJson(json);
}

/// Airtable 첨부파일
@freezed
class AirtableAttachment with _$AirtableAttachment {
  const factory AirtableAttachment({
    String? id,
    String? url,
    String? filename,
    int? size,
    String? type,
    int? width,
    int? height,
    AirtableThumbnails? thumbnails,
  }) = _AirtableAttachment;

  factory AirtableAttachment.fromJson(Map<String, dynamic> json) =>
      _$AirtableAttachmentFromJson(json);
}

/// Airtable 썸네일
@freezed
class AirtableThumbnails with _$AirtableThumbnails {
  const factory AirtableThumbnails({
    AirtableThumbnail? small,
    AirtableThumbnail? large,
    AirtableThumbnail? full,
  }) = _AirtableThumbnails;

  factory AirtableThumbnails.fromJson(Map<String, dynamic> json) =>
      _$AirtableThumbnailsFromJson(json);
}

/// Airtable 썸네일 상세
@freezed
class AirtableThumbnail with _$AirtableThumbnail {
  const factory AirtableThumbnail({
    String? url,
    int? width,
    int? height,
  }) = _AirtableThumbnail;

  factory AirtableThumbnail.fromJson(Map<String, dynamic> json) =>
      _$AirtableThumbnailFromJson(json);
}

// =============================================================================
// API 응답 DTO
// =============================================================================

/// 매물 목록 응답
@freezed
class PropertyListResponse with _$PropertyListResponse {
  const factory PropertyListResponse({
    @Default([]) List<PropertyRecord> records,
    String? error,
  }) = _PropertyListResponse;

  factory PropertyListResponse.fromJson(Map<String, dynamic> json) =>
      _$PropertyListResponseFromJson(json);
}

/// 카테고리별 매물 응답
@freezed
class CategoryPropertiesResponse with _$CategoryPropertiesResponse {
  const factory CategoryPropertiesResponse({
    @Default([]) List<PropertyRecord> records,
    @JsonKey(name: 'view_id') String? viewId,
    @JsonKey(name: 'total_count') @Default(0) int totalCount,
    String? source,
    String? error,
  }) = _CategoryPropertiesResponse;

  factory CategoryPropertiesResponse.fromJson(Map<String, dynamic> json) =>
      _$CategoryPropertiesResponseFromJson(json);
}

/// 매물 상세 응답
@freezed
class PropertyDetailResponse with _$PropertyDetailResponse {
  const factory PropertyDetailResponse({
    PropertyRecord? property,
    String? error,
  }) = _PropertyDetailResponse;

  factory PropertyDetailResponse.fromJson(Map<String, dynamic> json) =>
      _$PropertyDetailResponseFromJson(json);
}

/// 이미지 확인 응답
@freezed
class ImageCheckResponse with _$ImageCheckResponse {
  const factory ImageCheckResponse({
    @Default(false) bool hasImage,
    String? filename,
    String? error,
  }) = _ImageCheckResponse;

  factory ImageCheckResponse.fromJson(Map<String, dynamic> json) =>
      _$ImageCheckResponseFromJson(json);
}

// =============================================================================
// 지도 마커 DTO
// =============================================================================

/// 지도용 마커 데이터
@freezed
class PropertyMapMarker with _$PropertyMapMarker {
  const PropertyMapMarker._();

  const factory PropertyMapMarker({
    required double lat,
    required double lon,
    String? address,
    @JsonKey(fromJson: _doubleFromDynamic) double? price,
    @JsonKey(name: 'price_display') String? priceDisplay,
    @JsonKey(name: 'yield', fromJson: _doubleFromDynamic) double? yieldRate,
    @JsonKey(fromJson: _doubleFromDynamic) double? area,
    @JsonKey(name: 'approval_date') String? approvalDate,
    @JsonKey(name: 'record_id') String? recordId,
    String? popup,
  }) = _PropertyMapMarker;

  factory PropertyMapMarker.fromJson(Map<String, dynamic> json) =>
      _$PropertyMapMarkerFromJson(json);

  /// 표시용 가격
  String get displayPrice => priceDisplay ?? formatPrice(price?.toInt());

  /// 마커 ID (record_id 또는 주소 기반)
  String get markerId => recordId ?? address ?? '${lat}_$lon';
}

/// 좌표 데이터 (coordinates.json에서 로드)
@freezed
class PropertyCoordinate with _$PropertyCoordinate {
  const factory PropertyCoordinate({
    required double lat,
    required double lon,
    String? address,
  }) = _PropertyCoordinate;

  factory PropertyCoordinate.fromJson(Map<String, dynamic> json) =>
      _$PropertyCoordinateFromJson(json);
}

// =============================================================================
// 검색 요청 DTO
// =============================================================================

/// 매물 검색 요청
@freezed
class PropertySearchRequest with _$PropertySearchRequest {
  const factory PropertySearchRequest({
    @JsonKey(name: 'price_value') String? priceValue,
    @JsonKey(name: 'price_condition') @Default('all') String priceCondition,
    @JsonKey(name: 'yield_value') String? yieldValue,
    @JsonKey(name: 'yield_condition') @Default('all') String yieldCondition,
    @JsonKey(name: 'investment_value') String? investmentValue,
    @JsonKey(name: 'investment_condition') @Default('all') String investmentCondition,
    @JsonKey(name: 'area_value') String? areaValue,
    @JsonKey(name: 'area_condition') @Default('all') String areaCondition,
    @JsonKey(name: 'approval_date') String? approvalDate,
    @JsonKey(name: 'approval_condition') @Default('all') String approvalCondition,
  }) = _PropertySearchRequest;

  factory PropertySearchRequest.fromJson(Map<String, dynamic> json) =>
      _$PropertySearchRequestFromJson(json);
}

/// 검색 결과 응답 (마커 및 통계 포함)
@freezed
class PropertySearchResponse with _$PropertySearchResponse {
  const factory PropertySearchResponse({
    @Default(0) int count,
    @JsonKey(name: 'map_html') String? mapHtml,
    @Default([]) List<PropertyRecord> properties,
    @Default([]) List<PropertyMapMarker> markers,
    Map<String, dynamic>? statistics,
    String? error,
  }) = _PropertySearchResponse;

  factory PropertySearchResponse.fromJson(Map<String, dynamic> json) =>
      _$PropertySearchResponseFromJson(json);
}

// =============================================================================
// 카테고리 정의
// =============================================================================

/// 매물 카테고리
enum PropertyCategory {
  reconstruction('재건축용 토지', 'viwzEVzrr47fCbDNU'),
  highYield('고수익률 건물', 'viwxS4dKAcQWmB0Be'),
  lowCost('저가단독주택', 'viwUKnawSP8SkV9Sx');

  final String label;
  final String? viewId;

  const PropertyCategory(this.label, this.viewId);
}
