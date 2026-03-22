import 'package:dio/dio.dart';

class AirtableApi {
  final Dio _dio;

  AirtableApi(this._dio);

  /// 건축물 정보 Airtable 저장
  Future<Map<String, dynamic>> saveBuilding(Map<String, dynamic> data) async {
    final response = await _dio.post('/app/api/airtable/save/building', data: data);
    return response.data as Map<String, dynamic>;
  }

  /// 공동주택 정보 Airtable 저장
  Future<Map<String, dynamic>> saveMultiUnit(Map<String, dynamic> data) async {
    final response = await _dio.post('/app/api/airtable/save/multi-unit', data: data);
    return response.data as Map<String, dynamic>;
  }

  /// 일반건물 정보 Airtable 저장
  Future<Map<String, dynamic>> saveGeneral(Map<String, dynamic> data) async {
    final response = await _dio.post('/app/api/airtable/save/general', data: data);
    return response.data as Map<String, dynamic>;
  }
}
