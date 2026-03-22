import 'package:dio/dio.dart';
import 'package:propedia/data/dto/map_dto.dart';

class MapApi {
  final Dio _dio;

  MapApi(this._dio);

  /// 좌표 → 지번 변환
  Future<MapClickJibunResponse> clickToJibun(MapClickJibunRequest request) async {
    final response = await _dio.post(
      '/app/api/map/click-jibun',
      data: request.toJson(),
    );
    return MapClickJibunResponse.fromJson(response.data);
  }

  /// 필지 경계 조회
  Future<ParcelBoundaryResponse> getParcelBoundary({
    required String pnu,
    required double lat,
    required double lng,
  }) async {
    final response = await _dio.get(
      '/app/api/map/parcel-boundary',
      queryParameters: {
        'pnu': pnu,
        'lat': lat,
        'lng': lng,
      },
    );
    return ParcelBoundaryResponse.fromJson(response.data);
  }

  /// 주소 → 좌표 변환 (지오코딩)
  Future<GeocodingResponse> geocodeAddress(String address) async {
    final response = await _dio.get(
      '/app/api/map/geocode',
      queryParameters: {'address': address},
    );
    return GeocodingResponse.fromJson(response.data);
  }
}
