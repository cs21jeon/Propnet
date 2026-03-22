// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'building_dto.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

RoadSearchRequest _$RoadSearchRequestFromJson(Map<String, dynamic> json) {
  return _RoadSearchRequest.fromJson(json);
}

/// @nodoc
mixin _$RoadSearchRequest {
  @JsonKey(name: 'road_name')
  String get roadName => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $RoadSearchRequestCopyWith<RoadSearchRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RoadSearchRequestCopyWith<$Res> {
  factory $RoadSearchRequestCopyWith(
          RoadSearchRequest value, $Res Function(RoadSearchRequest) then) =
      _$RoadSearchRequestCopyWithImpl<$Res, RoadSearchRequest>;
  @useResult
  $Res call({@JsonKey(name: 'road_name') String roadName});
}

/// @nodoc
class _$RoadSearchRequestCopyWithImpl<$Res, $Val extends RoadSearchRequest>
    implements $RoadSearchRequestCopyWith<$Res> {
  _$RoadSearchRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? roadName = null,
  }) {
    return _then(_value.copyWith(
      roadName: null == roadName
          ? _value.roadName
          : roadName // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RoadSearchRequestImplCopyWith<$Res>
    implements $RoadSearchRequestCopyWith<$Res> {
  factory _$$RoadSearchRequestImplCopyWith(_$RoadSearchRequestImpl value,
          $Res Function(_$RoadSearchRequestImpl) then) =
      __$$RoadSearchRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({@JsonKey(name: 'road_name') String roadName});
}

/// @nodoc
class __$$RoadSearchRequestImplCopyWithImpl<$Res>
    extends _$RoadSearchRequestCopyWithImpl<$Res, _$RoadSearchRequestImpl>
    implements _$$RoadSearchRequestImplCopyWith<$Res> {
  __$$RoadSearchRequestImplCopyWithImpl(_$RoadSearchRequestImpl _value,
      $Res Function(_$RoadSearchRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? roadName = null,
  }) {
    return _then(_$RoadSearchRequestImpl(
      roadName: null == roadName
          ? _value.roadName
          : roadName // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RoadSearchRequestImpl implements _RoadSearchRequest {
  const _$RoadSearchRequestImpl(
      {@JsonKey(name: 'road_name') required this.roadName});

  factory _$RoadSearchRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$RoadSearchRequestImplFromJson(json);

  @override
  @JsonKey(name: 'road_name')
  final String roadName;

  @override
  String toString() {
    return 'RoadSearchRequest(roadName: $roadName)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RoadSearchRequestImpl &&
            (identical(other.roadName, roadName) ||
                other.roadName == roadName));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, roadName);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$RoadSearchRequestImplCopyWith<_$RoadSearchRequestImpl> get copyWith =>
      __$$RoadSearchRequestImplCopyWithImpl<_$RoadSearchRequestImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RoadSearchRequestImplToJson(
      this,
    );
  }
}

abstract class _RoadSearchRequest implements RoadSearchRequest {
  const factory _RoadSearchRequest(
          {@JsonKey(name: 'road_name') required final String roadName}) =
      _$RoadSearchRequestImpl;

  factory _RoadSearchRequest.fromJson(Map<String, dynamic> json) =
      _$RoadSearchRequestImpl.fromJson;

  @override
  @JsonKey(name: 'road_name')
  String get roadName;
  @override
  @JsonKey(ignore: true)
  _$$RoadSearchRequestImplCopyWith<_$RoadSearchRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

RoadSearchResultItem _$RoadSearchResultItemFromJson(Map<String, dynamic> json) {
  return _RoadSearchResultItem.fromJson(json);
}

/// @nodoc
mixin _$RoadSearchResultItem {
  String get roadAddr => throw _privateConstructorUsedError;
  String get jibunAddr => throw _privateConstructorUsedError;
  String get bdMgtSn => throw _privateConstructorUsedError;
  String? get bdNm => throw _privateConstructorUsedError;
  String? get zipNo => throw _privateConstructorUsedError;
  String? get lnbrMnnm => throw _privateConstructorUsedError; // 지번 본번 (토지 지번)
  String? get lnbrSlno => throw _privateConstructorUsedError; // 지번 부번 (토지 지번)
  String? get admCd => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $RoadSearchResultItemCopyWith<RoadSearchResultItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RoadSearchResultItemCopyWith<$Res> {
  factory $RoadSearchResultItemCopyWith(RoadSearchResultItem value,
          $Res Function(RoadSearchResultItem) then) =
      _$RoadSearchResultItemCopyWithImpl<$Res, RoadSearchResultItem>;
  @useResult
  $Res call(
      {String roadAddr,
      String jibunAddr,
      String bdMgtSn,
      String? bdNm,
      String? zipNo,
      String? lnbrMnnm,
      String? lnbrSlno,
      String? admCd});
}

/// @nodoc
class _$RoadSearchResultItemCopyWithImpl<$Res,
        $Val extends RoadSearchResultItem>
    implements $RoadSearchResultItemCopyWith<$Res> {
  _$RoadSearchResultItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? roadAddr = null,
    Object? jibunAddr = null,
    Object? bdMgtSn = null,
    Object? bdNm = freezed,
    Object? zipNo = freezed,
    Object? lnbrMnnm = freezed,
    Object? lnbrSlno = freezed,
    Object? admCd = freezed,
  }) {
    return _then(_value.copyWith(
      roadAddr: null == roadAddr
          ? _value.roadAddr
          : roadAddr // ignore: cast_nullable_to_non_nullable
              as String,
      jibunAddr: null == jibunAddr
          ? _value.jibunAddr
          : jibunAddr // ignore: cast_nullable_to_non_nullable
              as String,
      bdMgtSn: null == bdMgtSn
          ? _value.bdMgtSn
          : bdMgtSn // ignore: cast_nullable_to_non_nullable
              as String,
      bdNm: freezed == bdNm
          ? _value.bdNm
          : bdNm // ignore: cast_nullable_to_non_nullable
              as String?,
      zipNo: freezed == zipNo
          ? _value.zipNo
          : zipNo // ignore: cast_nullable_to_non_nullable
              as String?,
      lnbrMnnm: freezed == lnbrMnnm
          ? _value.lnbrMnnm
          : lnbrMnnm // ignore: cast_nullable_to_non_nullable
              as String?,
      lnbrSlno: freezed == lnbrSlno
          ? _value.lnbrSlno
          : lnbrSlno // ignore: cast_nullable_to_non_nullable
              as String?,
      admCd: freezed == admCd
          ? _value.admCd
          : admCd // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RoadSearchResultItemImplCopyWith<$Res>
    implements $RoadSearchResultItemCopyWith<$Res> {
  factory _$$RoadSearchResultItemImplCopyWith(_$RoadSearchResultItemImpl value,
          $Res Function(_$RoadSearchResultItemImpl) then) =
      __$$RoadSearchResultItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String roadAddr,
      String jibunAddr,
      String bdMgtSn,
      String? bdNm,
      String? zipNo,
      String? lnbrMnnm,
      String? lnbrSlno,
      String? admCd});
}

/// @nodoc
class __$$RoadSearchResultItemImplCopyWithImpl<$Res>
    extends _$RoadSearchResultItemCopyWithImpl<$Res, _$RoadSearchResultItemImpl>
    implements _$$RoadSearchResultItemImplCopyWith<$Res> {
  __$$RoadSearchResultItemImplCopyWithImpl(_$RoadSearchResultItemImpl _value,
      $Res Function(_$RoadSearchResultItemImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? roadAddr = null,
    Object? jibunAddr = null,
    Object? bdMgtSn = null,
    Object? bdNm = freezed,
    Object? zipNo = freezed,
    Object? lnbrMnnm = freezed,
    Object? lnbrSlno = freezed,
    Object? admCd = freezed,
  }) {
    return _then(_$RoadSearchResultItemImpl(
      roadAddr: null == roadAddr
          ? _value.roadAddr
          : roadAddr // ignore: cast_nullable_to_non_nullable
              as String,
      jibunAddr: null == jibunAddr
          ? _value.jibunAddr
          : jibunAddr // ignore: cast_nullable_to_non_nullable
              as String,
      bdMgtSn: null == bdMgtSn
          ? _value.bdMgtSn
          : bdMgtSn // ignore: cast_nullable_to_non_nullable
              as String,
      bdNm: freezed == bdNm
          ? _value.bdNm
          : bdNm // ignore: cast_nullable_to_non_nullable
              as String?,
      zipNo: freezed == zipNo
          ? _value.zipNo
          : zipNo // ignore: cast_nullable_to_non_nullable
              as String?,
      lnbrMnnm: freezed == lnbrMnnm
          ? _value.lnbrMnnm
          : lnbrMnnm // ignore: cast_nullable_to_non_nullable
              as String?,
      lnbrSlno: freezed == lnbrSlno
          ? _value.lnbrSlno
          : lnbrSlno // ignore: cast_nullable_to_non_nullable
              as String?,
      admCd: freezed == admCd
          ? _value.admCd
          : admCd // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RoadSearchResultItemImpl implements _RoadSearchResultItem {
  const _$RoadSearchResultItemImpl(
      {required this.roadAddr,
      required this.jibunAddr,
      required this.bdMgtSn,
      this.bdNm,
      this.zipNo,
      this.lnbrMnnm,
      this.lnbrSlno,
      this.admCd});

  factory _$RoadSearchResultItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$RoadSearchResultItemImplFromJson(json);

  @override
  final String roadAddr;
  @override
  final String jibunAddr;
  @override
  final String bdMgtSn;
  @override
  final String? bdNm;
  @override
  final String? zipNo;
  @override
  final String? lnbrMnnm;
// 지번 본번 (토지 지번)
  @override
  final String? lnbrSlno;
// 지번 부번 (토지 지번)
  @override
  final String? admCd;

  @override
  String toString() {
    return 'RoadSearchResultItem(roadAddr: $roadAddr, jibunAddr: $jibunAddr, bdMgtSn: $bdMgtSn, bdNm: $bdNm, zipNo: $zipNo, lnbrMnnm: $lnbrMnnm, lnbrSlno: $lnbrSlno, admCd: $admCd)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RoadSearchResultItemImpl &&
            (identical(other.roadAddr, roadAddr) ||
                other.roadAddr == roadAddr) &&
            (identical(other.jibunAddr, jibunAddr) ||
                other.jibunAddr == jibunAddr) &&
            (identical(other.bdMgtSn, bdMgtSn) || other.bdMgtSn == bdMgtSn) &&
            (identical(other.bdNm, bdNm) || other.bdNm == bdNm) &&
            (identical(other.zipNo, zipNo) || other.zipNo == zipNo) &&
            (identical(other.lnbrMnnm, lnbrMnnm) ||
                other.lnbrMnnm == lnbrMnnm) &&
            (identical(other.lnbrSlno, lnbrSlno) ||
                other.lnbrSlno == lnbrSlno) &&
            (identical(other.admCd, admCd) || other.admCd == admCd));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, roadAddr, jibunAddr, bdMgtSn,
      bdNm, zipNo, lnbrMnnm, lnbrSlno, admCd);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$RoadSearchResultItemImplCopyWith<_$RoadSearchResultItemImpl>
      get copyWith =>
          __$$RoadSearchResultItemImplCopyWithImpl<_$RoadSearchResultItemImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RoadSearchResultItemImplToJson(
      this,
    );
  }
}

abstract class _RoadSearchResultItem implements RoadSearchResultItem {
  const factory _RoadSearchResultItem(
      {required final String roadAddr,
      required final String jibunAddr,
      required final String bdMgtSn,
      final String? bdNm,
      final String? zipNo,
      final String? lnbrMnnm,
      final String? lnbrSlno,
      final String? admCd}) = _$RoadSearchResultItemImpl;

  factory _RoadSearchResultItem.fromJson(Map<String, dynamic> json) =
      _$RoadSearchResultItemImpl.fromJson;

  @override
  String get roadAddr;
  @override
  String get jibunAddr;
  @override
  String get bdMgtSn;
  @override
  String? get bdNm;
  @override
  String? get zipNo;
  @override
  String? get lnbrMnnm;
  @override // 지번 본번 (토지 지번)
  String? get lnbrSlno;
  @override // 지번 부번 (토지 지번)
  String? get admCd;
  @override
  @JsonKey(ignore: true)
  _$$RoadSearchResultItemImplCopyWith<_$RoadSearchResultItemImpl>
      get copyWith => throw _privateConstructorUsedError;
}

RoadSearchResponse _$RoadSearchResponseFromJson(Map<String, dynamic> json) {
  return _RoadSearchResponse.fromJson(json);
}

/// @nodoc
mixin _$RoadSearchResponse {
  bool get success => throw _privateConstructorUsedError;
  int get count => throw _privateConstructorUsedError;
  List<RoadSearchResultItem> get results => throw _privateConstructorUsedError;
  String? get message => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $RoadSearchResponseCopyWith<RoadSearchResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RoadSearchResponseCopyWith<$Res> {
  factory $RoadSearchResponseCopyWith(
          RoadSearchResponse value, $Res Function(RoadSearchResponse) then) =
      _$RoadSearchResponseCopyWithImpl<$Res, RoadSearchResponse>;
  @useResult
  $Res call(
      {bool success,
      int count,
      List<RoadSearchResultItem> results,
      String? message,
      String? error});
}

/// @nodoc
class _$RoadSearchResponseCopyWithImpl<$Res, $Val extends RoadSearchResponse>
    implements $RoadSearchResponseCopyWith<$Res> {
  _$RoadSearchResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? count = null,
    Object? results = null,
    Object? message = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      count: null == count
          ? _value.count
          : count // ignore: cast_nullable_to_non_nullable
              as int,
      results: null == results
          ? _value.results
          : results // ignore: cast_nullable_to_non_nullable
              as List<RoadSearchResultItem>,
      message: freezed == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RoadSearchResponseImplCopyWith<$Res>
    implements $RoadSearchResponseCopyWith<$Res> {
  factory _$$RoadSearchResponseImplCopyWith(_$RoadSearchResponseImpl value,
          $Res Function(_$RoadSearchResponseImpl) then) =
      __$$RoadSearchResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool success,
      int count,
      List<RoadSearchResultItem> results,
      String? message,
      String? error});
}

/// @nodoc
class __$$RoadSearchResponseImplCopyWithImpl<$Res>
    extends _$RoadSearchResponseCopyWithImpl<$Res, _$RoadSearchResponseImpl>
    implements _$$RoadSearchResponseImplCopyWith<$Res> {
  __$$RoadSearchResponseImplCopyWithImpl(_$RoadSearchResponseImpl _value,
      $Res Function(_$RoadSearchResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? count = null,
    Object? results = null,
    Object? message = freezed,
    Object? error = freezed,
  }) {
    return _then(_$RoadSearchResponseImpl(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      count: null == count
          ? _value.count
          : count // ignore: cast_nullable_to_non_nullable
              as int,
      results: null == results
          ? _value._results
          : results // ignore: cast_nullable_to_non_nullable
              as List<RoadSearchResultItem>,
      message: freezed == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RoadSearchResponseImpl implements _RoadSearchResponse {
  const _$RoadSearchResponseImpl(
      {required this.success,
      this.count = 0,
      final List<RoadSearchResultItem> results = const [],
      this.message,
      this.error})
      : _results = results;

  factory _$RoadSearchResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$RoadSearchResponseImplFromJson(json);

  @override
  final bool success;
  @override
  @JsonKey()
  final int count;
  final List<RoadSearchResultItem> _results;
  @override
  @JsonKey()
  List<RoadSearchResultItem> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  final String? message;
  @override
  final String? error;

  @override
  String toString() {
    return 'RoadSearchResponse(success: $success, count: $count, results: $results, message: $message, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RoadSearchResponseImpl &&
            (identical(other.success, success) || other.success == success) &&
            (identical(other.count, count) || other.count == count) &&
            const DeepCollectionEquality().equals(other._results, _results) &&
            (identical(other.message, message) || other.message == message) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, success, count,
      const DeepCollectionEquality().hash(_results), message, error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$RoadSearchResponseImplCopyWith<_$RoadSearchResponseImpl> get copyWith =>
      __$$RoadSearchResponseImplCopyWithImpl<_$RoadSearchResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RoadSearchResponseImplToJson(
      this,
    );
  }
}

abstract class _RoadSearchResponse implements RoadSearchResponse {
  const factory _RoadSearchResponse(
      {required final bool success,
      final int count,
      final List<RoadSearchResultItem> results,
      final String? message,
      final String? error}) = _$RoadSearchResponseImpl;

  factory _RoadSearchResponse.fromJson(Map<String, dynamic> json) =
      _$RoadSearchResponseImpl.fromJson;

  @override
  bool get success;
  @override
  int get count;
  @override
  List<RoadSearchResultItem> get results;
  @override
  String? get message;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$RoadSearchResponseImplCopyWith<_$RoadSearchResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

JibunSearchRequest _$JibunSearchRequestFromJson(Map<String, dynamic> json) {
  return _JibunSearchRequest.fromJson(json);
}

/// @nodoc
mixin _$JibunSearchRequest {
  @JsonKey(name: 'bjdong_code')
  String get bjdongCode => throw _privateConstructorUsedError;
  String get bun => throw _privateConstructorUsedError;
  String get ji => throw _privateConstructorUsedError;
  @JsonKey(name: 'land_type')
  String get landType => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $JibunSearchRequestCopyWith<JibunSearchRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $JibunSearchRequestCopyWith<$Res> {
  factory $JibunSearchRequestCopyWith(
          JibunSearchRequest value, $Res Function(JibunSearchRequest) then) =
      _$JibunSearchRequestCopyWithImpl<$Res, JibunSearchRequest>;
  @useResult
  $Res call(
      {@JsonKey(name: 'bjdong_code') String bjdongCode,
      String bun,
      String ji,
      @JsonKey(name: 'land_type') String landType});
}

/// @nodoc
class _$JibunSearchRequestCopyWithImpl<$Res, $Val extends JibunSearchRequest>
    implements $JibunSearchRequestCopyWith<$Res> {
  _$JibunSearchRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? bjdongCode = null,
    Object? bun = null,
    Object? ji = null,
    Object? landType = null,
  }) {
    return _then(_value.copyWith(
      bjdongCode: null == bjdongCode
          ? _value.bjdongCode
          : bjdongCode // ignore: cast_nullable_to_non_nullable
              as String,
      bun: null == bun
          ? _value.bun
          : bun // ignore: cast_nullable_to_non_nullable
              as String,
      ji: null == ji
          ? _value.ji
          : ji // ignore: cast_nullable_to_non_nullable
              as String,
      landType: null == landType
          ? _value.landType
          : landType // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$JibunSearchRequestImplCopyWith<$Res>
    implements $JibunSearchRequestCopyWith<$Res> {
  factory _$$JibunSearchRequestImplCopyWith(_$JibunSearchRequestImpl value,
          $Res Function(_$JibunSearchRequestImpl) then) =
      __$$JibunSearchRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'bjdong_code') String bjdongCode,
      String bun,
      String ji,
      @JsonKey(name: 'land_type') String landType});
}

/// @nodoc
class __$$JibunSearchRequestImplCopyWithImpl<$Res>
    extends _$JibunSearchRequestCopyWithImpl<$Res, _$JibunSearchRequestImpl>
    implements _$$JibunSearchRequestImplCopyWith<$Res> {
  __$$JibunSearchRequestImplCopyWithImpl(_$JibunSearchRequestImpl _value,
      $Res Function(_$JibunSearchRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? bjdongCode = null,
    Object? bun = null,
    Object? ji = null,
    Object? landType = null,
  }) {
    return _then(_$JibunSearchRequestImpl(
      bjdongCode: null == bjdongCode
          ? _value.bjdongCode
          : bjdongCode // ignore: cast_nullable_to_non_nullable
              as String,
      bun: null == bun
          ? _value.bun
          : bun // ignore: cast_nullable_to_non_nullable
              as String,
      ji: null == ji
          ? _value.ji
          : ji // ignore: cast_nullable_to_non_nullable
              as String,
      landType: null == landType
          ? _value.landType
          : landType // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$JibunSearchRequestImpl implements _JibunSearchRequest {
  const _$JibunSearchRequestImpl(
      {@JsonKey(name: 'bjdong_code') required this.bjdongCode,
      required this.bun,
      this.ji = '0000',
      @JsonKey(name: 'land_type') this.landType = '1'});

  factory _$JibunSearchRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$JibunSearchRequestImplFromJson(json);

  @override
  @JsonKey(name: 'bjdong_code')
  final String bjdongCode;
  @override
  final String bun;
  @override
  @JsonKey()
  final String ji;
  @override
  @JsonKey(name: 'land_type')
  final String landType;

  @override
  String toString() {
    return 'JibunSearchRequest(bjdongCode: $bjdongCode, bun: $bun, ji: $ji, landType: $landType)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$JibunSearchRequestImpl &&
            (identical(other.bjdongCode, bjdongCode) ||
                other.bjdongCode == bjdongCode) &&
            (identical(other.bun, bun) || other.bun == bun) &&
            (identical(other.ji, ji) || other.ji == ji) &&
            (identical(other.landType, landType) ||
                other.landType == landType));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, bjdongCode, bun, ji, landType);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$JibunSearchRequestImplCopyWith<_$JibunSearchRequestImpl> get copyWith =>
      __$$JibunSearchRequestImplCopyWithImpl<_$JibunSearchRequestImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$JibunSearchRequestImplToJson(
      this,
    );
  }
}

abstract class _JibunSearchRequest implements JibunSearchRequest {
  const factory _JibunSearchRequest(
          {@JsonKey(name: 'bjdong_code') required final String bjdongCode,
          required final String bun,
          final String ji,
          @JsonKey(name: 'land_type') final String landType}) =
      _$JibunSearchRequestImpl;

  factory _JibunSearchRequest.fromJson(Map<String, dynamic> json) =
      _$JibunSearchRequestImpl.fromJson;

  @override
  @JsonKey(name: 'bjdong_code')
  String get bjdongCode;
  @override
  String get bun;
  @override
  String get ji;
  @override
  @JsonKey(name: 'land_type')
  String get landType;
  @override
  @JsonKey(ignore: true)
  _$$JibunSearchRequestImplCopyWith<_$JibunSearchRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BdMgtSnSearchRequest _$BdMgtSnSearchRequestFromJson(Map<String, dynamic> json) {
  return _BdMgtSnSearchRequest.fromJson(json);
}

/// @nodoc
mixin _$BdMgtSnSearchRequest {
  String get bdMgtSn => throw _privateConstructorUsedError;
  String? get lnbrMnnm => throw _privateConstructorUsedError; // 지번 본번 (토지 지번)
  String? get lnbrSlno => throw _privateConstructorUsedError; // 지번 부번 (토지 지번)
  String? get admCd => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BdMgtSnSearchRequestCopyWith<BdMgtSnSearchRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BdMgtSnSearchRequestCopyWith<$Res> {
  factory $BdMgtSnSearchRequestCopyWith(BdMgtSnSearchRequest value,
          $Res Function(BdMgtSnSearchRequest) then) =
      _$BdMgtSnSearchRequestCopyWithImpl<$Res, BdMgtSnSearchRequest>;
  @useResult
  $Res call(
      {String bdMgtSn, String? lnbrMnnm, String? lnbrSlno, String? admCd});
}

/// @nodoc
class _$BdMgtSnSearchRequestCopyWithImpl<$Res,
        $Val extends BdMgtSnSearchRequest>
    implements $BdMgtSnSearchRequestCopyWith<$Res> {
  _$BdMgtSnSearchRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? bdMgtSn = null,
    Object? lnbrMnnm = freezed,
    Object? lnbrSlno = freezed,
    Object? admCd = freezed,
  }) {
    return _then(_value.copyWith(
      bdMgtSn: null == bdMgtSn
          ? _value.bdMgtSn
          : bdMgtSn // ignore: cast_nullable_to_non_nullable
              as String,
      lnbrMnnm: freezed == lnbrMnnm
          ? _value.lnbrMnnm
          : lnbrMnnm // ignore: cast_nullable_to_non_nullable
              as String?,
      lnbrSlno: freezed == lnbrSlno
          ? _value.lnbrSlno
          : lnbrSlno // ignore: cast_nullable_to_non_nullable
              as String?,
      admCd: freezed == admCd
          ? _value.admCd
          : admCd // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BdMgtSnSearchRequestImplCopyWith<$Res>
    implements $BdMgtSnSearchRequestCopyWith<$Res> {
  factory _$$BdMgtSnSearchRequestImplCopyWith(_$BdMgtSnSearchRequestImpl value,
          $Res Function(_$BdMgtSnSearchRequestImpl) then) =
      __$$BdMgtSnSearchRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String bdMgtSn, String? lnbrMnnm, String? lnbrSlno, String? admCd});
}

/// @nodoc
class __$$BdMgtSnSearchRequestImplCopyWithImpl<$Res>
    extends _$BdMgtSnSearchRequestCopyWithImpl<$Res, _$BdMgtSnSearchRequestImpl>
    implements _$$BdMgtSnSearchRequestImplCopyWith<$Res> {
  __$$BdMgtSnSearchRequestImplCopyWithImpl(_$BdMgtSnSearchRequestImpl _value,
      $Res Function(_$BdMgtSnSearchRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? bdMgtSn = null,
    Object? lnbrMnnm = freezed,
    Object? lnbrSlno = freezed,
    Object? admCd = freezed,
  }) {
    return _then(_$BdMgtSnSearchRequestImpl(
      bdMgtSn: null == bdMgtSn
          ? _value.bdMgtSn
          : bdMgtSn // ignore: cast_nullable_to_non_nullable
              as String,
      lnbrMnnm: freezed == lnbrMnnm
          ? _value.lnbrMnnm
          : lnbrMnnm // ignore: cast_nullable_to_non_nullable
              as String?,
      lnbrSlno: freezed == lnbrSlno
          ? _value.lnbrSlno
          : lnbrSlno // ignore: cast_nullable_to_non_nullable
              as String?,
      admCd: freezed == admCd
          ? _value.admCd
          : admCd // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BdMgtSnSearchRequestImpl implements _BdMgtSnSearchRequest {
  const _$BdMgtSnSearchRequestImpl(
      {required this.bdMgtSn, this.lnbrMnnm, this.lnbrSlno, this.admCd});

  factory _$BdMgtSnSearchRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$BdMgtSnSearchRequestImplFromJson(json);

  @override
  final String bdMgtSn;
  @override
  final String? lnbrMnnm;
// 지번 본번 (토지 지번)
  @override
  final String? lnbrSlno;
// 지번 부번 (토지 지번)
  @override
  final String? admCd;

  @override
  String toString() {
    return 'BdMgtSnSearchRequest(bdMgtSn: $bdMgtSn, lnbrMnnm: $lnbrMnnm, lnbrSlno: $lnbrSlno, admCd: $admCd)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BdMgtSnSearchRequestImpl &&
            (identical(other.bdMgtSn, bdMgtSn) || other.bdMgtSn == bdMgtSn) &&
            (identical(other.lnbrMnnm, lnbrMnnm) ||
                other.lnbrMnnm == lnbrMnnm) &&
            (identical(other.lnbrSlno, lnbrSlno) ||
                other.lnbrSlno == lnbrSlno) &&
            (identical(other.admCd, admCd) || other.admCd == admCd));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, bdMgtSn, lnbrMnnm, lnbrSlno, admCd);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BdMgtSnSearchRequestImplCopyWith<_$BdMgtSnSearchRequestImpl>
      get copyWith =>
          __$$BdMgtSnSearchRequestImplCopyWithImpl<_$BdMgtSnSearchRequestImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BdMgtSnSearchRequestImplToJson(
      this,
    );
  }
}

abstract class _BdMgtSnSearchRequest implements BdMgtSnSearchRequest {
  const factory _BdMgtSnSearchRequest(
      {required final String bdMgtSn,
      final String? lnbrMnnm,
      final String? lnbrSlno,
      final String? admCd}) = _$BdMgtSnSearchRequestImpl;

  factory _BdMgtSnSearchRequest.fromJson(Map<String, dynamic> json) =
      _$BdMgtSnSearchRequestImpl.fromJson;

  @override
  String get bdMgtSn;
  @override
  String? get lnbrMnnm;
  @override // 지번 본번 (토지 지번)
  String? get lnbrSlno;
  @override // 지번 부번 (토지 지번)
  String? get admCd;
  @override
  @JsonKey(ignore: true)
  _$$BdMgtSnSearchRequestImplCopyWith<_$BdMgtSnSearchRequestImpl>
      get copyWith => throw _privateConstructorUsedError;
}

CodeInfo _$CodeInfoFromJson(Map<String, dynamic> json) {
  return _CodeInfo.fromJson(json);
}

/// @nodoc
mixin _$CodeInfo {
  @JsonKey(name: 'sigungu_cd')
  String? get sigunguCd => throw _privateConstructorUsedError;
  @JsonKey(name: 'bjdong_cd')
  String? get bjdongCd => throw _privateConstructorUsedError;
  String? get pnu => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $CodeInfoCopyWith<CodeInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CodeInfoCopyWith<$Res> {
  factory $CodeInfoCopyWith(CodeInfo value, $Res Function(CodeInfo) then) =
      _$CodeInfoCopyWithImpl<$Res, CodeInfo>;
  @useResult
  $Res call(
      {@JsonKey(name: 'sigungu_cd') String? sigunguCd,
      @JsonKey(name: 'bjdong_cd') String? bjdongCd,
      String? pnu});
}

/// @nodoc
class _$CodeInfoCopyWithImpl<$Res, $Val extends CodeInfo>
    implements $CodeInfoCopyWith<$Res> {
  _$CodeInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sigunguCd = freezed,
    Object? bjdongCd = freezed,
    Object? pnu = freezed,
  }) {
    return _then(_value.copyWith(
      sigunguCd: freezed == sigunguCd
          ? _value.sigunguCd
          : sigunguCd // ignore: cast_nullable_to_non_nullable
              as String?,
      bjdongCd: freezed == bjdongCd
          ? _value.bjdongCd
          : bjdongCd // ignore: cast_nullable_to_non_nullable
              as String?,
      pnu: freezed == pnu
          ? _value.pnu
          : pnu // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CodeInfoImplCopyWith<$Res>
    implements $CodeInfoCopyWith<$Res> {
  factory _$$CodeInfoImplCopyWith(
          _$CodeInfoImpl value, $Res Function(_$CodeInfoImpl) then) =
      __$$CodeInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'sigungu_cd') String? sigunguCd,
      @JsonKey(name: 'bjdong_cd') String? bjdongCd,
      String? pnu});
}

/// @nodoc
class __$$CodeInfoImplCopyWithImpl<$Res>
    extends _$CodeInfoCopyWithImpl<$Res, _$CodeInfoImpl>
    implements _$$CodeInfoImplCopyWith<$Res> {
  __$$CodeInfoImplCopyWithImpl(
      _$CodeInfoImpl _value, $Res Function(_$CodeInfoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sigunguCd = freezed,
    Object? bjdongCd = freezed,
    Object? pnu = freezed,
  }) {
    return _then(_$CodeInfoImpl(
      sigunguCd: freezed == sigunguCd
          ? _value.sigunguCd
          : sigunguCd // ignore: cast_nullable_to_non_nullable
              as String?,
      bjdongCd: freezed == bjdongCd
          ? _value.bjdongCd
          : bjdongCd // ignore: cast_nullable_to_non_nullable
              as String?,
      pnu: freezed == pnu
          ? _value.pnu
          : pnu // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CodeInfoImpl implements _CodeInfo {
  const _$CodeInfoImpl(
      {@JsonKey(name: 'sigungu_cd') this.sigunguCd,
      @JsonKey(name: 'bjdong_cd') this.bjdongCd,
      this.pnu});

  factory _$CodeInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$CodeInfoImplFromJson(json);

  @override
  @JsonKey(name: 'sigungu_cd')
  final String? sigunguCd;
  @override
  @JsonKey(name: 'bjdong_cd')
  final String? bjdongCd;
  @override
  final String? pnu;

  @override
  String toString() {
    return 'CodeInfo(sigunguCd: $sigunguCd, bjdongCd: $bjdongCd, pnu: $pnu)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CodeInfoImpl &&
            (identical(other.sigunguCd, sigunguCd) ||
                other.sigunguCd == sigunguCd) &&
            (identical(other.bjdongCd, bjdongCd) ||
                other.bjdongCd == bjdongCd) &&
            (identical(other.pnu, pnu) || other.pnu == pnu));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, sigunguCd, bjdongCd, pnu);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$CodeInfoImplCopyWith<_$CodeInfoImpl> get copyWith =>
      __$$CodeInfoImplCopyWithImpl<_$CodeInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CodeInfoImplToJson(
      this,
    );
  }
}

abstract class _CodeInfo implements CodeInfo {
  const factory _CodeInfo(
      {@JsonKey(name: 'sigungu_cd') final String? sigunguCd,
      @JsonKey(name: 'bjdong_cd') final String? bjdongCd,
      final String? pnu}) = _$CodeInfoImpl;

  factory _CodeInfo.fromJson(Map<String, dynamic> json) =
      _$CodeInfoImpl.fromJson;

  @override
  @JsonKey(name: 'sigungu_cd')
  String? get sigunguCd;
  @override
  @JsonKey(name: 'bjdong_cd')
  String? get bjdongCd;
  @override
  String? get pnu;
  @override
  @JsonKey(ignore: true)
  _$$CodeInfoImplCopyWith<_$CodeInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AddressInfo _$AddressInfoFromJson(Map<String, dynamic> json) {
  return _AddressInfo.fromJson(json);
}

/// @nodoc
mixin _$AddressInfo {
  @JsonKey(name: 'bjdong_code')
  String? get bjdongCode => throw _privateConstructorUsedError;
  @JsonKey(name: 'full_address')
  String? get fullAddress => throw _privateConstructorUsedError;
  @JsonKey(name: 'sido_name')
  String? get sidoName => throw _privateConstructorUsedError;
  @JsonKey(name: 'sigungu_name')
  String? get sigunguName => throw _privateConstructorUsedError;
  @JsonKey(name: 'eupmyeondong_name')
  String? get eupmyeondongName => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AddressInfoCopyWith<AddressInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AddressInfoCopyWith<$Res> {
  factory $AddressInfoCopyWith(
          AddressInfo value, $Res Function(AddressInfo) then) =
      _$AddressInfoCopyWithImpl<$Res, AddressInfo>;
  @useResult
  $Res call(
      {@JsonKey(name: 'bjdong_code') String? bjdongCode,
      @JsonKey(name: 'full_address') String? fullAddress,
      @JsonKey(name: 'sido_name') String? sidoName,
      @JsonKey(name: 'sigungu_name') String? sigunguName,
      @JsonKey(name: 'eupmyeondong_name') String? eupmyeondongName});
}

/// @nodoc
class _$AddressInfoCopyWithImpl<$Res, $Val extends AddressInfo>
    implements $AddressInfoCopyWith<$Res> {
  _$AddressInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? bjdongCode = freezed,
    Object? fullAddress = freezed,
    Object? sidoName = freezed,
    Object? sigunguName = freezed,
    Object? eupmyeondongName = freezed,
  }) {
    return _then(_value.copyWith(
      bjdongCode: freezed == bjdongCode
          ? _value.bjdongCode
          : bjdongCode // ignore: cast_nullable_to_non_nullable
              as String?,
      fullAddress: freezed == fullAddress
          ? _value.fullAddress
          : fullAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      sidoName: freezed == sidoName
          ? _value.sidoName
          : sidoName // ignore: cast_nullable_to_non_nullable
              as String?,
      sigunguName: freezed == sigunguName
          ? _value.sigunguName
          : sigunguName // ignore: cast_nullable_to_non_nullable
              as String?,
      eupmyeondongName: freezed == eupmyeondongName
          ? _value.eupmyeondongName
          : eupmyeondongName // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$AddressInfoImplCopyWith<$Res>
    implements $AddressInfoCopyWith<$Res> {
  factory _$$AddressInfoImplCopyWith(
          _$AddressInfoImpl value, $Res Function(_$AddressInfoImpl) then) =
      __$$AddressInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'bjdong_code') String? bjdongCode,
      @JsonKey(name: 'full_address') String? fullAddress,
      @JsonKey(name: 'sido_name') String? sidoName,
      @JsonKey(name: 'sigungu_name') String? sigunguName,
      @JsonKey(name: 'eupmyeondong_name') String? eupmyeondongName});
}

/// @nodoc
class __$$AddressInfoImplCopyWithImpl<$Res>
    extends _$AddressInfoCopyWithImpl<$Res, _$AddressInfoImpl>
    implements _$$AddressInfoImplCopyWith<$Res> {
  __$$AddressInfoImplCopyWithImpl(
      _$AddressInfoImpl _value, $Res Function(_$AddressInfoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? bjdongCode = freezed,
    Object? fullAddress = freezed,
    Object? sidoName = freezed,
    Object? sigunguName = freezed,
    Object? eupmyeondongName = freezed,
  }) {
    return _then(_$AddressInfoImpl(
      bjdongCode: freezed == bjdongCode
          ? _value.bjdongCode
          : bjdongCode // ignore: cast_nullable_to_non_nullable
              as String?,
      fullAddress: freezed == fullAddress
          ? _value.fullAddress
          : fullAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      sidoName: freezed == sidoName
          ? _value.sidoName
          : sidoName // ignore: cast_nullable_to_non_nullable
              as String?,
      sigunguName: freezed == sigunguName
          ? _value.sigunguName
          : sigunguName // ignore: cast_nullable_to_non_nullable
              as String?,
      eupmyeondongName: freezed == eupmyeondongName
          ? _value.eupmyeondongName
          : eupmyeondongName // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AddressInfoImpl implements _AddressInfo {
  const _$AddressInfoImpl(
      {@JsonKey(name: 'bjdong_code') this.bjdongCode,
      @JsonKey(name: 'full_address') this.fullAddress,
      @JsonKey(name: 'sido_name') this.sidoName,
      @JsonKey(name: 'sigungu_name') this.sigunguName,
      @JsonKey(name: 'eupmyeondong_name') this.eupmyeondongName});

  factory _$AddressInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$AddressInfoImplFromJson(json);

  @override
  @JsonKey(name: 'bjdong_code')
  final String? bjdongCode;
  @override
  @JsonKey(name: 'full_address')
  final String? fullAddress;
  @override
  @JsonKey(name: 'sido_name')
  final String? sidoName;
  @override
  @JsonKey(name: 'sigungu_name')
  final String? sigunguName;
  @override
  @JsonKey(name: 'eupmyeondong_name')
  final String? eupmyeondongName;

  @override
  String toString() {
    return 'AddressInfo(bjdongCode: $bjdongCode, fullAddress: $fullAddress, sidoName: $sidoName, sigunguName: $sigunguName, eupmyeondongName: $eupmyeondongName)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AddressInfoImpl &&
            (identical(other.bjdongCode, bjdongCode) ||
                other.bjdongCode == bjdongCode) &&
            (identical(other.fullAddress, fullAddress) ||
                other.fullAddress == fullAddress) &&
            (identical(other.sidoName, sidoName) ||
                other.sidoName == sidoName) &&
            (identical(other.sigunguName, sigunguName) ||
                other.sigunguName == sigunguName) &&
            (identical(other.eupmyeondongName, eupmyeondongName) ||
                other.eupmyeondongName == eupmyeondongName));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, bjdongCode, fullAddress,
      sidoName, sigunguName, eupmyeondongName);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AddressInfoImplCopyWith<_$AddressInfoImpl> get copyWith =>
      __$$AddressInfoImplCopyWithImpl<_$AddressInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AddressInfoImplToJson(
      this,
    );
  }
}

abstract class _AddressInfo implements AddressInfo {
  const factory _AddressInfo(
          {@JsonKey(name: 'bjdong_code') final String? bjdongCode,
          @JsonKey(name: 'full_address') final String? fullAddress,
          @JsonKey(name: 'sido_name') final String? sidoName,
          @JsonKey(name: 'sigungu_name') final String? sigunguName,
          @JsonKey(name: 'eupmyeondong_name') final String? eupmyeondongName}) =
      _$AddressInfoImpl;

  factory _AddressInfo.fromJson(Map<String, dynamic> json) =
      _$AddressInfoImpl.fromJson;

  @override
  @JsonKey(name: 'bjdong_code')
  String? get bjdongCode;
  @override
  @JsonKey(name: 'full_address')
  String? get fullAddress;
  @override
  @JsonKey(name: 'sido_name')
  String? get sidoName;
  @override
  @JsonKey(name: 'sigungu_name')
  String? get sigunguName;
  @override
  @JsonKey(name: 'eupmyeondong_name')
  String? get eupmyeondongName;
  @override
  @JsonKey(ignore: true)
  _$$AddressInfoImplCopyWith<_$AddressInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BuildingBasicInfo _$BuildingBasicInfoFromJson(Map<String, dynamic> json) {
  return _BuildingBasicInfo.fromJson(json);
}

/// @nodoc
mixin _$BuildingBasicInfo {
// 기본 정보
  @JsonKey(name: 'building_name')
  String? get buildingName => throw _privateConstructorUsedError;
  @JsonKey(name: 'dong_nm')
  String? get dongNm => throw _privateConstructorUsedError;
  @JsonKey(name: 'plat_plc')
  String? get platPlc => throw _privateConstructorUsedError;
  @JsonKey(name: 'new_plat_plc')
  String? get newPlatPlc => throw _privateConstructorUsedError; // 용도
  @JsonKey(name: 'main_purpose')
  String? get mainPurpose => throw _privateConstructorUsedError;
  @JsonKey(name: 'etc_purpose')
  String? get etcPurpose => throw _privateConstructorUsedError; // 구조
  @JsonKey(name: 'main_structure')
  String? get mainStructure => throw _privateConstructorUsedError;
  String? get roof => throw _privateConstructorUsedError;
  @JsonKey(name: 'etc_roof')
  String? get etcRoof => throw _privateConstructorUsedError; // 층수
  @JsonKey(name: 'total_floors')
  int? get totalFloors => throw _privateConstructorUsedError;
  @JsonKey(name: 'basement_floors')
  int? get basementFloors => throw _privateConstructorUsedError;
  double? get height => throw _privateConstructorUsedError; // 면적
  @JsonKey(name: 'land_area')
  double? get landArea => throw _privateConstructorUsedError;
  @JsonKey(name: 'building_area')
  double? get buildingArea => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_area')
  double? get totalArea => throw _privateConstructorUsedError;
  @JsonKey(name: 'vl_rat_estm_tot_area')
  double? get vlRatEstmTotArea => throw _privateConstructorUsedError; // 비율
  @JsonKey(name: 'building_coverage')
  double? get buildingCoverage => throw _privateConstructorUsedError;
  @JsonKey(name: 'floor_area_ratio')
  double? get floorAreaRatio => throw _privateConstructorUsedError; // 세대/호수 정보
  @JsonKey(name: 'family_cnt', fromJson: _intFromDynamic)
  int? get familyCnt => throw _privateConstructorUsedError;
  @JsonKey(name: 'hhld_cnt', fromJson: _intFromDynamic)
  int? get hhldCnt => throw _privateConstructorUsedError;
  @JsonKey(name: 'ho_cnt', fromJson: _intFromDynamic)
  int? get hoCnt => throw _privateConstructorUsedError; // 설비
  @JsonKey(name: 'elevator_count', fromJson: _intFromDynamic)
  int? get elevatorCount => throw _privateConstructorUsedError;
  @JsonKey(name: 'emergency_elevator_count', fromJson: _intFromDynamic)
  int? get emergencyElevatorCount => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_parking', fromJson: _stringFromDynamic)
  String? get totalParking => throw _privateConstructorUsedError; // 일자
  @JsonKey(name: 'permit_date')
  String? get permitDate => throw _privateConstructorUsedError;
  @JsonKey(name: 'use_approval_date')
  String? get useApprovalDate => throw _privateConstructorUsedError;
  @JsonKey(name: 'permit_date_raw')
  String? get permitDateRaw => throw _privateConstructorUsedError;
  @JsonKey(name: 'use_approval_date_raw')
  String? get useApprovalDateRaw =>
      throw _privateConstructorUsedError; // 가격 (개별주택/공동주택)
  @JsonKey(name: 'house_price')
  int? get housePrice => throw _privateConstructorUsedError;
  @JsonKey(name: 'house_price_year')
  String? get housePriceYear => throw _privateConstructorUsedError;
  @JsonKey(name: 'house_price_month')
  String? get housePriceMonth => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BuildingBasicInfoCopyWith<BuildingBasicInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BuildingBasicInfoCopyWith<$Res> {
  factory $BuildingBasicInfoCopyWith(
          BuildingBasicInfo value, $Res Function(BuildingBasicInfo) then) =
      _$BuildingBasicInfoCopyWithImpl<$Res, BuildingBasicInfo>;
  @useResult
  $Res call(
      {@JsonKey(name: 'building_name') String? buildingName,
      @JsonKey(name: 'dong_nm') String? dongNm,
      @JsonKey(name: 'plat_plc') String? platPlc,
      @JsonKey(name: 'new_plat_plc') String? newPlatPlc,
      @JsonKey(name: 'main_purpose') String? mainPurpose,
      @JsonKey(name: 'etc_purpose') String? etcPurpose,
      @JsonKey(name: 'main_structure') String? mainStructure,
      String? roof,
      @JsonKey(name: 'etc_roof') String? etcRoof,
      @JsonKey(name: 'total_floors') int? totalFloors,
      @JsonKey(name: 'basement_floors') int? basementFloors,
      double? height,
      @JsonKey(name: 'land_area') double? landArea,
      @JsonKey(name: 'building_area') double? buildingArea,
      @JsonKey(name: 'total_area') double? totalArea,
      @JsonKey(name: 'vl_rat_estm_tot_area') double? vlRatEstmTotArea,
      @JsonKey(name: 'building_coverage') double? buildingCoverage,
      @JsonKey(name: 'floor_area_ratio') double? floorAreaRatio,
      @JsonKey(name: 'family_cnt', fromJson: _intFromDynamic) int? familyCnt,
      @JsonKey(name: 'hhld_cnt', fromJson: _intFromDynamic) int? hhldCnt,
      @JsonKey(name: 'ho_cnt', fromJson: _intFromDynamic) int? hoCnt,
      @JsonKey(name: 'elevator_count', fromJson: _intFromDynamic)
      int? elevatorCount,
      @JsonKey(name: 'emergency_elevator_count', fromJson: _intFromDynamic)
      int? emergencyElevatorCount,
      @JsonKey(name: 'total_parking', fromJson: _stringFromDynamic)
      String? totalParking,
      @JsonKey(name: 'permit_date') String? permitDate,
      @JsonKey(name: 'use_approval_date') String? useApprovalDate,
      @JsonKey(name: 'permit_date_raw') String? permitDateRaw,
      @JsonKey(name: 'use_approval_date_raw') String? useApprovalDateRaw,
      @JsonKey(name: 'house_price') int? housePrice,
      @JsonKey(name: 'house_price_year') String? housePriceYear,
      @JsonKey(name: 'house_price_month') String? housePriceMonth});
}

/// @nodoc
class _$BuildingBasicInfoCopyWithImpl<$Res, $Val extends BuildingBasicInfo>
    implements $BuildingBasicInfoCopyWith<$Res> {
  _$BuildingBasicInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? buildingName = freezed,
    Object? dongNm = freezed,
    Object? platPlc = freezed,
    Object? newPlatPlc = freezed,
    Object? mainPurpose = freezed,
    Object? etcPurpose = freezed,
    Object? mainStructure = freezed,
    Object? roof = freezed,
    Object? etcRoof = freezed,
    Object? totalFloors = freezed,
    Object? basementFloors = freezed,
    Object? height = freezed,
    Object? landArea = freezed,
    Object? buildingArea = freezed,
    Object? totalArea = freezed,
    Object? vlRatEstmTotArea = freezed,
    Object? buildingCoverage = freezed,
    Object? floorAreaRatio = freezed,
    Object? familyCnt = freezed,
    Object? hhldCnt = freezed,
    Object? hoCnt = freezed,
    Object? elevatorCount = freezed,
    Object? emergencyElevatorCount = freezed,
    Object? totalParking = freezed,
    Object? permitDate = freezed,
    Object? useApprovalDate = freezed,
    Object? permitDateRaw = freezed,
    Object? useApprovalDateRaw = freezed,
    Object? housePrice = freezed,
    Object? housePriceYear = freezed,
    Object? housePriceMonth = freezed,
  }) {
    return _then(_value.copyWith(
      buildingName: freezed == buildingName
          ? _value.buildingName
          : buildingName // ignore: cast_nullable_to_non_nullable
              as String?,
      dongNm: freezed == dongNm
          ? _value.dongNm
          : dongNm // ignore: cast_nullable_to_non_nullable
              as String?,
      platPlc: freezed == platPlc
          ? _value.platPlc
          : platPlc // ignore: cast_nullable_to_non_nullable
              as String?,
      newPlatPlc: freezed == newPlatPlc
          ? _value.newPlatPlc
          : newPlatPlc // ignore: cast_nullable_to_non_nullable
              as String?,
      mainPurpose: freezed == mainPurpose
          ? _value.mainPurpose
          : mainPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      etcPurpose: freezed == etcPurpose
          ? _value.etcPurpose
          : etcPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      mainStructure: freezed == mainStructure
          ? _value.mainStructure
          : mainStructure // ignore: cast_nullable_to_non_nullable
              as String?,
      roof: freezed == roof
          ? _value.roof
          : roof // ignore: cast_nullable_to_non_nullable
              as String?,
      etcRoof: freezed == etcRoof
          ? _value.etcRoof
          : etcRoof // ignore: cast_nullable_to_non_nullable
              as String?,
      totalFloors: freezed == totalFloors
          ? _value.totalFloors
          : totalFloors // ignore: cast_nullable_to_non_nullable
              as int?,
      basementFloors: freezed == basementFloors
          ? _value.basementFloors
          : basementFloors // ignore: cast_nullable_to_non_nullable
              as int?,
      height: freezed == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as double?,
      landArea: freezed == landArea
          ? _value.landArea
          : landArea // ignore: cast_nullable_to_non_nullable
              as double?,
      buildingArea: freezed == buildingArea
          ? _value.buildingArea
          : buildingArea // ignore: cast_nullable_to_non_nullable
              as double?,
      totalArea: freezed == totalArea
          ? _value.totalArea
          : totalArea // ignore: cast_nullable_to_non_nullable
              as double?,
      vlRatEstmTotArea: freezed == vlRatEstmTotArea
          ? _value.vlRatEstmTotArea
          : vlRatEstmTotArea // ignore: cast_nullable_to_non_nullable
              as double?,
      buildingCoverage: freezed == buildingCoverage
          ? _value.buildingCoverage
          : buildingCoverage // ignore: cast_nullable_to_non_nullable
              as double?,
      floorAreaRatio: freezed == floorAreaRatio
          ? _value.floorAreaRatio
          : floorAreaRatio // ignore: cast_nullable_to_non_nullable
              as double?,
      familyCnt: freezed == familyCnt
          ? _value.familyCnt
          : familyCnt // ignore: cast_nullable_to_non_nullable
              as int?,
      hhldCnt: freezed == hhldCnt
          ? _value.hhldCnt
          : hhldCnt // ignore: cast_nullable_to_non_nullable
              as int?,
      hoCnt: freezed == hoCnt
          ? _value.hoCnt
          : hoCnt // ignore: cast_nullable_to_non_nullable
              as int?,
      elevatorCount: freezed == elevatorCount
          ? _value.elevatorCount
          : elevatorCount // ignore: cast_nullable_to_non_nullable
              as int?,
      emergencyElevatorCount: freezed == emergencyElevatorCount
          ? _value.emergencyElevatorCount
          : emergencyElevatorCount // ignore: cast_nullable_to_non_nullable
              as int?,
      totalParking: freezed == totalParking
          ? _value.totalParking
          : totalParking // ignore: cast_nullable_to_non_nullable
              as String?,
      permitDate: freezed == permitDate
          ? _value.permitDate
          : permitDate // ignore: cast_nullable_to_non_nullable
              as String?,
      useApprovalDate: freezed == useApprovalDate
          ? _value.useApprovalDate
          : useApprovalDate // ignore: cast_nullable_to_non_nullable
              as String?,
      permitDateRaw: freezed == permitDateRaw
          ? _value.permitDateRaw
          : permitDateRaw // ignore: cast_nullable_to_non_nullable
              as String?,
      useApprovalDateRaw: freezed == useApprovalDateRaw
          ? _value.useApprovalDateRaw
          : useApprovalDateRaw // ignore: cast_nullable_to_non_nullable
              as String?,
      housePrice: freezed == housePrice
          ? _value.housePrice
          : housePrice // ignore: cast_nullable_to_non_nullable
              as int?,
      housePriceYear: freezed == housePriceYear
          ? _value.housePriceYear
          : housePriceYear // ignore: cast_nullable_to_non_nullable
              as String?,
      housePriceMonth: freezed == housePriceMonth
          ? _value.housePriceMonth
          : housePriceMonth // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BuildingBasicInfoImplCopyWith<$Res>
    implements $BuildingBasicInfoCopyWith<$Res> {
  factory _$$BuildingBasicInfoImplCopyWith(_$BuildingBasicInfoImpl value,
          $Res Function(_$BuildingBasicInfoImpl) then) =
      __$$BuildingBasicInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'building_name') String? buildingName,
      @JsonKey(name: 'dong_nm') String? dongNm,
      @JsonKey(name: 'plat_plc') String? platPlc,
      @JsonKey(name: 'new_plat_plc') String? newPlatPlc,
      @JsonKey(name: 'main_purpose') String? mainPurpose,
      @JsonKey(name: 'etc_purpose') String? etcPurpose,
      @JsonKey(name: 'main_structure') String? mainStructure,
      String? roof,
      @JsonKey(name: 'etc_roof') String? etcRoof,
      @JsonKey(name: 'total_floors') int? totalFloors,
      @JsonKey(name: 'basement_floors') int? basementFloors,
      double? height,
      @JsonKey(name: 'land_area') double? landArea,
      @JsonKey(name: 'building_area') double? buildingArea,
      @JsonKey(name: 'total_area') double? totalArea,
      @JsonKey(name: 'vl_rat_estm_tot_area') double? vlRatEstmTotArea,
      @JsonKey(name: 'building_coverage') double? buildingCoverage,
      @JsonKey(name: 'floor_area_ratio') double? floorAreaRatio,
      @JsonKey(name: 'family_cnt', fromJson: _intFromDynamic) int? familyCnt,
      @JsonKey(name: 'hhld_cnt', fromJson: _intFromDynamic) int? hhldCnt,
      @JsonKey(name: 'ho_cnt', fromJson: _intFromDynamic) int? hoCnt,
      @JsonKey(name: 'elevator_count', fromJson: _intFromDynamic)
      int? elevatorCount,
      @JsonKey(name: 'emergency_elevator_count', fromJson: _intFromDynamic)
      int? emergencyElevatorCount,
      @JsonKey(name: 'total_parking', fromJson: _stringFromDynamic)
      String? totalParking,
      @JsonKey(name: 'permit_date') String? permitDate,
      @JsonKey(name: 'use_approval_date') String? useApprovalDate,
      @JsonKey(name: 'permit_date_raw') String? permitDateRaw,
      @JsonKey(name: 'use_approval_date_raw') String? useApprovalDateRaw,
      @JsonKey(name: 'house_price') int? housePrice,
      @JsonKey(name: 'house_price_year') String? housePriceYear,
      @JsonKey(name: 'house_price_month') String? housePriceMonth});
}

/// @nodoc
class __$$BuildingBasicInfoImplCopyWithImpl<$Res>
    extends _$BuildingBasicInfoCopyWithImpl<$Res, _$BuildingBasicInfoImpl>
    implements _$$BuildingBasicInfoImplCopyWith<$Res> {
  __$$BuildingBasicInfoImplCopyWithImpl(_$BuildingBasicInfoImpl _value,
      $Res Function(_$BuildingBasicInfoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? buildingName = freezed,
    Object? dongNm = freezed,
    Object? platPlc = freezed,
    Object? newPlatPlc = freezed,
    Object? mainPurpose = freezed,
    Object? etcPurpose = freezed,
    Object? mainStructure = freezed,
    Object? roof = freezed,
    Object? etcRoof = freezed,
    Object? totalFloors = freezed,
    Object? basementFloors = freezed,
    Object? height = freezed,
    Object? landArea = freezed,
    Object? buildingArea = freezed,
    Object? totalArea = freezed,
    Object? vlRatEstmTotArea = freezed,
    Object? buildingCoverage = freezed,
    Object? floorAreaRatio = freezed,
    Object? familyCnt = freezed,
    Object? hhldCnt = freezed,
    Object? hoCnt = freezed,
    Object? elevatorCount = freezed,
    Object? emergencyElevatorCount = freezed,
    Object? totalParking = freezed,
    Object? permitDate = freezed,
    Object? useApprovalDate = freezed,
    Object? permitDateRaw = freezed,
    Object? useApprovalDateRaw = freezed,
    Object? housePrice = freezed,
    Object? housePriceYear = freezed,
    Object? housePriceMonth = freezed,
  }) {
    return _then(_$BuildingBasicInfoImpl(
      buildingName: freezed == buildingName
          ? _value.buildingName
          : buildingName // ignore: cast_nullable_to_non_nullable
              as String?,
      dongNm: freezed == dongNm
          ? _value.dongNm
          : dongNm // ignore: cast_nullable_to_non_nullable
              as String?,
      platPlc: freezed == platPlc
          ? _value.platPlc
          : platPlc // ignore: cast_nullable_to_non_nullable
              as String?,
      newPlatPlc: freezed == newPlatPlc
          ? _value.newPlatPlc
          : newPlatPlc // ignore: cast_nullable_to_non_nullable
              as String?,
      mainPurpose: freezed == mainPurpose
          ? _value.mainPurpose
          : mainPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      etcPurpose: freezed == etcPurpose
          ? _value.etcPurpose
          : etcPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      mainStructure: freezed == mainStructure
          ? _value.mainStructure
          : mainStructure // ignore: cast_nullable_to_non_nullable
              as String?,
      roof: freezed == roof
          ? _value.roof
          : roof // ignore: cast_nullable_to_non_nullable
              as String?,
      etcRoof: freezed == etcRoof
          ? _value.etcRoof
          : etcRoof // ignore: cast_nullable_to_non_nullable
              as String?,
      totalFloors: freezed == totalFloors
          ? _value.totalFloors
          : totalFloors // ignore: cast_nullable_to_non_nullable
              as int?,
      basementFloors: freezed == basementFloors
          ? _value.basementFloors
          : basementFloors // ignore: cast_nullable_to_non_nullable
              as int?,
      height: freezed == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as double?,
      landArea: freezed == landArea
          ? _value.landArea
          : landArea // ignore: cast_nullable_to_non_nullable
              as double?,
      buildingArea: freezed == buildingArea
          ? _value.buildingArea
          : buildingArea // ignore: cast_nullable_to_non_nullable
              as double?,
      totalArea: freezed == totalArea
          ? _value.totalArea
          : totalArea // ignore: cast_nullable_to_non_nullable
              as double?,
      vlRatEstmTotArea: freezed == vlRatEstmTotArea
          ? _value.vlRatEstmTotArea
          : vlRatEstmTotArea // ignore: cast_nullable_to_non_nullable
              as double?,
      buildingCoverage: freezed == buildingCoverage
          ? _value.buildingCoverage
          : buildingCoverage // ignore: cast_nullable_to_non_nullable
              as double?,
      floorAreaRatio: freezed == floorAreaRatio
          ? _value.floorAreaRatio
          : floorAreaRatio // ignore: cast_nullable_to_non_nullable
              as double?,
      familyCnt: freezed == familyCnt
          ? _value.familyCnt
          : familyCnt // ignore: cast_nullable_to_non_nullable
              as int?,
      hhldCnt: freezed == hhldCnt
          ? _value.hhldCnt
          : hhldCnt // ignore: cast_nullable_to_non_nullable
              as int?,
      hoCnt: freezed == hoCnt
          ? _value.hoCnt
          : hoCnt // ignore: cast_nullable_to_non_nullable
              as int?,
      elevatorCount: freezed == elevatorCount
          ? _value.elevatorCount
          : elevatorCount // ignore: cast_nullable_to_non_nullable
              as int?,
      emergencyElevatorCount: freezed == emergencyElevatorCount
          ? _value.emergencyElevatorCount
          : emergencyElevatorCount // ignore: cast_nullable_to_non_nullable
              as int?,
      totalParking: freezed == totalParking
          ? _value.totalParking
          : totalParking // ignore: cast_nullable_to_non_nullable
              as String?,
      permitDate: freezed == permitDate
          ? _value.permitDate
          : permitDate // ignore: cast_nullable_to_non_nullable
              as String?,
      useApprovalDate: freezed == useApprovalDate
          ? _value.useApprovalDate
          : useApprovalDate // ignore: cast_nullable_to_non_nullable
              as String?,
      permitDateRaw: freezed == permitDateRaw
          ? _value.permitDateRaw
          : permitDateRaw // ignore: cast_nullable_to_non_nullable
              as String?,
      useApprovalDateRaw: freezed == useApprovalDateRaw
          ? _value.useApprovalDateRaw
          : useApprovalDateRaw // ignore: cast_nullable_to_non_nullable
              as String?,
      housePrice: freezed == housePrice
          ? _value.housePrice
          : housePrice // ignore: cast_nullable_to_non_nullable
              as int?,
      housePriceYear: freezed == housePriceYear
          ? _value.housePriceYear
          : housePriceYear // ignore: cast_nullable_to_non_nullable
              as String?,
      housePriceMonth: freezed == housePriceMonth
          ? _value.housePriceMonth
          : housePriceMonth // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BuildingBasicInfoImpl implements _BuildingBasicInfo {
  const _$BuildingBasicInfoImpl(
      {@JsonKey(name: 'building_name') this.buildingName,
      @JsonKey(name: 'dong_nm') this.dongNm,
      @JsonKey(name: 'plat_plc') this.platPlc,
      @JsonKey(name: 'new_plat_plc') this.newPlatPlc,
      @JsonKey(name: 'main_purpose') this.mainPurpose,
      @JsonKey(name: 'etc_purpose') this.etcPurpose,
      @JsonKey(name: 'main_structure') this.mainStructure,
      this.roof,
      @JsonKey(name: 'etc_roof') this.etcRoof,
      @JsonKey(name: 'total_floors') this.totalFloors,
      @JsonKey(name: 'basement_floors') this.basementFloors,
      this.height,
      @JsonKey(name: 'land_area') this.landArea,
      @JsonKey(name: 'building_area') this.buildingArea,
      @JsonKey(name: 'total_area') this.totalArea,
      @JsonKey(name: 'vl_rat_estm_tot_area') this.vlRatEstmTotArea,
      @JsonKey(name: 'building_coverage') this.buildingCoverage,
      @JsonKey(name: 'floor_area_ratio') this.floorAreaRatio,
      @JsonKey(name: 'family_cnt', fromJson: _intFromDynamic) this.familyCnt,
      @JsonKey(name: 'hhld_cnt', fromJson: _intFromDynamic) this.hhldCnt,
      @JsonKey(name: 'ho_cnt', fromJson: _intFromDynamic) this.hoCnt,
      @JsonKey(name: 'elevator_count', fromJson: _intFromDynamic)
      this.elevatorCount,
      @JsonKey(name: 'emergency_elevator_count', fromJson: _intFromDynamic)
      this.emergencyElevatorCount,
      @JsonKey(name: 'total_parking', fromJson: _stringFromDynamic)
      this.totalParking,
      @JsonKey(name: 'permit_date') this.permitDate,
      @JsonKey(name: 'use_approval_date') this.useApprovalDate,
      @JsonKey(name: 'permit_date_raw') this.permitDateRaw,
      @JsonKey(name: 'use_approval_date_raw') this.useApprovalDateRaw,
      @JsonKey(name: 'house_price') this.housePrice,
      @JsonKey(name: 'house_price_year') this.housePriceYear,
      @JsonKey(name: 'house_price_month') this.housePriceMonth});

  factory _$BuildingBasicInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$BuildingBasicInfoImplFromJson(json);

// 기본 정보
  @override
  @JsonKey(name: 'building_name')
  final String? buildingName;
  @override
  @JsonKey(name: 'dong_nm')
  final String? dongNm;
  @override
  @JsonKey(name: 'plat_plc')
  final String? platPlc;
  @override
  @JsonKey(name: 'new_plat_plc')
  final String? newPlatPlc;
// 용도
  @override
  @JsonKey(name: 'main_purpose')
  final String? mainPurpose;
  @override
  @JsonKey(name: 'etc_purpose')
  final String? etcPurpose;
// 구조
  @override
  @JsonKey(name: 'main_structure')
  final String? mainStructure;
  @override
  final String? roof;
  @override
  @JsonKey(name: 'etc_roof')
  final String? etcRoof;
// 층수
  @override
  @JsonKey(name: 'total_floors')
  final int? totalFloors;
  @override
  @JsonKey(name: 'basement_floors')
  final int? basementFloors;
  @override
  final double? height;
// 면적
  @override
  @JsonKey(name: 'land_area')
  final double? landArea;
  @override
  @JsonKey(name: 'building_area')
  final double? buildingArea;
  @override
  @JsonKey(name: 'total_area')
  final double? totalArea;
  @override
  @JsonKey(name: 'vl_rat_estm_tot_area')
  final double? vlRatEstmTotArea;
// 비율
  @override
  @JsonKey(name: 'building_coverage')
  final double? buildingCoverage;
  @override
  @JsonKey(name: 'floor_area_ratio')
  final double? floorAreaRatio;
// 세대/호수 정보
  @override
  @JsonKey(name: 'family_cnt', fromJson: _intFromDynamic)
  final int? familyCnt;
  @override
  @JsonKey(name: 'hhld_cnt', fromJson: _intFromDynamic)
  final int? hhldCnt;
  @override
  @JsonKey(name: 'ho_cnt', fromJson: _intFromDynamic)
  final int? hoCnt;
// 설비
  @override
  @JsonKey(name: 'elevator_count', fromJson: _intFromDynamic)
  final int? elevatorCount;
  @override
  @JsonKey(name: 'emergency_elevator_count', fromJson: _intFromDynamic)
  final int? emergencyElevatorCount;
  @override
  @JsonKey(name: 'total_parking', fromJson: _stringFromDynamic)
  final String? totalParking;
// 일자
  @override
  @JsonKey(name: 'permit_date')
  final String? permitDate;
  @override
  @JsonKey(name: 'use_approval_date')
  final String? useApprovalDate;
  @override
  @JsonKey(name: 'permit_date_raw')
  final String? permitDateRaw;
  @override
  @JsonKey(name: 'use_approval_date_raw')
  final String? useApprovalDateRaw;
// 가격 (개별주택/공동주택)
  @override
  @JsonKey(name: 'house_price')
  final int? housePrice;
  @override
  @JsonKey(name: 'house_price_year')
  final String? housePriceYear;
  @override
  @JsonKey(name: 'house_price_month')
  final String? housePriceMonth;

  @override
  String toString() {
    return 'BuildingBasicInfo(buildingName: $buildingName, dongNm: $dongNm, platPlc: $platPlc, newPlatPlc: $newPlatPlc, mainPurpose: $mainPurpose, etcPurpose: $etcPurpose, mainStructure: $mainStructure, roof: $roof, etcRoof: $etcRoof, totalFloors: $totalFloors, basementFloors: $basementFloors, height: $height, landArea: $landArea, buildingArea: $buildingArea, totalArea: $totalArea, vlRatEstmTotArea: $vlRatEstmTotArea, buildingCoverage: $buildingCoverage, floorAreaRatio: $floorAreaRatio, familyCnt: $familyCnt, hhldCnt: $hhldCnt, hoCnt: $hoCnt, elevatorCount: $elevatorCount, emergencyElevatorCount: $emergencyElevatorCount, totalParking: $totalParking, permitDate: $permitDate, useApprovalDate: $useApprovalDate, permitDateRaw: $permitDateRaw, useApprovalDateRaw: $useApprovalDateRaw, housePrice: $housePrice, housePriceYear: $housePriceYear, housePriceMonth: $housePriceMonth)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BuildingBasicInfoImpl &&
            (identical(other.buildingName, buildingName) ||
                other.buildingName == buildingName) &&
            (identical(other.dongNm, dongNm) || other.dongNm == dongNm) &&
            (identical(other.platPlc, platPlc) || other.platPlc == platPlc) &&
            (identical(other.newPlatPlc, newPlatPlc) ||
                other.newPlatPlc == newPlatPlc) &&
            (identical(other.mainPurpose, mainPurpose) ||
                other.mainPurpose == mainPurpose) &&
            (identical(other.etcPurpose, etcPurpose) ||
                other.etcPurpose == etcPurpose) &&
            (identical(other.mainStructure, mainStructure) ||
                other.mainStructure == mainStructure) &&
            (identical(other.roof, roof) || other.roof == roof) &&
            (identical(other.etcRoof, etcRoof) || other.etcRoof == etcRoof) &&
            (identical(other.totalFloors, totalFloors) ||
                other.totalFloors == totalFloors) &&
            (identical(other.basementFloors, basementFloors) ||
                other.basementFloors == basementFloors) &&
            (identical(other.height, height) || other.height == height) &&
            (identical(other.landArea, landArea) ||
                other.landArea == landArea) &&
            (identical(other.buildingArea, buildingArea) ||
                other.buildingArea == buildingArea) &&
            (identical(other.totalArea, totalArea) ||
                other.totalArea == totalArea) &&
            (identical(other.vlRatEstmTotArea, vlRatEstmTotArea) ||
                other.vlRatEstmTotArea == vlRatEstmTotArea) &&
            (identical(other.buildingCoverage, buildingCoverage) ||
                other.buildingCoverage == buildingCoverage) &&
            (identical(other.floorAreaRatio, floorAreaRatio) ||
                other.floorAreaRatio == floorAreaRatio) &&
            (identical(other.familyCnt, familyCnt) ||
                other.familyCnt == familyCnt) &&
            (identical(other.hhldCnt, hhldCnt) || other.hhldCnt == hhldCnt) &&
            (identical(other.hoCnt, hoCnt) || other.hoCnt == hoCnt) &&
            (identical(other.elevatorCount, elevatorCount) ||
                other.elevatorCount == elevatorCount) &&
            (identical(other.emergencyElevatorCount, emergencyElevatorCount) ||
                other.emergencyElevatorCount == emergencyElevatorCount) &&
            (identical(other.totalParking, totalParking) ||
                other.totalParking == totalParking) &&
            (identical(other.permitDate, permitDate) ||
                other.permitDate == permitDate) &&
            (identical(other.useApprovalDate, useApprovalDate) ||
                other.useApprovalDate == useApprovalDate) &&
            (identical(other.permitDateRaw, permitDateRaw) ||
                other.permitDateRaw == permitDateRaw) &&
            (identical(other.useApprovalDateRaw, useApprovalDateRaw) ||
                other.useApprovalDateRaw == useApprovalDateRaw) &&
            (identical(other.housePrice, housePrice) ||
                other.housePrice == housePrice) &&
            (identical(other.housePriceYear, housePriceYear) ||
                other.housePriceYear == housePriceYear) &&
            (identical(other.housePriceMonth, housePriceMonth) ||
                other.housePriceMonth == housePriceMonth));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hashAll([
        runtimeType,
        buildingName,
        dongNm,
        platPlc,
        newPlatPlc,
        mainPurpose,
        etcPurpose,
        mainStructure,
        roof,
        etcRoof,
        totalFloors,
        basementFloors,
        height,
        landArea,
        buildingArea,
        totalArea,
        vlRatEstmTotArea,
        buildingCoverage,
        floorAreaRatio,
        familyCnt,
        hhldCnt,
        hoCnt,
        elevatorCount,
        emergencyElevatorCount,
        totalParking,
        permitDate,
        useApprovalDate,
        permitDateRaw,
        useApprovalDateRaw,
        housePrice,
        housePriceYear,
        housePriceMonth
      ]);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BuildingBasicInfoImplCopyWith<_$BuildingBasicInfoImpl> get copyWith =>
      __$$BuildingBasicInfoImplCopyWithImpl<_$BuildingBasicInfoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BuildingBasicInfoImplToJson(
      this,
    );
  }
}

abstract class _BuildingBasicInfo implements BuildingBasicInfo {
  const factory _BuildingBasicInfo(
      {@JsonKey(name: 'building_name') final String? buildingName,
      @JsonKey(name: 'dong_nm') final String? dongNm,
      @JsonKey(name: 'plat_plc') final String? platPlc,
      @JsonKey(name: 'new_plat_plc') final String? newPlatPlc,
      @JsonKey(name: 'main_purpose') final String? mainPurpose,
      @JsonKey(name: 'etc_purpose') final String? etcPurpose,
      @JsonKey(name: 'main_structure') final String? mainStructure,
      final String? roof,
      @JsonKey(name: 'etc_roof') final String? etcRoof,
      @JsonKey(name: 'total_floors') final int? totalFloors,
      @JsonKey(name: 'basement_floors') final int? basementFloors,
      final double? height,
      @JsonKey(name: 'land_area') final double? landArea,
      @JsonKey(name: 'building_area') final double? buildingArea,
      @JsonKey(name: 'total_area') final double? totalArea,
      @JsonKey(name: 'vl_rat_estm_tot_area') final double? vlRatEstmTotArea,
      @JsonKey(name: 'building_coverage') final double? buildingCoverage,
      @JsonKey(name: 'floor_area_ratio') final double? floorAreaRatio,
      @JsonKey(name: 'family_cnt', fromJson: _intFromDynamic)
      final int? familyCnt,
      @JsonKey(name: 'hhld_cnt', fromJson: _intFromDynamic) final int? hhldCnt,
      @JsonKey(name: 'ho_cnt', fromJson: _intFromDynamic) final int? hoCnt,
      @JsonKey(name: 'elevator_count', fromJson: _intFromDynamic)
      final int? elevatorCount,
      @JsonKey(name: 'emergency_elevator_count', fromJson: _intFromDynamic)
      final int? emergencyElevatorCount,
      @JsonKey(name: 'total_parking', fromJson: _stringFromDynamic)
      final String? totalParking,
      @JsonKey(name: 'permit_date') final String? permitDate,
      @JsonKey(name: 'use_approval_date') final String? useApprovalDate,
      @JsonKey(name: 'permit_date_raw') final String? permitDateRaw,
      @JsonKey(name: 'use_approval_date_raw') final String? useApprovalDateRaw,
      @JsonKey(name: 'house_price') final int? housePrice,
      @JsonKey(name: 'house_price_year') final String? housePriceYear,
      @JsonKey(name: 'house_price_month')
      final String? housePriceMonth}) = _$BuildingBasicInfoImpl;

  factory _BuildingBasicInfo.fromJson(Map<String, dynamic> json) =
      _$BuildingBasicInfoImpl.fromJson;

  @override // 기본 정보
  @JsonKey(name: 'building_name')
  String? get buildingName;
  @override
  @JsonKey(name: 'dong_nm')
  String? get dongNm;
  @override
  @JsonKey(name: 'plat_plc')
  String? get platPlc;
  @override
  @JsonKey(name: 'new_plat_plc')
  String? get newPlatPlc;
  @override // 용도
  @JsonKey(name: 'main_purpose')
  String? get mainPurpose;
  @override
  @JsonKey(name: 'etc_purpose')
  String? get etcPurpose;
  @override // 구조
  @JsonKey(name: 'main_structure')
  String? get mainStructure;
  @override
  String? get roof;
  @override
  @JsonKey(name: 'etc_roof')
  String? get etcRoof;
  @override // 층수
  @JsonKey(name: 'total_floors')
  int? get totalFloors;
  @override
  @JsonKey(name: 'basement_floors')
  int? get basementFloors;
  @override
  double? get height;
  @override // 면적
  @JsonKey(name: 'land_area')
  double? get landArea;
  @override
  @JsonKey(name: 'building_area')
  double? get buildingArea;
  @override
  @JsonKey(name: 'total_area')
  double? get totalArea;
  @override
  @JsonKey(name: 'vl_rat_estm_tot_area')
  double? get vlRatEstmTotArea;
  @override // 비율
  @JsonKey(name: 'building_coverage')
  double? get buildingCoverage;
  @override
  @JsonKey(name: 'floor_area_ratio')
  double? get floorAreaRatio;
  @override // 세대/호수 정보
  @JsonKey(name: 'family_cnt', fromJson: _intFromDynamic)
  int? get familyCnt;
  @override
  @JsonKey(name: 'hhld_cnt', fromJson: _intFromDynamic)
  int? get hhldCnt;
  @override
  @JsonKey(name: 'ho_cnt', fromJson: _intFromDynamic)
  int? get hoCnt;
  @override // 설비
  @JsonKey(name: 'elevator_count', fromJson: _intFromDynamic)
  int? get elevatorCount;
  @override
  @JsonKey(name: 'emergency_elevator_count', fromJson: _intFromDynamic)
  int? get emergencyElevatorCount;
  @override
  @JsonKey(name: 'total_parking', fromJson: _stringFromDynamic)
  String? get totalParking;
  @override // 일자
  @JsonKey(name: 'permit_date')
  String? get permitDate;
  @override
  @JsonKey(name: 'use_approval_date')
  String? get useApprovalDate;
  @override
  @JsonKey(name: 'permit_date_raw')
  String? get permitDateRaw;
  @override
  @JsonKey(name: 'use_approval_date_raw')
  String? get useApprovalDateRaw;
  @override // 가격 (개별주택/공동주택)
  @JsonKey(name: 'house_price')
  int? get housePrice;
  @override
  @JsonKey(name: 'house_price_year')
  String? get housePriceYear;
  @override
  @JsonKey(name: 'house_price_month')
  String? get housePriceMonth;
  @override
  @JsonKey(ignore: true)
  _$$BuildingBasicInfoImplCopyWith<_$BuildingBasicInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

FloorInfo _$FloorInfoFromJson(Map<String, dynamic> json) {
  return _FloorInfo.fromJson(json);
}

/// @nodoc
mixin _$FloorInfo {
  @JsonKey(name: 'floor_no')
  int? get floorNo => throw _privateConstructorUsedError;
  @JsonKey(name: 'floor_name')
  String? get floorName => throw _privateConstructorUsedError;
  @JsonKey(name: 'floor_gb')
  String? get floorGb => throw _privateConstructorUsedError;
  double? get area => throw _privateConstructorUsedError;
  String? get purpose => throw _privateConstructorUsedError;
  @JsonKey(name: 'etc_purpose')
  String? get etcPurpose => throw _privateConstructorUsedError;
  String? get structure => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $FloorInfoCopyWith<FloorInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $FloorInfoCopyWith<$Res> {
  factory $FloorInfoCopyWith(FloorInfo value, $Res Function(FloorInfo) then) =
      _$FloorInfoCopyWithImpl<$Res, FloorInfo>;
  @useResult
  $Res call(
      {@JsonKey(name: 'floor_no') int? floorNo,
      @JsonKey(name: 'floor_name') String? floorName,
      @JsonKey(name: 'floor_gb') String? floorGb,
      double? area,
      String? purpose,
      @JsonKey(name: 'etc_purpose') String? etcPurpose,
      String? structure});
}

/// @nodoc
class _$FloorInfoCopyWithImpl<$Res, $Val extends FloorInfo>
    implements $FloorInfoCopyWith<$Res> {
  _$FloorInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? floorNo = freezed,
    Object? floorName = freezed,
    Object? floorGb = freezed,
    Object? area = freezed,
    Object? purpose = freezed,
    Object? etcPurpose = freezed,
    Object? structure = freezed,
  }) {
    return _then(_value.copyWith(
      floorNo: freezed == floorNo
          ? _value.floorNo
          : floorNo // ignore: cast_nullable_to_non_nullable
              as int?,
      floorName: freezed == floorName
          ? _value.floorName
          : floorName // ignore: cast_nullable_to_non_nullable
              as String?,
      floorGb: freezed == floorGb
          ? _value.floorGb
          : floorGb // ignore: cast_nullable_to_non_nullable
              as String?,
      area: freezed == area
          ? _value.area
          : area // ignore: cast_nullable_to_non_nullable
              as double?,
      purpose: freezed == purpose
          ? _value.purpose
          : purpose // ignore: cast_nullable_to_non_nullable
              as String?,
      etcPurpose: freezed == etcPurpose
          ? _value.etcPurpose
          : etcPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      structure: freezed == structure
          ? _value.structure
          : structure // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$FloorInfoImplCopyWith<$Res>
    implements $FloorInfoCopyWith<$Res> {
  factory _$$FloorInfoImplCopyWith(
          _$FloorInfoImpl value, $Res Function(_$FloorInfoImpl) then) =
      __$$FloorInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'floor_no') int? floorNo,
      @JsonKey(name: 'floor_name') String? floorName,
      @JsonKey(name: 'floor_gb') String? floorGb,
      double? area,
      String? purpose,
      @JsonKey(name: 'etc_purpose') String? etcPurpose,
      String? structure});
}

/// @nodoc
class __$$FloorInfoImplCopyWithImpl<$Res>
    extends _$FloorInfoCopyWithImpl<$Res, _$FloorInfoImpl>
    implements _$$FloorInfoImplCopyWith<$Res> {
  __$$FloorInfoImplCopyWithImpl(
      _$FloorInfoImpl _value, $Res Function(_$FloorInfoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? floorNo = freezed,
    Object? floorName = freezed,
    Object? floorGb = freezed,
    Object? area = freezed,
    Object? purpose = freezed,
    Object? etcPurpose = freezed,
    Object? structure = freezed,
  }) {
    return _then(_$FloorInfoImpl(
      floorNo: freezed == floorNo
          ? _value.floorNo
          : floorNo // ignore: cast_nullable_to_non_nullable
              as int?,
      floorName: freezed == floorName
          ? _value.floorName
          : floorName // ignore: cast_nullable_to_non_nullable
              as String?,
      floorGb: freezed == floorGb
          ? _value.floorGb
          : floorGb // ignore: cast_nullable_to_non_nullable
              as String?,
      area: freezed == area
          ? _value.area
          : area // ignore: cast_nullable_to_non_nullable
              as double?,
      purpose: freezed == purpose
          ? _value.purpose
          : purpose // ignore: cast_nullable_to_non_nullable
              as String?,
      etcPurpose: freezed == etcPurpose
          ? _value.etcPurpose
          : etcPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      structure: freezed == structure
          ? _value.structure
          : structure // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$FloorInfoImpl implements _FloorInfo {
  const _$FloorInfoImpl(
      {@JsonKey(name: 'floor_no') this.floorNo,
      @JsonKey(name: 'floor_name') this.floorName,
      @JsonKey(name: 'floor_gb') this.floorGb,
      this.area,
      this.purpose,
      @JsonKey(name: 'etc_purpose') this.etcPurpose,
      this.structure});

  factory _$FloorInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$FloorInfoImplFromJson(json);

  @override
  @JsonKey(name: 'floor_no')
  final int? floorNo;
  @override
  @JsonKey(name: 'floor_name')
  final String? floorName;
  @override
  @JsonKey(name: 'floor_gb')
  final String? floorGb;
  @override
  final double? area;
  @override
  final String? purpose;
  @override
  @JsonKey(name: 'etc_purpose')
  final String? etcPurpose;
  @override
  final String? structure;

  @override
  String toString() {
    return 'FloorInfo(floorNo: $floorNo, floorName: $floorName, floorGb: $floorGb, area: $area, purpose: $purpose, etcPurpose: $etcPurpose, structure: $structure)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$FloorInfoImpl &&
            (identical(other.floorNo, floorNo) || other.floorNo == floorNo) &&
            (identical(other.floorName, floorName) ||
                other.floorName == floorName) &&
            (identical(other.floorGb, floorGb) || other.floorGb == floorGb) &&
            (identical(other.area, area) || other.area == area) &&
            (identical(other.purpose, purpose) || other.purpose == purpose) &&
            (identical(other.etcPurpose, etcPurpose) ||
                other.etcPurpose == etcPurpose) &&
            (identical(other.structure, structure) ||
                other.structure == structure));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, floorNo, floorName, floorGb,
      area, purpose, etcPurpose, structure);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$FloorInfoImplCopyWith<_$FloorInfoImpl> get copyWith =>
      __$$FloorInfoImplCopyWithImpl<_$FloorInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$FloorInfoImplToJson(
      this,
    );
  }
}

abstract class _FloorInfo implements FloorInfo {
  const factory _FloorInfo(
      {@JsonKey(name: 'floor_no') final int? floorNo,
      @JsonKey(name: 'floor_name') final String? floorName,
      @JsonKey(name: 'floor_gb') final String? floorGb,
      final double? area,
      final String? purpose,
      @JsonKey(name: 'etc_purpose') final String? etcPurpose,
      final String? structure}) = _$FloorInfoImpl;

  factory _FloorInfo.fromJson(Map<String, dynamic> json) =
      _$FloorInfoImpl.fromJson;

  @override
  @JsonKey(name: 'floor_no')
  int? get floorNo;
  @override
  @JsonKey(name: 'floor_name')
  String? get floorName;
  @override
  @JsonKey(name: 'floor_gb')
  String? get floorGb;
  @override
  double? get area;
  @override
  String? get purpose;
  @override
  @JsonKey(name: 'etc_purpose')
  String? get etcPurpose;
  @override
  String? get structure;
  @override
  @JsonKey(ignore: true)
  _$$FloorInfoImplCopyWith<_$FloorInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BuildingInfo _$BuildingInfoFromJson(Map<String, dynamic> json) {
  return _BuildingInfo.fromJson(json);
}

/// @nodoc
mixin _$BuildingInfo {
  @JsonKey(name: 'has_data')
  bool get hasData => throw _privateConstructorUsedError;
  String? get type => throw _privateConstructorUsedError;
  @JsonKey(name: 'building_info')
  BuildingBasicInfo? get buildingInfo => throw _privateConstructorUsedError;
  @JsonKey(name: 'recap_title_info')
  Map<String, dynamic>? get recapTitleInfo =>
      throw _privateConstructorUsedError;
  @JsonKey(name: 'dong_ho_dict')
  Map<String, dynamic>? get dongHoDict => throw _privateConstructorUsedError;
  @JsonKey(name: 'floor_info')
  List<FloorInfo>? get floorInfo => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BuildingInfoCopyWith<BuildingInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BuildingInfoCopyWith<$Res> {
  factory $BuildingInfoCopyWith(
          BuildingInfo value, $Res Function(BuildingInfo) then) =
      _$BuildingInfoCopyWithImpl<$Res, BuildingInfo>;
  @useResult
  $Res call(
      {@JsonKey(name: 'has_data') bool hasData,
      String? type,
      @JsonKey(name: 'building_info') BuildingBasicInfo? buildingInfo,
      @JsonKey(name: 'recap_title_info') Map<String, dynamic>? recapTitleInfo,
      @JsonKey(name: 'dong_ho_dict') Map<String, dynamic>? dongHoDict,
      @JsonKey(name: 'floor_info') List<FloorInfo>? floorInfo});

  $BuildingBasicInfoCopyWith<$Res>? get buildingInfo;
}

/// @nodoc
class _$BuildingInfoCopyWithImpl<$Res, $Val extends BuildingInfo>
    implements $BuildingInfoCopyWith<$Res> {
  _$BuildingInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? hasData = null,
    Object? type = freezed,
    Object? buildingInfo = freezed,
    Object? recapTitleInfo = freezed,
    Object? dongHoDict = freezed,
    Object? floorInfo = freezed,
  }) {
    return _then(_value.copyWith(
      hasData: null == hasData
          ? _value.hasData
          : hasData // ignore: cast_nullable_to_non_nullable
              as bool,
      type: freezed == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingInfo: freezed == buildingInfo
          ? _value.buildingInfo
          : buildingInfo // ignore: cast_nullable_to_non_nullable
              as BuildingBasicInfo?,
      recapTitleInfo: freezed == recapTitleInfo
          ? _value.recapTitleInfo
          : recapTitleInfo // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      dongHoDict: freezed == dongHoDict
          ? _value.dongHoDict
          : dongHoDict // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      floorInfo: freezed == floorInfo
          ? _value.floorInfo
          : floorInfo // ignore: cast_nullable_to_non_nullable
              as List<FloorInfo>?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $BuildingBasicInfoCopyWith<$Res>? get buildingInfo {
    if (_value.buildingInfo == null) {
      return null;
    }

    return $BuildingBasicInfoCopyWith<$Res>(_value.buildingInfo!, (value) {
      return _then(_value.copyWith(buildingInfo: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$BuildingInfoImplCopyWith<$Res>
    implements $BuildingInfoCopyWith<$Res> {
  factory _$$BuildingInfoImplCopyWith(
          _$BuildingInfoImpl value, $Res Function(_$BuildingInfoImpl) then) =
      __$$BuildingInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'has_data') bool hasData,
      String? type,
      @JsonKey(name: 'building_info') BuildingBasicInfo? buildingInfo,
      @JsonKey(name: 'recap_title_info') Map<String, dynamic>? recapTitleInfo,
      @JsonKey(name: 'dong_ho_dict') Map<String, dynamic>? dongHoDict,
      @JsonKey(name: 'floor_info') List<FloorInfo>? floorInfo});

  @override
  $BuildingBasicInfoCopyWith<$Res>? get buildingInfo;
}

/// @nodoc
class __$$BuildingInfoImplCopyWithImpl<$Res>
    extends _$BuildingInfoCopyWithImpl<$Res, _$BuildingInfoImpl>
    implements _$$BuildingInfoImplCopyWith<$Res> {
  __$$BuildingInfoImplCopyWithImpl(
      _$BuildingInfoImpl _value, $Res Function(_$BuildingInfoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? hasData = null,
    Object? type = freezed,
    Object? buildingInfo = freezed,
    Object? recapTitleInfo = freezed,
    Object? dongHoDict = freezed,
    Object? floorInfo = freezed,
  }) {
    return _then(_$BuildingInfoImpl(
      hasData: null == hasData
          ? _value.hasData
          : hasData // ignore: cast_nullable_to_non_nullable
              as bool,
      type: freezed == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingInfo: freezed == buildingInfo
          ? _value.buildingInfo
          : buildingInfo // ignore: cast_nullable_to_non_nullable
              as BuildingBasicInfo?,
      recapTitleInfo: freezed == recapTitleInfo
          ? _value._recapTitleInfo
          : recapTitleInfo // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      dongHoDict: freezed == dongHoDict
          ? _value._dongHoDict
          : dongHoDict // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      floorInfo: freezed == floorInfo
          ? _value._floorInfo
          : floorInfo // ignore: cast_nullable_to_non_nullable
              as List<FloorInfo>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BuildingInfoImpl implements _BuildingInfo {
  const _$BuildingInfoImpl(
      {@JsonKey(name: 'has_data') this.hasData = false,
      this.type,
      @JsonKey(name: 'building_info') this.buildingInfo,
      @JsonKey(name: 'recap_title_info')
      final Map<String, dynamic>? recapTitleInfo,
      @JsonKey(name: 'dong_ho_dict') final Map<String, dynamic>? dongHoDict,
      @JsonKey(name: 'floor_info') final List<FloorInfo>? floorInfo})
      : _recapTitleInfo = recapTitleInfo,
        _dongHoDict = dongHoDict,
        _floorInfo = floorInfo;

  factory _$BuildingInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$BuildingInfoImplFromJson(json);

  @override
  @JsonKey(name: 'has_data')
  final bool hasData;
  @override
  final String? type;
  @override
  @JsonKey(name: 'building_info')
  final BuildingBasicInfo? buildingInfo;
  final Map<String, dynamic>? _recapTitleInfo;
  @override
  @JsonKey(name: 'recap_title_info')
  Map<String, dynamic>? get recapTitleInfo {
    final value = _recapTitleInfo;
    if (value == null) return null;
    if (_recapTitleInfo is EqualUnmodifiableMapView) return _recapTitleInfo;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  final Map<String, dynamic>? _dongHoDict;
  @override
  @JsonKey(name: 'dong_ho_dict')
  Map<String, dynamic>? get dongHoDict {
    final value = _dongHoDict;
    if (value == null) return null;
    if (_dongHoDict is EqualUnmodifiableMapView) return _dongHoDict;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  final List<FloorInfo>? _floorInfo;
  @override
  @JsonKey(name: 'floor_info')
  List<FloorInfo>? get floorInfo {
    final value = _floorInfo;
    if (value == null) return null;
    if (_floorInfo is EqualUnmodifiableListView) return _floorInfo;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  String toString() {
    return 'BuildingInfo(hasData: $hasData, type: $type, buildingInfo: $buildingInfo, recapTitleInfo: $recapTitleInfo, dongHoDict: $dongHoDict, floorInfo: $floorInfo)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BuildingInfoImpl &&
            (identical(other.hasData, hasData) || other.hasData == hasData) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.buildingInfo, buildingInfo) ||
                other.buildingInfo == buildingInfo) &&
            const DeepCollectionEquality()
                .equals(other._recapTitleInfo, _recapTitleInfo) &&
            const DeepCollectionEquality()
                .equals(other._dongHoDict, _dongHoDict) &&
            const DeepCollectionEquality()
                .equals(other._floorInfo, _floorInfo));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      hasData,
      type,
      buildingInfo,
      const DeepCollectionEquality().hash(_recapTitleInfo),
      const DeepCollectionEquality().hash(_dongHoDict),
      const DeepCollectionEquality().hash(_floorInfo));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BuildingInfoImplCopyWith<_$BuildingInfoImpl> get copyWith =>
      __$$BuildingInfoImplCopyWithImpl<_$BuildingInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BuildingInfoImplToJson(
      this,
    );
  }
}

abstract class _BuildingInfo implements BuildingInfo {
  const factory _BuildingInfo(
          {@JsonKey(name: 'has_data') final bool hasData,
          final String? type,
          @JsonKey(name: 'building_info') final BuildingBasicInfo? buildingInfo,
          @JsonKey(name: 'recap_title_info')
          final Map<String, dynamic>? recapTitleInfo,
          @JsonKey(name: 'dong_ho_dict') final Map<String, dynamic>? dongHoDict,
          @JsonKey(name: 'floor_info') final List<FloorInfo>? floorInfo}) =
      _$BuildingInfoImpl;

  factory _BuildingInfo.fromJson(Map<String, dynamic> json) =
      _$BuildingInfoImpl.fromJson;

  @override
  @JsonKey(name: 'has_data')
  bool get hasData;
  @override
  String? get type;
  @override
  @JsonKey(name: 'building_info')
  BuildingBasicInfo? get buildingInfo;
  @override
  @JsonKey(name: 'recap_title_info')
  Map<String, dynamic>? get recapTitleInfo;
  @override
  @JsonKey(name: 'dong_ho_dict')
  Map<String, dynamic>? get dongHoDict;
  @override
  @JsonKey(name: 'floor_info')
  List<FloorInfo>? get floorInfo;
  @override
  @JsonKey(ignore: true)
  _$$BuildingInfoImplCopyWith<_$BuildingInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

LandInfo _$LandInfoFromJson(Map<String, dynamic> json) {
  return _LandInfo.fromJson(json);
}

/// @nodoc
mixin _$LandInfo {
  @JsonKey(name: 'land_area')
  double? get landArea => throw _privateConstructorUsedError;
  @JsonKey(name: 'parcel_count')
  int? get parcelCount => throw _privateConstructorUsedError;
  @JsonKey(name: 'land_category')
  String? get landCategory => throw _privateConstructorUsedError;
  @JsonKey(name: 'land_category_name')
  String? get landCategoryName => throw _privateConstructorUsedError;
  @JsonKey(name: 'public_land_price')
  int? get publicLandPrice => throw _privateConstructorUsedError;
  @JsonKey(name: 'price_year')
  String? get priceYear => throw _privateConstructorUsedError;
  @JsonKey(name: 'zone_classification')
  String? get zoneClassification => throw _privateConstructorUsedError;
  @JsonKey(name: 'land_use_situation_name')
  String? get landUseSituationName => throw _privateConstructorUsedError;
  @JsonKey(name: 'topography_height_name')
  String? get topographyHeightName => throw _privateConstructorUsedError;
  @JsonKey(name: 'topography_form_name')
  String? get topographyFormName => throw _privateConstructorUsedError;
  @JsonKey(name: 'road_side_name')
  String? get roadSideName => throw _privateConstructorUsedError;
  List<Map<String, dynamic>>? get details => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $LandInfoCopyWith<LandInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LandInfoCopyWith<$Res> {
  factory $LandInfoCopyWith(LandInfo value, $Res Function(LandInfo) then) =
      _$LandInfoCopyWithImpl<$Res, LandInfo>;
  @useResult
  $Res call(
      {@JsonKey(name: 'land_area') double? landArea,
      @JsonKey(name: 'parcel_count') int? parcelCount,
      @JsonKey(name: 'land_category') String? landCategory,
      @JsonKey(name: 'land_category_name') String? landCategoryName,
      @JsonKey(name: 'public_land_price') int? publicLandPrice,
      @JsonKey(name: 'price_year') String? priceYear,
      @JsonKey(name: 'zone_classification') String? zoneClassification,
      @JsonKey(name: 'land_use_situation_name') String? landUseSituationName,
      @JsonKey(name: 'topography_height_name') String? topographyHeightName,
      @JsonKey(name: 'topography_form_name') String? topographyFormName,
      @JsonKey(name: 'road_side_name') String? roadSideName,
      List<Map<String, dynamic>>? details});
}

/// @nodoc
class _$LandInfoCopyWithImpl<$Res, $Val extends LandInfo>
    implements $LandInfoCopyWith<$Res> {
  _$LandInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? landArea = freezed,
    Object? parcelCount = freezed,
    Object? landCategory = freezed,
    Object? landCategoryName = freezed,
    Object? publicLandPrice = freezed,
    Object? priceYear = freezed,
    Object? zoneClassification = freezed,
    Object? landUseSituationName = freezed,
    Object? topographyHeightName = freezed,
    Object? topographyFormName = freezed,
    Object? roadSideName = freezed,
    Object? details = freezed,
  }) {
    return _then(_value.copyWith(
      landArea: freezed == landArea
          ? _value.landArea
          : landArea // ignore: cast_nullable_to_non_nullable
              as double?,
      parcelCount: freezed == parcelCount
          ? _value.parcelCount
          : parcelCount // ignore: cast_nullable_to_non_nullable
              as int?,
      landCategory: freezed == landCategory
          ? _value.landCategory
          : landCategory // ignore: cast_nullable_to_non_nullable
              as String?,
      landCategoryName: freezed == landCategoryName
          ? _value.landCategoryName
          : landCategoryName // ignore: cast_nullable_to_non_nullable
              as String?,
      publicLandPrice: freezed == publicLandPrice
          ? _value.publicLandPrice
          : publicLandPrice // ignore: cast_nullable_to_non_nullable
              as int?,
      priceYear: freezed == priceYear
          ? _value.priceYear
          : priceYear // ignore: cast_nullable_to_non_nullable
              as String?,
      zoneClassification: freezed == zoneClassification
          ? _value.zoneClassification
          : zoneClassification // ignore: cast_nullable_to_non_nullable
              as String?,
      landUseSituationName: freezed == landUseSituationName
          ? _value.landUseSituationName
          : landUseSituationName // ignore: cast_nullable_to_non_nullable
              as String?,
      topographyHeightName: freezed == topographyHeightName
          ? _value.topographyHeightName
          : topographyHeightName // ignore: cast_nullable_to_non_nullable
              as String?,
      topographyFormName: freezed == topographyFormName
          ? _value.topographyFormName
          : topographyFormName // ignore: cast_nullable_to_non_nullable
              as String?,
      roadSideName: freezed == roadSideName
          ? _value.roadSideName
          : roadSideName // ignore: cast_nullable_to_non_nullable
              as String?,
      details: freezed == details
          ? _value.details
          : details // ignore: cast_nullable_to_non_nullable
              as List<Map<String, dynamic>>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$LandInfoImplCopyWith<$Res>
    implements $LandInfoCopyWith<$Res> {
  factory _$$LandInfoImplCopyWith(
          _$LandInfoImpl value, $Res Function(_$LandInfoImpl) then) =
      __$$LandInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'land_area') double? landArea,
      @JsonKey(name: 'parcel_count') int? parcelCount,
      @JsonKey(name: 'land_category') String? landCategory,
      @JsonKey(name: 'land_category_name') String? landCategoryName,
      @JsonKey(name: 'public_land_price') int? publicLandPrice,
      @JsonKey(name: 'price_year') String? priceYear,
      @JsonKey(name: 'zone_classification') String? zoneClassification,
      @JsonKey(name: 'land_use_situation_name') String? landUseSituationName,
      @JsonKey(name: 'topography_height_name') String? topographyHeightName,
      @JsonKey(name: 'topography_form_name') String? topographyFormName,
      @JsonKey(name: 'road_side_name') String? roadSideName,
      List<Map<String, dynamic>>? details});
}

/// @nodoc
class __$$LandInfoImplCopyWithImpl<$Res>
    extends _$LandInfoCopyWithImpl<$Res, _$LandInfoImpl>
    implements _$$LandInfoImplCopyWith<$Res> {
  __$$LandInfoImplCopyWithImpl(
      _$LandInfoImpl _value, $Res Function(_$LandInfoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? landArea = freezed,
    Object? parcelCount = freezed,
    Object? landCategory = freezed,
    Object? landCategoryName = freezed,
    Object? publicLandPrice = freezed,
    Object? priceYear = freezed,
    Object? zoneClassification = freezed,
    Object? landUseSituationName = freezed,
    Object? topographyHeightName = freezed,
    Object? topographyFormName = freezed,
    Object? roadSideName = freezed,
    Object? details = freezed,
  }) {
    return _then(_$LandInfoImpl(
      landArea: freezed == landArea
          ? _value.landArea
          : landArea // ignore: cast_nullable_to_non_nullable
              as double?,
      parcelCount: freezed == parcelCount
          ? _value.parcelCount
          : parcelCount // ignore: cast_nullable_to_non_nullable
              as int?,
      landCategory: freezed == landCategory
          ? _value.landCategory
          : landCategory // ignore: cast_nullable_to_non_nullable
              as String?,
      landCategoryName: freezed == landCategoryName
          ? _value.landCategoryName
          : landCategoryName // ignore: cast_nullable_to_non_nullable
              as String?,
      publicLandPrice: freezed == publicLandPrice
          ? _value.publicLandPrice
          : publicLandPrice // ignore: cast_nullable_to_non_nullable
              as int?,
      priceYear: freezed == priceYear
          ? _value.priceYear
          : priceYear // ignore: cast_nullable_to_non_nullable
              as String?,
      zoneClassification: freezed == zoneClassification
          ? _value.zoneClassification
          : zoneClassification // ignore: cast_nullable_to_non_nullable
              as String?,
      landUseSituationName: freezed == landUseSituationName
          ? _value.landUseSituationName
          : landUseSituationName // ignore: cast_nullable_to_non_nullable
              as String?,
      topographyHeightName: freezed == topographyHeightName
          ? _value.topographyHeightName
          : topographyHeightName // ignore: cast_nullable_to_non_nullable
              as String?,
      topographyFormName: freezed == topographyFormName
          ? _value.topographyFormName
          : topographyFormName // ignore: cast_nullable_to_non_nullable
              as String?,
      roadSideName: freezed == roadSideName
          ? _value.roadSideName
          : roadSideName // ignore: cast_nullable_to_non_nullable
              as String?,
      details: freezed == details
          ? _value._details
          : details // ignore: cast_nullable_to_non_nullable
              as List<Map<String, dynamic>>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$LandInfoImpl implements _LandInfo {
  const _$LandInfoImpl(
      {@JsonKey(name: 'land_area') this.landArea,
      @JsonKey(name: 'parcel_count') this.parcelCount,
      @JsonKey(name: 'land_category') this.landCategory,
      @JsonKey(name: 'land_category_name') this.landCategoryName,
      @JsonKey(name: 'public_land_price') this.publicLandPrice,
      @JsonKey(name: 'price_year') this.priceYear,
      @JsonKey(name: 'zone_classification') this.zoneClassification,
      @JsonKey(name: 'land_use_situation_name') this.landUseSituationName,
      @JsonKey(name: 'topography_height_name') this.topographyHeightName,
      @JsonKey(name: 'topography_form_name') this.topographyFormName,
      @JsonKey(name: 'road_side_name') this.roadSideName,
      final List<Map<String, dynamic>>? details})
      : _details = details;

  factory _$LandInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$LandInfoImplFromJson(json);

  @override
  @JsonKey(name: 'land_area')
  final double? landArea;
  @override
  @JsonKey(name: 'parcel_count')
  final int? parcelCount;
  @override
  @JsonKey(name: 'land_category')
  final String? landCategory;
  @override
  @JsonKey(name: 'land_category_name')
  final String? landCategoryName;
  @override
  @JsonKey(name: 'public_land_price')
  final int? publicLandPrice;
  @override
  @JsonKey(name: 'price_year')
  final String? priceYear;
  @override
  @JsonKey(name: 'zone_classification')
  final String? zoneClassification;
  @override
  @JsonKey(name: 'land_use_situation_name')
  final String? landUseSituationName;
  @override
  @JsonKey(name: 'topography_height_name')
  final String? topographyHeightName;
  @override
  @JsonKey(name: 'topography_form_name')
  final String? topographyFormName;
  @override
  @JsonKey(name: 'road_side_name')
  final String? roadSideName;
  final List<Map<String, dynamic>>? _details;
  @override
  List<Map<String, dynamic>>? get details {
    final value = _details;
    if (value == null) return null;
    if (_details is EqualUnmodifiableListView) return _details;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  String toString() {
    return 'LandInfo(landArea: $landArea, parcelCount: $parcelCount, landCategory: $landCategory, landCategoryName: $landCategoryName, publicLandPrice: $publicLandPrice, priceYear: $priceYear, zoneClassification: $zoneClassification, landUseSituationName: $landUseSituationName, topographyHeightName: $topographyHeightName, topographyFormName: $topographyFormName, roadSideName: $roadSideName, details: $details)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LandInfoImpl &&
            (identical(other.landArea, landArea) ||
                other.landArea == landArea) &&
            (identical(other.parcelCount, parcelCount) ||
                other.parcelCount == parcelCount) &&
            (identical(other.landCategory, landCategory) ||
                other.landCategory == landCategory) &&
            (identical(other.landCategoryName, landCategoryName) ||
                other.landCategoryName == landCategoryName) &&
            (identical(other.publicLandPrice, publicLandPrice) ||
                other.publicLandPrice == publicLandPrice) &&
            (identical(other.priceYear, priceYear) ||
                other.priceYear == priceYear) &&
            (identical(other.zoneClassification, zoneClassification) ||
                other.zoneClassification == zoneClassification) &&
            (identical(other.landUseSituationName, landUseSituationName) ||
                other.landUseSituationName == landUseSituationName) &&
            (identical(other.topographyHeightName, topographyHeightName) ||
                other.topographyHeightName == topographyHeightName) &&
            (identical(other.topographyFormName, topographyFormName) ||
                other.topographyFormName == topographyFormName) &&
            (identical(other.roadSideName, roadSideName) ||
                other.roadSideName == roadSideName) &&
            const DeepCollectionEquality().equals(other._details, _details));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      landArea,
      parcelCount,
      landCategory,
      landCategoryName,
      publicLandPrice,
      priceYear,
      zoneClassification,
      landUseSituationName,
      topographyHeightName,
      topographyFormName,
      roadSideName,
      const DeepCollectionEquality().hash(_details));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$LandInfoImplCopyWith<_$LandInfoImpl> get copyWith =>
      __$$LandInfoImplCopyWithImpl<_$LandInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$LandInfoImplToJson(
      this,
    );
  }
}

abstract class _LandInfo implements LandInfo {
  const factory _LandInfo(
      {@JsonKey(name: 'land_area') final double? landArea,
      @JsonKey(name: 'parcel_count') final int? parcelCount,
      @JsonKey(name: 'land_category') final String? landCategory,
      @JsonKey(name: 'land_category_name') final String? landCategoryName,
      @JsonKey(name: 'public_land_price') final int? publicLandPrice,
      @JsonKey(name: 'price_year') final String? priceYear,
      @JsonKey(name: 'zone_classification') final String? zoneClassification,
      @JsonKey(name: 'land_use_situation_name')
      final String? landUseSituationName,
      @JsonKey(name: 'topography_height_name')
      final String? topographyHeightName,
      @JsonKey(name: 'topography_form_name') final String? topographyFormName,
      @JsonKey(name: 'road_side_name') final String? roadSideName,
      final List<Map<String, dynamic>>? details}) = _$LandInfoImpl;

  factory _LandInfo.fromJson(Map<String, dynamic> json) =
      _$LandInfoImpl.fromJson;

  @override
  @JsonKey(name: 'land_area')
  double? get landArea;
  @override
  @JsonKey(name: 'parcel_count')
  int? get parcelCount;
  @override
  @JsonKey(name: 'land_category')
  String? get landCategory;
  @override
  @JsonKey(name: 'land_category_name')
  String? get landCategoryName;
  @override
  @JsonKey(name: 'public_land_price')
  int? get publicLandPrice;
  @override
  @JsonKey(name: 'price_year')
  String? get priceYear;
  @override
  @JsonKey(name: 'zone_classification')
  String? get zoneClassification;
  @override
  @JsonKey(name: 'land_use_situation_name')
  String? get landUseSituationName;
  @override
  @JsonKey(name: 'topography_height_name')
  String? get topographyHeightName;
  @override
  @JsonKey(name: 'topography_form_name')
  String? get topographyFormName;
  @override
  @JsonKey(name: 'road_side_name')
  String? get roadSideName;
  @override
  List<Map<String, dynamic>>? get details;
  @override
  @JsonKey(ignore: true)
  _$$LandInfoImplCopyWith<_$LandInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BuildingSearchResponse _$BuildingSearchResponseFromJson(
    Map<String, dynamic> json) {
  return _BuildingSearchResponse.fromJson(json);
}

/// @nodoc
mixin _$BuildingSearchResponse {
  bool get success => throw _privateConstructorUsedError;
  CodeInfo? get codes => throw _privateConstructorUsedError;
  AddressInfo? get address => throw _privateConstructorUsedError;
  BuildingInfo? get building => throw _privateConstructorUsedError;
  LandInfo? get land => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BuildingSearchResponseCopyWith<BuildingSearchResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BuildingSearchResponseCopyWith<$Res> {
  factory $BuildingSearchResponseCopyWith(BuildingSearchResponse value,
          $Res Function(BuildingSearchResponse) then) =
      _$BuildingSearchResponseCopyWithImpl<$Res, BuildingSearchResponse>;
  @useResult
  $Res call(
      {bool success,
      CodeInfo? codes,
      AddressInfo? address,
      BuildingInfo? building,
      LandInfo? land,
      String? error});

  $CodeInfoCopyWith<$Res>? get codes;
  $AddressInfoCopyWith<$Res>? get address;
  $BuildingInfoCopyWith<$Res>? get building;
  $LandInfoCopyWith<$Res>? get land;
}

/// @nodoc
class _$BuildingSearchResponseCopyWithImpl<$Res,
        $Val extends BuildingSearchResponse>
    implements $BuildingSearchResponseCopyWith<$Res> {
  _$BuildingSearchResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? codes = freezed,
    Object? address = freezed,
    Object? building = freezed,
    Object? land = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      codes: freezed == codes
          ? _value.codes
          : codes // ignore: cast_nullable_to_non_nullable
              as CodeInfo?,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as AddressInfo?,
      building: freezed == building
          ? _value.building
          : building // ignore: cast_nullable_to_non_nullable
              as BuildingInfo?,
      land: freezed == land
          ? _value.land
          : land // ignore: cast_nullable_to_non_nullable
              as LandInfo?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $CodeInfoCopyWith<$Res>? get codes {
    if (_value.codes == null) {
      return null;
    }

    return $CodeInfoCopyWith<$Res>(_value.codes!, (value) {
      return _then(_value.copyWith(codes: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $AddressInfoCopyWith<$Res>? get address {
    if (_value.address == null) {
      return null;
    }

    return $AddressInfoCopyWith<$Res>(_value.address!, (value) {
      return _then(_value.copyWith(address: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $BuildingInfoCopyWith<$Res>? get building {
    if (_value.building == null) {
      return null;
    }

    return $BuildingInfoCopyWith<$Res>(_value.building!, (value) {
      return _then(_value.copyWith(building: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $LandInfoCopyWith<$Res>? get land {
    if (_value.land == null) {
      return null;
    }

    return $LandInfoCopyWith<$Res>(_value.land!, (value) {
      return _then(_value.copyWith(land: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$BuildingSearchResponseImplCopyWith<$Res>
    implements $BuildingSearchResponseCopyWith<$Res> {
  factory _$$BuildingSearchResponseImplCopyWith(
          _$BuildingSearchResponseImpl value,
          $Res Function(_$BuildingSearchResponseImpl) then) =
      __$$BuildingSearchResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool success,
      CodeInfo? codes,
      AddressInfo? address,
      BuildingInfo? building,
      LandInfo? land,
      String? error});

  @override
  $CodeInfoCopyWith<$Res>? get codes;
  @override
  $AddressInfoCopyWith<$Res>? get address;
  @override
  $BuildingInfoCopyWith<$Res>? get building;
  @override
  $LandInfoCopyWith<$Res>? get land;
}

/// @nodoc
class __$$BuildingSearchResponseImplCopyWithImpl<$Res>
    extends _$BuildingSearchResponseCopyWithImpl<$Res,
        _$BuildingSearchResponseImpl>
    implements _$$BuildingSearchResponseImplCopyWith<$Res> {
  __$$BuildingSearchResponseImplCopyWithImpl(
      _$BuildingSearchResponseImpl _value,
      $Res Function(_$BuildingSearchResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? codes = freezed,
    Object? address = freezed,
    Object? building = freezed,
    Object? land = freezed,
    Object? error = freezed,
  }) {
    return _then(_$BuildingSearchResponseImpl(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      codes: freezed == codes
          ? _value.codes
          : codes // ignore: cast_nullable_to_non_nullable
              as CodeInfo?,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as AddressInfo?,
      building: freezed == building
          ? _value.building
          : building // ignore: cast_nullable_to_non_nullable
              as BuildingInfo?,
      land: freezed == land
          ? _value.land
          : land // ignore: cast_nullable_to_non_nullable
              as LandInfo?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BuildingSearchResponseImpl implements _BuildingSearchResponse {
  const _$BuildingSearchResponseImpl(
      {required this.success,
      this.codes,
      this.address,
      this.building,
      this.land,
      this.error});

  factory _$BuildingSearchResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$BuildingSearchResponseImplFromJson(json);

  @override
  final bool success;
  @override
  final CodeInfo? codes;
  @override
  final AddressInfo? address;
  @override
  final BuildingInfo? building;
  @override
  final LandInfo? land;
  @override
  final String? error;

  @override
  String toString() {
    return 'BuildingSearchResponse(success: $success, codes: $codes, address: $address, building: $building, land: $land, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BuildingSearchResponseImpl &&
            (identical(other.success, success) || other.success == success) &&
            (identical(other.codes, codes) || other.codes == codes) &&
            (identical(other.address, address) || other.address == address) &&
            (identical(other.building, building) ||
                other.building == building) &&
            (identical(other.land, land) || other.land == land) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, success, codes, address, building, land, error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BuildingSearchResponseImplCopyWith<_$BuildingSearchResponseImpl>
      get copyWith => __$$BuildingSearchResponseImplCopyWithImpl<
          _$BuildingSearchResponseImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BuildingSearchResponseImplToJson(
      this,
    );
  }
}

abstract class _BuildingSearchResponse implements BuildingSearchResponse {
  const factory _BuildingSearchResponse(
      {required final bool success,
      final CodeInfo? codes,
      final AddressInfo? address,
      final BuildingInfo? building,
      final LandInfo? land,
      final String? error}) = _$BuildingSearchResponseImpl;

  factory _BuildingSearchResponse.fromJson(Map<String, dynamic> json) =
      _$BuildingSearchResponseImpl.fromJson;

  @override
  bool get success;
  @override
  CodeInfo? get codes;
  @override
  AddressInfo? get address;
  @override
  BuildingInfo? get building;
  @override
  LandInfo? get land;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$BuildingSearchResponseImplCopyWith<_$BuildingSearchResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}

BjdongSearchItem _$BjdongSearchItemFromJson(Map<String, dynamic> json) {
  return _BjdongSearchItem.fromJson(json);
}

/// @nodoc
mixin _$BjdongSearchItem {
  @JsonKey(name: 'bjdong_code')
  String get code => throw _privateConstructorUsedError;
  @JsonKey(name: 'full_address')
  String? get fullAddress => throw _privateConstructorUsedError;
  @JsonKey(name: 'sido_name')
  String? get sidoName => throw _privateConstructorUsedError;
  @JsonKey(name: 'sigungu_name')
  String? get sigunguName => throw _privateConstructorUsedError;
  @JsonKey(name: 'eupmyeondong_name')
  String? get eupmyeondongName => throw _privateConstructorUsedError;
  @JsonKey(name: 'ri_name')
  String? get riName => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BjdongSearchItemCopyWith<BjdongSearchItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BjdongSearchItemCopyWith<$Res> {
  factory $BjdongSearchItemCopyWith(
          BjdongSearchItem value, $Res Function(BjdongSearchItem) then) =
      _$BjdongSearchItemCopyWithImpl<$Res, BjdongSearchItem>;
  @useResult
  $Res call(
      {@JsonKey(name: 'bjdong_code') String code,
      @JsonKey(name: 'full_address') String? fullAddress,
      @JsonKey(name: 'sido_name') String? sidoName,
      @JsonKey(name: 'sigungu_name') String? sigunguName,
      @JsonKey(name: 'eupmyeondong_name') String? eupmyeondongName,
      @JsonKey(name: 'ri_name') String? riName});
}

/// @nodoc
class _$BjdongSearchItemCopyWithImpl<$Res, $Val extends BjdongSearchItem>
    implements $BjdongSearchItemCopyWith<$Res> {
  _$BjdongSearchItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? code = null,
    Object? fullAddress = freezed,
    Object? sidoName = freezed,
    Object? sigunguName = freezed,
    Object? eupmyeondongName = freezed,
    Object? riName = freezed,
  }) {
    return _then(_value.copyWith(
      code: null == code
          ? _value.code
          : code // ignore: cast_nullable_to_non_nullable
              as String,
      fullAddress: freezed == fullAddress
          ? _value.fullAddress
          : fullAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      sidoName: freezed == sidoName
          ? _value.sidoName
          : sidoName // ignore: cast_nullable_to_non_nullable
              as String?,
      sigunguName: freezed == sigunguName
          ? _value.sigunguName
          : sigunguName // ignore: cast_nullable_to_non_nullable
              as String?,
      eupmyeondongName: freezed == eupmyeondongName
          ? _value.eupmyeondongName
          : eupmyeondongName // ignore: cast_nullable_to_non_nullable
              as String?,
      riName: freezed == riName
          ? _value.riName
          : riName // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BjdongSearchItemImplCopyWith<$Res>
    implements $BjdongSearchItemCopyWith<$Res> {
  factory _$$BjdongSearchItemImplCopyWith(_$BjdongSearchItemImpl value,
          $Res Function(_$BjdongSearchItemImpl) then) =
      __$$BjdongSearchItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'bjdong_code') String code,
      @JsonKey(name: 'full_address') String? fullAddress,
      @JsonKey(name: 'sido_name') String? sidoName,
      @JsonKey(name: 'sigungu_name') String? sigunguName,
      @JsonKey(name: 'eupmyeondong_name') String? eupmyeondongName,
      @JsonKey(name: 'ri_name') String? riName});
}

/// @nodoc
class __$$BjdongSearchItemImplCopyWithImpl<$Res>
    extends _$BjdongSearchItemCopyWithImpl<$Res, _$BjdongSearchItemImpl>
    implements _$$BjdongSearchItemImplCopyWith<$Res> {
  __$$BjdongSearchItemImplCopyWithImpl(_$BjdongSearchItemImpl _value,
      $Res Function(_$BjdongSearchItemImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? code = null,
    Object? fullAddress = freezed,
    Object? sidoName = freezed,
    Object? sigunguName = freezed,
    Object? eupmyeondongName = freezed,
    Object? riName = freezed,
  }) {
    return _then(_$BjdongSearchItemImpl(
      code: null == code
          ? _value.code
          : code // ignore: cast_nullable_to_non_nullable
              as String,
      fullAddress: freezed == fullAddress
          ? _value.fullAddress
          : fullAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      sidoName: freezed == sidoName
          ? _value.sidoName
          : sidoName // ignore: cast_nullable_to_non_nullable
              as String?,
      sigunguName: freezed == sigunguName
          ? _value.sigunguName
          : sigunguName // ignore: cast_nullable_to_non_nullable
              as String?,
      eupmyeondongName: freezed == eupmyeondongName
          ? _value.eupmyeondongName
          : eupmyeondongName // ignore: cast_nullable_to_non_nullable
              as String?,
      riName: freezed == riName
          ? _value.riName
          : riName // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BjdongSearchItemImpl implements _BjdongSearchItem {
  const _$BjdongSearchItemImpl(
      {@JsonKey(name: 'bjdong_code') required this.code,
      @JsonKey(name: 'full_address') this.fullAddress,
      @JsonKey(name: 'sido_name') this.sidoName,
      @JsonKey(name: 'sigungu_name') this.sigunguName,
      @JsonKey(name: 'eupmyeondong_name') this.eupmyeondongName,
      @JsonKey(name: 'ri_name') this.riName});

  factory _$BjdongSearchItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$BjdongSearchItemImplFromJson(json);

  @override
  @JsonKey(name: 'bjdong_code')
  final String code;
  @override
  @JsonKey(name: 'full_address')
  final String? fullAddress;
  @override
  @JsonKey(name: 'sido_name')
  final String? sidoName;
  @override
  @JsonKey(name: 'sigungu_name')
  final String? sigunguName;
  @override
  @JsonKey(name: 'eupmyeondong_name')
  final String? eupmyeondongName;
  @override
  @JsonKey(name: 'ri_name')
  final String? riName;

  @override
  String toString() {
    return 'BjdongSearchItem(code: $code, fullAddress: $fullAddress, sidoName: $sidoName, sigunguName: $sigunguName, eupmyeondongName: $eupmyeondongName, riName: $riName)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BjdongSearchItemImpl &&
            (identical(other.code, code) || other.code == code) &&
            (identical(other.fullAddress, fullAddress) ||
                other.fullAddress == fullAddress) &&
            (identical(other.sidoName, sidoName) ||
                other.sidoName == sidoName) &&
            (identical(other.sigunguName, sigunguName) ||
                other.sigunguName == sigunguName) &&
            (identical(other.eupmyeondongName, eupmyeondongName) ||
                other.eupmyeondongName == eupmyeondongName) &&
            (identical(other.riName, riName) || other.riName == riName));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, code, fullAddress, sidoName,
      sigunguName, eupmyeondongName, riName);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BjdongSearchItemImplCopyWith<_$BjdongSearchItemImpl> get copyWith =>
      __$$BjdongSearchItemImplCopyWithImpl<_$BjdongSearchItemImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BjdongSearchItemImplToJson(
      this,
    );
  }
}

abstract class _BjdongSearchItem implements BjdongSearchItem {
  const factory _BjdongSearchItem(
      {@JsonKey(name: 'bjdong_code') required final String code,
      @JsonKey(name: 'full_address') final String? fullAddress,
      @JsonKey(name: 'sido_name') final String? sidoName,
      @JsonKey(name: 'sigungu_name') final String? sigunguName,
      @JsonKey(name: 'eupmyeondong_name') final String? eupmyeondongName,
      @JsonKey(name: 'ri_name') final String? riName}) = _$BjdongSearchItemImpl;

  factory _BjdongSearchItem.fromJson(Map<String, dynamic> json) =
      _$BjdongSearchItemImpl.fromJson;

  @override
  @JsonKey(name: 'bjdong_code')
  String get code;
  @override
  @JsonKey(name: 'full_address')
  String? get fullAddress;
  @override
  @JsonKey(name: 'sido_name')
  String? get sidoName;
  @override
  @JsonKey(name: 'sigungu_name')
  String? get sigunguName;
  @override
  @JsonKey(name: 'eupmyeondong_name')
  String? get eupmyeondongName;
  @override
  @JsonKey(name: 'ri_name')
  String? get riName;
  @override
  @JsonKey(ignore: true)
  _$$BjdongSearchItemImplCopyWith<_$BjdongSearchItemImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BjdongSearchResponse _$BjdongSearchResponseFromJson(Map<String, dynamic> json) {
  return _BjdongSearchResponse.fromJson(json);
}

/// @nodoc
mixin _$BjdongSearchResponse {
  bool get success => throw _privateConstructorUsedError;
  int get count => throw _privateConstructorUsedError;
  List<BjdongSearchItem> get results => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BjdongSearchResponseCopyWith<BjdongSearchResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BjdongSearchResponseCopyWith<$Res> {
  factory $BjdongSearchResponseCopyWith(BjdongSearchResponse value,
          $Res Function(BjdongSearchResponse) then) =
      _$BjdongSearchResponseCopyWithImpl<$Res, BjdongSearchResponse>;
  @useResult
  $Res call(
      {bool success, int count, List<BjdongSearchItem> results, String? error});
}

/// @nodoc
class _$BjdongSearchResponseCopyWithImpl<$Res,
        $Val extends BjdongSearchResponse>
    implements $BjdongSearchResponseCopyWith<$Res> {
  _$BjdongSearchResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? count = null,
    Object? results = null,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      count: null == count
          ? _value.count
          : count // ignore: cast_nullable_to_non_nullable
              as int,
      results: null == results
          ? _value.results
          : results // ignore: cast_nullable_to_non_nullable
              as List<BjdongSearchItem>,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BjdongSearchResponseImplCopyWith<$Res>
    implements $BjdongSearchResponseCopyWith<$Res> {
  factory _$$BjdongSearchResponseImplCopyWith(_$BjdongSearchResponseImpl value,
          $Res Function(_$BjdongSearchResponseImpl) then) =
      __$$BjdongSearchResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool success, int count, List<BjdongSearchItem> results, String? error});
}

/// @nodoc
class __$$BjdongSearchResponseImplCopyWithImpl<$Res>
    extends _$BjdongSearchResponseCopyWithImpl<$Res, _$BjdongSearchResponseImpl>
    implements _$$BjdongSearchResponseImplCopyWith<$Res> {
  __$$BjdongSearchResponseImplCopyWithImpl(_$BjdongSearchResponseImpl _value,
      $Res Function(_$BjdongSearchResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? count = null,
    Object? results = null,
    Object? error = freezed,
  }) {
    return _then(_$BjdongSearchResponseImpl(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      count: null == count
          ? _value.count
          : count // ignore: cast_nullable_to_non_nullable
              as int,
      results: null == results
          ? _value._results
          : results // ignore: cast_nullable_to_non_nullable
              as List<BjdongSearchItem>,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BjdongSearchResponseImpl implements _BjdongSearchResponse {
  const _$BjdongSearchResponseImpl(
      {required this.success,
      this.count = 0,
      final List<BjdongSearchItem> results = const [],
      this.error})
      : _results = results;

  factory _$BjdongSearchResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$BjdongSearchResponseImplFromJson(json);

  @override
  final bool success;
  @override
  @JsonKey()
  final int count;
  final List<BjdongSearchItem> _results;
  @override
  @JsonKey()
  List<BjdongSearchItem> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  final String? error;

  @override
  String toString() {
    return 'BjdongSearchResponse(success: $success, count: $count, results: $results, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BjdongSearchResponseImpl &&
            (identical(other.success, success) || other.success == success) &&
            (identical(other.count, count) || other.count == count) &&
            const DeepCollectionEquality().equals(other._results, _results) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, success, count,
      const DeepCollectionEquality().hash(_results), error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BjdongSearchResponseImplCopyWith<_$BjdongSearchResponseImpl>
      get copyWith =>
          __$$BjdongSearchResponseImplCopyWithImpl<_$BjdongSearchResponseImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BjdongSearchResponseImplToJson(
      this,
    );
  }
}

abstract class _BjdongSearchResponse implements BjdongSearchResponse {
  const factory _BjdongSearchResponse(
      {required final bool success,
      final int count,
      final List<BjdongSearchItem> results,
      final String? error}) = _$BjdongSearchResponseImpl;

  factory _BjdongSearchResponse.fromJson(Map<String, dynamic> json) =
      _$BjdongSearchResponseImpl.fromJson;

  @override
  bool get success;
  @override
  int get count;
  @override
  List<BjdongSearchItem> get results;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$BjdongSearchResponseImplCopyWith<_$BjdongSearchResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}

AreaInfoRequest _$AreaInfoRequestFromJson(Map<String, dynamic> json) {
  return _AreaInfoRequest.fromJson(json);
}

/// @nodoc
mixin _$AreaInfoRequest {
  @JsonKey(name: 'bjdong_code')
  String get bjdongCode => throw _privateConstructorUsedError;
  String get bun => throw _privateConstructorUsedError;
  String get ji => throw _privateConstructorUsedError;
  @JsonKey(name: 'dong_nm')
  String get dongNm => throw _privateConstructorUsedError;
  @JsonKey(name: 'ho_nm')
  String get hoNm => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AreaInfoRequestCopyWith<AreaInfoRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AreaInfoRequestCopyWith<$Res> {
  factory $AreaInfoRequestCopyWith(
          AreaInfoRequest value, $Res Function(AreaInfoRequest) then) =
      _$AreaInfoRequestCopyWithImpl<$Res, AreaInfoRequest>;
  @useResult
  $Res call(
      {@JsonKey(name: 'bjdong_code') String bjdongCode,
      String bun,
      String ji,
      @JsonKey(name: 'dong_nm') String dongNm,
      @JsonKey(name: 'ho_nm') String hoNm});
}

/// @nodoc
class _$AreaInfoRequestCopyWithImpl<$Res, $Val extends AreaInfoRequest>
    implements $AreaInfoRequestCopyWith<$Res> {
  _$AreaInfoRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? bjdongCode = null,
    Object? bun = null,
    Object? ji = null,
    Object? dongNm = null,
    Object? hoNm = null,
  }) {
    return _then(_value.copyWith(
      bjdongCode: null == bjdongCode
          ? _value.bjdongCode
          : bjdongCode // ignore: cast_nullable_to_non_nullable
              as String,
      bun: null == bun
          ? _value.bun
          : bun // ignore: cast_nullable_to_non_nullable
              as String,
      ji: null == ji
          ? _value.ji
          : ji // ignore: cast_nullable_to_non_nullable
              as String,
      dongNm: null == dongNm
          ? _value.dongNm
          : dongNm // ignore: cast_nullable_to_non_nullable
              as String,
      hoNm: null == hoNm
          ? _value.hoNm
          : hoNm // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$AreaInfoRequestImplCopyWith<$Res>
    implements $AreaInfoRequestCopyWith<$Res> {
  factory _$$AreaInfoRequestImplCopyWith(_$AreaInfoRequestImpl value,
          $Res Function(_$AreaInfoRequestImpl) then) =
      __$$AreaInfoRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'bjdong_code') String bjdongCode,
      String bun,
      String ji,
      @JsonKey(name: 'dong_nm') String dongNm,
      @JsonKey(name: 'ho_nm') String hoNm});
}

/// @nodoc
class __$$AreaInfoRequestImplCopyWithImpl<$Res>
    extends _$AreaInfoRequestCopyWithImpl<$Res, _$AreaInfoRequestImpl>
    implements _$$AreaInfoRequestImplCopyWith<$Res> {
  __$$AreaInfoRequestImplCopyWithImpl(
      _$AreaInfoRequestImpl _value, $Res Function(_$AreaInfoRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? bjdongCode = null,
    Object? bun = null,
    Object? ji = null,
    Object? dongNm = null,
    Object? hoNm = null,
  }) {
    return _then(_$AreaInfoRequestImpl(
      bjdongCode: null == bjdongCode
          ? _value.bjdongCode
          : bjdongCode // ignore: cast_nullable_to_non_nullable
              as String,
      bun: null == bun
          ? _value.bun
          : bun // ignore: cast_nullable_to_non_nullable
              as String,
      ji: null == ji
          ? _value.ji
          : ji // ignore: cast_nullable_to_non_nullable
              as String,
      dongNm: null == dongNm
          ? _value.dongNm
          : dongNm // ignore: cast_nullable_to_non_nullable
              as String,
      hoNm: null == hoNm
          ? _value.hoNm
          : hoNm // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AreaInfoRequestImpl implements _AreaInfoRequest {
  const _$AreaInfoRequestImpl(
      {@JsonKey(name: 'bjdong_code') required this.bjdongCode,
      required this.bun,
      this.ji = '0000',
      @JsonKey(name: 'dong_nm') required this.dongNm,
      @JsonKey(name: 'ho_nm') required this.hoNm});

  factory _$AreaInfoRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$AreaInfoRequestImplFromJson(json);

  @override
  @JsonKey(name: 'bjdong_code')
  final String bjdongCode;
  @override
  final String bun;
  @override
  @JsonKey()
  final String ji;
  @override
  @JsonKey(name: 'dong_nm')
  final String dongNm;
  @override
  @JsonKey(name: 'ho_nm')
  final String hoNm;

  @override
  String toString() {
    return 'AreaInfoRequest(bjdongCode: $bjdongCode, bun: $bun, ji: $ji, dongNm: $dongNm, hoNm: $hoNm)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AreaInfoRequestImpl &&
            (identical(other.bjdongCode, bjdongCode) ||
                other.bjdongCode == bjdongCode) &&
            (identical(other.bun, bun) || other.bun == bun) &&
            (identical(other.ji, ji) || other.ji == ji) &&
            (identical(other.dongNm, dongNm) || other.dongNm == dongNm) &&
            (identical(other.hoNm, hoNm) || other.hoNm == hoNm));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, bjdongCode, bun, ji, dongNm, hoNm);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AreaInfoRequestImplCopyWith<_$AreaInfoRequestImpl> get copyWith =>
      __$$AreaInfoRequestImplCopyWithImpl<_$AreaInfoRequestImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AreaInfoRequestImplToJson(
      this,
    );
  }
}

abstract class _AreaInfoRequest implements AreaInfoRequest {
  const factory _AreaInfoRequest(
          {@JsonKey(name: 'bjdong_code') required final String bjdongCode,
          required final String bun,
          final String ji,
          @JsonKey(name: 'dong_nm') required final String dongNm,
          @JsonKey(name: 'ho_nm') required final String hoNm}) =
      _$AreaInfoRequestImpl;

  factory _AreaInfoRequest.fromJson(Map<String, dynamic> json) =
      _$AreaInfoRequestImpl.fromJson;

  @override
  @JsonKey(name: 'bjdong_code')
  String get bjdongCode;
  @override
  String get bun;
  @override
  String get ji;
  @override
  @JsonKey(name: 'dong_nm')
  String get dongNm;
  @override
  @JsonKey(name: 'ho_nm')
  String get hoNm;
  @override
  @JsonKey(ignore: true)
  _$$AreaInfoRequestImplCopyWith<_$AreaInfoRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AreaInfo _$AreaInfoFromJson(Map<String, dynamic> json) {
  return _AreaInfo.fromJson(json);
}

/// @nodoc
mixin _$AreaInfo {
  @JsonKey(name: 'dong_nm')
  String? get dongNm => throw _privateConstructorUsedError;
  @JsonKey(name: 'ho_nm')
  String? get hoNm => throw _privateConstructorUsedError;
  @JsonKey(name: 'bld_nm')
  String? get bldNm => throw _privateConstructorUsedError;
  @JsonKey(name: 'floor_no')
  int? get floorNo => throw _privateConstructorUsedError;
  @JsonKey(name: 'floor_gb')
  String? get floorGb => throw _privateConstructorUsedError;
  @JsonKey(name: 'exclusive_area')
  double? get exclusiveArea => throw _privateConstructorUsedError;
  @JsonKey(name: 'supply_area')
  double? get supplyArea => throw _privateConstructorUsedError;
  @JsonKey(name: 'sale_area')
  double? get saleArea => throw _privateConstructorUsedError;
  @JsonKey(name: 'land_share')
  double? get landShare => throw _privateConstructorUsedError;
  @JsonKey(name: 'land_share_ratio')
  String? get landShareRatio => throw _privateConstructorUsedError;
  @JsonKey(name: 'house_price')
  int? get housePrice => throw _privateConstructorUsedError;
  @JsonKey(name: 'house_price_year')
  String? get housePriceYear => throw _privateConstructorUsedError;
  @JsonKey(name: 'house_price_month')
  String? get housePriceMonth => throw _privateConstructorUsedError;
  @JsonKey(name: 'main_purpose')
  String? get mainPurpose => throw _privateConstructorUsedError;
  @JsonKey(name: 'etc_purpose')
  String? get etcPurpose => throw _privateConstructorUsedError;
  @JsonKey(name: 'dong_title_info')
  Map<String, dynamic>? get dongTitleInfo => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AreaInfoCopyWith<AreaInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AreaInfoCopyWith<$Res> {
  factory $AreaInfoCopyWith(AreaInfo value, $Res Function(AreaInfo) then) =
      _$AreaInfoCopyWithImpl<$Res, AreaInfo>;
  @useResult
  $Res call(
      {@JsonKey(name: 'dong_nm') String? dongNm,
      @JsonKey(name: 'ho_nm') String? hoNm,
      @JsonKey(name: 'bld_nm') String? bldNm,
      @JsonKey(name: 'floor_no') int? floorNo,
      @JsonKey(name: 'floor_gb') String? floorGb,
      @JsonKey(name: 'exclusive_area') double? exclusiveArea,
      @JsonKey(name: 'supply_area') double? supplyArea,
      @JsonKey(name: 'sale_area') double? saleArea,
      @JsonKey(name: 'land_share') double? landShare,
      @JsonKey(name: 'land_share_ratio') String? landShareRatio,
      @JsonKey(name: 'house_price') int? housePrice,
      @JsonKey(name: 'house_price_year') String? housePriceYear,
      @JsonKey(name: 'house_price_month') String? housePriceMonth,
      @JsonKey(name: 'main_purpose') String? mainPurpose,
      @JsonKey(name: 'etc_purpose') String? etcPurpose,
      @JsonKey(name: 'dong_title_info') Map<String, dynamic>? dongTitleInfo});
}

/// @nodoc
class _$AreaInfoCopyWithImpl<$Res, $Val extends AreaInfo>
    implements $AreaInfoCopyWith<$Res> {
  _$AreaInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? dongNm = freezed,
    Object? hoNm = freezed,
    Object? bldNm = freezed,
    Object? floorNo = freezed,
    Object? floorGb = freezed,
    Object? exclusiveArea = freezed,
    Object? supplyArea = freezed,
    Object? saleArea = freezed,
    Object? landShare = freezed,
    Object? landShareRatio = freezed,
    Object? housePrice = freezed,
    Object? housePriceYear = freezed,
    Object? housePriceMonth = freezed,
    Object? mainPurpose = freezed,
    Object? etcPurpose = freezed,
    Object? dongTitleInfo = freezed,
  }) {
    return _then(_value.copyWith(
      dongNm: freezed == dongNm
          ? _value.dongNm
          : dongNm // ignore: cast_nullable_to_non_nullable
              as String?,
      hoNm: freezed == hoNm
          ? _value.hoNm
          : hoNm // ignore: cast_nullable_to_non_nullable
              as String?,
      bldNm: freezed == bldNm
          ? _value.bldNm
          : bldNm // ignore: cast_nullable_to_non_nullable
              as String?,
      floorNo: freezed == floorNo
          ? _value.floorNo
          : floorNo // ignore: cast_nullable_to_non_nullable
              as int?,
      floorGb: freezed == floorGb
          ? _value.floorGb
          : floorGb // ignore: cast_nullable_to_non_nullable
              as String?,
      exclusiveArea: freezed == exclusiveArea
          ? _value.exclusiveArea
          : exclusiveArea // ignore: cast_nullable_to_non_nullable
              as double?,
      supplyArea: freezed == supplyArea
          ? _value.supplyArea
          : supplyArea // ignore: cast_nullable_to_non_nullable
              as double?,
      saleArea: freezed == saleArea
          ? _value.saleArea
          : saleArea // ignore: cast_nullable_to_non_nullable
              as double?,
      landShare: freezed == landShare
          ? _value.landShare
          : landShare // ignore: cast_nullable_to_non_nullable
              as double?,
      landShareRatio: freezed == landShareRatio
          ? _value.landShareRatio
          : landShareRatio // ignore: cast_nullable_to_non_nullable
              as String?,
      housePrice: freezed == housePrice
          ? _value.housePrice
          : housePrice // ignore: cast_nullable_to_non_nullable
              as int?,
      housePriceYear: freezed == housePriceYear
          ? _value.housePriceYear
          : housePriceYear // ignore: cast_nullable_to_non_nullable
              as String?,
      housePriceMonth: freezed == housePriceMonth
          ? _value.housePriceMonth
          : housePriceMonth // ignore: cast_nullable_to_non_nullable
              as String?,
      mainPurpose: freezed == mainPurpose
          ? _value.mainPurpose
          : mainPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      etcPurpose: freezed == etcPurpose
          ? _value.etcPurpose
          : etcPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      dongTitleInfo: freezed == dongTitleInfo
          ? _value.dongTitleInfo
          : dongTitleInfo // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$AreaInfoImplCopyWith<$Res>
    implements $AreaInfoCopyWith<$Res> {
  factory _$$AreaInfoImplCopyWith(
          _$AreaInfoImpl value, $Res Function(_$AreaInfoImpl) then) =
      __$$AreaInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'dong_nm') String? dongNm,
      @JsonKey(name: 'ho_nm') String? hoNm,
      @JsonKey(name: 'bld_nm') String? bldNm,
      @JsonKey(name: 'floor_no') int? floorNo,
      @JsonKey(name: 'floor_gb') String? floorGb,
      @JsonKey(name: 'exclusive_area') double? exclusiveArea,
      @JsonKey(name: 'supply_area') double? supplyArea,
      @JsonKey(name: 'sale_area') double? saleArea,
      @JsonKey(name: 'land_share') double? landShare,
      @JsonKey(name: 'land_share_ratio') String? landShareRatio,
      @JsonKey(name: 'house_price') int? housePrice,
      @JsonKey(name: 'house_price_year') String? housePriceYear,
      @JsonKey(name: 'house_price_month') String? housePriceMonth,
      @JsonKey(name: 'main_purpose') String? mainPurpose,
      @JsonKey(name: 'etc_purpose') String? etcPurpose,
      @JsonKey(name: 'dong_title_info') Map<String, dynamic>? dongTitleInfo});
}

/// @nodoc
class __$$AreaInfoImplCopyWithImpl<$Res>
    extends _$AreaInfoCopyWithImpl<$Res, _$AreaInfoImpl>
    implements _$$AreaInfoImplCopyWith<$Res> {
  __$$AreaInfoImplCopyWithImpl(
      _$AreaInfoImpl _value, $Res Function(_$AreaInfoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? dongNm = freezed,
    Object? hoNm = freezed,
    Object? bldNm = freezed,
    Object? floorNo = freezed,
    Object? floorGb = freezed,
    Object? exclusiveArea = freezed,
    Object? supplyArea = freezed,
    Object? saleArea = freezed,
    Object? landShare = freezed,
    Object? landShareRatio = freezed,
    Object? housePrice = freezed,
    Object? housePriceYear = freezed,
    Object? housePriceMonth = freezed,
    Object? mainPurpose = freezed,
    Object? etcPurpose = freezed,
    Object? dongTitleInfo = freezed,
  }) {
    return _then(_$AreaInfoImpl(
      dongNm: freezed == dongNm
          ? _value.dongNm
          : dongNm // ignore: cast_nullable_to_non_nullable
              as String?,
      hoNm: freezed == hoNm
          ? _value.hoNm
          : hoNm // ignore: cast_nullable_to_non_nullable
              as String?,
      bldNm: freezed == bldNm
          ? _value.bldNm
          : bldNm // ignore: cast_nullable_to_non_nullable
              as String?,
      floorNo: freezed == floorNo
          ? _value.floorNo
          : floorNo // ignore: cast_nullable_to_non_nullable
              as int?,
      floorGb: freezed == floorGb
          ? _value.floorGb
          : floorGb // ignore: cast_nullable_to_non_nullable
              as String?,
      exclusiveArea: freezed == exclusiveArea
          ? _value.exclusiveArea
          : exclusiveArea // ignore: cast_nullable_to_non_nullable
              as double?,
      supplyArea: freezed == supplyArea
          ? _value.supplyArea
          : supplyArea // ignore: cast_nullable_to_non_nullable
              as double?,
      saleArea: freezed == saleArea
          ? _value.saleArea
          : saleArea // ignore: cast_nullable_to_non_nullable
              as double?,
      landShare: freezed == landShare
          ? _value.landShare
          : landShare // ignore: cast_nullable_to_non_nullable
              as double?,
      landShareRatio: freezed == landShareRatio
          ? _value.landShareRatio
          : landShareRatio // ignore: cast_nullable_to_non_nullable
              as String?,
      housePrice: freezed == housePrice
          ? _value.housePrice
          : housePrice // ignore: cast_nullable_to_non_nullable
              as int?,
      housePriceYear: freezed == housePriceYear
          ? _value.housePriceYear
          : housePriceYear // ignore: cast_nullable_to_non_nullable
              as String?,
      housePriceMonth: freezed == housePriceMonth
          ? _value.housePriceMonth
          : housePriceMonth // ignore: cast_nullable_to_non_nullable
              as String?,
      mainPurpose: freezed == mainPurpose
          ? _value.mainPurpose
          : mainPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      etcPurpose: freezed == etcPurpose
          ? _value.etcPurpose
          : etcPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
      dongTitleInfo: freezed == dongTitleInfo
          ? _value._dongTitleInfo
          : dongTitleInfo // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AreaInfoImpl implements _AreaInfo {
  const _$AreaInfoImpl(
      {@JsonKey(name: 'dong_nm') this.dongNm,
      @JsonKey(name: 'ho_nm') this.hoNm,
      @JsonKey(name: 'bld_nm') this.bldNm,
      @JsonKey(name: 'floor_no') this.floorNo,
      @JsonKey(name: 'floor_gb') this.floorGb,
      @JsonKey(name: 'exclusive_area') this.exclusiveArea,
      @JsonKey(name: 'supply_area') this.supplyArea,
      @JsonKey(name: 'sale_area') this.saleArea,
      @JsonKey(name: 'land_share') this.landShare,
      @JsonKey(name: 'land_share_ratio') this.landShareRatio,
      @JsonKey(name: 'house_price') this.housePrice,
      @JsonKey(name: 'house_price_year') this.housePriceYear,
      @JsonKey(name: 'house_price_month') this.housePriceMonth,
      @JsonKey(name: 'main_purpose') this.mainPurpose,
      @JsonKey(name: 'etc_purpose') this.etcPurpose,
      @JsonKey(name: 'dong_title_info')
      final Map<String, dynamic>? dongTitleInfo})
      : _dongTitleInfo = dongTitleInfo;

  factory _$AreaInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$AreaInfoImplFromJson(json);

  @override
  @JsonKey(name: 'dong_nm')
  final String? dongNm;
  @override
  @JsonKey(name: 'ho_nm')
  final String? hoNm;
  @override
  @JsonKey(name: 'bld_nm')
  final String? bldNm;
  @override
  @JsonKey(name: 'floor_no')
  final int? floorNo;
  @override
  @JsonKey(name: 'floor_gb')
  final String? floorGb;
  @override
  @JsonKey(name: 'exclusive_area')
  final double? exclusiveArea;
  @override
  @JsonKey(name: 'supply_area')
  final double? supplyArea;
  @override
  @JsonKey(name: 'sale_area')
  final double? saleArea;
  @override
  @JsonKey(name: 'land_share')
  final double? landShare;
  @override
  @JsonKey(name: 'land_share_ratio')
  final String? landShareRatio;
  @override
  @JsonKey(name: 'house_price')
  final int? housePrice;
  @override
  @JsonKey(name: 'house_price_year')
  final String? housePriceYear;
  @override
  @JsonKey(name: 'house_price_month')
  final String? housePriceMonth;
  @override
  @JsonKey(name: 'main_purpose')
  final String? mainPurpose;
  @override
  @JsonKey(name: 'etc_purpose')
  final String? etcPurpose;
  final Map<String, dynamic>? _dongTitleInfo;
  @override
  @JsonKey(name: 'dong_title_info')
  Map<String, dynamic>? get dongTitleInfo {
    final value = _dongTitleInfo;
    if (value == null) return null;
    if (_dongTitleInfo is EqualUnmodifiableMapView) return _dongTitleInfo;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  String toString() {
    return 'AreaInfo(dongNm: $dongNm, hoNm: $hoNm, bldNm: $bldNm, floorNo: $floorNo, floorGb: $floorGb, exclusiveArea: $exclusiveArea, supplyArea: $supplyArea, saleArea: $saleArea, landShare: $landShare, landShareRatio: $landShareRatio, housePrice: $housePrice, housePriceYear: $housePriceYear, housePriceMonth: $housePriceMonth, mainPurpose: $mainPurpose, etcPurpose: $etcPurpose, dongTitleInfo: $dongTitleInfo)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AreaInfoImpl &&
            (identical(other.dongNm, dongNm) || other.dongNm == dongNm) &&
            (identical(other.hoNm, hoNm) || other.hoNm == hoNm) &&
            (identical(other.bldNm, bldNm) || other.bldNm == bldNm) &&
            (identical(other.floorNo, floorNo) || other.floorNo == floorNo) &&
            (identical(other.floorGb, floorGb) || other.floorGb == floorGb) &&
            (identical(other.exclusiveArea, exclusiveArea) ||
                other.exclusiveArea == exclusiveArea) &&
            (identical(other.supplyArea, supplyArea) ||
                other.supplyArea == supplyArea) &&
            (identical(other.saleArea, saleArea) ||
                other.saleArea == saleArea) &&
            (identical(other.landShare, landShare) ||
                other.landShare == landShare) &&
            (identical(other.landShareRatio, landShareRatio) ||
                other.landShareRatio == landShareRatio) &&
            (identical(other.housePrice, housePrice) ||
                other.housePrice == housePrice) &&
            (identical(other.housePriceYear, housePriceYear) ||
                other.housePriceYear == housePriceYear) &&
            (identical(other.housePriceMonth, housePriceMonth) ||
                other.housePriceMonth == housePriceMonth) &&
            (identical(other.mainPurpose, mainPurpose) ||
                other.mainPurpose == mainPurpose) &&
            (identical(other.etcPurpose, etcPurpose) ||
                other.etcPurpose == etcPurpose) &&
            const DeepCollectionEquality()
                .equals(other._dongTitleInfo, _dongTitleInfo));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      dongNm,
      hoNm,
      bldNm,
      floorNo,
      floorGb,
      exclusiveArea,
      supplyArea,
      saleArea,
      landShare,
      landShareRatio,
      housePrice,
      housePriceYear,
      housePriceMonth,
      mainPurpose,
      etcPurpose,
      const DeepCollectionEquality().hash(_dongTitleInfo));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AreaInfoImplCopyWith<_$AreaInfoImpl> get copyWith =>
      __$$AreaInfoImplCopyWithImpl<_$AreaInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AreaInfoImplToJson(
      this,
    );
  }
}

abstract class _AreaInfo implements AreaInfo {
  const factory _AreaInfo(
      {@JsonKey(name: 'dong_nm') final String? dongNm,
      @JsonKey(name: 'ho_nm') final String? hoNm,
      @JsonKey(name: 'bld_nm') final String? bldNm,
      @JsonKey(name: 'floor_no') final int? floorNo,
      @JsonKey(name: 'floor_gb') final String? floorGb,
      @JsonKey(name: 'exclusive_area') final double? exclusiveArea,
      @JsonKey(name: 'supply_area') final double? supplyArea,
      @JsonKey(name: 'sale_area') final double? saleArea,
      @JsonKey(name: 'land_share') final double? landShare,
      @JsonKey(name: 'land_share_ratio') final String? landShareRatio,
      @JsonKey(name: 'house_price') final int? housePrice,
      @JsonKey(name: 'house_price_year') final String? housePriceYear,
      @JsonKey(name: 'house_price_month') final String? housePriceMonth,
      @JsonKey(name: 'main_purpose') final String? mainPurpose,
      @JsonKey(name: 'etc_purpose') final String? etcPurpose,
      @JsonKey(name: 'dong_title_info')
      final Map<String, dynamic>? dongTitleInfo}) = _$AreaInfoImpl;

  factory _AreaInfo.fromJson(Map<String, dynamic> json) =
      _$AreaInfoImpl.fromJson;

  @override
  @JsonKey(name: 'dong_nm')
  String? get dongNm;
  @override
  @JsonKey(name: 'ho_nm')
  String? get hoNm;
  @override
  @JsonKey(name: 'bld_nm')
  String? get bldNm;
  @override
  @JsonKey(name: 'floor_no')
  int? get floorNo;
  @override
  @JsonKey(name: 'floor_gb')
  String? get floorGb;
  @override
  @JsonKey(name: 'exclusive_area')
  double? get exclusiveArea;
  @override
  @JsonKey(name: 'supply_area')
  double? get supplyArea;
  @override
  @JsonKey(name: 'sale_area')
  double? get saleArea;
  @override
  @JsonKey(name: 'land_share')
  double? get landShare;
  @override
  @JsonKey(name: 'land_share_ratio')
  String? get landShareRatio;
  @override
  @JsonKey(name: 'house_price')
  int? get housePrice;
  @override
  @JsonKey(name: 'house_price_year')
  String? get housePriceYear;
  @override
  @JsonKey(name: 'house_price_month')
  String? get housePriceMonth;
  @override
  @JsonKey(name: 'main_purpose')
  String? get mainPurpose;
  @override
  @JsonKey(name: 'etc_purpose')
  String? get etcPurpose;
  @override
  @JsonKey(name: 'dong_title_info')
  Map<String, dynamic>? get dongTitleInfo;
  @override
  @JsonKey(ignore: true)
  _$$AreaInfoImplCopyWith<_$AreaInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AreaInfoResponse _$AreaInfoResponseFromJson(Map<String, dynamic> json) {
  return _AreaInfoResponse.fromJson(json);
}

/// @nodoc
mixin _$AreaInfoResponse {
  bool get success => throw _privateConstructorUsedError;
  @JsonKey(name: 'area_info')
  AreaInfo? get areaInfo => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AreaInfoResponseCopyWith<AreaInfoResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AreaInfoResponseCopyWith<$Res> {
  factory $AreaInfoResponseCopyWith(
          AreaInfoResponse value, $Res Function(AreaInfoResponse) then) =
      _$AreaInfoResponseCopyWithImpl<$Res, AreaInfoResponse>;
  @useResult
  $Res call(
      {bool success,
      @JsonKey(name: 'area_info') AreaInfo? areaInfo,
      String? error});

  $AreaInfoCopyWith<$Res>? get areaInfo;
}

/// @nodoc
class _$AreaInfoResponseCopyWithImpl<$Res, $Val extends AreaInfoResponse>
    implements $AreaInfoResponseCopyWith<$Res> {
  _$AreaInfoResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? areaInfo = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      areaInfo: freezed == areaInfo
          ? _value.areaInfo
          : areaInfo // ignore: cast_nullable_to_non_nullable
              as AreaInfo?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $AreaInfoCopyWith<$Res>? get areaInfo {
    if (_value.areaInfo == null) {
      return null;
    }

    return $AreaInfoCopyWith<$Res>(_value.areaInfo!, (value) {
      return _then(_value.copyWith(areaInfo: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AreaInfoResponseImplCopyWith<$Res>
    implements $AreaInfoResponseCopyWith<$Res> {
  factory _$$AreaInfoResponseImplCopyWith(_$AreaInfoResponseImpl value,
          $Res Function(_$AreaInfoResponseImpl) then) =
      __$$AreaInfoResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool success,
      @JsonKey(name: 'area_info') AreaInfo? areaInfo,
      String? error});

  @override
  $AreaInfoCopyWith<$Res>? get areaInfo;
}

/// @nodoc
class __$$AreaInfoResponseImplCopyWithImpl<$Res>
    extends _$AreaInfoResponseCopyWithImpl<$Res, _$AreaInfoResponseImpl>
    implements _$$AreaInfoResponseImplCopyWith<$Res> {
  __$$AreaInfoResponseImplCopyWithImpl(_$AreaInfoResponseImpl _value,
      $Res Function(_$AreaInfoResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? areaInfo = freezed,
    Object? error = freezed,
  }) {
    return _then(_$AreaInfoResponseImpl(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      areaInfo: freezed == areaInfo
          ? _value.areaInfo
          : areaInfo // ignore: cast_nullable_to_non_nullable
              as AreaInfo?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AreaInfoResponseImpl implements _AreaInfoResponse {
  const _$AreaInfoResponseImpl(
      {required this.success,
      @JsonKey(name: 'area_info') this.areaInfo,
      this.error});

  factory _$AreaInfoResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$AreaInfoResponseImplFromJson(json);

  @override
  final bool success;
  @override
  @JsonKey(name: 'area_info')
  final AreaInfo? areaInfo;
  @override
  final String? error;

  @override
  String toString() {
    return 'AreaInfoResponse(success: $success, areaInfo: $areaInfo, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AreaInfoResponseImpl &&
            (identical(other.success, success) || other.success == success) &&
            (identical(other.areaInfo, areaInfo) ||
                other.areaInfo == areaInfo) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, success, areaInfo, error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AreaInfoResponseImplCopyWith<_$AreaInfoResponseImpl> get copyWith =>
      __$$AreaInfoResponseImplCopyWithImpl<_$AreaInfoResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AreaInfoResponseImplToJson(
      this,
    );
  }
}

abstract class _AreaInfoResponse implements AreaInfoResponse {
  const factory _AreaInfoResponse(
      {required final bool success,
      @JsonKey(name: 'area_info') final AreaInfo? areaInfo,
      final String? error}) = _$AreaInfoResponseImpl;

  factory _AreaInfoResponse.fromJson(Map<String, dynamic> json) =
      _$AreaInfoResponseImpl.fromJson;

  @override
  bool get success;
  @override
  @JsonKey(name: 'area_info')
  AreaInfo? get areaInfo;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$AreaInfoResponseImplCopyWith<_$AreaInfoResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
