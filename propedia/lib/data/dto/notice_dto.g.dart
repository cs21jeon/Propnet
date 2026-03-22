// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'notice_dto.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$NoticeListResponseImpl _$$NoticeListResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$NoticeListResponseImpl(
      success: json['success'] as bool,
      notices: (json['notices'] as List<dynamic>?)
              ?.map((e) => NoticeDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$NoticeListResponseImplToJson(
        _$NoticeListResponseImpl instance) =>
    <String, dynamic>{
      'success': instance.success,
      'notices': instance.notices,
    };

_$NoticeDtoImpl _$$NoticeDtoImplFromJson(Map<String, dynamic> json) =>
    _$NoticeDtoImpl(
      id: (json['id'] as num).toInt(),
      title: json['title'] as String,
      content: json['content'] as String,
      noticeType: json['notice_type'] as String,
      isDismissible: json['is_dismissible'] as bool? ?? true,
      startAt: json['start_at'] as String?,
      endAt: json['end_at'] as String?,
    );

Map<String, dynamic> _$$NoticeDtoImplToJson(_$NoticeDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'title': instance.title,
      'content': instance.content,
      'notice_type': instance.noticeType,
      'is_dismissible': instance.isDismissible,
      'start_at': instance.startAt,
      'end_at': instance.endAt,
    };
