import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:propedia/data/datasources/remote/notice_api.dart';
import 'package:propedia/data/dto/notice_dto.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';

// NoticeApi Provider
final noticeApiProvider = Provider<NoticeApi>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return NoticeApi(apiClient.dio);
});

// 공지 상태
class NoticeState {
  final List<NoticeDto> notices;
  final Set<int> dismissedIds;
  final bool isLoading;
  final bool hasShown;

  const NoticeState({
    this.notices = const [],
    this.dismissedIds = const {},
    this.isLoading = false,
    this.hasShown = false,
  });

  NoticeState copyWith({
    List<NoticeDto>? notices,
    Set<int>? dismissedIds,
    bool? isLoading,
    bool? hasShown,
  }) {
    return NoticeState(
      notices: notices ?? this.notices,
      dismissedIds: dismissedIds ?? this.dismissedIds,
      isLoading: isLoading ?? this.isLoading,
      hasShown: hasShown ?? this.hasShown,
    );
  }

  List<NoticeDto> get visibleNotices =>
      notices.where((n) => !dismissedIds.contains(n.id)).toList();
}

class NoticeNotifier extends StateNotifier<NoticeState> {
  final NoticeApi _noticeApi;

  NoticeNotifier(this._noticeApi) : super(const NoticeState());

  /// 활성 공지 가져오기
  Future<void> fetchNotices() async {
    state = state.copyWith(isLoading: true, hasShown: false);

    try {
      // "오늘 안보기" 목록 로드
      final dismissed = await _loadDismissedIds();

      final response = await _noticeApi.getActiveNotices();
      if (response.success) {
        state = state.copyWith(
          notices: response.notices,
          dismissedIds: dismissed,
          isLoading: false,
        );
      } else {
        state = state.copyWith(isLoading: false);
      }
    } catch (e) {
      debugPrint('[NOTICE] 공지 조회 오류: $e');
      state = state.copyWith(isLoading: false);
    }
  }

  /// 공지 닫기 (세션 내)
  void dismissNotice(int id) {
    final newDismissed = {...state.dismissedIds, id};
    state = state.copyWith(dismissedIds: newDismissed);
  }

  /// 오늘 하루 안보기
  Future<void> dismissForToday(int id) async {
    dismissNotice(id);
    await _saveDismissedId(id);
  }

  /// 다이얼로그 표시 완료 마킹
  void markShown() {
    state = state.copyWith(hasShown: true);
  }

  Future<Set<int>> _loadDismissedIds() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final today = DateFormat('yyyy-MM-dd').format(DateTime.now());
      final key = 'dismissed_notices_$today';
      final stored = prefs.getString(key);
      if (stored == null || stored.isEmpty) return {};
      return stored.split(',').map((s) => int.tryParse(s)).whereType<int>().toSet();
    } catch (_) {
      return {};
    }
  }

  Future<void> _saveDismissedId(int id) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final today = DateFormat('yyyy-MM-dd').format(DateTime.now());
      final key = 'dismissed_notices_$today';
      final existing = prefs.getString(key) ?? '';
      final ids = existing.isEmpty ? <String>{} : existing.split(',').toSet();
      ids.add(id.toString());
      await prefs.setString(key, ids.join(','));
    } catch (_) {}
  }
}

// NoticeNotifier Provider
final noticeProvider = StateNotifierProvider<NoticeNotifier, NoticeState>((ref) {
  final noticeApi = ref.watch(noticeApiProvider);
  return NoticeNotifier(noticeApi);
});
