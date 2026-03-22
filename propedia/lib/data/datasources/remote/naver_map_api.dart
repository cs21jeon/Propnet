import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

/// 네이버 Maps Static API 클라이언트
/// 정적 지도 이미지를 PNG로 반환합니다.
class NaverMapApi {
  final Dio _dio;
  final String? _clientId;
  final String? _clientSecret;

  static const String _baseUrl =
      'https://naveropenapi.apigw.ntruss.com/map-static/v2/raster';

  NaverMapApi({Dio? dio})
      : _dio = dio ?? Dio(),
        _clientId = dotenv.env['NAVER_MAP_CLIENT_ID'],
        _clientSecret = dotenv.env['NAVER_MAP_CLIENT_SECRET'];

  /// API 키가 설정되어 있는지 확인
  bool get isConfigured =>
      _clientId != null &&
      _clientId!.isNotEmpty &&
      _clientId != 'YOUR_NAVER_CLIENT_ID' &&
      _clientSecret != null &&
      _clientSecret!.isNotEmpty &&
      _clientSecret != 'YOUR_NAVER_CLIENT_SECRET';

  /// 정적 지도 이미지를 가져옵니다.
  ///
  /// [lat] 위도
  /// [lng] 경도
  /// [width] 이미지 너비 (최대 1024)
  /// [height] 이미지 높이 (최대 1024)
  /// [level] 줌 레벨 (1-20, 기본값 16)
  /// [showMarker] 마커 표시 여부
  ///
  /// 성공 시 PNG 이미지 바이트를 반환하고, 실패 시 null을 반환합니다.
  Future<Uint8List?> getStaticMapImage({
    required double lat,
    required double lng,
    int width = 600,
    int height = 400,
    int level = 16,
    bool showMarker = true,
  }) async {
    if (!isConfigured) {
      return null;
    }

    try {
      // 이미지 크기 제한
      width = width.clamp(100, 1024);
      height = height.clamp(100, 1024);
      level = level.clamp(1, 20);

      // 마커 파라미터 구성
      String? markers;
      if (showMarker) {
        markers = 'type:d|size:mid|pos:$lng $lat|color:red';
      }

      final queryParams = <String, dynamic>{
        'center': '$lng,$lat',
        'level': level,
        'w': width,
        'h': height,
      };

      if (markers != null) {
        queryParams['markers'] = markers;
      }

      final response = await _dio.get<List<int>>(
        _baseUrl,
        queryParameters: queryParams,
        options: Options(
          headers: {
            'X-NCP-APIGW-API-KEY-ID': _clientId,
            'X-NCP-APIGW-API-KEY': _clientSecret,
          },
          responseType: ResponseType.bytes,
        ),
      );

      if (response.statusCode == 200 && response.data != null) {
        return Uint8List.fromList(response.data!);
      }

      return null;
    } catch (e) {
      // 에러 로깅
      print('NaverMapApi error: $e');
      return null;
    }
  }
}
