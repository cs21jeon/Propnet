import 'package:dio/dio.dart';
import 'package:propedia/data/dto/notice_dto.dart';

class NoticeApi {
  final Dio _dio;

  NoticeApi(this._dio);

  /// 활성 공지사항 조회
  Future<NoticeListResponse> getActiveNotices() async {
    try {
      final response = await _dio.get('/app/api/notices');
      return NoticeListResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map<String, dynamic>) {
        return NoticeListResponse.fromJson(e.response!.data);
      }
      return const NoticeListResponse(success: false, notices: []);
    }
  }
}
