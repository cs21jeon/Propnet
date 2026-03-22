import 'package:hive_flutter/hive_flutter.dart';
import 'package:propedia/data/models/search_history.dart';
import 'package:propedia/data/models/favorite.dart';

class DatabaseService {
  static const String searchHistoryBoxName = 'search_history';
  static const String favoritesBoxName = 'favorites';

  static Box<SearchHistory>? _searchHistoryBox;
  static Box<Favorite>? _favoritesBox;

  /// Hive 초기화
  static Future<void> init() async {
    await Hive.initFlutter();

    // TypeAdapter 등록
    if (!Hive.isAdapterRegistered(0)) {
      Hive.registerAdapter(SearchHistoryAdapter());
    }
    if (!Hive.isAdapterRegistered(1)) {
      Hive.registerAdapter(FavoriteAdapter());
    }

    // Box 열기
    _searchHistoryBox = await Hive.openBox<SearchHistory>(searchHistoryBoxName);
    _favoritesBox = await Hive.openBox<Favorite>(favoritesBoxName);
  }

  // ==================== 검색 기록 ====================

  static Box<SearchHistory> get searchHistoryBox {
    if (_searchHistoryBox == null || !_searchHistoryBox!.isOpen) {
      throw Exception('SearchHistory box is not initialized');
    }
    return _searchHistoryBox!;
  }

  /// 검색 기록 추가
  static Future<void> addSearchHistory(SearchHistory history) async {
    // 중복 제거 (같은 PNU + 동 + 호가 있으면 삭제 후 다시 추가)
    // PNU가 없으면 jibunAddress로 비교
    final existing = searchHistoryBox.values.where((h) {
      // PNU가 있으면 PNU로 비교 (지번까지 정확히 일치)
      if (history.pnu != null && history.pnu!.isNotEmpty) {
        return h.pnu == history.pnu &&
            h.dongName == history.dongName &&
            h.hoName == history.hoName;
      }
      // PNU가 없으면 지번주소로 비교
      return h.jibunAddress == history.jibunAddress &&
          h.dongName == history.dongName &&
          h.hoName == history.hoName;
    });
    for (final item in existing) {
      await item.delete();
    }

    await searchHistoryBox.put(history.id, history);

    // 최대 100개 유지
    if (searchHistoryBox.length > 100) {
      final sortedKeys = searchHistoryBox.keys.toList();
      final oldestKeys = sortedKeys.take(searchHistoryBox.length - 100);
      for (final key in oldestKeys) {
        await searchHistoryBox.delete(key);
      }
    }
  }

  /// 검색 기록 조회 (최신순)
  static List<SearchHistory> getSearchHistory() {
    final list = searchHistoryBox.values.toList();
    list.sort((a, b) => b.searchedAt.compareTo(a.searchedAt));
    return list;
  }

  /// 검색 기록 삭제
  static Future<void> deleteSearchHistory(String id) async {
    await searchHistoryBox.delete(id);
  }

  /// 검색 기록 전체 삭제
  static Future<void> clearSearchHistory() async {
    await searchHistoryBox.clear();
  }

  // ==================== 즐겨찾기 ====================

  static Box<Favorite> get favoritesBox {
    if (_favoritesBox == null || !_favoritesBox!.isOpen) {
      throw Exception('Favorites box is not initialized');
    }
    return _favoritesBox!;
  }

  /// 즐겨찾기 추가
  static Future<void> addFavorite(Favorite favorite) async {
    await favoritesBox.put(favorite.id, favorite);
  }

  /// 즐겨찾기 조회 (최신순)
  static List<Favorite> getFavorites() {
    final list = favoritesBox.values.toList();
    list.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return list;
  }

  /// 즐겨찾기 삭제
  static Future<void> deleteFavorite(String id) async {
    await favoritesBox.delete(id);
  }

  /// 즐겨찾기 전체 삭제
  static Future<void> clearFavorites() async {
    await favoritesBox.clear();
  }

  /// 즐겨찾기 여부 확인
  static bool isFavorite(String displayAddress, {String? dongName, String? hoName}) {
    return favoritesBox.values.any(
      (f) => f.displayAddress == displayAddress &&
          f.dongName == dongName &&
          f.hoName == hoName,
    );
  }

  /// 즐겨찾기 ID 찾기
  static String? findFavoriteId(String displayAddress, {String? dongName, String? hoName}) {
    final favorite = favoritesBox.values.firstWhere(
      (f) => f.displayAddress == displayAddress &&
          f.dongName == dongName &&
          f.hoName == hoName,
      orElse: () => Favorite(
        id: '',
        displayAddress: '',
        createdAt: DateTime.now(),
      ),
    );
    return favorite.id.isEmpty ? null : favorite.id;
  }

  /// 즐겨찾기 메모 수정
  static Future<void> updateFavoriteMemo(String id, String? memo) async {
    final favorite = favoritesBox.get(id);
    if (favorite != null) {
      favorite.memo = memo;
      await favorite.save();
    }
  }
}
