import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:propedia/data/datasources/remote/map_api.dart';
import 'package:propedia/data/dto/map_dto.dart';

class MapRepository {
  final MapApi _mapApi;

  MapRepository({required MapApi mapApi}) : _mapApi = mapApi;

  /// 좌표 → 지번 변환
  Future<MapClickJibunResponse> clickToJibun({
    required double lat,
    required double lng,
  }) async {
    try {
      debugPrint('📡 API 호출: clickToJibun(lat=$lat, lng=$lng)');
      final request = MapClickJibunRequest(lat: lat, lng: lng);
      final response = await _mapApi.clickToJibun(request);
      debugPrint('📡 API 응답: success=${response.success}');
      return response;
    } on DioException catch (e) {
      debugPrint('📡 API DioException: ${e.type} - ${e.message}');
      debugPrint('📡 Response: ${e.response?.data}');
      final message = e.response?.data?['error'] ?? '좌표 변환 중 오류가 발생했습니다';
      return MapClickJibunResponse(
        success: false,
        error: message,
      );
    }
  }

  /// 필지 경계 조회
  Future<ParcelBoundaryResponse> getParcelBoundary({
    required String pnu,
    required double lat,
    required double lng,
  }) async {
    try {
      debugPrint('📡 API 호출: getParcelBoundary(pnu=$pnu)');
      final response = await _mapApi.getParcelBoundary(
        pnu: pnu,
        lat: lat,
        lng: lng,
      );
      debugPrint('📡 API 응답: success=${response.success}');
      return response;
    } on DioException catch (e) {
      debugPrint('📡 API DioException: ${e.type} - ${e.message}');
      final message = e.response?.data?['error'] ?? '필지 경계 조회 중 오류가 발생했습니다';
      return ParcelBoundaryResponse(
        success: false,
        error: message,
      );
    }
  }

  /// 주소 → 좌표 변환 (지오코딩)
  Future<GeocodingResponse> geocodeAddress(String address) async {
    try {
      debugPrint('📡 API 호출: geocodeAddress($address)');
      final response = await _mapApi.geocodeAddress(address);
      debugPrint('📡 API 응답: success=${response.success}, lat=${response.lat}, lng=${response.lng}');
      return response;
    } on DioException catch (e) {
      debugPrint('📡 API DioException: ${e.type} - ${e.message}');
      final message = e.response?.data?['error'] ?? '주소 변환 중 오류가 발생했습니다';
      return GeocodingResponse(
        success: false,
        error: message,
      );
    }
  }
}
