import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:propedia/data/dto/property_dto.dart';

/// 매물 API (PropSheet DB)
class PropertyApi {
  final Dio _dio;

  /// 기본 db_id (금토끼부동산)
  static const int defaultDbId = 39;

  PropertyApi(this._dio);

  /// 조건 값 변환 (gte/lte → above/below)
  String _mapCondition(String condition) {
    switch (condition) {
      case 'gte':
        return 'above';
      case 'lte':
        return 'below';
      default:
        return condition;
    }
  }

  /// 전체 매물 지도 데이터 조회 (마커 + 좌표)
  Future<MapDataResponse> getMapData() async {
    debugPrint('📍 지도 데이터 API 호출');
    final response = await _dio.get('/propsheet/api/propsheet/map-data');
    return MapDataResponse.fromJson(response.data);
  }

  /// 카테고리별 매물 목록 조회
  Future<CategoryPropertiesResponse> getCategoryProperties(String viewId) async {
    final response = await _dio.get(
      '/propsheet/api/propsheet/category-properties',
      queryParameters: {'view_id': viewId},
    );
    return CategoryPropertiesResponse.fromJson(response.data);
  }

  /// 매물 상세 조회 (PropSheet 형식 → PropertyRecord 변환)
  Future<PropertyDetailResponse> getPropertyDetail(String recordId) async {
    final response = await _dio.get(
      '/propsheet/api/propsheet/property-detail',
      queryParameters: {'id': recordId, 'db_id': defaultDbId},
    );
    final data = response.data as Map<String, dynamic>;
    final propData = data['property'] as Map<String, dynamic>?;

    if (propData == null) {
      return PropertyDetailResponse(error: data['error'] as String? ?? '매물을 찾을 수 없습니다');
    }

    // PropSheet 영문 필드 → 한글 필드명 변환
    final fields = _convertDetailToFields(propData);
    final record = PropertyRecord(
      id: propData['record_id'] as String? ?? recordId,
      fields: PropertyFields.fromJson(fields),
    );
    return PropertyDetailResponse(property: record);
  }

  /// PropSheet 상세 응답(영문) → PropertyFields 한글 필드 매핑
  Map<String, dynamic> _convertDetailToFields(Map<String, dynamic> p) {
    // 이미지: photo 문자열 → 대표사진 배열
    List<Map<String, dynamic>>? photos;
    if (p['photo'] != null && (p['photo'] as String).isNotEmpty) {
      photos = [{'url': p['photo']}];
    }

    return {
      '지번 주소': p['address'],
      '도로명주소': p['road_address'],
      '매가(만원)': p['price'],
      '보증금(만원)': p['deposit'],
      '월세(만원)': p['rent'],
      '융자(만원)': p['loan'],
      '실투자금': p['investment'],
      '융자제외수익률(%)': p['yield_rate'],
      '토지면적(㎡)': p['land_area'],
      '연면적(㎡)': p['total_area'],
      '건축면적(㎡)': null,
      '건폐율(%)': p['bcr'],
      '용적률(%)': p['far'],
      '층수': p['floors'],
      '주용도': p['usage'],
      '사용승인일': p['approval_date'],
      '건물명': p['building_name'],
      '인접역': p['station'],
      '거리(m)': p['distance'],
      '용도지역': p['zoning'],
      '광고(자동완성)': p['description'],
      '현황': p['status'] is String ? [p['status']] : p['status'],
      '대표사진': photos,
    };
  }

  /// 조건 검색 (마커 데이터 반환)
  Future<PropertySearchResponse> searchProperties(PropertySearchRequest request) async {
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
      '/propsheet/api/propsheet/search-map',
      data: mappedRequest.toJson(),
    );
    return PropertySearchResponse.fromJson(response.data);
  }
}
