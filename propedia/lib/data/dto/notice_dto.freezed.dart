// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'notice_dto.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

NoticeListResponse _$NoticeListResponseFromJson(Map<String, dynamic> json) {
  return _NoticeListResponse.fromJson(json);
}

/// @nodoc
mixin _$NoticeListResponse {
  bool get success => throw _privateConstructorUsedError;
  List<NoticeDto> get notices => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $NoticeListResponseCopyWith<NoticeListResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $NoticeListResponseCopyWith<$Res> {
  factory $NoticeListResponseCopyWith(
          NoticeListResponse value, $Res Function(NoticeListResponse) then) =
      _$NoticeListResponseCopyWithImpl<$Res, NoticeListResponse>;
  @useResult
  $Res call({bool success, List<NoticeDto> notices});
}

/// @nodoc
class _$NoticeListResponseCopyWithImpl<$Res, $Val extends NoticeListResponse>
    implements $NoticeListResponseCopyWith<$Res> {
  _$NoticeListResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? notices = null,
  }) {
    return _then(_value.copyWith(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      notices: null == notices
          ? _value.notices
          : notices // ignore: cast_nullable_to_non_nullable
              as List<NoticeDto>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$NoticeListResponseImplCopyWith<$Res>
    implements $NoticeListResponseCopyWith<$Res> {
  factory _$$NoticeListResponseImplCopyWith(_$NoticeListResponseImpl value,
          $Res Function(_$NoticeListResponseImpl) then) =
      __$$NoticeListResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({bool success, List<NoticeDto> notices});
}

/// @nodoc
class __$$NoticeListResponseImplCopyWithImpl<$Res>
    extends _$NoticeListResponseCopyWithImpl<$Res, _$NoticeListResponseImpl>
    implements _$$NoticeListResponseImplCopyWith<$Res> {
  __$$NoticeListResponseImplCopyWithImpl(_$NoticeListResponseImpl _value,
      $Res Function(_$NoticeListResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? notices = null,
  }) {
    return _then(_$NoticeListResponseImpl(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      notices: null == notices
          ? _value._notices
          : notices // ignore: cast_nullable_to_non_nullable
              as List<NoticeDto>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$NoticeListResponseImpl implements _NoticeListResponse {
  const _$NoticeListResponseImpl(
      {required this.success, final List<NoticeDto> notices = const []})
      : _notices = notices;

  factory _$NoticeListResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$NoticeListResponseImplFromJson(json);

  @override
  final bool success;
  final List<NoticeDto> _notices;
  @override
  @JsonKey()
  List<NoticeDto> get notices {
    if (_notices is EqualUnmodifiableListView) return _notices;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_notices);
  }

  @override
  String toString() {
    return 'NoticeListResponse(success: $success, notices: $notices)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$NoticeListResponseImpl &&
            (identical(other.success, success) || other.success == success) &&
            const DeepCollectionEquality().equals(other._notices, _notices));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, success, const DeepCollectionEquality().hash(_notices));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$NoticeListResponseImplCopyWith<_$NoticeListResponseImpl> get copyWith =>
      __$$NoticeListResponseImplCopyWithImpl<_$NoticeListResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$NoticeListResponseImplToJson(
      this,
    );
  }
}

abstract class _NoticeListResponse implements NoticeListResponse {
  const factory _NoticeListResponse(
      {required final bool success,
      final List<NoticeDto> notices}) = _$NoticeListResponseImpl;

  factory _NoticeListResponse.fromJson(Map<String, dynamic> json) =
      _$NoticeListResponseImpl.fromJson;

  @override
  bool get success;
  @override
  List<NoticeDto> get notices;
  @override
  @JsonKey(ignore: true)
  _$$NoticeListResponseImplCopyWith<_$NoticeListResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

NoticeDto _$NoticeDtoFromJson(Map<String, dynamic> json) {
  return _NoticeDto.fromJson(json);
}

/// @nodoc
mixin _$NoticeDto {
  int get id => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String get content => throw _privateConstructorUsedError;
  @JsonKey(name: 'notice_type')
  String get noticeType => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_dismissible')
  bool get isDismissible => throw _privateConstructorUsedError;
  @JsonKey(name: 'start_at')
  String? get startAt => throw _privateConstructorUsedError;
  @JsonKey(name: 'end_at')
  String? get endAt => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $NoticeDtoCopyWith<NoticeDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $NoticeDtoCopyWith<$Res> {
  factory $NoticeDtoCopyWith(NoticeDto value, $Res Function(NoticeDto) then) =
      _$NoticeDtoCopyWithImpl<$Res, NoticeDto>;
  @useResult
  $Res call(
      {int id,
      String title,
      String content,
      @JsonKey(name: 'notice_type') String noticeType,
      @JsonKey(name: 'is_dismissible') bool isDismissible,
      @JsonKey(name: 'start_at') String? startAt,
      @JsonKey(name: 'end_at') String? endAt});
}

/// @nodoc
class _$NoticeDtoCopyWithImpl<$Res, $Val extends NoticeDto>
    implements $NoticeDtoCopyWith<$Res> {
  _$NoticeDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? title = null,
    Object? content = null,
    Object? noticeType = null,
    Object? isDismissible = null,
    Object? startAt = freezed,
    Object? endAt = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as int,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      content: null == content
          ? _value.content
          : content // ignore: cast_nullable_to_non_nullable
              as String,
      noticeType: null == noticeType
          ? _value.noticeType
          : noticeType // ignore: cast_nullable_to_non_nullable
              as String,
      isDismissible: null == isDismissible
          ? _value.isDismissible
          : isDismissible // ignore: cast_nullable_to_non_nullable
              as bool,
      startAt: freezed == startAt
          ? _value.startAt
          : startAt // ignore: cast_nullable_to_non_nullable
              as String?,
      endAt: freezed == endAt
          ? _value.endAt
          : endAt // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$NoticeDtoImplCopyWith<$Res>
    implements $NoticeDtoCopyWith<$Res> {
  factory _$$NoticeDtoImplCopyWith(
          _$NoticeDtoImpl value, $Res Function(_$NoticeDtoImpl) then) =
      __$$NoticeDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int id,
      String title,
      String content,
      @JsonKey(name: 'notice_type') String noticeType,
      @JsonKey(name: 'is_dismissible') bool isDismissible,
      @JsonKey(name: 'start_at') String? startAt,
      @JsonKey(name: 'end_at') String? endAt});
}

/// @nodoc
class __$$NoticeDtoImplCopyWithImpl<$Res>
    extends _$NoticeDtoCopyWithImpl<$Res, _$NoticeDtoImpl>
    implements _$$NoticeDtoImplCopyWith<$Res> {
  __$$NoticeDtoImplCopyWithImpl(
      _$NoticeDtoImpl _value, $Res Function(_$NoticeDtoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? title = null,
    Object? content = null,
    Object? noticeType = null,
    Object? isDismissible = null,
    Object? startAt = freezed,
    Object? endAt = freezed,
  }) {
    return _then(_$NoticeDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as int,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      content: null == content
          ? _value.content
          : content // ignore: cast_nullable_to_non_nullable
              as String,
      noticeType: null == noticeType
          ? _value.noticeType
          : noticeType // ignore: cast_nullable_to_non_nullable
              as String,
      isDismissible: null == isDismissible
          ? _value.isDismissible
          : isDismissible // ignore: cast_nullable_to_non_nullable
              as bool,
      startAt: freezed == startAt
          ? _value.startAt
          : startAt // ignore: cast_nullable_to_non_nullable
              as String?,
      endAt: freezed == endAt
          ? _value.endAt
          : endAt // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$NoticeDtoImpl implements _NoticeDto {
  const _$NoticeDtoImpl(
      {required this.id,
      required this.title,
      required this.content,
      @JsonKey(name: 'notice_type') required this.noticeType,
      @JsonKey(name: 'is_dismissible') this.isDismissible = true,
      @JsonKey(name: 'start_at') this.startAt,
      @JsonKey(name: 'end_at') this.endAt});

  factory _$NoticeDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$NoticeDtoImplFromJson(json);

  @override
  final int id;
  @override
  final String title;
  @override
  final String content;
  @override
  @JsonKey(name: 'notice_type')
  final String noticeType;
  @override
  @JsonKey(name: 'is_dismissible')
  final bool isDismissible;
  @override
  @JsonKey(name: 'start_at')
  final String? startAt;
  @override
  @JsonKey(name: 'end_at')
  final String? endAt;

  @override
  String toString() {
    return 'NoticeDto(id: $id, title: $title, content: $content, noticeType: $noticeType, isDismissible: $isDismissible, startAt: $startAt, endAt: $endAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$NoticeDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.content, content) || other.content == content) &&
            (identical(other.noticeType, noticeType) ||
                other.noticeType == noticeType) &&
            (identical(other.isDismissible, isDismissible) ||
                other.isDismissible == isDismissible) &&
            (identical(other.startAt, startAt) || other.startAt == startAt) &&
            (identical(other.endAt, endAt) || other.endAt == endAt));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, id, title, content, noticeType,
      isDismissible, startAt, endAt);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$NoticeDtoImplCopyWith<_$NoticeDtoImpl> get copyWith =>
      __$$NoticeDtoImplCopyWithImpl<_$NoticeDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$NoticeDtoImplToJson(
      this,
    );
  }
}

abstract class _NoticeDto implements NoticeDto {
  const factory _NoticeDto(
      {required final int id,
      required final String title,
      required final String content,
      @JsonKey(name: 'notice_type') required final String noticeType,
      @JsonKey(name: 'is_dismissible') final bool isDismissible,
      @JsonKey(name: 'start_at') final String? startAt,
      @JsonKey(name: 'end_at') final String? endAt}) = _$NoticeDtoImpl;

  factory _NoticeDto.fromJson(Map<String, dynamic> json) =
      _$NoticeDtoImpl.fromJson;

  @override
  int get id;
  @override
  String get title;
  @override
  String get content;
  @override
  @JsonKey(name: 'notice_type')
  String get noticeType;
  @override
  @JsonKey(name: 'is_dismissible')
  bool get isDismissible;
  @override
  @JsonKey(name: 'start_at')
  String? get startAt;
  @override
  @JsonKey(name: 'end_at')
  String? get endAt;
  @override
  @JsonKey(ignore: true)
  _$$NoticeDtoImplCopyWith<_$NoticeDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
