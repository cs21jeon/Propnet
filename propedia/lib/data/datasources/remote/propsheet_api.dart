import 'package:dio/dio.dart';

class PropSheetApi {
  final Dio _dio;

  PropSheetApi(this._dio);

  /// PropSheet에 부동산 정보 저장
  Future<Map<String, dynamic>> saveProperty(Map<String, dynamic> data) async {
    final response = await _dio.post('/app/api/propsheet/save/property', data: data);
    return response.data as Map<String, dynamic>;
  }
}
