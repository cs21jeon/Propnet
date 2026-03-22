import 'package:dio/dio.dart';
import 'package:propedia/data/dto/building_dto.dart';

class BuildingApi {
  final Dio _dio;

  BuildingApi(this._dio);

  /// 도로명 주소로 검색
  Future<RoadSearchResponse> searchByRoad(RoadSearchRequest request) async {
    final response = await _dio.post(
      '/app/api/search/road',
      data: request.toJson(),
    );
    return RoadSearchResponse.fromJson(response.data);
  }

  /// 지번 주소로 검색
  Future<BuildingSearchResponse> searchByJibun(JibunSearchRequest request) async {
    final response = await _dio.post(
      '/app/api/search/jibun',
      data: request.toJson(),
    );
    return BuildingSearchResponse.fromJson(response.data);
  }

  /// 건물관리번호로 검색
  Future<BuildingSearchResponse> searchByBdMgtSn(BdMgtSnSearchRequest request) async {
    final response = await _dio.post(
      '/app/api/search/bdmgtsn',
      data: request.toJson(),
    );
    return BuildingSearchResponse.fromJson(response.data);
  }

  /// 법정동 검색 (지번 필터링 지원)
  Future<BjdongSearchResponse> searchBjdong(String query, {String? bun, String? ji}) async {
    final params = <String, dynamic>{'query': query};
    if (bun != null && bun.isNotEmpty) {
      params['bun'] = bun;
      params['ji'] = ji ?? '0';
    }
    final response = await _dio.get(
      '/app/api/bjdong/search',
      queryParameters: params,
    );
    return BjdongSearchResponse.fromJson(response.data);
  }

  /// 공동주택 동/호별 상세 정보 조회
  Future<AreaInfoResponse> getAreaInfo(AreaInfoRequest request) async {
    final response = await _dio.post(
      '/app/api/area',
      data: request.toJson(),
    );
    return AreaInfoResponse.fromJson(response.data);
  }
}
