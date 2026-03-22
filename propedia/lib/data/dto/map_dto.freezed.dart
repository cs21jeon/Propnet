// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'map_dto.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

MapClickJibunRequest _$MapClickJibunRequestFromJson(Map<String, dynamic> json) {
  return _MapClickJibunRequest.fromJson(json);
}

/// @nodoc
mixin _$MapClickJibunRequest {
  double get lat => throw _privateConstructorUsedError;
  double get lng => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $MapClickJibunRequestCopyWith<MapClickJibunRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MapClickJibunRequestCopyWith<$Res> {
  factory $MapClickJibunRequestCopyWith(MapClickJibunRequest value,
          $Res Function(MapClickJibunRequest) then) =
      _$MapClickJibunRequestCopyWithImpl<$Res, MapClickJibunRequest>;
  @useResult
  $Res call({double lat, double lng});
}

/// @nodoc
class _$MapClickJibunRequestCopyWithImpl<$Res,
        $Val extends MapClickJibunRequest>
    implements $MapClickJibunRequestCopyWith<$Res> {
  _$MapClickJibunRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? lat = null,
    Object? lng = null,
  }) {
    return _then(_value.copyWith(
      lat: null == lat
          ? _value.lat
          : lat // ignore: cast_nullable_to_non_nullable
              as double,
      lng: null == lng
          ? _value.lng
          : lng // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MapClickJibunRequestImplCopyWith<$Res>
    implements $MapClickJibunRequestCopyWith<$Res> {
  factory _$$MapClickJibunRequestImplCopyWith(_$MapClickJibunRequestImpl value,
          $Res Function(_$MapClickJibunRequestImpl) then) =
      __$$MapClickJibunRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({double lat, double lng});
}

/// @nodoc
class __$$MapClickJibunRequestImplCopyWithImpl<$Res>
    extends _$MapClickJibunRequestCopyWithImpl<$Res, _$MapClickJibunRequestImpl>
    implements _$$MapClickJibunRequestImplCopyWith<$Res> {
  __$$MapClickJibunRequestImplCopyWithImpl(_$MapClickJibunRequestImpl _value,
      $Res Function(_$MapClickJibunRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? lat = null,
    Object? lng = null,
  }) {
    return _then(_$MapClickJibunRequestImpl(
      lat: null == lat
          ? _value.lat
          : lat // ignore: cast_nullable_to_non_nullable
              as double,
      lng: null == lng
          ? _value.lng
          : lng // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MapClickJibunRequestImpl implements _MapClickJibunRequest {
  const _$MapClickJibunRequestImpl({required this.lat, required this.lng});

  factory _$MapClickJibunRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$MapClickJibunRequestImplFromJson(json);

  @override
  final double lat;
  @override
  final double lng;

  @override
  String toString() {
    return 'MapClickJibunRequest(lat: $lat, lng: $lng)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MapClickJibunRequestImpl &&
            (identical(other.lat, lat) || other.lat == lat) &&
            (identical(other.lng, lng) || other.lng == lng));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, lat, lng);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$MapClickJibunRequestImplCopyWith<_$MapClickJibunRequestImpl>
      get copyWith =>
          __$$MapClickJibunRequestImplCopyWithImpl<_$MapClickJibunRequestImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MapClickJibunRequestImplToJson(
      this,
    );
  }
}

abstract class _MapClickJibunRequest implements MapClickJibunRequest {
  const factory _MapClickJibunRequest(
      {required final double lat,
      required final double lng}) = _$MapClickJibunRequestImpl;

  factory _MapClickJibunRequest.fromJson(Map<String, dynamic> json) =
      _$MapClickJibunRequestImpl.fromJson;

  @override
  double get lat;
  @override
  double get lng;
  @override
  @JsonKey(ignore: true)
  _$$MapClickJibunRequestImplCopyWith<_$MapClickJibunRequestImpl>
      get copyWith => throw _privateConstructorUsedError;
}

JibunInfo _$JibunInfoFromJson(Map<String, dynamic> json) {
  return _JibunInfo.fromJson(json);
}

/// @nodoc
mixin _$JibunInfo {
  String get address => throw _privateConstructorUsedError;
  String get pnu => throw _privateConstructorUsedError;
  @JsonKey(name: 'bjdong_code')
  String get bjdongCode => throw _privateConstructorUsedError;
  String get bun => throw _privateConstructorUsedError;
  String get ji => throw _privateConstructorUsedError;
  @JsonKey(name: 'land_type')
  String get landType => throw _privateConstructorUsedError;
  @JsonKey(name: 'land_type_name')
  String? get landTypeName => throw _privateConstructorUsedError;
  @JsonKey(name: 'road_address')
  String? get roadAddress => throw _privateConstructorUsedError;
  @JsonKey(name: 'main_purpose')
  String? get mainPurpose => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $JibunInfoCopyWith<JibunInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $JibunInfoCopyWith<$Res> {
  factory $JibunInfoCopyWith(JibunInfo value, $Res Function(JibunInfo) then) =
      _$JibunInfoCopyWithImpl<$Res, JibunInfo>;
  @useResult
  $Res call(
      {String address,
      String pnu,
      @JsonKey(name: 'bjdong_code') String bjdongCode,
      String bun,
      String ji,
      @JsonKey(name: 'land_type') String landType,
      @JsonKey(name: 'land_type_name') String? landTypeName,
      @JsonKey(name: 'road_address') String? roadAddress,
      @JsonKey(name: 'main_purpose') String? mainPurpose});
}

/// @nodoc
class _$JibunInfoCopyWithImpl<$Res, $Val extends JibunInfo>
    implements $JibunInfoCopyWith<$Res> {
  _$JibunInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? address = null,
    Object? pnu = null,
    Object? bjdongCode = null,
    Object? bun = null,
    Object? ji = null,
    Object? landType = null,
    Object? landTypeName = freezed,
    Object? roadAddress = freezed,
    Object? mainPurpose = freezed,
  }) {
    return _then(_value.copyWith(
      address: null == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String,
      pnu: null == pnu
          ? _value.pnu
          : pnu // ignore: cast_nullable_to_non_nullable
              as String,
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
      landTypeName: freezed == landTypeName
          ? _value.landTypeName
          : landTypeName // ignore: cast_nullable_to_non_nullable
              as String?,
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      mainPurpose: freezed == mainPurpose
          ? _value.mainPurpose
          : mainPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$JibunInfoImplCopyWith<$Res>
    implements $JibunInfoCopyWith<$Res> {
  factory _$$JibunInfoImplCopyWith(
          _$JibunInfoImpl value, $Res Function(_$JibunInfoImpl) then) =
      __$$JibunInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String address,
      String pnu,
      @JsonKey(name: 'bjdong_code') String bjdongCode,
      String bun,
      String ji,
      @JsonKey(name: 'land_type') String landType,
      @JsonKey(name: 'land_type_name') String? landTypeName,
      @JsonKey(name: 'road_address') String? roadAddress,
      @JsonKey(name: 'main_purpose') String? mainPurpose});
}

/// @nodoc
class __$$JibunInfoImplCopyWithImpl<$Res>
    extends _$JibunInfoCopyWithImpl<$Res, _$JibunInfoImpl>
    implements _$$JibunInfoImplCopyWith<$Res> {
  __$$JibunInfoImplCopyWithImpl(
      _$JibunInfoImpl _value, $Res Function(_$JibunInfoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? address = null,
    Object? pnu = null,
    Object? bjdongCode = null,
    Object? bun = null,
    Object? ji = null,
    Object? landType = null,
    Object? landTypeName = freezed,
    Object? roadAddress = freezed,
    Object? mainPurpose = freezed,
  }) {
    return _then(_$JibunInfoImpl(
      address: null == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String,
      pnu: null == pnu
          ? _value.pnu
          : pnu // ignore: cast_nullable_to_non_nullable
              as String,
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
      landTypeName: freezed == landTypeName
          ? _value.landTypeName
          : landTypeName // ignore: cast_nullable_to_non_nullable
              as String?,
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      mainPurpose: freezed == mainPurpose
          ? _value.mainPurpose
          : mainPurpose // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$JibunInfoImpl implements _JibunInfo {
  const _$JibunInfoImpl(
      {required this.address,
      required this.pnu,
      @JsonKey(name: 'bjdong_code') required this.bjdongCode,
      required this.bun,
      required this.ji,
      @JsonKey(name: 'land_type') required this.landType,
      @JsonKey(name: 'land_type_name') this.landTypeName,
      @JsonKey(name: 'road_address') this.roadAddress,
      @JsonKey(name: 'main_purpose') this.mainPurpose});

  factory _$JibunInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$JibunInfoImplFromJson(json);

  @override
  final String address;
  @override
  final String pnu;
  @override
  @JsonKey(name: 'bjdong_code')
  final String bjdongCode;
  @override
  final String bun;
  @override
  final String ji;
  @override
  @JsonKey(name: 'land_type')
  final String landType;
  @override
  @JsonKey(name: 'land_type_name')
  final String? landTypeName;
  @override
  @JsonKey(name: 'road_address')
  final String? roadAddress;
  @override
  @JsonKey(name: 'main_purpose')
  final String? mainPurpose;

  @override
  String toString() {
    return 'JibunInfo(address: $address, pnu: $pnu, bjdongCode: $bjdongCode, bun: $bun, ji: $ji, landType: $landType, landTypeName: $landTypeName, roadAddress: $roadAddress, mainPurpose: $mainPurpose)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$JibunInfoImpl &&
            (identical(other.address, address) || other.address == address) &&
            (identical(other.pnu, pnu) || other.pnu == pnu) &&
            (identical(other.bjdongCode, bjdongCode) ||
                other.bjdongCode == bjdongCode) &&
            (identical(other.bun, bun) || other.bun == bun) &&
            (identical(other.ji, ji) || other.ji == ji) &&
            (identical(other.landType, landType) ||
                other.landType == landType) &&
            (identical(other.landTypeName, landTypeName) ||
                other.landTypeName == landTypeName) &&
            (identical(other.roadAddress, roadAddress) ||
                other.roadAddress == roadAddress) &&
            (identical(other.mainPurpose, mainPurpose) ||
                other.mainPurpose == mainPurpose));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, address, pnu, bjdongCode, bun,
      ji, landType, landTypeName, roadAddress, mainPurpose);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$JibunInfoImplCopyWith<_$JibunInfoImpl> get copyWith =>
      __$$JibunInfoImplCopyWithImpl<_$JibunInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$JibunInfoImplToJson(
      this,
    );
  }
}

abstract class _JibunInfo implements JibunInfo {
  const factory _JibunInfo(
          {required final String address,
          required final String pnu,
          @JsonKey(name: 'bjdong_code') required final String bjdongCode,
          required final String bun,
          required final String ji,
          @JsonKey(name: 'land_type') required final String landType,
          @JsonKey(name: 'land_type_name') final String? landTypeName,
          @JsonKey(name: 'road_address') final String? roadAddress,
          @JsonKey(name: 'main_purpose') final String? mainPurpose}) =
      _$JibunInfoImpl;

  factory _JibunInfo.fromJson(Map<String, dynamic> json) =
      _$JibunInfoImpl.fromJson;

  @override
  String get address;
  @override
  String get pnu;
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
  @JsonKey(name: 'land_type_name')
  String? get landTypeName;
  @override
  @JsonKey(name: 'road_address')
  String? get roadAddress;
  @override
  @JsonKey(name: 'main_purpose')
  String? get mainPurpose;
  @override
  @JsonKey(ignore: true)
  _$$JibunInfoImplCopyWith<_$JibunInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MapClickJibunResponse _$MapClickJibunResponseFromJson(
    Map<String, dynamic> json) {
  return _MapClickJibunResponse.fromJson(json);
}

/// @nodoc
mixin _$MapClickJibunResponse {
  bool get success => throw _privateConstructorUsedError;
  @JsonKey(name: 'jibun_info')
  JibunInfo? get jibunInfo => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $MapClickJibunResponseCopyWith<MapClickJibunResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MapClickJibunResponseCopyWith<$Res> {
  factory $MapClickJibunResponseCopyWith(MapClickJibunResponse value,
          $Res Function(MapClickJibunResponse) then) =
      _$MapClickJibunResponseCopyWithImpl<$Res, MapClickJibunResponse>;
  @useResult
  $Res call(
      {bool success,
      @JsonKey(name: 'jibun_info') JibunInfo? jibunInfo,
      String? error});

  $JibunInfoCopyWith<$Res>? get jibunInfo;
}

/// @nodoc
class _$MapClickJibunResponseCopyWithImpl<$Res,
        $Val extends MapClickJibunResponse>
    implements $MapClickJibunResponseCopyWith<$Res> {
  _$MapClickJibunResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? jibunInfo = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      jibunInfo: freezed == jibunInfo
          ? _value.jibunInfo
          : jibunInfo // ignore: cast_nullable_to_non_nullable
              as JibunInfo?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $JibunInfoCopyWith<$Res>? get jibunInfo {
    if (_value.jibunInfo == null) {
      return null;
    }

    return $JibunInfoCopyWith<$Res>(_value.jibunInfo!, (value) {
      return _then(_value.copyWith(jibunInfo: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$MapClickJibunResponseImplCopyWith<$Res>
    implements $MapClickJibunResponseCopyWith<$Res> {
  factory _$$MapClickJibunResponseImplCopyWith(
          _$MapClickJibunResponseImpl value,
          $Res Function(_$MapClickJibunResponseImpl) then) =
      __$$MapClickJibunResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool success,
      @JsonKey(name: 'jibun_info') JibunInfo? jibunInfo,
      String? error});

  @override
  $JibunInfoCopyWith<$Res>? get jibunInfo;
}

/// @nodoc
class __$$MapClickJibunResponseImplCopyWithImpl<$Res>
    extends _$MapClickJibunResponseCopyWithImpl<$Res,
        _$MapClickJibunResponseImpl>
    implements _$$MapClickJibunResponseImplCopyWith<$Res> {
  __$$MapClickJibunResponseImplCopyWithImpl(_$MapClickJibunResponseImpl _value,
      $Res Function(_$MapClickJibunResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? jibunInfo = freezed,
    Object? error = freezed,
  }) {
    return _then(_$MapClickJibunResponseImpl(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      jibunInfo: freezed == jibunInfo
          ? _value.jibunInfo
          : jibunInfo // ignore: cast_nullable_to_non_nullable
              as JibunInfo?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MapClickJibunResponseImpl implements _MapClickJibunResponse {
  const _$MapClickJibunResponseImpl(
      {required this.success,
      @JsonKey(name: 'jibun_info') this.jibunInfo,
      this.error});

  factory _$MapClickJibunResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$MapClickJibunResponseImplFromJson(json);

  @override
  final bool success;
  @override
  @JsonKey(name: 'jibun_info')
  final JibunInfo? jibunInfo;
  @override
  final String? error;

  @override
  String toString() {
    return 'MapClickJibunResponse(success: $success, jibunInfo: $jibunInfo, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MapClickJibunResponseImpl &&
            (identical(other.success, success) || other.success == success) &&
            (identical(other.jibunInfo, jibunInfo) ||
                other.jibunInfo == jibunInfo) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, success, jibunInfo, error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$MapClickJibunResponseImplCopyWith<_$MapClickJibunResponseImpl>
      get copyWith => __$$MapClickJibunResponseImplCopyWithImpl<
          _$MapClickJibunResponseImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MapClickJibunResponseImplToJson(
      this,
    );
  }
}

abstract class _MapClickJibunResponse implements MapClickJibunResponse {
  const factory _MapClickJibunResponse(
      {required final bool success,
      @JsonKey(name: 'jibun_info') final JibunInfo? jibunInfo,
      final String? error}) = _$MapClickJibunResponseImpl;

  factory _MapClickJibunResponse.fromJson(Map<String, dynamic> json) =
      _$MapClickJibunResponseImpl.fromJson;

  @override
  bool get success;
  @override
  @JsonKey(name: 'jibun_info')
  JibunInfo? get jibunInfo;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$MapClickJibunResponseImplCopyWith<_$MapClickJibunResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}

ParcelGeometry _$ParcelGeometryFromJson(Map<String, dynamic> json) {
  return _ParcelGeometry.fromJson(json);
}

/// @nodoc
mixin _$ParcelGeometry {
  String get type => throw _privateConstructorUsedError;
  List<dynamic> get coordinates => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ParcelGeometryCopyWith<ParcelGeometry> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ParcelGeometryCopyWith<$Res> {
  factory $ParcelGeometryCopyWith(
          ParcelGeometry value, $Res Function(ParcelGeometry) then) =
      _$ParcelGeometryCopyWithImpl<$Res, ParcelGeometry>;
  @useResult
  $Res call({String type, List<dynamic> coordinates});
}

/// @nodoc
class _$ParcelGeometryCopyWithImpl<$Res, $Val extends ParcelGeometry>
    implements $ParcelGeometryCopyWith<$Res> {
  _$ParcelGeometryCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? type = null,
    Object? coordinates = null,
  }) {
    return _then(_value.copyWith(
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String,
      coordinates: null == coordinates
          ? _value.coordinates
          : coordinates // ignore: cast_nullable_to_non_nullable
              as List<dynamic>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ParcelGeometryImplCopyWith<$Res>
    implements $ParcelGeometryCopyWith<$Res> {
  factory _$$ParcelGeometryImplCopyWith(_$ParcelGeometryImpl value,
          $Res Function(_$ParcelGeometryImpl) then) =
      __$$ParcelGeometryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String type, List<dynamic> coordinates});
}

/// @nodoc
class __$$ParcelGeometryImplCopyWithImpl<$Res>
    extends _$ParcelGeometryCopyWithImpl<$Res, _$ParcelGeometryImpl>
    implements _$$ParcelGeometryImplCopyWith<$Res> {
  __$$ParcelGeometryImplCopyWithImpl(
      _$ParcelGeometryImpl _value, $Res Function(_$ParcelGeometryImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? type = null,
    Object? coordinates = null,
  }) {
    return _then(_$ParcelGeometryImpl(
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String,
      coordinates: null == coordinates
          ? _value._coordinates
          : coordinates // ignore: cast_nullable_to_non_nullable
              as List<dynamic>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ParcelGeometryImpl implements _ParcelGeometry {
  const _$ParcelGeometryImpl(
      {required this.type, required final List<dynamic> coordinates})
      : _coordinates = coordinates;

  factory _$ParcelGeometryImpl.fromJson(Map<String, dynamic> json) =>
      _$$ParcelGeometryImplFromJson(json);

  @override
  final String type;
  final List<dynamic> _coordinates;
  @override
  List<dynamic> get coordinates {
    if (_coordinates is EqualUnmodifiableListView) return _coordinates;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_coordinates);
  }

  @override
  String toString() {
    return 'ParcelGeometry(type: $type, coordinates: $coordinates)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ParcelGeometryImpl &&
            (identical(other.type, type) || other.type == type) &&
            const DeepCollectionEquality()
                .equals(other._coordinates, _coordinates));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, type, const DeepCollectionEquality().hash(_coordinates));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ParcelGeometryImplCopyWith<_$ParcelGeometryImpl> get copyWith =>
      __$$ParcelGeometryImplCopyWithImpl<_$ParcelGeometryImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ParcelGeometryImplToJson(
      this,
    );
  }
}

abstract class _ParcelGeometry implements ParcelGeometry {
  const factory _ParcelGeometry(
      {required final String type,
      required final List<dynamic> coordinates}) = _$ParcelGeometryImpl;

  factory _ParcelGeometry.fromJson(Map<String, dynamic> json) =
      _$ParcelGeometryImpl.fromJson;

  @override
  String get type;
  @override
  List<dynamic> get coordinates;
  @override
  @JsonKey(ignore: true)
  _$$ParcelGeometryImplCopyWith<_$ParcelGeometryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ParcelProperties _$ParcelPropertiesFromJson(Map<String, dynamic> json) {
  return _ParcelProperties.fromJson(json);
}

/// @nodoc
mixin _$ParcelProperties {
  String? get addr => throw _privateConstructorUsedError;
  String? get pnu => throw _privateConstructorUsedError;
  String? get jibun => throw _privateConstructorUsedError;
  String? get jiga => throw _privateConstructorUsedError;
  @JsonKey(name: 'gosi_year')
  String? get gosiYear => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ParcelPropertiesCopyWith<ParcelProperties> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ParcelPropertiesCopyWith<$Res> {
  factory $ParcelPropertiesCopyWith(
          ParcelProperties value, $Res Function(ParcelProperties) then) =
      _$ParcelPropertiesCopyWithImpl<$Res, ParcelProperties>;
  @useResult
  $Res call(
      {String? addr,
      String? pnu,
      String? jibun,
      String? jiga,
      @JsonKey(name: 'gosi_year') String? gosiYear});
}

/// @nodoc
class _$ParcelPropertiesCopyWithImpl<$Res, $Val extends ParcelProperties>
    implements $ParcelPropertiesCopyWith<$Res> {
  _$ParcelPropertiesCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? addr = freezed,
    Object? pnu = freezed,
    Object? jibun = freezed,
    Object? jiga = freezed,
    Object? gosiYear = freezed,
  }) {
    return _then(_value.copyWith(
      addr: freezed == addr
          ? _value.addr
          : addr // ignore: cast_nullable_to_non_nullable
              as String?,
      pnu: freezed == pnu
          ? _value.pnu
          : pnu // ignore: cast_nullable_to_non_nullable
              as String?,
      jibun: freezed == jibun
          ? _value.jibun
          : jibun // ignore: cast_nullable_to_non_nullable
              as String?,
      jiga: freezed == jiga
          ? _value.jiga
          : jiga // ignore: cast_nullable_to_non_nullable
              as String?,
      gosiYear: freezed == gosiYear
          ? _value.gosiYear
          : gosiYear // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ParcelPropertiesImplCopyWith<$Res>
    implements $ParcelPropertiesCopyWith<$Res> {
  factory _$$ParcelPropertiesImplCopyWith(_$ParcelPropertiesImpl value,
          $Res Function(_$ParcelPropertiesImpl) then) =
      __$$ParcelPropertiesImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String? addr,
      String? pnu,
      String? jibun,
      String? jiga,
      @JsonKey(name: 'gosi_year') String? gosiYear});
}

/// @nodoc
class __$$ParcelPropertiesImplCopyWithImpl<$Res>
    extends _$ParcelPropertiesCopyWithImpl<$Res, _$ParcelPropertiesImpl>
    implements _$$ParcelPropertiesImplCopyWith<$Res> {
  __$$ParcelPropertiesImplCopyWithImpl(_$ParcelPropertiesImpl _value,
      $Res Function(_$ParcelPropertiesImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? addr = freezed,
    Object? pnu = freezed,
    Object? jibun = freezed,
    Object? jiga = freezed,
    Object? gosiYear = freezed,
  }) {
    return _then(_$ParcelPropertiesImpl(
      addr: freezed == addr
          ? _value.addr
          : addr // ignore: cast_nullable_to_non_nullable
              as String?,
      pnu: freezed == pnu
          ? _value.pnu
          : pnu // ignore: cast_nullable_to_non_nullable
              as String?,
      jibun: freezed == jibun
          ? _value.jibun
          : jibun // ignore: cast_nullable_to_non_nullable
              as String?,
      jiga: freezed == jiga
          ? _value.jiga
          : jiga // ignore: cast_nullable_to_non_nullable
              as String?,
      gosiYear: freezed == gosiYear
          ? _value.gosiYear
          : gosiYear // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ParcelPropertiesImpl implements _ParcelProperties {
  const _$ParcelPropertiesImpl(
      {this.addr,
      this.pnu,
      this.jibun,
      this.jiga,
      @JsonKey(name: 'gosi_year') this.gosiYear});

  factory _$ParcelPropertiesImpl.fromJson(Map<String, dynamic> json) =>
      _$$ParcelPropertiesImplFromJson(json);

  @override
  final String? addr;
  @override
  final String? pnu;
  @override
  final String? jibun;
  @override
  final String? jiga;
  @override
  @JsonKey(name: 'gosi_year')
  final String? gosiYear;

  @override
  String toString() {
    return 'ParcelProperties(addr: $addr, pnu: $pnu, jibun: $jibun, jiga: $jiga, gosiYear: $gosiYear)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ParcelPropertiesImpl &&
            (identical(other.addr, addr) || other.addr == addr) &&
            (identical(other.pnu, pnu) || other.pnu == pnu) &&
            (identical(other.jibun, jibun) || other.jibun == jibun) &&
            (identical(other.jiga, jiga) || other.jiga == jiga) &&
            (identical(other.gosiYear, gosiYear) ||
                other.gosiYear == gosiYear));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, addr, pnu, jibun, jiga, gosiYear);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ParcelPropertiesImplCopyWith<_$ParcelPropertiesImpl> get copyWith =>
      __$$ParcelPropertiesImplCopyWithImpl<_$ParcelPropertiesImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ParcelPropertiesImplToJson(
      this,
    );
  }
}

abstract class _ParcelProperties implements ParcelProperties {
  const factory _ParcelProperties(
          {final String? addr,
          final String? pnu,
          final String? jibun,
          final String? jiga,
          @JsonKey(name: 'gosi_year') final String? gosiYear}) =
      _$ParcelPropertiesImpl;

  factory _ParcelProperties.fromJson(Map<String, dynamic> json) =
      _$ParcelPropertiesImpl.fromJson;

  @override
  String? get addr;
  @override
  String? get pnu;
  @override
  String? get jibun;
  @override
  String? get jiga;
  @override
  @JsonKey(name: 'gosi_year')
  String? get gosiYear;
  @override
  @JsonKey(ignore: true)
  _$$ParcelPropertiesImplCopyWith<_$ParcelPropertiesImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ParcelBoundaryResponse _$ParcelBoundaryResponseFromJson(
    Map<String, dynamic> json) {
  return _ParcelBoundaryResponse.fromJson(json);
}

/// @nodoc
mixin _$ParcelBoundaryResponse {
  bool get success => throw _privateConstructorUsedError;
  ParcelGeometry? get geometry => throw _privateConstructorUsedError;
  ParcelProperties? get properties => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ParcelBoundaryResponseCopyWith<ParcelBoundaryResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ParcelBoundaryResponseCopyWith<$Res> {
  factory $ParcelBoundaryResponseCopyWith(ParcelBoundaryResponse value,
          $Res Function(ParcelBoundaryResponse) then) =
      _$ParcelBoundaryResponseCopyWithImpl<$Res, ParcelBoundaryResponse>;
  @useResult
  $Res call(
      {bool success,
      ParcelGeometry? geometry,
      ParcelProperties? properties,
      String? error});

  $ParcelGeometryCopyWith<$Res>? get geometry;
  $ParcelPropertiesCopyWith<$Res>? get properties;
}

/// @nodoc
class _$ParcelBoundaryResponseCopyWithImpl<$Res,
        $Val extends ParcelBoundaryResponse>
    implements $ParcelBoundaryResponseCopyWith<$Res> {
  _$ParcelBoundaryResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? geometry = freezed,
    Object? properties = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      geometry: freezed == geometry
          ? _value.geometry
          : geometry // ignore: cast_nullable_to_non_nullable
              as ParcelGeometry?,
      properties: freezed == properties
          ? _value.properties
          : properties // ignore: cast_nullable_to_non_nullable
              as ParcelProperties?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ParcelGeometryCopyWith<$Res>? get geometry {
    if (_value.geometry == null) {
      return null;
    }

    return $ParcelGeometryCopyWith<$Res>(_value.geometry!, (value) {
      return _then(_value.copyWith(geometry: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $ParcelPropertiesCopyWith<$Res>? get properties {
    if (_value.properties == null) {
      return null;
    }

    return $ParcelPropertiesCopyWith<$Res>(_value.properties!, (value) {
      return _then(_value.copyWith(properties: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ParcelBoundaryResponseImplCopyWith<$Res>
    implements $ParcelBoundaryResponseCopyWith<$Res> {
  factory _$$ParcelBoundaryResponseImplCopyWith(
          _$ParcelBoundaryResponseImpl value,
          $Res Function(_$ParcelBoundaryResponseImpl) then) =
      __$$ParcelBoundaryResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool success,
      ParcelGeometry? geometry,
      ParcelProperties? properties,
      String? error});

  @override
  $ParcelGeometryCopyWith<$Res>? get geometry;
  @override
  $ParcelPropertiesCopyWith<$Res>? get properties;
}

/// @nodoc
class __$$ParcelBoundaryResponseImplCopyWithImpl<$Res>
    extends _$ParcelBoundaryResponseCopyWithImpl<$Res,
        _$ParcelBoundaryResponseImpl>
    implements _$$ParcelBoundaryResponseImplCopyWith<$Res> {
  __$$ParcelBoundaryResponseImplCopyWithImpl(
      _$ParcelBoundaryResponseImpl _value,
      $Res Function(_$ParcelBoundaryResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? geometry = freezed,
    Object? properties = freezed,
    Object? error = freezed,
  }) {
    return _then(_$ParcelBoundaryResponseImpl(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      geometry: freezed == geometry
          ? _value.geometry
          : geometry // ignore: cast_nullable_to_non_nullable
              as ParcelGeometry?,
      properties: freezed == properties
          ? _value.properties
          : properties // ignore: cast_nullable_to_non_nullable
              as ParcelProperties?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ParcelBoundaryResponseImpl implements _ParcelBoundaryResponse {
  const _$ParcelBoundaryResponseImpl(
      {required this.success, this.geometry, this.properties, this.error});

  factory _$ParcelBoundaryResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$ParcelBoundaryResponseImplFromJson(json);

  @override
  final bool success;
  @override
  final ParcelGeometry? geometry;
  @override
  final ParcelProperties? properties;
  @override
  final String? error;

  @override
  String toString() {
    return 'ParcelBoundaryResponse(success: $success, geometry: $geometry, properties: $properties, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ParcelBoundaryResponseImpl &&
            (identical(other.success, success) || other.success == success) &&
            (identical(other.geometry, geometry) ||
                other.geometry == geometry) &&
            (identical(other.properties, properties) ||
                other.properties == properties) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, success, geometry, properties, error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ParcelBoundaryResponseImplCopyWith<_$ParcelBoundaryResponseImpl>
      get copyWith => __$$ParcelBoundaryResponseImplCopyWithImpl<
          _$ParcelBoundaryResponseImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ParcelBoundaryResponseImplToJson(
      this,
    );
  }
}

abstract class _ParcelBoundaryResponse implements ParcelBoundaryResponse {
  const factory _ParcelBoundaryResponse(
      {required final bool success,
      final ParcelGeometry? geometry,
      final ParcelProperties? properties,
      final String? error}) = _$ParcelBoundaryResponseImpl;

  factory _ParcelBoundaryResponse.fromJson(Map<String, dynamic> json) =
      _$ParcelBoundaryResponseImpl.fromJson;

  @override
  bool get success;
  @override
  ParcelGeometry? get geometry;
  @override
  ParcelProperties? get properties;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$ParcelBoundaryResponseImplCopyWith<_$ParcelBoundaryResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}

GeocodingResponse _$GeocodingResponseFromJson(Map<String, dynamic> json) {
  return _GeocodingResponse.fromJson(json);
}

/// @nodoc
mixin _$GeocodingResponse {
  bool get success => throw _privateConstructorUsedError;
  double? get lat => throw _privateConstructorUsedError;
  double? get lng => throw _privateConstructorUsedError;
  String? get address => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $GeocodingResponseCopyWith<GeocodingResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $GeocodingResponseCopyWith<$Res> {
  factory $GeocodingResponseCopyWith(
          GeocodingResponse value, $Res Function(GeocodingResponse) then) =
      _$GeocodingResponseCopyWithImpl<$Res, GeocodingResponse>;
  @useResult
  $Res call(
      {bool success, double? lat, double? lng, String? address, String? error});
}

/// @nodoc
class _$GeocodingResponseCopyWithImpl<$Res, $Val extends GeocodingResponse>
    implements $GeocodingResponseCopyWith<$Res> {
  _$GeocodingResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? lat = freezed,
    Object? lng = freezed,
    Object? address = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      lat: freezed == lat
          ? _value.lat
          : lat // ignore: cast_nullable_to_non_nullable
              as double?,
      lng: freezed == lng
          ? _value.lng
          : lng // ignore: cast_nullable_to_non_nullable
              as double?,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$GeocodingResponseImplCopyWith<$Res>
    implements $GeocodingResponseCopyWith<$Res> {
  factory _$$GeocodingResponseImplCopyWith(_$GeocodingResponseImpl value,
          $Res Function(_$GeocodingResponseImpl) then) =
      __$$GeocodingResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool success, double? lat, double? lng, String? address, String? error});
}

/// @nodoc
class __$$GeocodingResponseImplCopyWithImpl<$Res>
    extends _$GeocodingResponseCopyWithImpl<$Res, _$GeocodingResponseImpl>
    implements _$$GeocodingResponseImplCopyWith<$Res> {
  __$$GeocodingResponseImplCopyWithImpl(_$GeocodingResponseImpl _value,
      $Res Function(_$GeocodingResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? lat = freezed,
    Object? lng = freezed,
    Object? address = freezed,
    Object? error = freezed,
  }) {
    return _then(_$GeocodingResponseImpl(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      lat: freezed == lat
          ? _value.lat
          : lat // ignore: cast_nullable_to_non_nullable
              as double?,
      lng: freezed == lng
          ? _value.lng
          : lng // ignore: cast_nullable_to_non_nullable
              as double?,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
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
class _$GeocodingResponseImpl implements _GeocodingResponse {
  const _$GeocodingResponseImpl(
      {required this.success, this.lat, this.lng, this.address, this.error});

  factory _$GeocodingResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$GeocodingResponseImplFromJson(json);

  @override
  final bool success;
  @override
  final double? lat;
  @override
  final double? lng;
  @override
  final String? address;
  @override
  final String? error;

  @override
  String toString() {
    return 'GeocodingResponse(success: $success, lat: $lat, lng: $lng, address: $address, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$GeocodingResponseImpl &&
            (identical(other.success, success) || other.success == success) &&
            (identical(other.lat, lat) || other.lat == lat) &&
            (identical(other.lng, lng) || other.lng == lng) &&
            (identical(other.address, address) || other.address == address) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, success, lat, lng, address, error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$GeocodingResponseImplCopyWith<_$GeocodingResponseImpl> get copyWith =>
      __$$GeocodingResponseImplCopyWithImpl<_$GeocodingResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$GeocodingResponseImplToJson(
      this,
    );
  }
}

abstract class _GeocodingResponse implements GeocodingResponse {
  const factory _GeocodingResponse(
      {required final bool success,
      final double? lat,
      final double? lng,
      final String? address,
      final String? error}) = _$GeocodingResponseImpl;

  factory _GeocodingResponse.fromJson(Map<String, dynamic> json) =
      _$GeocodingResponseImpl.fromJson;

  @override
  bool get success;
  @override
  double? get lat;
  @override
  double? get lng;
  @override
  String? get address;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$GeocodingResponseImplCopyWith<_$GeocodingResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
