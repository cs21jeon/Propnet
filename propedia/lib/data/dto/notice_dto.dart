import 'package:freezed_annotation/freezed_annotation.dart';

part 'notice_dto.freezed.dart';
part 'notice_dto.g.dart';

/// 공지사항 응답
@freezed
class NoticeListResponse with _$NoticeListResponse {
  const factory NoticeListResponse({
    required bool success,
    @Default([]) List<NoticeDto> notices,
  }) = _NoticeListResponse;

  factory NoticeListResponse.fromJson(Map<String, dynamic> json) =>
      _$NoticeListResponseFromJson(json);
}

/// 공지사항 DTO
@freezed
class NoticeDto with _$NoticeDto {
  const factory NoticeDto({
    required int id,
    required String title,
    required String content,
    @JsonKey(name: 'notice_type') required String noticeType,
    @JsonKey(name: 'is_dismissible') @Default(true) bool isDismissible,
    @JsonKey(name: 'start_at') String? startAt,
    @JsonKey(name: 'end_at') String? endAt,
  }) = _NoticeDto;

  factory NoticeDto.fromJson(Map<String, dynamic> json) =>
      _$NoticeDtoFromJson(json);
}
