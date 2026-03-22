import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:propedia/data/datasources/remote/property_api.dart';
import 'package:propedia/data/dto/property_dto.dart';

class PropertyRepository {
  final PropertyApi _propertyApi;

  PropertyRepository({required PropertyApi propertyApi})
      : _propertyApi = propertyApi;

  /// 전체 매물 목록 조회
  Future<List<PropertyRecord>> getPropertyList() async {
    try {
      debugPrint('📡 API 호출: getPropertyList()');
      final response = await _propertyApi.getPropertyList();
      debugPrint('📡 API 응답: ${response.records.length}개 매물');

      // 비공개 매물 필터링
      final filtered = response.records.where((r) => !r.isPrivate).toList();
      debugPrint('📡 필터링 후: ${filtered.length}개 매물 (비공개 제외)');

      return filtered;
    } on DioException catch (e) {
      debugPrint('📡 API DioException: ${e.type} - ${e.message}');
      debugPrint('📡 Response: ${e.response?.data}');
      final message = e.response?.data?['error'] ?? '매물 목록 조회 중 오류가 발생했습니다';
      throw Exception(message);
    }
  }

  /// 카테고리별 매물 목록 조회
  Future<List<PropertyRecord>> getCategoryProperties(PropertyCategory category) async {
    try {
      final viewId = category.viewId;
      if (viewId == null) {
        // viewId가 없으면 기본 목록 반환
        return await getPropertyList();
      }

      debugPrint('📡 API 호출: getCategoryProperties($viewId)');
      final response = await _propertyApi.getCategoryProperties(viewId);
      debugPrint('📡 API 응답: ${response.records.length}개 매물');

      // 비공개 매물 필터링
      final filtered = response.records.where((r) => !r.isPrivate).toList();
      debugPrint('📡 필터링 후: ${filtered.length}개 매물');

      return filtered;
    } on DioException catch (e) {
      debugPrint('📡 API DioException: ${e.type} - ${e.message}');
      final message = e.response?.data?['error'] ?? '카테고리 매물 조회 중 오류가 발생했습니다';
      throw Exception(message);
    }
  }

  /// 매물 상세 조회
  Future<PropertyRecord?> getPropertyDetail(String recordId) async {
    try {
      debugPrint('📡 API 호출: getPropertyDetail($recordId)');
      final response = await _propertyApi.getPropertyDetail(recordId);
      debugPrint('📡 API 응답: property=${response.property?.id}');
      return response.property;
    } on DioException catch (e) {
      debugPrint('📡 API DioException: ${e.type} - ${e.message}');
      final message = e.response?.data?['error'] ?? '매물 상세 조회 중 오류가 발생했습니다';
      throw Exception(message);
    }
  }

  /// 이미지 존재 여부 확인
  Future<ImageCheckResponse> checkImage(String recordId) async {
    try {
      return await _propertyApi.checkImage(recordId);
    } on DioException catch (e) {
      debugPrint('📡 이미지 확인 실패: ${e.message}');
      return const ImageCheckResponse(hasImage: false);
    }
  }

  /// 매물 이미지 URL 생성
  String getPropertyImageUrl(String recordId, {String? filename}) {
    final baseUrl = _propertyApi.getPropertyImageUrl(recordId);
    if (filename != null) {
      return '$baseUrl$filename';
    }
    return baseUrl;
  }

  /// 좌표 데이터 조회
  Future<Map<String, PropertyCoordinate>> getCoordinates() async {
    try {
      debugPrint('📡 API 호출: getCoordinates()');
      return await _propertyApi.getCoordinates();
    } on DioException catch (e) {
      debugPrint('📡 좌표 API 오류: ${e.message}');
      throw Exception('좌표 데이터 조회 중 오류가 발생했습니다');
    }
  }

  /// 조건 검색
  Future<PropertySearchResponse> searchProperties({
    String? priceValue,
    String priceCondition = 'all',
    String? yieldValue,
    String yieldCondition = 'all',
    String? investmentValue,
    String investmentCondition = 'all',
    String? areaValue,
    String areaCondition = 'all',
    String? approvalDate,
    String approvalCondition = 'all',
  }) async {
    try {
      debugPrint('📡 API 호출: searchProperties(price=$priceValue/$priceCondition, yield=$yieldValue/$yieldCondition)');

      final request = PropertySearchRequest(
        priceValue: priceValue,
        priceCondition: priceCondition,
        yieldValue: yieldValue,
        yieldCondition: yieldCondition,
        investmentValue: investmentValue,
        investmentCondition: investmentCondition,
        areaValue: areaValue,
        areaCondition: areaCondition,
        approvalDate: approvalDate,
        approvalCondition: approvalCondition,
      );

      final response = await _propertyApi.searchProperties(request);
      debugPrint('📡 API 응답: ${response.count}개 결과');
      return response;
    } on DioException catch (e) {
      debugPrint('📡 API DioException: ${e.type} - ${e.message}');
      final message = e.response?.data?['error'] ?? '검색 중 오류가 발생했습니다';
      throw Exception(message);
    }
  }
}
