import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:propedia/data/dto/property_dto.dart';

/// 매물 API (Port 8000 서버)
class PropertyApi {
  final Dio _dio;

  PropertyApi(this._dio);

  /// 조건 값 변환 (gte/lte → above/below)
  String _mapCondition(String condition) {
    switch (condition) {
      case 'gte':
        return 'above';
      case 'lte':
        return 'below';
      default:
        return condition; // all, above, below 그대로 반환
    }
  }

  /// 전체 매물 목록 조회
  Future<PropertyListResponse> getPropertyList() async {
    final response = await _dio.get('/api/property-list');
    return PropertyListResponse.fromJson(response.data);
  }

  /// 카테고리별 매물 목록 조회
  Future<CategoryPropertiesResponse> getCategoryProperties(String viewId) async {
    final response = await _dio.get(
      '/api/category-properties',
      queryParameters: {'view': viewId},
    );
    return CategoryPropertiesResponse.fromJson(response.data);
  }

  /// 매물 상세 조회
  Future<PropertyDetailResponse> getPropertyDetail(String recordId) async {
    final response = await _dio.get(
      '/api/property-detail',
      queryParameters: {'id': recordId},
    );
    return PropertyDetailResponse.fromJson(response.data);
  }

  /// 이미지 존재 여부 확인
  Future<ImageCheckResponse> checkImage(String recordId) async {
    final response = await _dio.get(
      '/api/check-image',
      queryParameters: {'record_id': recordId},
    );
    return ImageCheckResponse.fromJson(response.data);
  }

  /// 매물 이미지 URL 생성
  String getPropertyImageUrl(String recordId) {
    return '${_dio.options.baseUrl}/airtable_backup/images/$recordId/';
  }

  /// 좌표 데이터 조회
  Future<Map<String, PropertyCoordinate>> getCoordinates() async {
    debugPrint('📍 좌표 API 호출: /api/coordinates');
    final response = await _dio.get('/api/coordinates');
    final data = response.data as Map<String, dynamic>;
    debugPrint('📍 좌표 로드 완료: ${data.length}개');
    return data.map((key, value) => MapEntry(
      key,
      PropertyCoordinate.fromJson(value as Map<String, dynamic>),
    ));
  }

  /// 조건 검색 (마커 데이터 반환)
  Future<PropertySearchResponse> searchProperties(PropertySearchRequest request) async {
    // 조건 값 변환 적용
    final mappedRequest = PropertySearchRequest(
      priceValue: request.priceValue,
      priceCondition: _mapCondition(request.priceCondition),
      yieldValue: request.yieldValue,
      yieldCondition: _mapCondition(request.yieldCondition),
      investmentValue: request.investmentValue,
      investmentCondition: _mapCondition(request.investmentCondition),
      areaValue: request.areaValue,
      areaCondition: _mapCondition(request.areaCondition),
      approvalDate: request.approvalDate,
      approvalCondition: _mapCondition(request.approvalCondition),
    );

    debugPrint('🔍 검색 API 호출: ${mappedRequest.toJson()}');
    final response = await _dio.post(
      '/api/search-map',
      data: mappedRequest.toJson(),
    );
    return PropertySearchResponse.fromJson(response.data);
  }
}
