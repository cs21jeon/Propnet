// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'property_dto.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$PropertyRecordImpl _$$PropertyRecordImplFromJson(Map<String, dynamic> json) =>
    _$PropertyRecordImpl(
      id: json['id'] as String,
      fields: PropertyFields.fromJson(json['fields'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$PropertyRecordImplToJson(
        _$PropertyRecordImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'fields': instance.fields,
    };

_$PropertyFieldsImpl _$$PropertyFieldsImplFromJson(Map<String, dynamic> json) =>
    _$PropertyFieldsImpl(
      address: json['지번 주소'] as String?,
      roadAddress: json['도로명주소'] as String?,
      price: _intFromDynamic(json['매가(만원)']),
      deposit: _intFromDynamic(json['보증금(만원)']),
      monthlyRent: _intFromDynamic(json['월세(만원)']),
      loan: _intFromDynamic(json['융자(만원)']),
      investment: _intFromDynamic(json['실투자금']),
      yieldRate: _doubleFromDynamic(json['융자제외수익률(%)']),
      appraisedValue: _intFromDynamic(json['감정가(만원,랜드북)']),
      appraisalRate: _doubleFromDynamic(json['감정가율(%)']),
      landArea: _doubleFromDynamic(json['토지면적(㎡)']),
      totalFloorArea: _doubleFromDynamic(json['연면적(㎡)']),
      buildingArea: _doubleFromDynamic(json['건축면적(㎡)']),
      farArea: _doubleFromDynamic(json['용적률산정용연면적(㎡)']),
      floors: json['층수'] as String?,
      mainUsage: json['주용도'] as String?,
      etcUsage: json['기타용도'] as String?,
      structure: json['주구조'] as String?,
      roof: json['지붕'] as String?,
      approvalDate: json['사용승인일'] as String?,
      buildingName: json['건물명'] as String?,
      buildingComposition: json['건물구성'] as String?,
      buildingCoverageRatio: _doubleFromDynamic(json['건폐율(%)']),
      floorAreaRatio: _doubleFromDynamic(json['용적률(%)']),
      height: _doubleFromDynamic(json['높이(m)']),
      parkingCount: _intFromDynamic(json['주차대수']),
      elevatorCount: _intFromDynamic(json['승강기수']),
      householdInfo: json['세대/가구/호'] as String?,
      zoning: json['용도지역'] as String?,
      landPrice: _intFromDynamic(json['공시지가(원/㎡)']),
      nearStation: json['인접역'] as String?,
      stationDistance: _intFromDynamic(json['거리(m)']),
      status: _statusFromDynamic(json['현황']),
      description: json['광고(자동완성)'] as String?,
      mapLink: json['지도'] as String?,
      photoLink: json['사진링크'] as String?,
      discoLink: json['디스코광고'] as String?,
      representativePhoto: (json['대표사진'] as List<dynamic>?)
          ?.map((e) => AirtableAttachment.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$$PropertyFieldsImplToJson(
        _$PropertyFieldsImpl instance) =>
    <String, dynamic>{
      '지번 주소': instance.address,
      '도로명주소': instance.roadAddress,
      '매가(만원)': instance.price,
      '보증금(만원)': instance.deposit,
      '월세(만원)': instance.monthlyRent,
      '융자(만원)': instance.loan,
      '실투자금': instance.investment,
      '융자제외수익률(%)': instance.yieldRate,
      '감정가(만원,랜드북)': instance.appraisedValue,
      '감정가율(%)': instance.appraisalRate,
      '토지면적(㎡)': instance.landArea,
      '연면적(㎡)': instance.totalFloorArea,
      '건축면적(㎡)': instance.buildingArea,
      '용적률산정용연면적(㎡)': instance.farArea,
      '층수': instance.floors,
      '주용도': instance.mainUsage,
      '기타용도': instance.etcUsage,
      '주구조': instance.structure,
      '지붕': instance.roof,
      '사용승인일': instance.approvalDate,
      '건물명': instance.buildingName,
      '건물구성': instance.buildingComposition,
      '건폐율(%)': instance.buildingCoverageRatio,
      '용적률(%)': instance.floorAreaRatio,
      '높이(m)': instance.height,
      '주차대수': instance.parkingCount,
      '승강기수': instance.elevatorCount,
      '세대/가구/호': instance.householdInfo,
      '용도지역': instance.zoning,
      '공시지가(원/㎡)': instance.landPrice,
      '인접역': instance.nearStation,
      '거리(m)': instance.stationDistance,
      '현황': instance.status,
      '광고(자동완성)': instance.description,
      '지도': instance.mapLink,
      '사진링크': instance.photoLink,
      '디스코광고': instance.discoLink,
      '대표사진': instance.representativePhoto,
    };

_$AirtableAttachmentImpl _$$AirtableAttachmentImplFromJson(
        Map<String, dynamic> json) =>
    _$AirtableAttachmentImpl(
      id: json['id'] as String?,
      url: json['url'] as String?,
      filename: json['filename'] as String?,
      size: (json['size'] as num?)?.toInt(),
      type: json['type'] as String?,
      width: (json['width'] as num?)?.toInt(),
      height: (json['height'] as num?)?.toInt(),
      thumbnails: json['thumbnails'] == null
          ? null
          : AirtableThumbnails.fromJson(
              json['thumbnails'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$AirtableAttachmentImplToJson(
        _$AirtableAttachmentImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'url': instance.url,
      'filename': instance.filename,
      'size': instance.size,
      'type': instance.type,
      'width': instance.width,
      'height': instance.height,
      'thumbnails': instance.thumbnails,
    };

_$AirtableThumbnailsImpl _$$AirtableThumbnailsImplFromJson(
        Map<String, dynamic> json) =>
    _$AirtableThumbnailsImpl(
      small: json['small'] == null
          ? null
          : AirtableThumbnail.fromJson(json['small'] as Map<String, dynamic>),
      large: json['large'] == null
          ? null
          : AirtableThumbnail.fromJson(json['large'] as Map<String, dynamic>),
      full: json['full'] == null
          ? null
          : AirtableThumbnail.fromJson(json['full'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$AirtableThumbnailsImplToJson(
        _$AirtableThumbnailsImpl instance) =>
    <String, dynamic>{
      'small': instance.small,
      'large': instance.large,
      'full': instance.full,
    };

_$AirtableThumbnailImpl _$$AirtableThumbnailImplFromJson(
        Map<String, dynamic> json) =>
    _$AirtableThumbnailImpl(
      url: json['url'] as String?,
      width: (json['width'] as num?)?.toInt(),
      height: (json['height'] as num?)?.toInt(),
    );

Map<String, dynamic> _$$AirtableThumbnailImplToJson(
        _$AirtableThumbnailImpl instance) =>
    <String, dynamic>{
      'url': instance.url,
      'width': instance.width,
      'height': instance.height,
    };

_$PropertyListResponseImpl _$$PropertyListResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$PropertyListResponseImpl(
      records: (json['records'] as List<dynamic>?)
              ?.map((e) => PropertyRecord.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$PropertyListResponseImplToJson(
        _$PropertyListResponseImpl instance) =>
    <String, dynamic>{
      'records': instance.records,
      'error': instance.error,
    };

_$CategoryPropertiesResponseImpl _$$CategoryPropertiesResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$CategoryPropertiesResponseImpl(
      records: (json['records'] as List<dynamic>?)
              ?.map((e) => PropertyRecord.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      viewId: json['view_id'] as String?,
      totalCount: (json['total_count'] as num?)?.toInt() ?? 0,
      source: json['source'] as String?,
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$CategoryPropertiesResponseImplToJson(
        _$CategoryPropertiesResponseImpl instance) =>
    <String, dynamic>{
      'records': instance.records,
      'view_id': instance.viewId,
      'total_count': instance.totalCount,
      'source': instance.source,
      'error': instance.error,
    };

_$PropertyDetailResponseImpl _$$PropertyDetailResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$PropertyDetailResponseImpl(
      property: json['property'] == null
          ? null
          : PropertyRecord.fromJson(json['property'] as Map<String, dynamic>),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$PropertyDetailResponseImplToJson(
        _$PropertyDetailResponseImpl instance) =>
    <String, dynamic>{
      'property': instance.property,
      'error': instance.error,
    };

_$ImageCheckResponseImpl _$$ImageCheckResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$ImageCheckResponseImpl(
      hasImage: json['hasImage'] as bool? ?? false,
      filename: json['filename'] as String?,
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$ImageCheckResponseImplToJson(
        _$ImageCheckResponseImpl instance) =>
    <String, dynamic>{
      'hasImage': instance.hasImage,
      'filename': instance.filename,
      'error': instance.error,
    };

_$PropertyMapMarkerImpl _$$PropertyMapMarkerImplFromJson(
        Map<String, dynamic> json) =>
    _$PropertyMapMarkerImpl(
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
      address: json['address'] as String?,
      price: _doubleFromDynamic(json['price']),
      priceDisplay: json['price_display'] as String?,
      yieldRate: _doubleFromDynamic(json['yield']),
      area: _doubleFromDynamic(json['area']),
      approvalDate: json['approval_date'] as String?,
      recordId: json['record_id'] as String?,
      popup: json['popup'] as String?,
    );

Map<String, dynamic> _$$PropertyMapMarkerImplToJson(
        _$PropertyMapMarkerImpl instance) =>
    <String, dynamic>{
      'lat': instance.lat,
      'lon': instance.lon,
      'address': instance.address,
      'price': instance.price,
      'price_display': instance.priceDisplay,
      'yield': instance.yieldRate,
      'area': instance.area,
      'approval_date': instance.approvalDate,
      'record_id': instance.recordId,
      'popup': instance.popup,
    };

_$PropertyCoordinateImpl _$$PropertyCoordinateImplFromJson(
        Map<String, dynamic> json) =>
    _$PropertyCoordinateImpl(
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
      address: json['address'] as String?,
    );

Map<String, dynamic> _$$PropertyCoordinateImplToJson(
        _$PropertyCoordinateImpl instance) =>
    <String, dynamic>{
      'lat': instance.lat,
      'lon': instance.lon,
      'address': instance.address,
    };

_$PropertySearchRequestImpl _$$PropertySearchRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$PropertySearchRequestImpl(
      priceValue: json['price_value'] as String?,
      priceCondition: json['price_condition'] as String? ?? 'all',
      yieldValue: json['yield_value'] as String?,
      yieldCondition: json['yield_condition'] as String? ?? 'all',
      investmentValue: json['investment_value'] as String?,
      investmentCondition: json['investment_condition'] as String? ?? 'all',
      areaValue: json['area_value'] as String?,
      areaCondition: json['area_condition'] as String? ?? 'all',
      approvalDate: json['approval_date'] as String?,
      approvalCondition: json['approval_condition'] as String? ?? 'all',
    );

Map<String, dynamic> _$$PropertySearchRequestImplToJson(
        _$PropertySearchRequestImpl instance) =>
    <String, dynamic>{
      'price_value': instance.priceValue,
      'price_condition': instance.priceCondition,
      'yield_value': instance.yieldValue,
      'yield_condition': instance.yieldCondition,
      'investment_value': instance.investmentValue,
      'investment_condition': instance.investmentCondition,
      'area_value': instance.areaValue,
      'area_condition': instance.areaCondition,
      'approval_date': instance.approvalDate,
      'approval_condition': instance.approvalCondition,
    };

_$PropertySearchResponseImpl _$$PropertySearchResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$PropertySearchResponseImpl(
      count: (json['count'] as num?)?.toInt() ?? 0,
      mapHtml: json['map_html'] as String?,
      properties: (json['properties'] as List<dynamic>?)
              ?.map((e) => PropertyRecord.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      markers: (json['markers'] as List<dynamic>?)
              ?.map(
                  (e) => PropertyMapMarker.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      statistics: json['statistics'] as Map<String, dynamic>?,
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$PropertySearchResponseImplToJson(
        _$PropertySearchResponseImpl instance) =>
    <String, dynamic>{
      'count': instance.count,
      'map_html': instance.mapHtml,
      'properties': instance.properties,
      'markers': instance.markers,
      'statistics': instance.statistics,
      'error': instance.error,
    };
