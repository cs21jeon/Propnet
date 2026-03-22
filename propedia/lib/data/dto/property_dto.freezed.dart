// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'property_dto.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

PropertyRecord _$PropertyRecordFromJson(Map<String, dynamic> json) {
  return _PropertyRecord.fromJson(json);
}

/// @nodoc
mixin _$PropertyRecord {
  String get id => throw _privateConstructorUsedError;
  PropertyFields get fields => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PropertyRecordCopyWith<PropertyRecord> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PropertyRecordCopyWith<$Res> {
  factory $PropertyRecordCopyWith(
          PropertyRecord value, $Res Function(PropertyRecord) then) =
      _$PropertyRecordCopyWithImpl<$Res, PropertyRecord>;
  @useResult
  $Res call({String id, PropertyFields fields});

  $PropertyFieldsCopyWith<$Res> get fields;
}

/// @nodoc
class _$PropertyRecordCopyWithImpl<$Res, $Val extends PropertyRecord>
    implements $PropertyRecordCopyWith<$Res> {
  _$PropertyRecordCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? fields = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      fields: null == fields
          ? _value.fields
          : fields // ignore: cast_nullable_to_non_nullable
              as PropertyFields,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $PropertyFieldsCopyWith<$Res> get fields {
    return $PropertyFieldsCopyWith<$Res>(_value.fields, (value) {
      return _then(_value.copyWith(fields: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$PropertyRecordImplCopyWith<$Res>
    implements $PropertyRecordCopyWith<$Res> {
  factory _$$PropertyRecordImplCopyWith(_$PropertyRecordImpl value,
          $Res Function(_$PropertyRecordImpl) then) =
      __$$PropertyRecordImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String id, PropertyFields fields});

  @override
  $PropertyFieldsCopyWith<$Res> get fields;
}

/// @nodoc
class __$$PropertyRecordImplCopyWithImpl<$Res>
    extends _$PropertyRecordCopyWithImpl<$Res, _$PropertyRecordImpl>
    implements _$$PropertyRecordImplCopyWith<$Res> {
  __$$PropertyRecordImplCopyWithImpl(
      _$PropertyRecordImpl _value, $Res Function(_$PropertyRecordImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? fields = null,
  }) {
    return _then(_$PropertyRecordImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      fields: null == fields
          ? _value.fields
          : fields // ignore: cast_nullable_to_non_nullable
              as PropertyFields,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PropertyRecordImpl extends _PropertyRecord {
  const _$PropertyRecordImpl({required this.id, required this.fields})
      : super._();

  factory _$PropertyRecordImpl.fromJson(Map<String, dynamic> json) =>
      _$$PropertyRecordImplFromJson(json);

  @override
  final String id;
  @override
  final PropertyFields fields;

  @override
  String toString() {
    return 'PropertyRecord(id: $id, fields: $fields)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PropertyRecordImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.fields, fields) || other.fields == fields));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, id, fields);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PropertyRecordImplCopyWith<_$PropertyRecordImpl> get copyWith =>
      __$$PropertyRecordImplCopyWithImpl<_$PropertyRecordImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PropertyRecordImplToJson(
      this,
    );
  }
}

abstract class _PropertyRecord extends PropertyRecord {
  const factory _PropertyRecord(
      {required final String id,
      required final PropertyFields fields}) = _$PropertyRecordImpl;
  const _PropertyRecord._() : super._();

  factory _PropertyRecord.fromJson(Map<String, dynamic> json) =
      _$PropertyRecordImpl.fromJson;

  @override
  String get id;
  @override
  PropertyFields get fields;
  @override
  @JsonKey(ignore: true)
  _$$PropertyRecordImplCopyWith<_$PropertyRecordImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PropertyFields _$PropertyFieldsFromJson(Map<String, dynamic> json) {
  return _PropertyFields.fromJson(json);
}

/// @nodoc
mixin _$PropertyFields {
// 주소
  @JsonKey(name: '지번 주소')
  String? get address => throw _privateConstructorUsedError;
  @JsonKey(name: '도로명주소')
  String? get roadAddress => throw _privateConstructorUsedError; // 가격 정보
  @JsonKey(name: '매가(만원)', fromJson: _intFromDynamic)
  int? get price => throw _privateConstructorUsedError;
  @JsonKey(name: '보증금(만원)', fromJson: _intFromDynamic)
  int? get deposit => throw _privateConstructorUsedError;
  @JsonKey(name: '월세(만원)', fromJson: _intFromDynamic)
  int? get monthlyRent => throw _privateConstructorUsedError;
  @JsonKey(name: '융자(만원)', fromJson: _intFromDynamic)
  int? get loan => throw _privateConstructorUsedError;
  @JsonKey(name: '실투자금', fromJson: _intFromDynamic)
  int? get investment => throw _privateConstructorUsedError;
  @JsonKey(name: '융자제외수익률(%)', fromJson: _doubleFromDynamic)
  double? get yieldRate => throw _privateConstructorUsedError;
  @JsonKey(name: '감정가(만원,랜드북)', fromJson: _intFromDynamic)
  int? get appraisedValue => throw _privateConstructorUsedError;
  @JsonKey(name: '감정가율(%)', fromJson: _doubleFromDynamic)
  double? get appraisalRate => throw _privateConstructorUsedError; // 면적 정보
  @JsonKey(name: '토지면적(㎡)', fromJson: _doubleFromDynamic)
  double? get landArea => throw _privateConstructorUsedError;
  @JsonKey(name: '연면적(㎡)', fromJson: _doubleFromDynamic)
  double? get totalFloorArea => throw _privateConstructorUsedError;
  @JsonKey(name: '건축면적(㎡)', fromJson: _doubleFromDynamic)
  double? get buildingArea => throw _privateConstructorUsedError;
  @JsonKey(name: '용적률산정용연면적(㎡)', fromJson: _doubleFromDynamic)
  double? get farArea => throw _privateConstructorUsedError; // 건물 정보
  @JsonKey(name: '층수')
  String? get floors => throw _privateConstructorUsedError;
  @JsonKey(name: '주용도')
  String? get mainUsage => throw _privateConstructorUsedError;
  @JsonKey(name: '기타용도')
  String? get etcUsage => throw _privateConstructorUsedError;
  @JsonKey(name: '주구조')
  String? get structure => throw _privateConstructorUsedError;
  @JsonKey(name: '지붕')
  String? get roof => throw _privateConstructorUsedError;
  @JsonKey(name: '사용승인일')
  String? get approvalDate => throw _privateConstructorUsedError;
  @JsonKey(name: '건물명')
  String? get buildingName => throw _privateConstructorUsedError;
  @JsonKey(name: '건물구성')
  String? get buildingComposition => throw _privateConstructorUsedError;
  @JsonKey(name: '건폐율(%)', fromJson: _doubleFromDynamic)
  double? get buildingCoverageRatio => throw _privateConstructorUsedError;
  @JsonKey(name: '용적률(%)', fromJson: _doubleFromDynamic)
  double? get floorAreaRatio => throw _privateConstructorUsedError;
  @JsonKey(name: '높이(m)', fromJson: _doubleFromDynamic)
  double? get height => throw _privateConstructorUsedError; // 설비
  @JsonKey(name: '주차대수', fromJson: _intFromDynamic)
  int? get parkingCount => throw _privateConstructorUsedError;
  @JsonKey(name: '승강기수', fromJson: _intFromDynamic)
  int? get elevatorCount => throw _privateConstructorUsedError;
  @JsonKey(name: '세대/가구/호')
  String? get householdInfo => throw _privateConstructorUsedError; // 위치 정보
  @JsonKey(name: '용도지역')
  String? get zoning => throw _privateConstructorUsedError;
  @JsonKey(name: '공시지가(원/㎡)', fromJson: _intFromDynamic)
  int? get landPrice => throw _privateConstructorUsedError;
  @JsonKey(name: '인접역')
  String? get nearStation => throw _privateConstructorUsedError;
  @JsonKey(name: '거리(m)', fromJson: _intFromDynamic)
  int? get stationDistance => throw _privateConstructorUsedError; // 상태 및 링크
  @JsonKey(name: '현황', fromJson: _statusFromDynamic)
  List<String>? get status => throw _privateConstructorUsedError;
  @JsonKey(name: '광고(자동완성)')
  String? get description => throw _privateConstructorUsedError;
  @JsonKey(name: '지도')
  String? get mapLink => throw _privateConstructorUsedError;
  @JsonKey(name: '사진링크')
  String? get photoLink => throw _privateConstructorUsedError;
  @JsonKey(name: '디스코광고')
  String? get discoLink =>
      throw _privateConstructorUsedError; // 이미지 (Airtable attachment)
  @JsonKey(name: '대표사진')
  List<AirtableAttachment>? get representativePhoto =>
      throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PropertyFieldsCopyWith<PropertyFields> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PropertyFieldsCopyWith<$Res> {
  factory $PropertyFieldsCopyWith(
          PropertyFields value, $Res Function(PropertyFields) then) =
      _$PropertyFieldsCopyWithImpl<$Res, PropertyFields>;
  @useResult
  $Res call(
      {@JsonKey(name: '지번 주소') String? address,
      @JsonKey(name: '도로명주소') String? roadAddress,
      @JsonKey(name: '매가(만원)', fromJson: _intFromDynamic) int? price,
      @JsonKey(name: '보증금(만원)', fromJson: _intFromDynamic) int? deposit,
      @JsonKey(name: '월세(만원)', fromJson: _intFromDynamic) int? monthlyRent,
      @JsonKey(name: '융자(만원)', fromJson: _intFromDynamic) int? loan,
      @JsonKey(name: '실투자금', fromJson: _intFromDynamic) int? investment,
      @JsonKey(name: '융자제외수익률(%)', fromJson: _doubleFromDynamic)
      double? yieldRate,
      @JsonKey(name: '감정가(만원,랜드북)', fromJson: _intFromDynamic)
      int? appraisedValue,
      @JsonKey(name: '감정가율(%)', fromJson: _doubleFromDynamic)
      double? appraisalRate,
      @JsonKey(name: '토지면적(㎡)', fromJson: _doubleFromDynamic) double? landArea,
      @JsonKey(name: '연면적(㎡)', fromJson: _doubleFromDynamic)
      double? totalFloorArea,
      @JsonKey(name: '건축면적(㎡)', fromJson: _doubleFromDynamic)
      double? buildingArea,
      @JsonKey(name: '용적률산정용연면적(㎡)', fromJson: _doubleFromDynamic)
      double? farArea,
      @JsonKey(name: '층수') String? floors,
      @JsonKey(name: '주용도') String? mainUsage,
      @JsonKey(name: '기타용도') String? etcUsage,
      @JsonKey(name: '주구조') String? structure,
      @JsonKey(name: '지붕') String? roof,
      @JsonKey(name: '사용승인일') String? approvalDate,
      @JsonKey(name: '건물명') String? buildingName,
      @JsonKey(name: '건물구성') String? buildingComposition,
      @JsonKey(name: '건폐율(%)', fromJson: _doubleFromDynamic)
      double? buildingCoverageRatio,
      @JsonKey(name: '용적률(%)', fromJson: _doubleFromDynamic)
      double? floorAreaRatio,
      @JsonKey(name: '높이(m)', fromJson: _doubleFromDynamic) double? height,
      @JsonKey(name: '주차대수', fromJson: _intFromDynamic) int? parkingCount,
      @JsonKey(name: '승강기수', fromJson: _intFromDynamic) int? elevatorCount,
      @JsonKey(name: '세대/가구/호') String? householdInfo,
      @JsonKey(name: '용도지역') String? zoning,
      @JsonKey(name: '공시지가(원/㎡)', fromJson: _intFromDynamic) int? landPrice,
      @JsonKey(name: '인접역') String? nearStation,
      @JsonKey(name: '거리(m)', fromJson: _intFromDynamic) int? stationDistance,
      @JsonKey(name: '현황', fromJson: _statusFromDynamic) List<String>? status,
      @JsonKey(name: '광고(자동완성)') String? description,
      @JsonKey(name: '지도') String? mapLink,
      @JsonKey(name: '사진링크') String? photoLink,
      @JsonKey(name: '디스코광고') String? discoLink,
      @JsonKey(name: '대표사진') List<AirtableAttachment>? representativePhoto});
}

/// @nodoc
class _$PropertyFieldsCopyWithImpl<$Res, $Val extends PropertyFields>
    implements $PropertyFieldsCopyWith<$Res> {
  _$PropertyFieldsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? address = freezed,
    Object? roadAddress = freezed,
    Object? price = freezed,
    Object? deposit = freezed,
    Object? monthlyRent = freezed,
    Object? loan = freezed,
    Object? investment = freezed,
    Object? yieldRate = freezed,
    Object? appraisedValue = freezed,
    Object? appraisalRate = freezed,
    Object? landArea = freezed,
    Object? totalFloorArea = freezed,
    Object? buildingArea = freezed,
    Object? farArea = freezed,
    Object? floors = freezed,
    Object? mainUsage = freezed,
    Object? etcUsage = freezed,
    Object? structure = freezed,
    Object? roof = freezed,
    Object? approvalDate = freezed,
    Object? buildingName = freezed,
    Object? buildingComposition = freezed,
    Object? buildingCoverageRatio = freezed,
    Object? floorAreaRatio = freezed,
    Object? height = freezed,
    Object? parkingCount = freezed,
    Object? elevatorCount = freezed,
    Object? householdInfo = freezed,
    Object? zoning = freezed,
    Object? landPrice = freezed,
    Object? nearStation = freezed,
    Object? stationDistance = freezed,
    Object? status = freezed,
    Object? description = freezed,
    Object? mapLink = freezed,
    Object? photoLink = freezed,
    Object? discoLink = freezed,
    Object? representativePhoto = freezed,
  }) {
    return _then(_value.copyWith(
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      price: freezed == price
          ? _value.price
          : price // ignore: cast_nullable_to_non_nullable
              as int?,
      deposit: freezed == deposit
          ? _value.deposit
          : deposit // ignore: cast_nullable_to_non_nullable
              as int?,
      monthlyRent: freezed == monthlyRent
          ? _value.monthlyRent
          : monthlyRent // ignore: cast_nullable_to_non_nullable
              as int?,
      loan: freezed == loan
          ? _value.loan
          : loan // ignore: cast_nullable_to_non_nullable
              as int?,
      investment: freezed == investment
          ? _value.investment
          : investment // ignore: cast_nullable_to_non_nullable
              as int?,
      yieldRate: freezed == yieldRate
          ? _value.yieldRate
          : yieldRate // ignore: cast_nullable_to_non_nullable
              as double?,
      appraisedValue: freezed == appraisedValue
          ? _value.appraisedValue
          : appraisedValue // ignore: cast_nullable_to_non_nullable
              as int?,
      appraisalRate: freezed == appraisalRate
          ? _value.appraisalRate
          : appraisalRate // ignore: cast_nullable_to_non_nullable
              as double?,
      landArea: freezed == landArea
          ? _value.landArea
          : landArea // ignore: cast_nullable_to_non_nullable
              as double?,
      totalFloorArea: freezed == totalFloorArea
          ? _value.totalFloorArea
          : totalFloorArea // ignore: cast_nullable_to_non_nullable
              as double?,
      buildingArea: freezed == buildingArea
          ? _value.buildingArea
          : buildingArea // ignore: cast_nullable_to_non_nullable
              as double?,
      farArea: freezed == farArea
          ? _value.farArea
          : farArea // ignore: cast_nullable_to_non_nullable
              as double?,
      floors: freezed == floors
          ? _value.floors
          : floors // ignore: cast_nullable_to_non_nullable
              as String?,
      mainUsage: freezed == mainUsage
          ? _value.mainUsage
          : mainUsage // ignore: cast_nullable_to_non_nullable
              as String?,
      etcUsage: freezed == etcUsage
          ? _value.etcUsage
          : etcUsage // ignore: cast_nullable_to_non_nullable
              as String?,
      structure: freezed == structure
          ? _value.structure
          : structure // ignore: cast_nullable_to_non_nullable
              as String?,
      roof: freezed == roof
          ? _value.roof
          : roof // ignore: cast_nullable_to_non_nullable
              as String?,
      approvalDate: freezed == approvalDate
          ? _value.approvalDate
          : approvalDate // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingName: freezed == buildingName
          ? _value.buildingName
          : buildingName // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingComposition: freezed == buildingComposition
          ? _value.buildingComposition
          : buildingComposition // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingCoverageRatio: freezed == buildingCoverageRatio
          ? _value.buildingCoverageRatio
          : buildingCoverageRatio // ignore: cast_nullable_to_non_nullable
              as double?,
      floorAreaRatio: freezed == floorAreaRatio
          ? _value.floorAreaRatio
          : floorAreaRatio // ignore: cast_nullable_to_non_nullable
              as double?,
      height: freezed == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as double?,
      parkingCount: freezed == parkingCount
          ? _value.parkingCount
          : parkingCount // ignore: cast_nullable_to_non_nullable
              as int?,
      elevatorCount: freezed == elevatorCount
          ? _value.elevatorCount
          : elevatorCount // ignore: cast_nullable_to_non_nullable
              as int?,
      householdInfo: freezed == householdInfo
          ? _value.householdInfo
          : householdInfo // ignore: cast_nullable_to_non_nullable
              as String?,
      zoning: freezed == zoning
          ? _value.zoning
          : zoning // ignore: cast_nullable_to_non_nullable
              as String?,
      landPrice: freezed == landPrice
          ? _value.landPrice
          : landPrice // ignore: cast_nullable_to_non_nullable
              as int?,
      nearStation: freezed == nearStation
          ? _value.nearStation
          : nearStation // ignore: cast_nullable_to_non_nullable
              as String?,
      stationDistance: freezed == stationDistance
          ? _value.stationDistance
          : stationDistance // ignore: cast_nullable_to_non_nullable
              as int?,
      status: freezed == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      mapLink: freezed == mapLink
          ? _value.mapLink
          : mapLink // ignore: cast_nullable_to_non_nullable
              as String?,
      photoLink: freezed == photoLink
          ? _value.photoLink
          : photoLink // ignore: cast_nullable_to_non_nullable
              as String?,
      discoLink: freezed == discoLink
          ? _value.discoLink
          : discoLink // ignore: cast_nullable_to_non_nullable
              as String?,
      representativePhoto: freezed == representativePhoto
          ? _value.representativePhoto
          : representativePhoto // ignore: cast_nullable_to_non_nullable
              as List<AirtableAttachment>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PropertyFieldsImplCopyWith<$Res>
    implements $PropertyFieldsCopyWith<$Res> {
  factory _$$PropertyFieldsImplCopyWith(_$PropertyFieldsImpl value,
          $Res Function(_$PropertyFieldsImpl) then) =
      __$$PropertyFieldsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: '지번 주소') String? address,
      @JsonKey(name: '도로명주소') String? roadAddress,
      @JsonKey(name: '매가(만원)', fromJson: _intFromDynamic) int? price,
      @JsonKey(name: '보증금(만원)', fromJson: _intFromDynamic) int? deposit,
      @JsonKey(name: '월세(만원)', fromJson: _intFromDynamic) int? monthlyRent,
      @JsonKey(name: '융자(만원)', fromJson: _intFromDynamic) int? loan,
      @JsonKey(name: '실투자금', fromJson: _intFromDynamic) int? investment,
      @JsonKey(name: '융자제외수익률(%)', fromJson: _doubleFromDynamic)
      double? yieldRate,
      @JsonKey(name: '감정가(만원,랜드북)', fromJson: _intFromDynamic)
      int? appraisedValue,
      @JsonKey(name: '감정가율(%)', fromJson: _doubleFromDynamic)
      double? appraisalRate,
      @JsonKey(name: '토지면적(㎡)', fromJson: _doubleFromDynamic) double? landArea,
      @JsonKey(name: '연면적(㎡)', fromJson: _doubleFromDynamic)
      double? totalFloorArea,
      @JsonKey(name: '건축면적(㎡)', fromJson: _doubleFromDynamic)
      double? buildingArea,
      @JsonKey(name: '용적률산정용연면적(㎡)', fromJson: _doubleFromDynamic)
      double? farArea,
      @JsonKey(name: '층수') String? floors,
      @JsonKey(name: '주용도') String? mainUsage,
      @JsonKey(name: '기타용도') String? etcUsage,
      @JsonKey(name: '주구조') String? structure,
      @JsonKey(name: '지붕') String? roof,
      @JsonKey(name: '사용승인일') String? approvalDate,
      @JsonKey(name: '건물명') String? buildingName,
      @JsonKey(name: '건물구성') String? buildingComposition,
      @JsonKey(name: '건폐율(%)', fromJson: _doubleFromDynamic)
      double? buildingCoverageRatio,
      @JsonKey(name: '용적률(%)', fromJson: _doubleFromDynamic)
      double? floorAreaRatio,
      @JsonKey(name: '높이(m)', fromJson: _doubleFromDynamic) double? height,
      @JsonKey(name: '주차대수', fromJson: _intFromDynamic) int? parkingCount,
      @JsonKey(name: '승강기수', fromJson: _intFromDynamic) int? elevatorCount,
      @JsonKey(name: '세대/가구/호') String? householdInfo,
      @JsonKey(name: '용도지역') String? zoning,
      @JsonKey(name: '공시지가(원/㎡)', fromJson: _intFromDynamic) int? landPrice,
      @JsonKey(name: '인접역') String? nearStation,
      @JsonKey(name: '거리(m)', fromJson: _intFromDynamic) int? stationDistance,
      @JsonKey(name: '현황', fromJson: _statusFromDynamic) List<String>? status,
      @JsonKey(name: '광고(자동완성)') String? description,
      @JsonKey(name: '지도') String? mapLink,
      @JsonKey(name: '사진링크') String? photoLink,
      @JsonKey(name: '디스코광고') String? discoLink,
      @JsonKey(name: '대표사진') List<AirtableAttachment>? representativePhoto});
}

/// @nodoc
class __$$PropertyFieldsImplCopyWithImpl<$Res>
    extends _$PropertyFieldsCopyWithImpl<$Res, _$PropertyFieldsImpl>
    implements _$$PropertyFieldsImplCopyWith<$Res> {
  __$$PropertyFieldsImplCopyWithImpl(
      _$PropertyFieldsImpl _value, $Res Function(_$PropertyFieldsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? address = freezed,
    Object? roadAddress = freezed,
    Object? price = freezed,
    Object? deposit = freezed,
    Object? monthlyRent = freezed,
    Object? loan = freezed,
    Object? investment = freezed,
    Object? yieldRate = freezed,
    Object? appraisedValue = freezed,
    Object? appraisalRate = freezed,
    Object? landArea = freezed,
    Object? totalFloorArea = freezed,
    Object? buildingArea = freezed,
    Object? farArea = freezed,
    Object? floors = freezed,
    Object? mainUsage = freezed,
    Object? etcUsage = freezed,
    Object? structure = freezed,
    Object? roof = freezed,
    Object? approvalDate = freezed,
    Object? buildingName = freezed,
    Object? buildingComposition = freezed,
    Object? buildingCoverageRatio = freezed,
    Object? floorAreaRatio = freezed,
    Object? height = freezed,
    Object? parkingCount = freezed,
    Object? elevatorCount = freezed,
    Object? householdInfo = freezed,
    Object? zoning = freezed,
    Object? landPrice = freezed,
    Object? nearStation = freezed,
    Object? stationDistance = freezed,
    Object? status = freezed,
    Object? description = freezed,
    Object? mapLink = freezed,
    Object? photoLink = freezed,
    Object? discoLink = freezed,
    Object? representativePhoto = freezed,
  }) {
    return _then(_$PropertyFieldsImpl(
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      price: freezed == price
          ? _value.price
          : price // ignore: cast_nullable_to_non_nullable
              as int?,
      deposit: freezed == deposit
          ? _value.deposit
          : deposit // ignore: cast_nullable_to_non_nullable
              as int?,
      monthlyRent: freezed == monthlyRent
          ? _value.monthlyRent
          : monthlyRent // ignore: cast_nullable_to_non_nullable
              as int?,
      loan: freezed == loan
          ? _value.loan
          : loan // ignore: cast_nullable_to_non_nullable
              as int?,
      investment: freezed == investment
          ? _value.investment
          : investment // ignore: cast_nullable_to_non_nullable
              as int?,
      yieldRate: freezed == yieldRate
          ? _value.yieldRate
          : yieldRate // ignore: cast_nullable_to_non_nullable
              as double?,
      appraisedValue: freezed == appraisedValue
          ? _value.appraisedValue
          : appraisedValue // ignore: cast_nullable_to_non_nullable
              as int?,
      appraisalRate: freezed == appraisalRate
          ? _value.appraisalRate
          : appraisalRate // ignore: cast_nullable_to_non_nullable
              as double?,
      landArea: freezed == landArea
          ? _value.landArea
          : landArea // ignore: cast_nullable_to_non_nullable
              as double?,
      totalFloorArea: freezed == totalFloorArea
          ? _value.totalFloorArea
          : totalFloorArea // ignore: cast_nullable_to_non_nullable
              as double?,
      buildingArea: freezed == buildingArea
          ? _value.buildingArea
          : buildingArea // ignore: cast_nullable_to_non_nullable
              as double?,
      farArea: freezed == farArea
          ? _value.farArea
          : farArea // ignore: cast_nullable_to_non_nullable
              as double?,
      floors: freezed == floors
          ? _value.floors
          : floors // ignore: cast_nullable_to_non_nullable
              as String?,
      mainUsage: freezed == mainUsage
          ? _value.mainUsage
          : mainUsage // ignore: cast_nullable_to_non_nullable
              as String?,
      etcUsage: freezed == etcUsage
          ? _value.etcUsage
          : etcUsage // ignore: cast_nullable_to_non_nullable
              as String?,
      structure: freezed == structure
          ? _value.structure
          : structure // ignore: cast_nullable_to_non_nullable
              as String?,
      roof: freezed == roof
          ? _value.roof
          : roof // ignore: cast_nullable_to_non_nullable
              as String?,
      approvalDate: freezed == approvalDate
          ? _value.approvalDate
          : approvalDate // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingName: freezed == buildingName
          ? _value.buildingName
          : buildingName // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingComposition: freezed == buildingComposition
          ? _value.buildingComposition
          : buildingComposition // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingCoverageRatio: freezed == buildingCoverageRatio
          ? _value.buildingCoverageRatio
          : buildingCoverageRatio // ignore: cast_nullable_to_non_nullable
              as double?,
      floorAreaRatio: freezed == floorAreaRatio
          ? _value.floorAreaRatio
          : floorAreaRatio // ignore: cast_nullable_to_non_nullable
              as double?,
      height: freezed == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as double?,
      parkingCount: freezed == parkingCount
          ? _value.parkingCount
          : parkingCount // ignore: cast_nullable_to_non_nullable
              as int?,
      elevatorCount: freezed == elevatorCount
          ? _value.elevatorCount
          : elevatorCount // ignore: cast_nullable_to_non_nullable
              as int?,
      householdInfo: freezed == householdInfo
          ? _value.householdInfo
          : householdInfo // ignore: cast_nullable_to_non_nullable
              as String?,
      zoning: freezed == zoning
          ? _value.zoning
          : zoning // ignore: cast_nullable_to_non_nullable
              as String?,
      landPrice: freezed == landPrice
          ? _value.landPrice
          : landPrice // ignore: cast_nullable_to_non_nullable
              as int?,
      nearStation: freezed == nearStation
          ? _value.nearStation
          : nearStation // ignore: cast_nullable_to_non_nullable
              as String?,
      stationDistance: freezed == stationDistance
          ? _value.stationDistance
          : stationDistance // ignore: cast_nullable_to_non_nullable
              as int?,
      status: freezed == status
          ? _value._status
          : status // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      mapLink: freezed == mapLink
          ? _value.mapLink
          : mapLink // ignore: cast_nullable_to_non_nullable
              as String?,
      photoLink: freezed == photoLink
          ? _value.photoLink
          : photoLink // ignore: cast_nullable_to_non_nullable
              as String?,
      discoLink: freezed == discoLink
          ? _value.discoLink
          : discoLink // ignore: cast_nullable_to_non_nullable
              as String?,
      representativePhoto: freezed == representativePhoto
          ? _value._representativePhoto
          : representativePhoto // ignore: cast_nullable_to_non_nullable
              as List<AirtableAttachment>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PropertyFieldsImpl implements _PropertyFields {
  const _$PropertyFieldsImpl(
      {@JsonKey(name: '지번 주소') this.address,
      @JsonKey(name: '도로명주소') this.roadAddress,
      @JsonKey(name: '매가(만원)', fromJson: _intFromDynamic) this.price,
      @JsonKey(name: '보증금(만원)', fromJson: _intFromDynamic) this.deposit,
      @JsonKey(name: '월세(만원)', fromJson: _intFromDynamic) this.monthlyRent,
      @JsonKey(name: '융자(만원)', fromJson: _intFromDynamic) this.loan,
      @JsonKey(name: '실투자금', fromJson: _intFromDynamic) this.investment,
      @JsonKey(name: '융자제외수익률(%)', fromJson: _doubleFromDynamic) this.yieldRate,
      @JsonKey(name: '감정가(만원,랜드북)', fromJson: _intFromDynamic)
      this.appraisedValue,
      @JsonKey(name: '감정가율(%)', fromJson: _doubleFromDynamic)
      this.appraisalRate,
      @JsonKey(name: '토지면적(㎡)', fromJson: _doubleFromDynamic) this.landArea,
      @JsonKey(name: '연면적(㎡)', fromJson: _doubleFromDynamic)
      this.totalFloorArea,
      @JsonKey(name: '건축면적(㎡)', fromJson: _doubleFromDynamic) this.buildingArea,
      @JsonKey(name: '용적률산정용연면적(㎡)', fromJson: _doubleFromDynamic) this.farArea,
      @JsonKey(name: '층수') this.floors,
      @JsonKey(name: '주용도') this.mainUsage,
      @JsonKey(name: '기타용도') this.etcUsage,
      @JsonKey(name: '주구조') this.structure,
      @JsonKey(name: '지붕') this.roof,
      @JsonKey(name: '사용승인일') this.approvalDate,
      @JsonKey(name: '건물명') this.buildingName,
      @JsonKey(name: '건물구성') this.buildingComposition,
      @JsonKey(name: '건폐율(%)', fromJson: _doubleFromDynamic)
      this.buildingCoverageRatio,
      @JsonKey(name: '용적률(%)', fromJson: _doubleFromDynamic)
      this.floorAreaRatio,
      @JsonKey(name: '높이(m)', fromJson: _doubleFromDynamic) this.height,
      @JsonKey(name: '주차대수', fromJson: _intFromDynamic) this.parkingCount,
      @JsonKey(name: '승강기수', fromJson: _intFromDynamic) this.elevatorCount,
      @JsonKey(name: '세대/가구/호') this.householdInfo,
      @JsonKey(name: '용도지역') this.zoning,
      @JsonKey(name: '공시지가(원/㎡)', fromJson: _intFromDynamic) this.landPrice,
      @JsonKey(name: '인접역') this.nearStation,
      @JsonKey(name: '거리(m)', fromJson: _intFromDynamic) this.stationDistance,
      @JsonKey(name: '현황', fromJson: _statusFromDynamic)
      final List<String>? status,
      @JsonKey(name: '광고(자동완성)') this.description,
      @JsonKey(name: '지도') this.mapLink,
      @JsonKey(name: '사진링크') this.photoLink,
      @JsonKey(name: '디스코광고') this.discoLink,
      @JsonKey(name: '대표사진')
      final List<AirtableAttachment>? representativePhoto})
      : _status = status,
        _representativePhoto = representativePhoto;

  factory _$PropertyFieldsImpl.fromJson(Map<String, dynamic> json) =>
      _$$PropertyFieldsImplFromJson(json);

// 주소
  @override
  @JsonKey(name: '지번 주소')
  final String? address;
  @override
  @JsonKey(name: '도로명주소')
  final String? roadAddress;
// 가격 정보
  @override
  @JsonKey(name: '매가(만원)', fromJson: _intFromDynamic)
  final int? price;
  @override
  @JsonKey(name: '보증금(만원)', fromJson: _intFromDynamic)
  final int? deposit;
  @override
  @JsonKey(name: '월세(만원)', fromJson: _intFromDynamic)
  final int? monthlyRent;
  @override
  @JsonKey(name: '융자(만원)', fromJson: _intFromDynamic)
  final int? loan;
  @override
  @JsonKey(name: '실투자금', fromJson: _intFromDynamic)
  final int? investment;
  @override
  @JsonKey(name: '융자제외수익률(%)', fromJson: _doubleFromDynamic)
  final double? yieldRate;
  @override
  @JsonKey(name: '감정가(만원,랜드북)', fromJson: _intFromDynamic)
  final int? appraisedValue;
  @override
  @JsonKey(name: '감정가율(%)', fromJson: _doubleFromDynamic)
  final double? appraisalRate;
// 면적 정보
  @override
  @JsonKey(name: '토지면적(㎡)', fromJson: _doubleFromDynamic)
  final double? landArea;
  @override
  @JsonKey(name: '연면적(㎡)', fromJson: _doubleFromDynamic)
  final double? totalFloorArea;
  @override
  @JsonKey(name: '건축면적(㎡)', fromJson: _doubleFromDynamic)
  final double? buildingArea;
  @override
  @JsonKey(name: '용적률산정용연면적(㎡)', fromJson: _doubleFromDynamic)
  final double? farArea;
// 건물 정보
  @override
  @JsonKey(name: '층수')
  final String? floors;
  @override
  @JsonKey(name: '주용도')
  final String? mainUsage;
  @override
  @JsonKey(name: '기타용도')
  final String? etcUsage;
  @override
  @JsonKey(name: '주구조')
  final String? structure;
  @override
  @JsonKey(name: '지붕')
  final String? roof;
  @override
  @JsonKey(name: '사용승인일')
  final String? approvalDate;
  @override
  @JsonKey(name: '건물명')
  final String? buildingName;
  @override
  @JsonKey(name: '건물구성')
  final String? buildingComposition;
  @override
  @JsonKey(name: '건폐율(%)', fromJson: _doubleFromDynamic)
  final double? buildingCoverageRatio;
  @override
  @JsonKey(name: '용적률(%)', fromJson: _doubleFromDynamic)
  final double? floorAreaRatio;
  @override
  @JsonKey(name: '높이(m)', fromJson: _doubleFromDynamic)
  final double? height;
// 설비
  @override
  @JsonKey(name: '주차대수', fromJson: _intFromDynamic)
  final int? parkingCount;
  @override
  @JsonKey(name: '승강기수', fromJson: _intFromDynamic)
  final int? elevatorCount;
  @override
  @JsonKey(name: '세대/가구/호')
  final String? householdInfo;
// 위치 정보
  @override
  @JsonKey(name: '용도지역')
  final String? zoning;
  @override
  @JsonKey(name: '공시지가(원/㎡)', fromJson: _intFromDynamic)
  final int? landPrice;
  @override
  @JsonKey(name: '인접역')
  final String? nearStation;
  @override
  @JsonKey(name: '거리(m)', fromJson: _intFromDynamic)
  final int? stationDistance;
// 상태 및 링크
  final List<String>? _status;
// 상태 및 링크
  @override
  @JsonKey(name: '현황', fromJson: _statusFromDynamic)
  List<String>? get status {
    final value = _status;
    if (value == null) return null;
    if (_status is EqualUnmodifiableListView) return _status;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  @JsonKey(name: '광고(자동완성)')
  final String? description;
  @override
  @JsonKey(name: '지도')
  final String? mapLink;
  @override
  @JsonKey(name: '사진링크')
  final String? photoLink;
  @override
  @JsonKey(name: '디스코광고')
  final String? discoLink;
// 이미지 (Airtable attachment)
  final List<AirtableAttachment>? _representativePhoto;
// 이미지 (Airtable attachment)
  @override
  @JsonKey(name: '대표사진')
  List<AirtableAttachment>? get representativePhoto {
    final value = _representativePhoto;
    if (value == null) return null;
    if (_representativePhoto is EqualUnmodifiableListView)
      return _representativePhoto;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  String toString() {
    return 'PropertyFields(address: $address, roadAddress: $roadAddress, price: $price, deposit: $deposit, monthlyRent: $monthlyRent, loan: $loan, investment: $investment, yieldRate: $yieldRate, appraisedValue: $appraisedValue, appraisalRate: $appraisalRate, landArea: $landArea, totalFloorArea: $totalFloorArea, buildingArea: $buildingArea, farArea: $farArea, floors: $floors, mainUsage: $mainUsage, etcUsage: $etcUsage, structure: $structure, roof: $roof, approvalDate: $approvalDate, buildingName: $buildingName, buildingComposition: $buildingComposition, buildingCoverageRatio: $buildingCoverageRatio, floorAreaRatio: $floorAreaRatio, height: $height, parkingCount: $parkingCount, elevatorCount: $elevatorCount, householdInfo: $householdInfo, zoning: $zoning, landPrice: $landPrice, nearStation: $nearStation, stationDistance: $stationDistance, status: $status, description: $description, mapLink: $mapLink, photoLink: $photoLink, discoLink: $discoLink, representativePhoto: $representativePhoto)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PropertyFieldsImpl &&
            (identical(other.address, address) || other.address == address) &&
            (identical(other.roadAddress, roadAddress) ||
                other.roadAddress == roadAddress) &&
            (identical(other.price, price) || other.price == price) &&
            (identical(other.deposit, deposit) || other.deposit == deposit) &&
            (identical(other.monthlyRent, monthlyRent) ||
                other.monthlyRent == monthlyRent) &&
            (identical(other.loan, loan) || other.loan == loan) &&
            (identical(other.investment, investment) ||
                other.investment == investment) &&
            (identical(other.yieldRate, yieldRate) ||
                other.yieldRate == yieldRate) &&
            (identical(other.appraisedValue, appraisedValue) ||
                other.appraisedValue == appraisedValue) &&
            (identical(other.appraisalRate, appraisalRate) ||
                other.appraisalRate == appraisalRate) &&
            (identical(other.landArea, landArea) ||
                other.landArea == landArea) &&
            (identical(other.totalFloorArea, totalFloorArea) ||
                other.totalFloorArea == totalFloorArea) &&
            (identical(other.buildingArea, buildingArea) ||
                other.buildingArea == buildingArea) &&
            (identical(other.farArea, farArea) || other.farArea == farArea) &&
            (identical(other.floors, floors) || other.floors == floors) &&
            (identical(other.mainUsage, mainUsage) ||
                other.mainUsage == mainUsage) &&
            (identical(other.etcUsage, etcUsage) ||
                other.etcUsage == etcUsage) &&
            (identical(other.structure, structure) ||
                other.structure == structure) &&
            (identical(other.roof, roof) || other.roof == roof) &&
            (identical(other.approvalDate, approvalDate) ||
                other.approvalDate == approvalDate) &&
            (identical(other.buildingName, buildingName) ||
                other.buildingName == buildingName) &&
            (identical(other.buildingComposition, buildingComposition) ||
                other.buildingComposition == buildingComposition) &&
            (identical(other.buildingCoverageRatio, buildingCoverageRatio) ||
                other.buildingCoverageRatio == buildingCoverageRatio) &&
            (identical(other.floorAreaRatio, floorAreaRatio) ||
                other.floorAreaRatio == floorAreaRatio) &&
            (identical(other.height, height) || other.height == height) &&
            (identical(other.parkingCount, parkingCount) ||
                other.parkingCount == parkingCount) &&
            (identical(other.elevatorCount, elevatorCount) ||
                other.elevatorCount == elevatorCount) &&
            (identical(other.householdInfo, householdInfo) ||
                other.householdInfo == householdInfo) &&
            (identical(other.zoning, zoning) || other.zoning == zoning) &&
            (identical(other.landPrice, landPrice) ||
                other.landPrice == landPrice) &&
            (identical(other.nearStation, nearStation) ||
                other.nearStation == nearStation) &&
            (identical(other.stationDistance, stationDistance) ||
                other.stationDistance == stationDistance) &&
            const DeepCollectionEquality().equals(other._status, _status) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.mapLink, mapLink) || other.mapLink == mapLink) &&
            (identical(other.photoLink, photoLink) ||
                other.photoLink == photoLink) &&
            (identical(other.discoLink, discoLink) ||
                other.discoLink == discoLink) &&
            const DeepCollectionEquality()
                .equals(other._representativePhoto, _representativePhoto));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hashAll([
        runtimeType,
        address,
        roadAddress,
        price,
        deposit,
        monthlyRent,
        loan,
        investment,
        yieldRate,
        appraisedValue,
        appraisalRate,
        landArea,
        totalFloorArea,
        buildingArea,
        farArea,
        floors,
        mainUsage,
        etcUsage,
        structure,
        roof,
        approvalDate,
        buildingName,
        buildingComposition,
        buildingCoverageRatio,
        floorAreaRatio,
        height,
        parkingCount,
        elevatorCount,
        householdInfo,
        zoning,
        landPrice,
        nearStation,
        stationDistance,
        const DeepCollectionEquality().hash(_status),
        description,
        mapLink,
        photoLink,
        discoLink,
        const DeepCollectionEquality().hash(_representativePhoto)
      ]);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PropertyFieldsImplCopyWith<_$PropertyFieldsImpl> get copyWith =>
      __$$PropertyFieldsImplCopyWithImpl<_$PropertyFieldsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PropertyFieldsImplToJson(
      this,
    );
  }
}

abstract class _PropertyFields implements PropertyFields {
  const factory _PropertyFields(
      {@JsonKey(name: '지번 주소') final String? address,
      @JsonKey(name: '도로명주소') final String? roadAddress,
      @JsonKey(name: '매가(만원)', fromJson: _intFromDynamic) final int? price,
      @JsonKey(name: '보증금(만원)', fromJson: _intFromDynamic) final int? deposit,
      @JsonKey(name: '월세(만원)', fromJson: _intFromDynamic)
      final int? monthlyRent,
      @JsonKey(name: '융자(만원)', fromJson: _intFromDynamic) final int? loan,
      @JsonKey(name: '실투자금', fromJson: _intFromDynamic) final int? investment,
      @JsonKey(name: '융자제외수익률(%)', fromJson: _doubleFromDynamic)
      final double? yieldRate,
      @JsonKey(name: '감정가(만원,랜드북)', fromJson: _intFromDynamic)
      final int? appraisedValue,
      @JsonKey(name: '감정가율(%)', fromJson: _doubleFromDynamic)
      final double? appraisalRate,
      @JsonKey(name: '토지면적(㎡)', fromJson: _doubleFromDynamic)
      final double? landArea,
      @JsonKey(name: '연면적(㎡)', fromJson: _doubleFromDynamic)
      final double? totalFloorArea,
      @JsonKey(name: '건축면적(㎡)', fromJson: _doubleFromDynamic)
      final double? buildingArea,
      @JsonKey(name: '용적률산정용연면적(㎡)', fromJson: _doubleFromDynamic)
      final double? farArea,
      @JsonKey(name: '층수') final String? floors,
      @JsonKey(name: '주용도') final String? mainUsage,
      @JsonKey(name: '기타용도') final String? etcUsage,
      @JsonKey(name: '주구조') final String? structure,
      @JsonKey(name: '지붕') final String? roof,
      @JsonKey(name: '사용승인일') final String? approvalDate,
      @JsonKey(name: '건물명') final String? buildingName,
      @JsonKey(name: '건물구성') final String? buildingComposition,
      @JsonKey(name: '건폐율(%)', fromJson: _doubleFromDynamic)
      final double? buildingCoverageRatio,
      @JsonKey(name: '용적률(%)', fromJson: _doubleFromDynamic)
      final double? floorAreaRatio,
      @JsonKey(name: '높이(m)', fromJson: _doubleFromDynamic)
      final double? height,
      @JsonKey(name: '주차대수', fromJson: _intFromDynamic) final int? parkingCount,
      @JsonKey(name: '승강기수', fromJson: _intFromDynamic)
      final int? elevatorCount,
      @JsonKey(name: '세대/가구/호') final String? householdInfo,
      @JsonKey(name: '용도지역') final String? zoning,
      @JsonKey(name: '공시지가(원/㎡)', fromJson: _intFromDynamic)
      final int? landPrice,
      @JsonKey(name: '인접역') final String? nearStation,
      @JsonKey(name: '거리(m)', fromJson: _intFromDynamic)
      final int? stationDistance,
      @JsonKey(name: '현황', fromJson: _statusFromDynamic)
      final List<String>? status,
      @JsonKey(name: '광고(자동완성)') final String? description,
      @JsonKey(name: '지도') final String? mapLink,
      @JsonKey(name: '사진링크') final String? photoLink,
      @JsonKey(name: '디스코광고') final String? discoLink,
      @JsonKey(name: '대표사진')
      final List<AirtableAttachment>?
          representativePhoto}) = _$PropertyFieldsImpl;

  factory _PropertyFields.fromJson(Map<String, dynamic> json) =
      _$PropertyFieldsImpl.fromJson;

  @override // 주소
  @JsonKey(name: '지번 주소')
  String? get address;
  @override
  @JsonKey(name: '도로명주소')
  String? get roadAddress;
  @override // 가격 정보
  @JsonKey(name: '매가(만원)', fromJson: _intFromDynamic)
  int? get price;
  @override
  @JsonKey(name: '보증금(만원)', fromJson: _intFromDynamic)
  int? get deposit;
  @override
  @JsonKey(name: '월세(만원)', fromJson: _intFromDynamic)
  int? get monthlyRent;
  @override
  @JsonKey(name: '융자(만원)', fromJson: _intFromDynamic)
  int? get loan;
  @override
  @JsonKey(name: '실투자금', fromJson: _intFromDynamic)
  int? get investment;
  @override
  @JsonKey(name: '융자제외수익률(%)', fromJson: _doubleFromDynamic)
  double? get yieldRate;
  @override
  @JsonKey(name: '감정가(만원,랜드북)', fromJson: _intFromDynamic)
  int? get appraisedValue;
  @override
  @JsonKey(name: '감정가율(%)', fromJson: _doubleFromDynamic)
  double? get appraisalRate;
  @override // 면적 정보
  @JsonKey(name: '토지면적(㎡)', fromJson: _doubleFromDynamic)
  double? get landArea;
  @override
  @JsonKey(name: '연면적(㎡)', fromJson: _doubleFromDynamic)
  double? get totalFloorArea;
  @override
  @JsonKey(name: '건축면적(㎡)', fromJson: _doubleFromDynamic)
  double? get buildingArea;
  @override
  @JsonKey(name: '용적률산정용연면적(㎡)', fromJson: _doubleFromDynamic)
  double? get farArea;
  @override // 건물 정보
  @JsonKey(name: '층수')
  String? get floors;
  @override
  @JsonKey(name: '주용도')
  String? get mainUsage;
  @override
  @JsonKey(name: '기타용도')
  String? get etcUsage;
  @override
  @JsonKey(name: '주구조')
  String? get structure;
  @override
  @JsonKey(name: '지붕')
  String? get roof;
  @override
  @JsonKey(name: '사용승인일')
  String? get approvalDate;
  @override
  @JsonKey(name: '건물명')
  String? get buildingName;
  @override
  @JsonKey(name: '건물구성')
  String? get buildingComposition;
  @override
  @JsonKey(name: '건폐율(%)', fromJson: _doubleFromDynamic)
  double? get buildingCoverageRatio;
  @override
  @JsonKey(name: '용적률(%)', fromJson: _doubleFromDynamic)
  double? get floorAreaRatio;
  @override
  @JsonKey(name: '높이(m)', fromJson: _doubleFromDynamic)
  double? get height;
  @override // 설비
  @JsonKey(name: '주차대수', fromJson: _intFromDynamic)
  int? get parkingCount;
  @override
  @JsonKey(name: '승강기수', fromJson: _intFromDynamic)
  int? get elevatorCount;
  @override
  @JsonKey(name: '세대/가구/호')
  String? get householdInfo;
  @override // 위치 정보
  @JsonKey(name: '용도지역')
  String? get zoning;
  @override
  @JsonKey(name: '공시지가(원/㎡)', fromJson: _intFromDynamic)
  int? get landPrice;
  @override
  @JsonKey(name: '인접역')
  String? get nearStation;
  @override
  @JsonKey(name: '거리(m)', fromJson: _intFromDynamic)
  int? get stationDistance;
  @override // 상태 및 링크
  @JsonKey(name: '현황', fromJson: _statusFromDynamic)
  List<String>? get status;
  @override
  @JsonKey(name: '광고(자동완성)')
  String? get description;
  @override
  @JsonKey(name: '지도')
  String? get mapLink;
  @override
  @JsonKey(name: '사진링크')
  String? get photoLink;
  @override
  @JsonKey(name: '디스코광고')
  String? get discoLink;
  @override // 이미지 (Airtable attachment)
  @JsonKey(name: '대표사진')
  List<AirtableAttachment>? get representativePhoto;
  @override
  @JsonKey(ignore: true)
  _$$PropertyFieldsImplCopyWith<_$PropertyFieldsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AirtableAttachment _$AirtableAttachmentFromJson(Map<String, dynamic> json) {
  return _AirtableAttachment.fromJson(json);
}

/// @nodoc
mixin _$AirtableAttachment {
  String? get id => throw _privateConstructorUsedError;
  String? get url => throw _privateConstructorUsedError;
  String? get filename => throw _privateConstructorUsedError;
  int? get size => throw _privateConstructorUsedError;
  String? get type => throw _privateConstructorUsedError;
  int? get width => throw _privateConstructorUsedError;
  int? get height => throw _privateConstructorUsedError;
  AirtableThumbnails? get thumbnails => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AirtableAttachmentCopyWith<AirtableAttachment> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AirtableAttachmentCopyWith<$Res> {
  factory $AirtableAttachmentCopyWith(
          AirtableAttachment value, $Res Function(AirtableAttachment) then) =
      _$AirtableAttachmentCopyWithImpl<$Res, AirtableAttachment>;
  @useResult
  $Res call(
      {String? id,
      String? url,
      String? filename,
      int? size,
      String? type,
      int? width,
      int? height,
      AirtableThumbnails? thumbnails});

  $AirtableThumbnailsCopyWith<$Res>? get thumbnails;
}

/// @nodoc
class _$AirtableAttachmentCopyWithImpl<$Res, $Val extends AirtableAttachment>
    implements $AirtableAttachmentCopyWith<$Res> {
  _$AirtableAttachmentCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = freezed,
    Object? url = freezed,
    Object? filename = freezed,
    Object? size = freezed,
    Object? type = freezed,
    Object? width = freezed,
    Object? height = freezed,
    Object? thumbnails = freezed,
  }) {
    return _then(_value.copyWith(
      id: freezed == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String?,
      url: freezed == url
          ? _value.url
          : url // ignore: cast_nullable_to_non_nullable
              as String?,
      filename: freezed == filename
          ? _value.filename
          : filename // ignore: cast_nullable_to_non_nullable
              as String?,
      size: freezed == size
          ? _value.size
          : size // ignore: cast_nullable_to_non_nullable
              as int?,
      type: freezed == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String?,
      width: freezed == width
          ? _value.width
          : width // ignore: cast_nullable_to_non_nullable
              as int?,
      height: freezed == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as int?,
      thumbnails: freezed == thumbnails
          ? _value.thumbnails
          : thumbnails // ignore: cast_nullable_to_non_nullable
              as AirtableThumbnails?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $AirtableThumbnailsCopyWith<$Res>? get thumbnails {
    if (_value.thumbnails == null) {
      return null;
    }

    return $AirtableThumbnailsCopyWith<$Res>(_value.thumbnails!, (value) {
      return _then(_value.copyWith(thumbnails: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AirtableAttachmentImplCopyWith<$Res>
    implements $AirtableAttachmentCopyWith<$Res> {
  factory _$$AirtableAttachmentImplCopyWith(_$AirtableAttachmentImpl value,
          $Res Function(_$AirtableAttachmentImpl) then) =
      __$$AirtableAttachmentImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String? id,
      String? url,
      String? filename,
      int? size,
      String? type,
      int? width,
      int? height,
      AirtableThumbnails? thumbnails});

  @override
  $AirtableThumbnailsCopyWith<$Res>? get thumbnails;
}

/// @nodoc
class __$$AirtableAttachmentImplCopyWithImpl<$Res>
    extends _$AirtableAttachmentCopyWithImpl<$Res, _$AirtableAttachmentImpl>
    implements _$$AirtableAttachmentImplCopyWith<$Res> {
  __$$AirtableAttachmentImplCopyWithImpl(_$AirtableAttachmentImpl _value,
      $Res Function(_$AirtableAttachmentImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = freezed,
    Object? url = freezed,
    Object? filename = freezed,
    Object? size = freezed,
    Object? type = freezed,
    Object? width = freezed,
    Object? height = freezed,
    Object? thumbnails = freezed,
  }) {
    return _then(_$AirtableAttachmentImpl(
      id: freezed == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String?,
      url: freezed == url
          ? _value.url
          : url // ignore: cast_nullable_to_non_nullable
              as String?,
      filename: freezed == filename
          ? _value.filename
          : filename // ignore: cast_nullable_to_non_nullable
              as String?,
      size: freezed == size
          ? _value.size
          : size // ignore: cast_nullable_to_non_nullable
              as int?,
      type: freezed == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String?,
      width: freezed == width
          ? _value.width
          : width // ignore: cast_nullable_to_non_nullable
              as int?,
      height: freezed == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as int?,
      thumbnails: freezed == thumbnails
          ? _value.thumbnails
          : thumbnails // ignore: cast_nullable_to_non_nullable
              as AirtableThumbnails?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AirtableAttachmentImpl implements _AirtableAttachment {
  const _$AirtableAttachmentImpl(
      {this.id,
      this.url,
      this.filename,
      this.size,
      this.type,
      this.width,
      this.height,
      this.thumbnails});

  factory _$AirtableAttachmentImpl.fromJson(Map<String, dynamic> json) =>
      _$$AirtableAttachmentImplFromJson(json);

  @override
  final String? id;
  @override
  final String? url;
  @override
  final String? filename;
  @override
  final int? size;
  @override
  final String? type;
  @override
  final int? width;
  @override
  final int? height;
  @override
  final AirtableThumbnails? thumbnails;

  @override
  String toString() {
    return 'AirtableAttachment(id: $id, url: $url, filename: $filename, size: $size, type: $type, width: $width, height: $height, thumbnails: $thumbnails)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AirtableAttachmentImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.url, url) || other.url == url) &&
            (identical(other.filename, filename) ||
                other.filename == filename) &&
            (identical(other.size, size) || other.size == size) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.width, width) || other.width == width) &&
            (identical(other.height, height) || other.height == height) &&
            (identical(other.thumbnails, thumbnails) ||
                other.thumbnails == thumbnails));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, id, url, filename, size, type, width, height, thumbnails);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AirtableAttachmentImplCopyWith<_$AirtableAttachmentImpl> get copyWith =>
      __$$AirtableAttachmentImplCopyWithImpl<_$AirtableAttachmentImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AirtableAttachmentImplToJson(
      this,
    );
  }
}

abstract class _AirtableAttachment implements AirtableAttachment {
  const factory _AirtableAttachment(
      {final String? id,
      final String? url,
      final String? filename,
      final int? size,
      final String? type,
      final int? width,
      final int? height,
      final AirtableThumbnails? thumbnails}) = _$AirtableAttachmentImpl;

  factory _AirtableAttachment.fromJson(Map<String, dynamic> json) =
      _$AirtableAttachmentImpl.fromJson;

  @override
  String? get id;
  @override
  String? get url;
  @override
  String? get filename;
  @override
  int? get size;
  @override
  String? get type;
  @override
  int? get width;
  @override
  int? get height;
  @override
  AirtableThumbnails? get thumbnails;
  @override
  @JsonKey(ignore: true)
  _$$AirtableAttachmentImplCopyWith<_$AirtableAttachmentImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AirtableThumbnails _$AirtableThumbnailsFromJson(Map<String, dynamic> json) {
  return _AirtableThumbnails.fromJson(json);
}

/// @nodoc
mixin _$AirtableThumbnails {
  AirtableThumbnail? get small => throw _privateConstructorUsedError;
  AirtableThumbnail? get large => throw _privateConstructorUsedError;
  AirtableThumbnail? get full => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AirtableThumbnailsCopyWith<AirtableThumbnails> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AirtableThumbnailsCopyWith<$Res> {
  factory $AirtableThumbnailsCopyWith(
          AirtableThumbnails value, $Res Function(AirtableThumbnails) then) =
      _$AirtableThumbnailsCopyWithImpl<$Res, AirtableThumbnails>;
  @useResult
  $Res call(
      {AirtableThumbnail? small,
      AirtableThumbnail? large,
      AirtableThumbnail? full});

  $AirtableThumbnailCopyWith<$Res>? get small;
  $AirtableThumbnailCopyWith<$Res>? get large;
  $AirtableThumbnailCopyWith<$Res>? get full;
}

/// @nodoc
class _$AirtableThumbnailsCopyWithImpl<$Res, $Val extends AirtableThumbnails>
    implements $AirtableThumbnailsCopyWith<$Res> {
  _$AirtableThumbnailsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? small = freezed,
    Object? large = freezed,
    Object? full = freezed,
  }) {
    return _then(_value.copyWith(
      small: freezed == small
          ? _value.small
          : small // ignore: cast_nullable_to_non_nullable
              as AirtableThumbnail?,
      large: freezed == large
          ? _value.large
          : large // ignore: cast_nullable_to_non_nullable
              as AirtableThumbnail?,
      full: freezed == full
          ? _value.full
          : full // ignore: cast_nullable_to_non_nullable
              as AirtableThumbnail?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $AirtableThumbnailCopyWith<$Res>? get small {
    if (_value.small == null) {
      return null;
    }

    return $AirtableThumbnailCopyWith<$Res>(_value.small!, (value) {
      return _then(_value.copyWith(small: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $AirtableThumbnailCopyWith<$Res>? get large {
    if (_value.large == null) {
      return null;
    }

    return $AirtableThumbnailCopyWith<$Res>(_value.large!, (value) {
      return _then(_value.copyWith(large: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $AirtableThumbnailCopyWith<$Res>? get full {
    if (_value.full == null) {
      return null;
    }

    return $AirtableThumbnailCopyWith<$Res>(_value.full!, (value) {
      return _then(_value.copyWith(full: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AirtableThumbnailsImplCopyWith<$Res>
    implements $AirtableThumbnailsCopyWith<$Res> {
  factory _$$AirtableThumbnailsImplCopyWith(_$AirtableThumbnailsImpl value,
          $Res Function(_$AirtableThumbnailsImpl) then) =
      __$$AirtableThumbnailsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {AirtableThumbnail? small,
      AirtableThumbnail? large,
      AirtableThumbnail? full});

  @override
  $AirtableThumbnailCopyWith<$Res>? get small;
  @override
  $AirtableThumbnailCopyWith<$Res>? get large;
  @override
  $AirtableThumbnailCopyWith<$Res>? get full;
}

/// @nodoc
class __$$AirtableThumbnailsImplCopyWithImpl<$Res>
    extends _$AirtableThumbnailsCopyWithImpl<$Res, _$AirtableThumbnailsImpl>
    implements _$$AirtableThumbnailsImplCopyWith<$Res> {
  __$$AirtableThumbnailsImplCopyWithImpl(_$AirtableThumbnailsImpl _value,
      $Res Function(_$AirtableThumbnailsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? small = freezed,
    Object? large = freezed,
    Object? full = freezed,
  }) {
    return _then(_$AirtableThumbnailsImpl(
      small: freezed == small
          ? _value.small
          : small // ignore: cast_nullable_to_non_nullable
              as AirtableThumbnail?,
      large: freezed == large
          ? _value.large
          : large // ignore: cast_nullable_to_non_nullable
              as AirtableThumbnail?,
      full: freezed == full
          ? _value.full
          : full // ignore: cast_nullable_to_non_nullable
              as AirtableThumbnail?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AirtableThumbnailsImpl implements _AirtableThumbnails {
  const _$AirtableThumbnailsImpl({this.small, this.large, this.full});

  factory _$AirtableThumbnailsImpl.fromJson(Map<String, dynamic> json) =>
      _$$AirtableThumbnailsImplFromJson(json);

  @override
  final AirtableThumbnail? small;
  @override
  final AirtableThumbnail? large;
  @override
  final AirtableThumbnail? full;

  @override
  String toString() {
    return 'AirtableThumbnails(small: $small, large: $large, full: $full)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AirtableThumbnailsImpl &&
            (identical(other.small, small) || other.small == small) &&
            (identical(other.large, large) || other.large == large) &&
            (identical(other.full, full) || other.full == full));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, small, large, full);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AirtableThumbnailsImplCopyWith<_$AirtableThumbnailsImpl> get copyWith =>
      __$$AirtableThumbnailsImplCopyWithImpl<_$AirtableThumbnailsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AirtableThumbnailsImplToJson(
      this,
    );
  }
}

abstract class _AirtableThumbnails implements AirtableThumbnails {
  const factory _AirtableThumbnails(
      {final AirtableThumbnail? small,
      final AirtableThumbnail? large,
      final AirtableThumbnail? full}) = _$AirtableThumbnailsImpl;

  factory _AirtableThumbnails.fromJson(Map<String, dynamic> json) =
      _$AirtableThumbnailsImpl.fromJson;

  @override
  AirtableThumbnail? get small;
  @override
  AirtableThumbnail? get large;
  @override
  AirtableThumbnail? get full;
  @override
  @JsonKey(ignore: true)
  _$$AirtableThumbnailsImplCopyWith<_$AirtableThumbnailsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AirtableThumbnail _$AirtableThumbnailFromJson(Map<String, dynamic> json) {
  return _AirtableThumbnail.fromJson(json);
}

/// @nodoc
mixin _$AirtableThumbnail {
  String? get url => throw _privateConstructorUsedError;
  int? get width => throw _privateConstructorUsedError;
  int? get height => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AirtableThumbnailCopyWith<AirtableThumbnail> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AirtableThumbnailCopyWith<$Res> {
  factory $AirtableThumbnailCopyWith(
          AirtableThumbnail value, $Res Function(AirtableThumbnail) then) =
      _$AirtableThumbnailCopyWithImpl<$Res, AirtableThumbnail>;
  @useResult
  $Res call({String? url, int? width, int? height});
}

/// @nodoc
class _$AirtableThumbnailCopyWithImpl<$Res, $Val extends AirtableThumbnail>
    implements $AirtableThumbnailCopyWith<$Res> {
  _$AirtableThumbnailCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? url = freezed,
    Object? width = freezed,
    Object? height = freezed,
  }) {
    return _then(_value.copyWith(
      url: freezed == url
          ? _value.url
          : url // ignore: cast_nullable_to_non_nullable
              as String?,
      width: freezed == width
          ? _value.width
          : width // ignore: cast_nullable_to_non_nullable
              as int?,
      height: freezed == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as int?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$AirtableThumbnailImplCopyWith<$Res>
    implements $AirtableThumbnailCopyWith<$Res> {
  factory _$$AirtableThumbnailImplCopyWith(_$AirtableThumbnailImpl value,
          $Res Function(_$AirtableThumbnailImpl) then) =
      __$$AirtableThumbnailImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String? url, int? width, int? height});
}

/// @nodoc
class __$$AirtableThumbnailImplCopyWithImpl<$Res>
    extends _$AirtableThumbnailCopyWithImpl<$Res, _$AirtableThumbnailImpl>
    implements _$$AirtableThumbnailImplCopyWith<$Res> {
  __$$AirtableThumbnailImplCopyWithImpl(_$AirtableThumbnailImpl _value,
      $Res Function(_$AirtableThumbnailImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? url = freezed,
    Object? width = freezed,
    Object? height = freezed,
  }) {
    return _then(_$AirtableThumbnailImpl(
      url: freezed == url
          ? _value.url
          : url // ignore: cast_nullable_to_non_nullable
              as String?,
      width: freezed == width
          ? _value.width
          : width // ignore: cast_nullable_to_non_nullable
              as int?,
      height: freezed == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AirtableThumbnailImpl implements _AirtableThumbnail {
  const _$AirtableThumbnailImpl({this.url, this.width, this.height});

  factory _$AirtableThumbnailImpl.fromJson(Map<String, dynamic> json) =>
      _$$AirtableThumbnailImplFromJson(json);

  @override
  final String? url;
  @override
  final int? width;
  @override
  final int? height;

  @override
  String toString() {
    return 'AirtableThumbnail(url: $url, width: $width, height: $height)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AirtableThumbnailImpl &&
            (identical(other.url, url) || other.url == url) &&
            (identical(other.width, width) || other.width == width) &&
            (identical(other.height, height) || other.height == height));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, url, width, height);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AirtableThumbnailImplCopyWith<_$AirtableThumbnailImpl> get copyWith =>
      __$$AirtableThumbnailImplCopyWithImpl<_$AirtableThumbnailImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AirtableThumbnailImplToJson(
      this,
    );
  }
}

abstract class _AirtableThumbnail implements AirtableThumbnail {
  const factory _AirtableThumbnail(
      {final String? url,
      final int? width,
      final int? height}) = _$AirtableThumbnailImpl;

  factory _AirtableThumbnail.fromJson(Map<String, dynamic> json) =
      _$AirtableThumbnailImpl.fromJson;

  @override
  String? get url;
  @override
  int? get width;
  @override
  int? get height;
  @override
  @JsonKey(ignore: true)
  _$$AirtableThumbnailImplCopyWith<_$AirtableThumbnailImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PropertyListResponse _$PropertyListResponseFromJson(Map<String, dynamic> json) {
  return _PropertyListResponse.fromJson(json);
}

/// @nodoc
mixin _$PropertyListResponse {
  List<PropertyRecord> get records => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PropertyListResponseCopyWith<PropertyListResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PropertyListResponseCopyWith<$Res> {
  factory $PropertyListResponseCopyWith(PropertyListResponse value,
          $Res Function(PropertyListResponse) then) =
      _$PropertyListResponseCopyWithImpl<$Res, PropertyListResponse>;
  @useResult
  $Res call({List<PropertyRecord> records, String? error});
}

/// @nodoc
class _$PropertyListResponseCopyWithImpl<$Res,
        $Val extends PropertyListResponse>
    implements $PropertyListResponseCopyWith<$Res> {
  _$PropertyListResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? records = null,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      records: null == records
          ? _value.records
          : records // ignore: cast_nullable_to_non_nullable
              as List<PropertyRecord>,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PropertyListResponseImplCopyWith<$Res>
    implements $PropertyListResponseCopyWith<$Res> {
  factory _$$PropertyListResponseImplCopyWith(_$PropertyListResponseImpl value,
          $Res Function(_$PropertyListResponseImpl) then) =
      __$$PropertyListResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({List<PropertyRecord> records, String? error});
}

/// @nodoc
class __$$PropertyListResponseImplCopyWithImpl<$Res>
    extends _$PropertyListResponseCopyWithImpl<$Res, _$PropertyListResponseImpl>
    implements _$$PropertyListResponseImplCopyWith<$Res> {
  __$$PropertyListResponseImplCopyWithImpl(_$PropertyListResponseImpl _value,
      $Res Function(_$PropertyListResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? records = null,
    Object? error = freezed,
  }) {
    return _then(_$PropertyListResponseImpl(
      records: null == records
          ? _value._records
          : records // ignore: cast_nullable_to_non_nullable
              as List<PropertyRecord>,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PropertyListResponseImpl implements _PropertyListResponse {
  const _$PropertyListResponseImpl(
      {final List<PropertyRecord> records = const [], this.error})
      : _records = records;

  factory _$PropertyListResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$PropertyListResponseImplFromJson(json);

  final List<PropertyRecord> _records;
  @override
  @JsonKey()
  List<PropertyRecord> get records {
    if (_records is EqualUnmodifiableListView) return _records;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_records);
  }

  @override
  final String? error;

  @override
  String toString() {
    return 'PropertyListResponse(records: $records, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PropertyListResponseImpl &&
            const DeepCollectionEquality().equals(other._records, _records) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, const DeepCollectionEquality().hash(_records), error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PropertyListResponseImplCopyWith<_$PropertyListResponseImpl>
      get copyWith =>
          __$$PropertyListResponseImplCopyWithImpl<_$PropertyListResponseImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PropertyListResponseImplToJson(
      this,
    );
  }
}

abstract class _PropertyListResponse implements PropertyListResponse {
  const factory _PropertyListResponse(
      {final List<PropertyRecord> records,
      final String? error}) = _$PropertyListResponseImpl;

  factory _PropertyListResponse.fromJson(Map<String, dynamic> json) =
      _$PropertyListResponseImpl.fromJson;

  @override
  List<PropertyRecord> get records;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$PropertyListResponseImplCopyWith<_$PropertyListResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}

CategoryPropertiesResponse _$CategoryPropertiesResponseFromJson(
    Map<String, dynamic> json) {
  return _CategoryPropertiesResponse.fromJson(json);
}

/// @nodoc
mixin _$CategoryPropertiesResponse {
  List<PropertyRecord> get records => throw _privateConstructorUsedError;
  @JsonKey(name: 'view_id')
  String? get viewId => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_count')
  int get totalCount => throw _privateConstructorUsedError;
  String? get source => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $CategoryPropertiesResponseCopyWith<CategoryPropertiesResponse>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CategoryPropertiesResponseCopyWith<$Res> {
  factory $CategoryPropertiesResponseCopyWith(CategoryPropertiesResponse value,
          $Res Function(CategoryPropertiesResponse) then) =
      _$CategoryPropertiesResponseCopyWithImpl<$Res,
          CategoryPropertiesResponse>;
  @useResult
  $Res call(
      {List<PropertyRecord> records,
      @JsonKey(name: 'view_id') String? viewId,
      @JsonKey(name: 'total_count') int totalCount,
      String? source,
      String? error});
}

/// @nodoc
class _$CategoryPropertiesResponseCopyWithImpl<$Res,
        $Val extends CategoryPropertiesResponse>
    implements $CategoryPropertiesResponseCopyWith<$Res> {
  _$CategoryPropertiesResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? records = null,
    Object? viewId = freezed,
    Object? totalCount = null,
    Object? source = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      records: null == records
          ? _value.records
          : records // ignore: cast_nullable_to_non_nullable
              as List<PropertyRecord>,
      viewId: freezed == viewId
          ? _value.viewId
          : viewId // ignore: cast_nullable_to_non_nullable
              as String?,
      totalCount: null == totalCount
          ? _value.totalCount
          : totalCount // ignore: cast_nullable_to_non_nullable
              as int,
      source: freezed == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as String?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CategoryPropertiesResponseImplCopyWith<$Res>
    implements $CategoryPropertiesResponseCopyWith<$Res> {
  factory _$$CategoryPropertiesResponseImplCopyWith(
          _$CategoryPropertiesResponseImpl value,
          $Res Function(_$CategoryPropertiesResponseImpl) then) =
      __$$CategoryPropertiesResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<PropertyRecord> records,
      @JsonKey(name: 'view_id') String? viewId,
      @JsonKey(name: 'total_count') int totalCount,
      String? source,
      String? error});
}

/// @nodoc
class __$$CategoryPropertiesResponseImplCopyWithImpl<$Res>
    extends _$CategoryPropertiesResponseCopyWithImpl<$Res,
        _$CategoryPropertiesResponseImpl>
    implements _$$CategoryPropertiesResponseImplCopyWith<$Res> {
  __$$CategoryPropertiesResponseImplCopyWithImpl(
      _$CategoryPropertiesResponseImpl _value,
      $Res Function(_$CategoryPropertiesResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? records = null,
    Object? viewId = freezed,
    Object? totalCount = null,
    Object? source = freezed,
    Object? error = freezed,
  }) {
    return _then(_$CategoryPropertiesResponseImpl(
      records: null == records
          ? _value._records
          : records // ignore: cast_nullable_to_non_nullable
              as List<PropertyRecord>,
      viewId: freezed == viewId
          ? _value.viewId
          : viewId // ignore: cast_nullable_to_non_nullable
              as String?,
      totalCount: null == totalCount
          ? _value.totalCount
          : totalCount // ignore: cast_nullable_to_non_nullable
              as int,
      source: freezed == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
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
class _$CategoryPropertiesResponseImpl implements _CategoryPropertiesResponse {
  const _$CategoryPropertiesResponseImpl(
      {final List<PropertyRecord> records = const [],
      @JsonKey(name: 'view_id') this.viewId,
      @JsonKey(name: 'total_count') this.totalCount = 0,
      this.source,
      this.error})
      : _records = records;

  factory _$CategoryPropertiesResponseImpl.fromJson(
          Map<String, dynamic> json) =>
      _$$CategoryPropertiesResponseImplFromJson(json);

  final List<PropertyRecord> _records;
  @override
  @JsonKey()
  List<PropertyRecord> get records {
    if (_records is EqualUnmodifiableListView) return _records;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_records);
  }

  @override
  @JsonKey(name: 'view_id')
  final String? viewId;
  @override
  @JsonKey(name: 'total_count')
  final int totalCount;
  @override
  final String? source;
  @override
  final String? error;

  @override
  String toString() {
    return 'CategoryPropertiesResponse(records: $records, viewId: $viewId, totalCount: $totalCount, source: $source, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CategoryPropertiesResponseImpl &&
            const DeepCollectionEquality().equals(other._records, _records) &&
            (identical(other.viewId, viewId) || other.viewId == viewId) &&
            (identical(other.totalCount, totalCount) ||
                other.totalCount == totalCount) &&
            (identical(other.source, source) || other.source == source) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_records),
      viewId,
      totalCount,
      source,
      error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$CategoryPropertiesResponseImplCopyWith<_$CategoryPropertiesResponseImpl>
      get copyWith => __$$CategoryPropertiesResponseImplCopyWithImpl<
          _$CategoryPropertiesResponseImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CategoryPropertiesResponseImplToJson(
      this,
    );
  }
}

abstract class _CategoryPropertiesResponse
    implements CategoryPropertiesResponse {
  const factory _CategoryPropertiesResponse(
      {final List<PropertyRecord> records,
      @JsonKey(name: 'view_id') final String? viewId,
      @JsonKey(name: 'total_count') final int totalCount,
      final String? source,
      final String? error}) = _$CategoryPropertiesResponseImpl;

  factory _CategoryPropertiesResponse.fromJson(Map<String, dynamic> json) =
      _$CategoryPropertiesResponseImpl.fromJson;

  @override
  List<PropertyRecord> get records;
  @override
  @JsonKey(name: 'view_id')
  String? get viewId;
  @override
  @JsonKey(name: 'total_count')
  int get totalCount;
  @override
  String? get source;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$CategoryPropertiesResponseImplCopyWith<_$CategoryPropertiesResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}

PropertyDetailResponse _$PropertyDetailResponseFromJson(
    Map<String, dynamic> json) {
  return _PropertyDetailResponse.fromJson(json);
}

/// @nodoc
mixin _$PropertyDetailResponse {
  PropertyRecord? get property => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PropertyDetailResponseCopyWith<PropertyDetailResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PropertyDetailResponseCopyWith<$Res> {
  factory $PropertyDetailResponseCopyWith(PropertyDetailResponse value,
          $Res Function(PropertyDetailResponse) then) =
      _$PropertyDetailResponseCopyWithImpl<$Res, PropertyDetailResponse>;
  @useResult
  $Res call({PropertyRecord? property, String? error});

  $PropertyRecordCopyWith<$Res>? get property;
}

/// @nodoc
class _$PropertyDetailResponseCopyWithImpl<$Res,
        $Val extends PropertyDetailResponse>
    implements $PropertyDetailResponseCopyWith<$Res> {
  _$PropertyDetailResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? property = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      property: freezed == property
          ? _value.property
          : property // ignore: cast_nullable_to_non_nullable
              as PropertyRecord?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $PropertyRecordCopyWith<$Res>? get property {
    if (_value.property == null) {
      return null;
    }

    return $PropertyRecordCopyWith<$Res>(_value.property!, (value) {
      return _then(_value.copyWith(property: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$PropertyDetailResponseImplCopyWith<$Res>
    implements $PropertyDetailResponseCopyWith<$Res> {
  factory _$$PropertyDetailResponseImplCopyWith(
          _$PropertyDetailResponseImpl value,
          $Res Function(_$PropertyDetailResponseImpl) then) =
      __$$PropertyDetailResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({PropertyRecord? property, String? error});

  @override
  $PropertyRecordCopyWith<$Res>? get property;
}

/// @nodoc
class __$$PropertyDetailResponseImplCopyWithImpl<$Res>
    extends _$PropertyDetailResponseCopyWithImpl<$Res,
        _$PropertyDetailResponseImpl>
    implements _$$PropertyDetailResponseImplCopyWith<$Res> {
  __$$PropertyDetailResponseImplCopyWithImpl(
      _$PropertyDetailResponseImpl _value,
      $Res Function(_$PropertyDetailResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? property = freezed,
    Object? error = freezed,
  }) {
    return _then(_$PropertyDetailResponseImpl(
      property: freezed == property
          ? _value.property
          : property // ignore: cast_nullable_to_non_nullable
              as PropertyRecord?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PropertyDetailResponseImpl implements _PropertyDetailResponse {
  const _$PropertyDetailResponseImpl({this.property, this.error});

  factory _$PropertyDetailResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$PropertyDetailResponseImplFromJson(json);

  @override
  final PropertyRecord? property;
  @override
  final String? error;

  @override
  String toString() {
    return 'PropertyDetailResponse(property: $property, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PropertyDetailResponseImpl &&
            (identical(other.property, property) ||
                other.property == property) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, property, error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PropertyDetailResponseImplCopyWith<_$PropertyDetailResponseImpl>
      get copyWith => __$$PropertyDetailResponseImplCopyWithImpl<
          _$PropertyDetailResponseImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PropertyDetailResponseImplToJson(
      this,
    );
  }
}

abstract class _PropertyDetailResponse implements PropertyDetailResponse {
  const factory _PropertyDetailResponse(
      {final PropertyRecord? property,
      final String? error}) = _$PropertyDetailResponseImpl;

  factory _PropertyDetailResponse.fromJson(Map<String, dynamic> json) =
      _$PropertyDetailResponseImpl.fromJson;

  @override
  PropertyRecord? get property;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$PropertyDetailResponseImplCopyWith<_$PropertyDetailResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}

ImageCheckResponse _$ImageCheckResponseFromJson(Map<String, dynamic> json) {
  return _ImageCheckResponse.fromJson(json);
}

/// @nodoc
mixin _$ImageCheckResponse {
  bool get hasImage => throw _privateConstructorUsedError;
  String? get filename => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ImageCheckResponseCopyWith<ImageCheckResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ImageCheckResponseCopyWith<$Res> {
  factory $ImageCheckResponseCopyWith(
          ImageCheckResponse value, $Res Function(ImageCheckResponse) then) =
      _$ImageCheckResponseCopyWithImpl<$Res, ImageCheckResponse>;
  @useResult
  $Res call({bool hasImage, String? filename, String? error});
}

/// @nodoc
class _$ImageCheckResponseCopyWithImpl<$Res, $Val extends ImageCheckResponse>
    implements $ImageCheckResponseCopyWith<$Res> {
  _$ImageCheckResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? hasImage = null,
    Object? filename = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      hasImage: null == hasImage
          ? _value.hasImage
          : hasImage // ignore: cast_nullable_to_non_nullable
              as bool,
      filename: freezed == filename
          ? _value.filename
          : filename // ignore: cast_nullable_to_non_nullable
              as String?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ImageCheckResponseImplCopyWith<$Res>
    implements $ImageCheckResponseCopyWith<$Res> {
  factory _$$ImageCheckResponseImplCopyWith(_$ImageCheckResponseImpl value,
          $Res Function(_$ImageCheckResponseImpl) then) =
      __$$ImageCheckResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({bool hasImage, String? filename, String? error});
}

/// @nodoc
class __$$ImageCheckResponseImplCopyWithImpl<$Res>
    extends _$ImageCheckResponseCopyWithImpl<$Res, _$ImageCheckResponseImpl>
    implements _$$ImageCheckResponseImplCopyWith<$Res> {
  __$$ImageCheckResponseImplCopyWithImpl(_$ImageCheckResponseImpl _value,
      $Res Function(_$ImageCheckResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? hasImage = null,
    Object? filename = freezed,
    Object? error = freezed,
  }) {
    return _then(_$ImageCheckResponseImpl(
      hasImage: null == hasImage
          ? _value.hasImage
          : hasImage // ignore: cast_nullable_to_non_nullable
              as bool,
      filename: freezed == filename
          ? _value.filename
          : filename // ignore: cast_nullable_to_non_nullable
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
class _$ImageCheckResponseImpl implements _ImageCheckResponse {
  const _$ImageCheckResponseImpl(
      {this.hasImage = false, this.filename, this.error});

  factory _$ImageCheckResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$ImageCheckResponseImplFromJson(json);

  @override
  @JsonKey()
  final bool hasImage;
  @override
  final String? filename;
  @override
  final String? error;

  @override
  String toString() {
    return 'ImageCheckResponse(hasImage: $hasImage, filename: $filename, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ImageCheckResponseImpl &&
            (identical(other.hasImage, hasImage) ||
                other.hasImage == hasImage) &&
            (identical(other.filename, filename) ||
                other.filename == filename) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, hasImage, filename, error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ImageCheckResponseImplCopyWith<_$ImageCheckResponseImpl> get copyWith =>
      __$$ImageCheckResponseImplCopyWithImpl<_$ImageCheckResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ImageCheckResponseImplToJson(
      this,
    );
  }
}

abstract class _ImageCheckResponse implements ImageCheckResponse {
  const factory _ImageCheckResponse(
      {final bool hasImage,
      final String? filename,
      final String? error}) = _$ImageCheckResponseImpl;

  factory _ImageCheckResponse.fromJson(Map<String, dynamic> json) =
      _$ImageCheckResponseImpl.fromJson;

  @override
  bool get hasImage;
  @override
  String? get filename;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$ImageCheckResponseImplCopyWith<_$ImageCheckResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PropertyMapMarker _$PropertyMapMarkerFromJson(Map<String, dynamic> json) {
  return _PropertyMapMarker.fromJson(json);
}

/// @nodoc
mixin _$PropertyMapMarker {
  double get lat => throw _privateConstructorUsedError;
  double get lon => throw _privateConstructorUsedError;
  String? get address => throw _privateConstructorUsedError;
  @JsonKey(fromJson: _doubleFromDynamic)
  double? get price => throw _privateConstructorUsedError;
  @JsonKey(name: 'price_display')
  String? get priceDisplay => throw _privateConstructorUsedError;
  @JsonKey(name: 'yield', fromJson: _doubleFromDynamic)
  double? get yieldRate => throw _privateConstructorUsedError;
  @JsonKey(fromJson: _doubleFromDynamic)
  double? get area => throw _privateConstructorUsedError;
  @JsonKey(name: 'approval_date')
  String? get approvalDate => throw _privateConstructorUsedError;
  @JsonKey(name: 'record_id')
  String? get recordId => throw _privateConstructorUsedError;
  String? get popup => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PropertyMapMarkerCopyWith<PropertyMapMarker> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PropertyMapMarkerCopyWith<$Res> {
  factory $PropertyMapMarkerCopyWith(
          PropertyMapMarker value, $Res Function(PropertyMapMarker) then) =
      _$PropertyMapMarkerCopyWithImpl<$Res, PropertyMapMarker>;
  @useResult
  $Res call(
      {double lat,
      double lon,
      String? address,
      @JsonKey(fromJson: _doubleFromDynamic) double? price,
      @JsonKey(name: 'price_display') String? priceDisplay,
      @JsonKey(name: 'yield', fromJson: _doubleFromDynamic) double? yieldRate,
      @JsonKey(fromJson: _doubleFromDynamic) double? area,
      @JsonKey(name: 'approval_date') String? approvalDate,
      @JsonKey(name: 'record_id') String? recordId,
      String? popup});
}

/// @nodoc
class _$PropertyMapMarkerCopyWithImpl<$Res, $Val extends PropertyMapMarker>
    implements $PropertyMapMarkerCopyWith<$Res> {
  _$PropertyMapMarkerCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? lat = null,
    Object? lon = null,
    Object? address = freezed,
    Object? price = freezed,
    Object? priceDisplay = freezed,
    Object? yieldRate = freezed,
    Object? area = freezed,
    Object? approvalDate = freezed,
    Object? recordId = freezed,
    Object? popup = freezed,
  }) {
    return _then(_value.copyWith(
      lat: null == lat
          ? _value.lat
          : lat // ignore: cast_nullable_to_non_nullable
              as double,
      lon: null == lon
          ? _value.lon
          : lon // ignore: cast_nullable_to_non_nullable
              as double,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
      price: freezed == price
          ? _value.price
          : price // ignore: cast_nullable_to_non_nullable
              as double?,
      priceDisplay: freezed == priceDisplay
          ? _value.priceDisplay
          : priceDisplay // ignore: cast_nullable_to_non_nullable
              as String?,
      yieldRate: freezed == yieldRate
          ? _value.yieldRate
          : yieldRate // ignore: cast_nullable_to_non_nullable
              as double?,
      area: freezed == area
          ? _value.area
          : area // ignore: cast_nullable_to_non_nullable
              as double?,
      approvalDate: freezed == approvalDate
          ? _value.approvalDate
          : approvalDate // ignore: cast_nullable_to_non_nullable
              as String?,
      recordId: freezed == recordId
          ? _value.recordId
          : recordId // ignore: cast_nullable_to_non_nullable
              as String?,
      popup: freezed == popup
          ? _value.popup
          : popup // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PropertyMapMarkerImplCopyWith<$Res>
    implements $PropertyMapMarkerCopyWith<$Res> {
  factory _$$PropertyMapMarkerImplCopyWith(_$PropertyMapMarkerImpl value,
          $Res Function(_$PropertyMapMarkerImpl) then) =
      __$$PropertyMapMarkerImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {double lat,
      double lon,
      String? address,
      @JsonKey(fromJson: _doubleFromDynamic) double? price,
      @JsonKey(name: 'price_display') String? priceDisplay,
      @JsonKey(name: 'yield', fromJson: _doubleFromDynamic) double? yieldRate,
      @JsonKey(fromJson: _doubleFromDynamic) double? area,
      @JsonKey(name: 'approval_date') String? approvalDate,
      @JsonKey(name: 'record_id') String? recordId,
      String? popup});
}

/// @nodoc
class __$$PropertyMapMarkerImplCopyWithImpl<$Res>
    extends _$PropertyMapMarkerCopyWithImpl<$Res, _$PropertyMapMarkerImpl>
    implements _$$PropertyMapMarkerImplCopyWith<$Res> {
  __$$PropertyMapMarkerImplCopyWithImpl(_$PropertyMapMarkerImpl _value,
      $Res Function(_$PropertyMapMarkerImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? lat = null,
    Object? lon = null,
    Object? address = freezed,
    Object? price = freezed,
    Object? priceDisplay = freezed,
    Object? yieldRate = freezed,
    Object? area = freezed,
    Object? approvalDate = freezed,
    Object? recordId = freezed,
    Object? popup = freezed,
  }) {
    return _then(_$PropertyMapMarkerImpl(
      lat: null == lat
          ? _value.lat
          : lat // ignore: cast_nullable_to_non_nullable
              as double,
      lon: null == lon
          ? _value.lon
          : lon // ignore: cast_nullable_to_non_nullable
              as double,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
      price: freezed == price
          ? _value.price
          : price // ignore: cast_nullable_to_non_nullable
              as double?,
      priceDisplay: freezed == priceDisplay
          ? _value.priceDisplay
          : priceDisplay // ignore: cast_nullable_to_non_nullable
              as String?,
      yieldRate: freezed == yieldRate
          ? _value.yieldRate
          : yieldRate // ignore: cast_nullable_to_non_nullable
              as double?,
      area: freezed == area
          ? _value.area
          : area // ignore: cast_nullable_to_non_nullable
              as double?,
      approvalDate: freezed == approvalDate
          ? _value.approvalDate
          : approvalDate // ignore: cast_nullable_to_non_nullable
              as String?,
      recordId: freezed == recordId
          ? _value.recordId
          : recordId // ignore: cast_nullable_to_non_nullable
              as String?,
      popup: freezed == popup
          ? _value.popup
          : popup // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PropertyMapMarkerImpl extends _PropertyMapMarker {
  const _$PropertyMapMarkerImpl(
      {required this.lat,
      required this.lon,
      this.address,
      @JsonKey(fromJson: _doubleFromDynamic) this.price,
      @JsonKey(name: 'price_display') this.priceDisplay,
      @JsonKey(name: 'yield', fromJson: _doubleFromDynamic) this.yieldRate,
      @JsonKey(fromJson: _doubleFromDynamic) this.area,
      @JsonKey(name: 'approval_date') this.approvalDate,
      @JsonKey(name: 'record_id') this.recordId,
      this.popup})
      : super._();

  factory _$PropertyMapMarkerImpl.fromJson(Map<String, dynamic> json) =>
      _$$PropertyMapMarkerImplFromJson(json);

  @override
  final double lat;
  @override
  final double lon;
  @override
  final String? address;
  @override
  @JsonKey(fromJson: _doubleFromDynamic)
  final double? price;
  @override
  @JsonKey(name: 'price_display')
  final String? priceDisplay;
  @override
  @JsonKey(name: 'yield', fromJson: _doubleFromDynamic)
  final double? yieldRate;
  @override
  @JsonKey(fromJson: _doubleFromDynamic)
  final double? area;
  @override
  @JsonKey(name: 'approval_date')
  final String? approvalDate;
  @override
  @JsonKey(name: 'record_id')
  final String? recordId;
  @override
  final String? popup;

  @override
  String toString() {
    return 'PropertyMapMarker(lat: $lat, lon: $lon, address: $address, price: $price, priceDisplay: $priceDisplay, yieldRate: $yieldRate, area: $area, approvalDate: $approvalDate, recordId: $recordId, popup: $popup)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PropertyMapMarkerImpl &&
            (identical(other.lat, lat) || other.lat == lat) &&
            (identical(other.lon, lon) || other.lon == lon) &&
            (identical(other.address, address) || other.address == address) &&
            (identical(other.price, price) || other.price == price) &&
            (identical(other.priceDisplay, priceDisplay) ||
                other.priceDisplay == priceDisplay) &&
            (identical(other.yieldRate, yieldRate) ||
                other.yieldRate == yieldRate) &&
            (identical(other.area, area) || other.area == area) &&
            (identical(other.approvalDate, approvalDate) ||
                other.approvalDate == approvalDate) &&
            (identical(other.recordId, recordId) ||
                other.recordId == recordId) &&
            (identical(other.popup, popup) || other.popup == popup));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, lat, lon, address, price,
      priceDisplay, yieldRate, area, approvalDate, recordId, popup);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PropertyMapMarkerImplCopyWith<_$PropertyMapMarkerImpl> get copyWith =>
      __$$PropertyMapMarkerImplCopyWithImpl<_$PropertyMapMarkerImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PropertyMapMarkerImplToJson(
      this,
    );
  }
}

abstract class _PropertyMapMarker extends PropertyMapMarker {
  const factory _PropertyMapMarker(
      {required final double lat,
      required final double lon,
      final String? address,
      @JsonKey(fromJson: _doubleFromDynamic) final double? price,
      @JsonKey(name: 'price_display') final String? priceDisplay,
      @JsonKey(name: 'yield', fromJson: _doubleFromDynamic)
      final double? yieldRate,
      @JsonKey(fromJson: _doubleFromDynamic) final double? area,
      @JsonKey(name: 'approval_date') final String? approvalDate,
      @JsonKey(name: 'record_id') final String? recordId,
      final String? popup}) = _$PropertyMapMarkerImpl;
  const _PropertyMapMarker._() : super._();

  factory _PropertyMapMarker.fromJson(Map<String, dynamic> json) =
      _$PropertyMapMarkerImpl.fromJson;

  @override
  double get lat;
  @override
  double get lon;
  @override
  String? get address;
  @override
  @JsonKey(fromJson: _doubleFromDynamic)
  double? get price;
  @override
  @JsonKey(name: 'price_display')
  String? get priceDisplay;
  @override
  @JsonKey(name: 'yield', fromJson: _doubleFromDynamic)
  double? get yieldRate;
  @override
  @JsonKey(fromJson: _doubleFromDynamic)
  double? get area;
  @override
  @JsonKey(name: 'approval_date')
  String? get approvalDate;
  @override
  @JsonKey(name: 'record_id')
  String? get recordId;
  @override
  String? get popup;
  @override
  @JsonKey(ignore: true)
  _$$PropertyMapMarkerImplCopyWith<_$PropertyMapMarkerImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PropertyCoordinate _$PropertyCoordinateFromJson(Map<String, dynamic> json) {
  return _PropertyCoordinate.fromJson(json);
}

/// @nodoc
mixin _$PropertyCoordinate {
  double get lat => throw _privateConstructorUsedError;
  double get lon => throw _privateConstructorUsedError;
  String? get address => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PropertyCoordinateCopyWith<PropertyCoordinate> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PropertyCoordinateCopyWith<$Res> {
  factory $PropertyCoordinateCopyWith(
          PropertyCoordinate value, $Res Function(PropertyCoordinate) then) =
      _$PropertyCoordinateCopyWithImpl<$Res, PropertyCoordinate>;
  @useResult
  $Res call({double lat, double lon, String? address});
}

/// @nodoc
class _$PropertyCoordinateCopyWithImpl<$Res, $Val extends PropertyCoordinate>
    implements $PropertyCoordinateCopyWith<$Res> {
  _$PropertyCoordinateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? lat = null,
    Object? lon = null,
    Object? address = freezed,
  }) {
    return _then(_value.copyWith(
      lat: null == lat
          ? _value.lat
          : lat // ignore: cast_nullable_to_non_nullable
              as double,
      lon: null == lon
          ? _value.lon
          : lon // ignore: cast_nullable_to_non_nullable
              as double,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PropertyCoordinateImplCopyWith<$Res>
    implements $PropertyCoordinateCopyWith<$Res> {
  factory _$$PropertyCoordinateImplCopyWith(_$PropertyCoordinateImpl value,
          $Res Function(_$PropertyCoordinateImpl) then) =
      __$$PropertyCoordinateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({double lat, double lon, String? address});
}

/// @nodoc
class __$$PropertyCoordinateImplCopyWithImpl<$Res>
    extends _$PropertyCoordinateCopyWithImpl<$Res, _$PropertyCoordinateImpl>
    implements _$$PropertyCoordinateImplCopyWith<$Res> {
  __$$PropertyCoordinateImplCopyWithImpl(_$PropertyCoordinateImpl _value,
      $Res Function(_$PropertyCoordinateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? lat = null,
    Object? lon = null,
    Object? address = freezed,
  }) {
    return _then(_$PropertyCoordinateImpl(
      lat: null == lat
          ? _value.lat
          : lat // ignore: cast_nullable_to_non_nullable
              as double,
      lon: null == lon
          ? _value.lon
          : lon // ignore: cast_nullable_to_non_nullable
              as double,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PropertyCoordinateImpl implements _PropertyCoordinate {
  const _$PropertyCoordinateImpl(
      {required this.lat, required this.lon, this.address});

  factory _$PropertyCoordinateImpl.fromJson(Map<String, dynamic> json) =>
      _$$PropertyCoordinateImplFromJson(json);

  @override
  final double lat;
  @override
  final double lon;
  @override
  final String? address;

  @override
  String toString() {
    return 'PropertyCoordinate(lat: $lat, lon: $lon, address: $address)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PropertyCoordinateImpl &&
            (identical(other.lat, lat) || other.lat == lat) &&
            (identical(other.lon, lon) || other.lon == lon) &&
            (identical(other.address, address) || other.address == address));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, lat, lon, address);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PropertyCoordinateImplCopyWith<_$PropertyCoordinateImpl> get copyWith =>
      __$$PropertyCoordinateImplCopyWithImpl<_$PropertyCoordinateImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PropertyCoordinateImplToJson(
      this,
    );
  }
}

abstract class _PropertyCoordinate implements PropertyCoordinate {
  const factory _PropertyCoordinate(
      {required final double lat,
      required final double lon,
      final String? address}) = _$PropertyCoordinateImpl;

  factory _PropertyCoordinate.fromJson(Map<String, dynamic> json) =
      _$PropertyCoordinateImpl.fromJson;

  @override
  double get lat;
  @override
  double get lon;
  @override
  String? get address;
  @override
  @JsonKey(ignore: true)
  _$$PropertyCoordinateImplCopyWith<_$PropertyCoordinateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PropertySearchRequest _$PropertySearchRequestFromJson(
    Map<String, dynamic> json) {
  return _PropertySearchRequest.fromJson(json);
}

/// @nodoc
mixin _$PropertySearchRequest {
  @JsonKey(name: 'price_value')
  String? get priceValue => throw _privateConstructorUsedError;
  @JsonKey(name: 'price_condition')
  String get priceCondition => throw _privateConstructorUsedError;
  @JsonKey(name: 'yield_value')
  String? get yieldValue => throw _privateConstructorUsedError;
  @JsonKey(name: 'yield_condition')
  String get yieldCondition => throw _privateConstructorUsedError;
  @JsonKey(name: 'investment_value')
  String? get investmentValue => throw _privateConstructorUsedError;
  @JsonKey(name: 'investment_condition')
  String get investmentCondition => throw _privateConstructorUsedError;
  @JsonKey(name: 'area_value')
  String? get areaValue => throw _privateConstructorUsedError;
  @JsonKey(name: 'area_condition')
  String get areaCondition => throw _privateConstructorUsedError;
  @JsonKey(name: 'approval_date')
  String? get approvalDate => throw _privateConstructorUsedError;
  @JsonKey(name: 'approval_condition')
  String get approvalCondition => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PropertySearchRequestCopyWith<PropertySearchRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PropertySearchRequestCopyWith<$Res> {
  factory $PropertySearchRequestCopyWith(PropertySearchRequest value,
          $Res Function(PropertySearchRequest) then) =
      _$PropertySearchRequestCopyWithImpl<$Res, PropertySearchRequest>;
  @useResult
  $Res call(
      {@JsonKey(name: 'price_value') String? priceValue,
      @JsonKey(name: 'price_condition') String priceCondition,
      @JsonKey(name: 'yield_value') String? yieldValue,
      @JsonKey(name: 'yield_condition') String yieldCondition,
      @JsonKey(name: 'investment_value') String? investmentValue,
      @JsonKey(name: 'investment_condition') String investmentCondition,
      @JsonKey(name: 'area_value') String? areaValue,
      @JsonKey(name: 'area_condition') String areaCondition,
      @JsonKey(name: 'approval_date') String? approvalDate,
      @JsonKey(name: 'approval_condition') String approvalCondition});
}

/// @nodoc
class _$PropertySearchRequestCopyWithImpl<$Res,
        $Val extends PropertySearchRequest>
    implements $PropertySearchRequestCopyWith<$Res> {
  _$PropertySearchRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? priceValue = freezed,
    Object? priceCondition = null,
    Object? yieldValue = freezed,
    Object? yieldCondition = null,
    Object? investmentValue = freezed,
    Object? investmentCondition = null,
    Object? areaValue = freezed,
    Object? areaCondition = null,
    Object? approvalDate = freezed,
    Object? approvalCondition = null,
  }) {
    return _then(_value.copyWith(
      priceValue: freezed == priceValue
          ? _value.priceValue
          : priceValue // ignore: cast_nullable_to_non_nullable
              as String?,
      priceCondition: null == priceCondition
          ? _value.priceCondition
          : priceCondition // ignore: cast_nullable_to_non_nullable
              as String,
      yieldValue: freezed == yieldValue
          ? _value.yieldValue
          : yieldValue // ignore: cast_nullable_to_non_nullable
              as String?,
      yieldCondition: null == yieldCondition
          ? _value.yieldCondition
          : yieldCondition // ignore: cast_nullable_to_non_nullable
              as String,
      investmentValue: freezed == investmentValue
          ? _value.investmentValue
          : investmentValue // ignore: cast_nullable_to_non_nullable
              as String?,
      investmentCondition: null == investmentCondition
          ? _value.investmentCondition
          : investmentCondition // ignore: cast_nullable_to_non_nullable
              as String,
      areaValue: freezed == areaValue
          ? _value.areaValue
          : areaValue // ignore: cast_nullable_to_non_nullable
              as String?,
      areaCondition: null == areaCondition
          ? _value.areaCondition
          : areaCondition // ignore: cast_nullable_to_non_nullable
              as String,
      approvalDate: freezed == approvalDate
          ? _value.approvalDate
          : approvalDate // ignore: cast_nullable_to_non_nullable
              as String?,
      approvalCondition: null == approvalCondition
          ? _value.approvalCondition
          : approvalCondition // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PropertySearchRequestImplCopyWith<$Res>
    implements $PropertySearchRequestCopyWith<$Res> {
  factory _$$PropertySearchRequestImplCopyWith(
          _$PropertySearchRequestImpl value,
          $Res Function(_$PropertySearchRequestImpl) then) =
      __$$PropertySearchRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'price_value') String? priceValue,
      @JsonKey(name: 'price_condition') String priceCondition,
      @JsonKey(name: 'yield_value') String? yieldValue,
      @JsonKey(name: 'yield_condition') String yieldCondition,
      @JsonKey(name: 'investment_value') String? investmentValue,
      @JsonKey(name: 'investment_condition') String investmentCondition,
      @JsonKey(name: 'area_value') String? areaValue,
      @JsonKey(name: 'area_condition') String areaCondition,
      @JsonKey(name: 'approval_date') String? approvalDate,
      @JsonKey(name: 'approval_condition') String approvalCondition});
}

/// @nodoc
class __$$PropertySearchRequestImplCopyWithImpl<$Res>
    extends _$PropertySearchRequestCopyWithImpl<$Res,
        _$PropertySearchRequestImpl>
    implements _$$PropertySearchRequestImplCopyWith<$Res> {
  __$$PropertySearchRequestImplCopyWithImpl(_$PropertySearchRequestImpl _value,
      $Res Function(_$PropertySearchRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? priceValue = freezed,
    Object? priceCondition = null,
    Object? yieldValue = freezed,
    Object? yieldCondition = null,
    Object? investmentValue = freezed,
    Object? investmentCondition = null,
    Object? areaValue = freezed,
    Object? areaCondition = null,
    Object? approvalDate = freezed,
    Object? approvalCondition = null,
  }) {
    return _then(_$PropertySearchRequestImpl(
      priceValue: freezed == priceValue
          ? _value.priceValue
          : priceValue // ignore: cast_nullable_to_non_nullable
              as String?,
      priceCondition: null == priceCondition
          ? _value.priceCondition
          : priceCondition // ignore: cast_nullable_to_non_nullable
              as String,
      yieldValue: freezed == yieldValue
          ? _value.yieldValue
          : yieldValue // ignore: cast_nullable_to_non_nullable
              as String?,
      yieldCondition: null == yieldCondition
          ? _value.yieldCondition
          : yieldCondition // ignore: cast_nullable_to_non_nullable
              as String,
      investmentValue: freezed == investmentValue
          ? _value.investmentValue
          : investmentValue // ignore: cast_nullable_to_non_nullable
              as String?,
      investmentCondition: null == investmentCondition
          ? _value.investmentCondition
          : investmentCondition // ignore: cast_nullable_to_non_nullable
              as String,
      areaValue: freezed == areaValue
          ? _value.areaValue
          : areaValue // ignore: cast_nullable_to_non_nullable
              as String?,
      areaCondition: null == areaCondition
          ? _value.areaCondition
          : areaCondition // ignore: cast_nullable_to_non_nullable
              as String,
      approvalDate: freezed == approvalDate
          ? _value.approvalDate
          : approvalDate // ignore: cast_nullable_to_non_nullable
              as String?,
      approvalCondition: null == approvalCondition
          ? _value.approvalCondition
          : approvalCondition // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PropertySearchRequestImpl implements _PropertySearchRequest {
  const _$PropertySearchRequestImpl(
      {@JsonKey(name: 'price_value') this.priceValue,
      @JsonKey(name: 'price_condition') this.priceCondition = 'all',
      @JsonKey(name: 'yield_value') this.yieldValue,
      @JsonKey(name: 'yield_condition') this.yieldCondition = 'all',
      @JsonKey(name: 'investment_value') this.investmentValue,
      @JsonKey(name: 'investment_condition') this.investmentCondition = 'all',
      @JsonKey(name: 'area_value') this.areaValue,
      @JsonKey(name: 'area_condition') this.areaCondition = 'all',
      @JsonKey(name: 'approval_date') this.approvalDate,
      @JsonKey(name: 'approval_condition') this.approvalCondition = 'all'});

  factory _$PropertySearchRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$PropertySearchRequestImplFromJson(json);

  @override
  @JsonKey(name: 'price_value')
  final String? priceValue;
  @override
  @JsonKey(name: 'price_condition')
  final String priceCondition;
  @override
  @JsonKey(name: 'yield_value')
  final String? yieldValue;
  @override
  @JsonKey(name: 'yield_condition')
  final String yieldCondition;
  @override
  @JsonKey(name: 'investment_value')
  final String? investmentValue;
  @override
  @JsonKey(name: 'investment_condition')
  final String investmentCondition;
  @override
  @JsonKey(name: 'area_value')
  final String? areaValue;
  @override
  @JsonKey(name: 'area_condition')
  final String areaCondition;
  @override
  @JsonKey(name: 'approval_date')
  final String? approvalDate;
  @override
  @JsonKey(name: 'approval_condition')
  final String approvalCondition;

  @override
  String toString() {
    return 'PropertySearchRequest(priceValue: $priceValue, priceCondition: $priceCondition, yieldValue: $yieldValue, yieldCondition: $yieldCondition, investmentValue: $investmentValue, investmentCondition: $investmentCondition, areaValue: $areaValue, areaCondition: $areaCondition, approvalDate: $approvalDate, approvalCondition: $approvalCondition)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PropertySearchRequestImpl &&
            (identical(other.priceValue, priceValue) ||
                other.priceValue == priceValue) &&
            (identical(other.priceCondition, priceCondition) ||
                other.priceCondition == priceCondition) &&
            (identical(other.yieldValue, yieldValue) ||
                other.yieldValue == yieldValue) &&
            (identical(other.yieldCondition, yieldCondition) ||
                other.yieldCondition == yieldCondition) &&
            (identical(other.investmentValue, investmentValue) ||
                other.investmentValue == investmentValue) &&
            (identical(other.investmentCondition, investmentCondition) ||
                other.investmentCondition == investmentCondition) &&
            (identical(other.areaValue, areaValue) ||
                other.areaValue == areaValue) &&
            (identical(other.areaCondition, areaCondition) ||
                other.areaCondition == areaCondition) &&
            (identical(other.approvalDate, approvalDate) ||
                other.approvalDate == approvalDate) &&
            (identical(other.approvalCondition, approvalCondition) ||
                other.approvalCondition == approvalCondition));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      priceValue,
      priceCondition,
      yieldValue,
      yieldCondition,
      investmentValue,
      investmentCondition,
      areaValue,
      areaCondition,
      approvalDate,
      approvalCondition);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PropertySearchRequestImplCopyWith<_$PropertySearchRequestImpl>
      get copyWith => __$$PropertySearchRequestImplCopyWithImpl<
          _$PropertySearchRequestImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PropertySearchRequestImplToJson(
      this,
    );
  }
}

abstract class _PropertySearchRequest implements PropertySearchRequest {
  const factory _PropertySearchRequest(
      {@JsonKey(name: 'price_value') final String? priceValue,
      @JsonKey(name: 'price_condition') final String priceCondition,
      @JsonKey(name: 'yield_value') final String? yieldValue,
      @JsonKey(name: 'yield_condition') final String yieldCondition,
      @JsonKey(name: 'investment_value') final String? investmentValue,
      @JsonKey(name: 'investment_condition') final String investmentCondition,
      @JsonKey(name: 'area_value') final String? areaValue,
      @JsonKey(name: 'area_condition') final String areaCondition,
      @JsonKey(name: 'approval_date') final String? approvalDate,
      @JsonKey(name: 'approval_condition')
      final String approvalCondition}) = _$PropertySearchRequestImpl;

  factory _PropertySearchRequest.fromJson(Map<String, dynamic> json) =
      _$PropertySearchRequestImpl.fromJson;

  @override
  @JsonKey(name: 'price_value')
  String? get priceValue;
  @override
  @JsonKey(name: 'price_condition')
  String get priceCondition;
  @override
  @JsonKey(name: 'yield_value')
  String? get yieldValue;
  @override
  @JsonKey(name: 'yield_condition')
  String get yieldCondition;
  @override
  @JsonKey(name: 'investment_value')
  String? get investmentValue;
  @override
  @JsonKey(name: 'investment_condition')
  String get investmentCondition;
  @override
  @JsonKey(name: 'area_value')
  String? get areaValue;
  @override
  @JsonKey(name: 'area_condition')
  String get areaCondition;
  @override
  @JsonKey(name: 'approval_date')
  String? get approvalDate;
  @override
  @JsonKey(name: 'approval_condition')
  String get approvalCondition;
  @override
  @JsonKey(ignore: true)
  _$$PropertySearchRequestImplCopyWith<_$PropertySearchRequestImpl>
      get copyWith => throw _privateConstructorUsedError;
}

PropertySearchResponse _$PropertySearchResponseFromJson(
    Map<String, dynamic> json) {
  return _PropertySearchResponse.fromJson(json);
}

/// @nodoc
mixin _$PropertySearchResponse {
  int get count => throw _privateConstructorUsedError;
  @JsonKey(name: 'map_html')
  String? get mapHtml => throw _privateConstructorUsedError;
  List<PropertyRecord> get properties => throw _privateConstructorUsedError;
  List<PropertyMapMarker> get markers => throw _privateConstructorUsedError;
  Map<String, dynamic>? get statistics => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PropertySearchResponseCopyWith<PropertySearchResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PropertySearchResponseCopyWith<$Res> {
  factory $PropertySearchResponseCopyWith(PropertySearchResponse value,
          $Res Function(PropertySearchResponse) then) =
      _$PropertySearchResponseCopyWithImpl<$Res, PropertySearchResponse>;
  @useResult
  $Res call(
      {int count,
      @JsonKey(name: 'map_html') String? mapHtml,
      List<PropertyRecord> properties,
      List<PropertyMapMarker> markers,
      Map<String, dynamic>? statistics,
      String? error});
}

/// @nodoc
class _$PropertySearchResponseCopyWithImpl<$Res,
        $Val extends PropertySearchResponse>
    implements $PropertySearchResponseCopyWith<$Res> {
  _$PropertySearchResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? count = null,
    Object? mapHtml = freezed,
    Object? properties = null,
    Object? markers = null,
    Object? statistics = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      count: null == count
          ? _value.count
          : count // ignore: cast_nullable_to_non_nullable
              as int,
      mapHtml: freezed == mapHtml
          ? _value.mapHtml
          : mapHtml // ignore: cast_nullable_to_non_nullable
              as String?,
      properties: null == properties
          ? _value.properties
          : properties // ignore: cast_nullable_to_non_nullable
              as List<PropertyRecord>,
      markers: null == markers
          ? _value.markers
          : markers // ignore: cast_nullable_to_non_nullable
              as List<PropertyMapMarker>,
      statistics: freezed == statistics
          ? _value.statistics
          : statistics // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PropertySearchResponseImplCopyWith<$Res>
    implements $PropertySearchResponseCopyWith<$Res> {
  factory _$$PropertySearchResponseImplCopyWith(
          _$PropertySearchResponseImpl value,
          $Res Function(_$PropertySearchResponseImpl) then) =
      __$$PropertySearchResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int count,
      @JsonKey(name: 'map_html') String? mapHtml,
      List<PropertyRecord> properties,
      List<PropertyMapMarker> markers,
      Map<String, dynamic>? statistics,
      String? error});
}

/// @nodoc
class __$$PropertySearchResponseImplCopyWithImpl<$Res>
    extends _$PropertySearchResponseCopyWithImpl<$Res,
        _$PropertySearchResponseImpl>
    implements _$$PropertySearchResponseImplCopyWith<$Res> {
  __$$PropertySearchResponseImplCopyWithImpl(
      _$PropertySearchResponseImpl _value,
      $Res Function(_$PropertySearchResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? count = null,
    Object? mapHtml = freezed,
    Object? properties = null,
    Object? markers = null,
    Object? statistics = freezed,
    Object? error = freezed,
  }) {
    return _then(_$PropertySearchResponseImpl(
      count: null == count
          ? _value.count
          : count // ignore: cast_nullable_to_non_nullable
              as int,
      mapHtml: freezed == mapHtml
          ? _value.mapHtml
          : mapHtml // ignore: cast_nullable_to_non_nullable
              as String?,
      properties: null == properties
          ? _value._properties
          : properties // ignore: cast_nullable_to_non_nullable
              as List<PropertyRecord>,
      markers: null == markers
          ? _value._markers
          : markers // ignore: cast_nullable_to_non_nullable
              as List<PropertyMapMarker>,
      statistics: freezed == statistics
          ? _value._statistics
          : statistics // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PropertySearchResponseImpl implements _PropertySearchResponse {
  const _$PropertySearchResponseImpl(
      {this.count = 0,
      @JsonKey(name: 'map_html') this.mapHtml,
      final List<PropertyRecord> properties = const [],
      final List<PropertyMapMarker> markers = const [],
      final Map<String, dynamic>? statistics,
      this.error})
      : _properties = properties,
        _markers = markers,
        _statistics = statistics;

  factory _$PropertySearchResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$PropertySearchResponseImplFromJson(json);

  @override
  @JsonKey()
  final int count;
  @override
  @JsonKey(name: 'map_html')
  final String? mapHtml;
  final List<PropertyRecord> _properties;
  @override
  @JsonKey()
  List<PropertyRecord> get properties {
    if (_properties is EqualUnmodifiableListView) return _properties;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_properties);
  }

  final List<PropertyMapMarker> _markers;
  @override
  @JsonKey()
  List<PropertyMapMarker> get markers {
    if (_markers is EqualUnmodifiableListView) return _markers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_markers);
  }

  final Map<String, dynamic>? _statistics;
  @override
  Map<String, dynamic>? get statistics {
    final value = _statistics;
    if (value == null) return null;
    if (_statistics is EqualUnmodifiableMapView) return _statistics;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  final String? error;

  @override
  String toString() {
    return 'PropertySearchResponse(count: $count, mapHtml: $mapHtml, properties: $properties, markers: $markers, statistics: $statistics, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PropertySearchResponseImpl &&
            (identical(other.count, count) || other.count == count) &&
            (identical(other.mapHtml, mapHtml) || other.mapHtml == mapHtml) &&
            const DeepCollectionEquality()
                .equals(other._properties, _properties) &&
            const DeepCollectionEquality().equals(other._markers, _markers) &&
            const DeepCollectionEquality()
                .equals(other._statistics, _statistics) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      count,
      mapHtml,
      const DeepCollectionEquality().hash(_properties),
      const DeepCollectionEquality().hash(_markers),
      const DeepCollectionEquality().hash(_statistics),
      error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PropertySearchResponseImplCopyWith<_$PropertySearchResponseImpl>
      get copyWith => __$$PropertySearchResponseImplCopyWithImpl<
          _$PropertySearchResponseImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PropertySearchResponseImplToJson(
      this,
    );
  }
}

abstract class _PropertySearchResponse implements PropertySearchResponse {
  const factory _PropertySearchResponse(
      {final int count,
      @JsonKey(name: 'map_html') final String? mapHtml,
      final List<PropertyRecord> properties,
      final List<PropertyMapMarker> markers,
      final Map<String, dynamic>? statistics,
      final String? error}) = _$PropertySearchResponseImpl;

  factory _PropertySearchResponse.fromJson(Map<String, dynamic> json) =
      _$PropertySearchResponseImpl.fromJson;

  @override
  int get count;
  @override
  @JsonKey(name: 'map_html')
  String? get mapHtml;
  @override
  List<PropertyRecord> get properties;
  @override
  List<PropertyMapMarker> get markers;
  @override
  Map<String, dynamic>? get statistics;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$PropertySearchResponseImplCopyWith<_$PropertySearchResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}
