import 'package:dio/dio.dart';
import 'package:propedia/core/database/database_service.dart';
import 'package:propedia/data/datasources/remote/favorites_api.dart';
import 'package:propedia/data/models/favorite.dart';

class FavoritesRepository {
  final FavoritesApi _api;

  FavoritesRepository(Dio dio) : _api = FavoritesApi(dio);

  /// 즐겨찾기 추가 (로컬 + 서버)
  /// [skipServerSync] - true면 서버 동기화 건너뛰기 (게스트 모드)
  Future<bool> addFavorite({
    required String displayAddress,
    String? roadAddress,
    String? jibunAddress,
    String? buildingName,
    String? pnu,
    String? bdMgtSn,
    String? dongName,
    String? hoName,
    String? buildingType,
    String? memo,
    bool skipServerSync = false,
  }) async {
    // 로컬 저장
    final favorite = Favorite(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      displayAddress: displayAddress,
      roadAddress: roadAddress,
      jibunAddress: jibunAddress,
      buildingName: buildingName,
      pnu: pnu,
      bdMgtSn: bdMgtSn,
      createdAt: DateTime.now(),
      dongName: dongName,
      hoName: hoName,
      buildingType: buildingType,
      memo: memo,
    );

    await DatabaseService.addFavorite(favorite);

    // 게스트 모드면 서버 동기화 건너뛰기
    if (skipServerSync) {
      return true;
    }

    // 서버 저장
    try {
      final response = await _api.addFavorite({
        'pnu': pnu,
        'address_text': displayAddress,
        'building_name': buildingName,
        'memo': memo,
      });

      // 서버 ID 업데이트
      if (response['id'] != null) {
        favorite.serverId = response['id'] as int;
        await favorite.save();
      }
      return true;
    } catch (_) {
      // 서버 저장 실패해도 로컬은 유지
      return true;
    }
  }

  /// 즐겨찾기 조회 (로컬)
  List<Favorite> getFavorites() {
    return DatabaseService.getFavorites();
  }

  /// 즐겨찾기 조회 (서버)
  Future<List<Map<String, dynamic>>> getServerFavorites({
    int limit = 100,
  }) async {
    try {
      final response = await _api.getFavorites(limit: limit);
      if (response['success'] == true) {
        return (response['favorites'] as List)
            .map((e) => e as Map<String, dynamic>)
            .toList();
      }
      return [];
    } catch (_) {
      return [];
    }
  }

  /// 즐겨찾기 삭제 (로컬)
  Future<void> deleteFavorite(String id) async {
    await DatabaseService.deleteFavorite(id);
  }

  /// 즐겨찾기 삭제 (서버)
  Future<void> deleteServerFavorite(int id) async {
    await _api.deleteFavorite(id);
  }

  /// 즐겨찾기 전체 삭제 (로컬)
  Future<void> clearFavorites() async {
    await DatabaseService.clearFavorites();
  }

  /// 즐겨찾기 여부 확인
  bool isFavorite(String displayAddress, {String? dongName, String? hoName}) {
    return DatabaseService.isFavorite(displayAddress, dongName: dongName, hoName: hoName);
  }

  /// 즐겨찾기 ID 찾기
  String? findFavoriteId(String displayAddress, {String? dongName, String? hoName}) {
    return DatabaseService.findFavoriteId(displayAddress, dongName: dongName, hoName: hoName);
  }

  /// 즐겨찾기 메모 수정 (로컬)
  Future<void> updateMemo(String id, String? memo) async {
    await DatabaseService.updateFavoriteMemo(id, memo);
  }

  /// 즐겨찾기 메모 수정 (서버)
  Future<void> updateServerMemo(int id, String? memo) async {
    await _api.updateFavoriteMemo(id, memo);
  }

  /// 서버 즐겨찾기를 로컬에 동기화
  Future<int> syncFromServer() async {
    try {
      final serverFavorites = await getServerFavorites(limit: 100);
      int syncedCount = 0;

      for (final item in serverFavorites) {
        final pnu = item['pnu'] as String?;

        // PNU로 중복 체크
        if (pnu != null && pnu.isNotEmpty) {
          final existingByPnu = DatabaseService.favoritesBox.values.where(
            (f) => f.pnu == pnu,
          );

          if (existingByPnu.isEmpty) {
            final favorite = Favorite(
              id: 'server_${item['id']}',
              displayAddress: item['address_text'] ?? '',
              jibunAddress: item['address_text'],
              buildingName: item['building_name'],
              pnu: pnu,
              createdAt: item['created_at'] != null
                  ? DateTime.parse(item['created_at'])
                  : DateTime.now(),
              memo: item['memo'],
              serverId: item['id'] as int?,
            );

            await DatabaseService.addFavorite(favorite);
            syncedCount++;
          }
        }
      }

      return syncedCount;
    } catch (e) {
      // 동기화 실패 시 무시 (오프라인 지원)
      return 0;
    }
  }
}
