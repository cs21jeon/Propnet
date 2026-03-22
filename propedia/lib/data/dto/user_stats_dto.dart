import 'package:json_annotation/json_annotation.dart';

part 'user_stats_dto.g.dart';

/// 사용 통계 응답 DTO
@JsonSerializable()
class UsageStatsResponse {
  final bool success;
  final UsageStats? data;
  final String? message;

  UsageStatsResponse({
    required this.success,
    this.data,
    this.message,
  });

  factory UsageStatsResponse.fromJson(Map<String, dynamic> json) =>
      _$UsageStatsResponseFromJson(json);

  Map<String, dynamic> toJson() => _$UsageStatsResponseToJson(this);
}

/// 사용 통계 데이터
@JsonSerializable()
class UsageStats {
  @JsonKey(name: 'total_searches')
  final int totalSearches;

  @JsonKey(name: 'total_favorites')
  final int totalFavorites;

  @JsonKey(name: 'searches_today')
  final int searchesToday;

  @JsonKey(name: 'searches_this_week')
  final int searchesThisWeek;

  @JsonKey(name: 'searches_this_month')
  final int searchesThisMonth;

  @JsonKey(name: 'last_search_at')
  final String? lastSearchAt;

  @JsonKey(name: 'member_since')
  final String? memberSince;

  @JsonKey(name: 'search_by_type')
  final SearchByType? searchByType;

  UsageStats({
    required this.totalSearches,
    required this.totalFavorites,
    required this.searchesToday,
    required this.searchesThisWeek,
    required this.searchesThisMonth,
    this.lastSearchAt,
    this.memberSince,
    this.searchByType,
  });

  factory UsageStats.fromJson(Map<String, dynamic> json) =>
      _$UsageStatsFromJson(json);

  Map<String, dynamic> toJson() => _$UsageStatsToJson(this);
}

/// 검색 타입별 통계
@JsonSerializable()
class SearchByType {
  final int road;
  final int jibun;
  final int map;

  SearchByType({
    required this.road,
    required this.jibun,
    required this.map,
  });

  factory SearchByType.fromJson(Map<String, dynamic> json) =>
      _$SearchByTypeFromJson(json);

  Map<String, dynamic> toJson() => _$SearchByTypeToJson(this);
}
