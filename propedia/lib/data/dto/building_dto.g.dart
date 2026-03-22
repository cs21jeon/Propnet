// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'building_dto.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$RoadSearchRequestImpl _$$RoadSearchRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$RoadSearchRequestImpl(
      roadName: json['road_name'] as String,
    );

Map<String, dynamic> _$$RoadSearchRequestImplToJson(
        _$RoadSearchRequestImpl instance) =>
    <String, dynamic>{
      'road_name': instance.roadName,
    };

_$RoadSearchResultItemImpl _$$RoadSearchResultItemImplFromJson(
        Map<String, dynamic> json) =>
    _$RoadSearchResultItemImpl(
      roadAddr: json['roadAddr'] as String,
      jibunAddr: json['jibunAddr'] as String,
      bdMgtSn: json['bdMgtSn'] as String,
      bdNm: json['bdNm'] as String?,
      zipNo: json['zipNo'] as String?,
      lnbrMnnm: json['lnbrMnnm'] as String?,
      lnbrSlno: json['lnbrSlno'] as String?,
      admCd: json['admCd'] as String?,
    );

Map<String, dynamic> _$$RoadSearchResultItemImplToJson(
        _$RoadSearchResultItemImpl instance) =>
    <String, dynamic>{
      'roadAddr': instance.roadAddr,
      'jibunAddr': instance.jibunAddr,
      'bdMgtSn': instance.bdMgtSn,
      'bdNm': instance.bdNm,
      'zipNo': instance.zipNo,
      'lnbrMnnm': instance.lnbrMnnm,
      'lnbrSlno': instance.lnbrSlno,
      'admCd': instance.admCd,
    };

_$RoadSearchResponseImpl _$$RoadSearchResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$RoadSearchResponseImpl(
      success: json['success'] as bool,
      count: (json['count'] as num?)?.toInt() ?? 0,
      results: (json['results'] as List<dynamic>?)
              ?.map((e) =>
                  RoadSearchResultItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      message: json['message'] as String?,
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$RoadSearchResponseImplToJson(
        _$RoadSearchResponseImpl instance) =>
    <String, dynamic>{
      'success': instance.success,
      'count': instance.count,
      'results': instance.results,
      'message': instance.message,
      'error': instance.error,
    };

_$JibunSearchRequestImpl _$$JibunSearchRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$JibunSearchRequestImpl(
      bjdongCode: json['bjdong_code'] as String,
      bun: json['bun'] as String,
      ji: json['ji'] as String? ?? '0000',
      landType: json['land_type'] as String? ?? '1',
    );

Map<String, dynamic> _$$JibunSearchRequestImplToJson(
        _$JibunSearchRequestImpl instance) =>
    <String, dynamic>{
      'bjdong_code': instance.bjdongCode,
      'bun': instance.bun,
      'ji': instance.ji,
      'land_type': instance.landType,
    };

_$BdMgtSnSearchRequestImpl _$$BdMgtSnSearchRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$BdMgtSnSearchRequestImpl(
      bdMgtSn: json['bdMgtSn'] as String,
      lnbrMnnm: json['lnbrMnnm'] as String?,
      lnbrSlno: json['lnbrSlno'] as String?,
      admCd: json['admCd'] as String?,
    );

Map<String, dynamic> _$$BdMgtSnSearchRequestImplToJson(
        _$BdMgtSnSearchRequestImpl instance) =>
    <String, dynamic>{
      'bdMgtSn': instance.bdMgtSn,
      'lnbrMnnm': instance.lnbrMnnm,
      'lnbrSlno': instance.lnbrSlno,
      'admCd': instance.admCd,
    };

_$CodeInfoImpl _$$CodeInfoImplFromJson(Map<String, dynamic> json) =>
    _$CodeInfoImpl(
      sigunguCd: json['sigungu_cd'] as String?,
      bjdongCd: json['bjdong_cd'] as String?,
      pnu: json['pnu'] as String?,
    );

Map<String, dynamic> _$$CodeInfoImplToJson(_$CodeInfoImpl instance) =>
    <String, dynamic>{
      'sigungu_cd': instance.sigunguCd,
      'bjdong_cd': instance.bjdongCd,
      'pnu': instance.pnu,
    };

_$AddressInfoImpl _$$AddressInfoImplFromJson(Map<String, dynamic> json) =>
    _$AddressInfoImpl(
      bjdongCode: json['bjdong_code'] as String?,
      fullAddress: json['full_address'] as String?,
      sidoName: json['sido_name'] as String?,
      sigunguName: json['sigungu_name'] as String?,
      eupmyeondongName: json['eupmyeondong_name'] as String?,
    );

Map<String, dynamic> _$$AddressInfoImplToJson(_$AddressInfoImpl instance) =>
    <String, dynamic>{
      'bjdong_code': instance.bjdongCode,
      'full_address': instance.fullAddress,
      'sido_name': instance.sidoName,
      'sigungu_name': instance.sigunguName,
      'eupmyeondong_name': instance.eupmyeondongName,
    };

_$BuildingBasicInfoImpl _$$BuildingBasicInfoImplFromJson(
        Map<String, dynamic> json) =>
    _$BuildingBasicInfoImpl(
      buildingName: json['building_name'] as String?,
      dongNm: json['dong_nm'] as String?,
      platPlc: json['plat_plc'] as String?,
      newPlatPlc: json['new_plat_plc'] as String?,
      mainPurpose: json['main_purpose'] as String?,
      etcPurpose: json['etc_purpose'] as String?,
      mainStructure: json['main_structure'] as String?,
      roof: json['roof'] as String?,
      etcRoof: json['etc_roof'] as String?,
      totalFloors: (json['total_floors'] as num?)?.toInt(),
      basementFloors: (json['basement_floors'] as num?)?.toInt(),
      height: (json['height'] as num?)?.toDouble(),
      landArea: (json['land_area'] as num?)?.toDouble(),
      buildingArea: (json['building_area'] as num?)?.toDouble(),
      totalArea: (json['total_area'] as num?)?.toDouble(),
      vlRatEstmTotArea: (json['vl_rat_estm_tot_area'] as num?)?.toDouble(),
      buildingCoverage: (json['building_coverage'] as num?)?.toDouble(),
      floorAreaRatio: (json['floor_area_ratio'] as num?)?.toDouble(),
      familyCnt: _intFromDynamic(json['family_cnt']),
      hhldCnt: _intFromDynamic(json['hhld_cnt']),
      hoCnt: _intFromDynamic(json['ho_cnt']),
      elevatorCount: _intFromDynamic(json['elevator_count']),
      emergencyElevatorCount: _intFromDynamic(json['emergency_elevator_count']),
      totalParking: _stringFromDynamic(json['total_parking']),
      permitDate: json['permit_date'] as String?,
      useApprovalDate: json['use_approval_date'] as String?,
      permitDateRaw: json['permit_date_raw'] as String?,
      useApprovalDateRaw: json['use_approval_date_raw'] as String?,
      housePrice: (json['house_price'] as num?)?.toInt(),
      housePriceYear: json['house_price_year'] as String?,
      housePriceMonth: json['house_price_month'] as String?,
    );

Map<String, dynamic> _$$BuildingBasicInfoImplToJson(
        _$BuildingBasicInfoImpl instance) =>
    <String, dynamic>{
      'building_name': instance.buildingName,
      'dong_nm': instance.dongNm,
      'plat_plc': instance.platPlc,
      'new_plat_plc': instance.newPlatPlc,
      'main_purpose': instance.mainPurpose,
      'etc_purpose': instance.etcPurpose,
      'main_structure': instance.mainStructure,
      'roof': instance.roof,
      'etc_roof': instance.etcRoof,
      'total_floors': instance.totalFloors,
      'basement_floors': instance.basementFloors,
      'height': instance.height,
      'land_area': instance.landArea,
      'building_area': instance.buildingArea,
      'total_area': instance.totalArea,
      'vl_rat_estm_tot_area': instance.vlRatEstmTotArea,
      'building_coverage': instance.buildingCoverage,
      'floor_area_ratio': instance.floorAreaRatio,
      'family_cnt': instance.familyCnt,
      'hhld_cnt': instance.hhldCnt,
      'ho_cnt': instance.hoCnt,
      'elevator_count': instance.elevatorCount,
      'emergency_elevator_count': instance.emergencyElevatorCount,
      'total_parking': instance.totalParking,
      'permit_date': instance.permitDate,
      'use_approval_date': instance.useApprovalDate,
      'permit_date_raw': instance.permitDateRaw,
      'use_approval_date_raw': instance.useApprovalDateRaw,
      'house_price': instance.housePrice,
      'house_price_year': instance.housePriceYear,
      'house_price_month': instance.housePriceMonth,
    };

_$FloorInfoImpl _$$FloorInfoImplFromJson(Map<String, dynamic> json) =>
    _$FloorInfoImpl(
      floorNo: (json['floor_no'] as num?)?.toInt(),
      floorName: json['floor_name'] as String?,
      floorGb: json['floor_gb'] as String?,
      area: (json['area'] as num?)?.toDouble(),
      purpose: json['purpose'] as String?,
      etcPurpose: json['etc_purpose'] as String?,
      structure: json['structure'] as String?,
    );

Map<String, dynamic> _$$FloorInfoImplToJson(_$FloorInfoImpl instance) =>
    <String, dynamic>{
      'floor_no': instance.floorNo,
      'floor_name': instance.floorName,
      'floor_gb': instance.floorGb,
      'area': instance.area,
      'purpose': instance.purpose,
      'etc_purpose': instance.etcPurpose,
      'structure': instance.structure,
    };

_$BuildingInfoImpl _$$BuildingInfoImplFromJson(Map<String, dynamic> json) =>
    _$BuildingInfoImpl(
      hasData: json['has_data'] as bool? ?? false,
      type: json['type'] as String?,
      buildingInfo: json['building_info'] == null
          ? null
          : BuildingBasicInfo.fromJson(
              json['building_info'] as Map<String, dynamic>),
      recapTitleInfo: json['recap_title_info'] as Map<String, dynamic>?,
      dongHoDict: json['dong_ho_dict'] as Map<String, dynamic>?,
      floorInfo: (json['floor_info'] as List<dynamic>?)
          ?.map((e) => FloorInfo.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$$BuildingInfoImplToJson(_$BuildingInfoImpl instance) =>
    <String, dynamic>{
      'has_data': instance.hasData,
      'type': instance.type,
      'building_info': instance.buildingInfo,
      'recap_title_info': instance.recapTitleInfo,
      'dong_ho_dict': instance.dongHoDict,
      'floor_info': instance.floorInfo,
    };

_$LandInfoImpl _$$LandInfoImplFromJson(Map<String, dynamic> json) =>
    _$LandInfoImpl(
      landArea: (json['land_area'] as num?)?.toDouble(),
      parcelCount: (json['parcel_count'] as num?)?.toInt(),
      landCategory: json['land_category'] as String?,
      landCategoryName: json['land_category_name'] as String?,
      publicLandPrice: (json['public_land_price'] as num?)?.toInt(),
      priceYear: json['price_year'] as String?,
      zoneClassification: json['zone_classification'] as String?,
      landUseSituationName: json['land_use_situation_name'] as String?,
      topographyHeightName: json['topography_height_name'] as String?,
      topographyFormName: json['topography_form_name'] as String?,
      roadSideName: json['road_side_name'] as String?,
      details: (json['details'] as List<dynamic>?)
          ?.map((e) => e as Map<String, dynamic>)
          .toList(),
    );

Map<String, dynamic> _$$LandInfoImplToJson(_$LandInfoImpl instance) =>
    <String, dynamic>{
      'land_area': instance.landArea,
      'parcel_count': instance.parcelCount,
      'land_category': instance.landCategory,
      'land_category_name': instance.landCategoryName,
      'public_land_price': instance.publicLandPrice,
      'price_year': instance.priceYear,
      'zone_classification': instance.zoneClassification,
      'land_use_situation_name': instance.landUseSituationName,
      'topography_height_name': instance.topographyHeightName,
      'topography_form_name': instance.topographyFormName,
      'road_side_name': instance.roadSideName,
      'details': instance.details,
    };

_$BuildingSearchResponseImpl _$$BuildingSearchResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$BuildingSearchResponseImpl(
      success: json['success'] as bool,
      codes: json['codes'] == null
          ? null
          : CodeInfo.fromJson(json['codes'] as Map<String, dynamic>),
      address: json['address'] == null
          ? null
          : AddressInfo.fromJson(json['address'] as Map<String, dynamic>),
      building: json['building'] == null
          ? null
          : BuildingInfo.fromJson(json['building'] as Map<String, dynamic>),
      land: json['land'] == null
          ? null
          : LandInfo.fromJson(json['land'] as Map<String, dynamic>),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$BuildingSearchResponseImplToJson(
        _$BuildingSearchResponseImpl instance) =>
    <String, dynamic>{
      'success': instance.success,
      'codes': instance.codes,
      'address': instance.address,
      'building': instance.building,
      'land': instance.land,
      'error': instance.error,
    };

_$BjdongSearchItemImpl _$$BjdongSearchItemImplFromJson(
        Map<String, dynamic> json) =>
    _$BjdongSearchItemImpl(
      code: json['bjdong_code'] as String,
      fullAddress: json['full_address'] as String?,
      sidoName: json['sido_name'] as String?,
      sigunguName: json['sigungu_name'] as String?,
      eupmyeondongName: json['eupmyeondong_name'] as String?,
      riName: json['ri_name'] as String?,
    );

Map<String, dynamic> _$$BjdongSearchItemImplToJson(
        _$BjdongSearchItemImpl instance) =>
    <String, dynamic>{
      'bjdong_code': instance.code,
      'full_address': instance.fullAddress,
      'sido_name': instance.sidoName,
      'sigungu_name': instance.sigunguName,
      'eupmyeondong_name': instance.eupmyeondongName,
      'ri_name': instance.riName,
    };

_$BjdongSearchResponseImpl _$$BjdongSearchResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$BjdongSearchResponseImpl(
      success: json['success'] as bool,
      count: (json['count'] as num?)?.toInt() ?? 0,
      results: (json['results'] as List<dynamic>?)
              ?.map((e) => BjdongSearchItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$BjdongSearchResponseImplToJson(
        _$BjdongSearchResponseImpl instance) =>
    <String, dynamic>{
      'success': instance.success,
      'count': instance.count,
      'results': instance.results,
      'error': instance.error,
    };

_$AreaInfoRequestImpl _$$AreaInfoRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$AreaInfoRequestImpl(
      bjdongCode: json['bjdong_code'] as String,
      bun: json['bun'] as String,
      ji: json['ji'] as String? ?? '0000',
      dongNm: json['dong_nm'] as String,
      hoNm: json['ho_nm'] as String,
    );

Map<String, dynamic> _$$AreaInfoRequestImplToJson(
        _$AreaInfoRequestImpl instance) =>
    <String, dynamic>{
      'bjdong_code': instance.bjdongCode,
      'bun': instance.bun,
      'ji': instance.ji,
      'dong_nm': instance.dongNm,
      'ho_nm': instance.hoNm,
    };

_$AreaInfoImpl _$$AreaInfoImplFromJson(Map<String, dynamic> json) =>
    _$AreaInfoImpl(
      dongNm: json['dong_nm'] as String?,
      hoNm: json['ho_nm'] as String?,
      bldNm: json['bld_nm'] as String?,
      floorNo: (json['floor_no'] as num?)?.toInt(),
      floorGb: json['floor_gb'] as String?,
      exclusiveArea: (json['exclusive_area'] as num?)?.toDouble(),
      supplyArea: (json['supply_area'] as num?)?.toDouble(),
      saleArea: (json['sale_area'] as num?)?.toDouble(),
      landShare: (json['land_share'] as num?)?.toDouble(),
      landShareRatio: json['land_share_ratio'] as String?,
      housePrice: (json['house_price'] as num?)?.toInt(),
      housePriceYear: json['house_price_year'] as String?,
      housePriceMonth: json['house_price_month'] as String?,
      mainPurpose: json['main_purpose'] as String?,
      etcPurpose: json['etc_purpose'] as String?,
      dongTitleInfo: json['dong_title_info'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$$AreaInfoImplToJson(_$AreaInfoImpl instance) =>
    <String, dynamic>{
      'dong_nm': instance.dongNm,
      'ho_nm': instance.hoNm,
      'bld_nm': instance.bldNm,
      'floor_no': instance.floorNo,
      'floor_gb': instance.floorGb,
      'exclusive_area': instance.exclusiveArea,
      'supply_area': instance.supplyArea,
      'sale_area': instance.saleArea,
      'land_share': instance.landShare,
      'land_share_ratio': instance.landShareRatio,
      'house_price': instance.housePrice,
      'house_price_year': instance.housePriceYear,
      'house_price_month': instance.housePriceMonth,
      'main_purpose': instance.mainPurpose,
      'etc_purpose': instance.etcPurpose,
      'dong_title_info': instance.dongTitleInfo,
    };

_$AreaInfoResponseImpl _$$AreaInfoResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$AreaInfoResponseImpl(
      success: json['success'] as bool,
      areaInfo: json['area_info'] == null
          ? null
          : AreaInfo.fromJson(json['area_info'] as Map<String, dynamic>),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$AreaInfoResponseImplToJson(
        _$AreaInfoResponseImpl instance) =>
    <String, dynamic>{
      'success': instance.success,
      'area_info': instance.areaInfo,
      'error': instance.error,
    };
