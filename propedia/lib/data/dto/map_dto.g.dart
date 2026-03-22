// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'map_dto.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$MapClickJibunRequestImpl _$$MapClickJibunRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$MapClickJibunRequestImpl(
      lat: (json['lat'] as num).toDouble(),
      lng: (json['lng'] as num).toDouble(),
    );

Map<String, dynamic> _$$MapClickJibunRequestImplToJson(
        _$MapClickJibunRequestImpl instance) =>
    <String, dynamic>{
      'lat': instance.lat,
      'lng': instance.lng,
    };

_$JibunInfoImpl _$$JibunInfoImplFromJson(Map<String, dynamic> json) =>
    _$JibunInfoImpl(
      address: json['address'] as String,
      pnu: json['pnu'] as String,
      bjdongCode: json['bjdong_code'] as String,
      bun: json['bun'] as String,
      ji: json['ji'] as String,
      landType: json['land_type'] as String,
      landTypeName: json['land_type_name'] as String?,
      roadAddress: json['road_address'] as String?,
      mainPurpose: json['main_purpose'] as String?,
    );

Map<String, dynamic> _$$JibunInfoImplToJson(_$JibunInfoImpl instance) =>
    <String, dynamic>{
      'address': instance.address,
      'pnu': instance.pnu,
      'bjdong_code': instance.bjdongCode,
      'bun': instance.bun,
      'ji': instance.ji,
      'land_type': instance.landType,
      'land_type_name': instance.landTypeName,
      'road_address': instance.roadAddress,
      'main_purpose': instance.mainPurpose,
    };

_$MapClickJibunResponseImpl _$$MapClickJibunResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$MapClickJibunResponseImpl(
      success: json['success'] as bool,
      jibunInfo: json['jibun_info'] == null
          ? null
          : JibunInfo.fromJson(json['jibun_info'] as Map<String, dynamic>),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$MapClickJibunResponseImplToJson(
        _$MapClickJibunResponseImpl instance) =>
    <String, dynamic>{
      'success': instance.success,
      'jibun_info': instance.jibunInfo,
      'error': instance.error,
    };

_$ParcelGeometryImpl _$$ParcelGeometryImplFromJson(Map<String, dynamic> json) =>
    _$ParcelGeometryImpl(
      type: json['type'] as String,
      coordinates: json['coordinates'] as List<dynamic>,
    );

Map<String, dynamic> _$$ParcelGeometryImplToJson(
        _$ParcelGeometryImpl instance) =>
    <String, dynamic>{
      'type': instance.type,
      'coordinates': instance.coordinates,
    };

_$ParcelPropertiesImpl _$$ParcelPropertiesImplFromJson(
        Map<String, dynamic> json) =>
    _$ParcelPropertiesImpl(
      addr: json['addr'] as String?,
      pnu: json['pnu'] as String?,
      jibun: json['jibun'] as String?,
      jiga: json['jiga'] as String?,
      gosiYear: json['gosi_year'] as String?,
    );

Map<String, dynamic> _$$ParcelPropertiesImplToJson(
        _$ParcelPropertiesImpl instance) =>
    <String, dynamic>{
      'addr': instance.addr,
      'pnu': instance.pnu,
      'jibun': instance.jibun,
      'jiga': instance.jiga,
      'gosi_year': instance.gosiYear,
    };

_$ParcelBoundaryResponseImpl _$$ParcelBoundaryResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$ParcelBoundaryResponseImpl(
      success: json['success'] as bool,
      geometry: json['geometry'] == null
          ? null
          : ParcelGeometry.fromJson(json['geometry'] as Map<String, dynamic>),
      properties: json['properties'] == null
          ? null
          : ParcelProperties.fromJson(
              json['properties'] as Map<String, dynamic>),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$ParcelBoundaryResponseImplToJson(
        _$ParcelBoundaryResponseImpl instance) =>
    <String, dynamic>{
      'success': instance.success,
      'geometry': instance.geometry,
      'properties': instance.properties,
      'error': instance.error,
    };

_$GeocodingResponseImpl _$$GeocodingResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$GeocodingResponseImpl(
      success: json['success'] as bool,
      lat: (json['lat'] as num?)?.toDouble(),
      lng: (json['lng'] as num?)?.toDouble(),
      address: json['address'] as String?,
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$GeocodingResponseImplToJson(
        _$GeocodingResponseImpl instance) =>
    <String, dynamic>{
      'success': instance.success,
      'lat': instance.lat,
      'lng': instance.lng,
      'address': instance.address,
      'error': instance.error,
    };
