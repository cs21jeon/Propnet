// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_stats_dto.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UsageStatsResponse _$UsageStatsResponseFromJson(Map<String, dynamic> json) =>
    UsageStatsResponse(
      success: json['success'] as bool,
      data: json['data'] == null
          ? null
          : UsageStats.fromJson(json['data'] as Map<String, dynamic>),
      message: json['message'] as String?,
    );

Map<String, dynamic> _$UsageStatsResponseToJson(UsageStatsResponse instance) =>
    <String, dynamic>{
      'success': instance.success,
      'data': instance.data,
      'message': instance.message,
    };

UsageStats _$UsageStatsFromJson(Map<String, dynamic> json) => UsageStats(
      totalSearches: (json['total_searches'] as num).toInt(),
      totalFavorites: (json['total_favorites'] as num).toInt(),
      searchesToday: (json['searches_today'] as num).toInt(),
      searchesThisWeek: (json['searches_this_week'] as num).toInt(),
      searchesThisMonth: (json['searches_this_month'] as num).toInt(),
      lastSearchAt: json['last_search_at'] as String?,
      memberSince: json['member_since'] as String?,
      searchByType: json['search_by_type'] == null
          ? null
          : SearchByType.fromJson(
              json['search_by_type'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$UsageStatsToJson(UsageStats instance) =>
    <String, dynamic>{
      'total_searches': instance.totalSearches,
      'total_favorites': instance.totalFavorites,
      'searches_today': instance.searchesToday,
      'searches_this_week': instance.searchesThisWeek,
      'searches_this_month': instance.searchesThisMonth,
      'last_search_at': instance.lastSearchAt,
      'member_since': instance.memberSince,
      'search_by_type': instance.searchByType,
    };

SearchByType _$SearchByTypeFromJson(Map<String, dynamic> json) => SearchByType(
      road: (json['road'] as num).toInt(),
      jibun: (json['jibun'] as num).toInt(),
      map: (json['map'] as num).toInt(),
    );

Map<String, dynamic> _$SearchByTypeToJson(SearchByType instance) =>
    <String, dynamic>{
      'road': instance.road,
      'jibun': instance.jibun,
      'map': instance.map,
    };
