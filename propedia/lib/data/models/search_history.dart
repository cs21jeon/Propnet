import 'package:hive_flutter/hive_flutter.dart';

part 'search_history.g.dart';

@HiveType(typeId: 0)
class SearchHistory extends HiveObject {
  @HiveField(0)
  String id;

  @HiveField(1)
  String searchType; // 'road', 'jibun', 'map', 'bdmgtsn'

  @HiveField(2)
  String displayAddress; // 표시용 주소

  @HiveField(3)
  String? roadAddress; // 도로명주소

  @HiveField(4)
  String? jibunAddress; // 지번주소

  @HiveField(5)
  String? buildingName; // 건물명

  @HiveField(6)
  String? pnu; // PNU 코드

  @HiveField(7)
  String? bdMgtSn; // 건물관리번호

  @HiveField(8)
  DateTime searchedAt;

  @HiveField(9)
  String? dongName; // 공동주택 동명

  @HiveField(10)
  String? hoName; // 공동주택 호명

  @HiveField(11)
  String? buildingType; // 'general', 'multi_unit', 'land_only'

  SearchHistory({
    required this.id,
    required this.searchType,
    required this.displayAddress,
    this.roadAddress,
    this.jibunAddress,
    this.buildingName,
    this.pnu,
    this.bdMgtSn,
    required this.searchedAt,
    this.dongName,
    this.hoName,
    this.buildingType,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'search_type': searchType,
        'display_address': displayAddress,
        'road_address': roadAddress,
        'jibun_address': jibunAddress,
        'building_name': buildingName,
        'pnu': pnu,
        'bd_mgt_sn': bdMgtSn,
        'searched_at': searchedAt.toIso8601String(),
        'dong_name': dongName,
        'ho_name': hoName,
        'building_type': buildingType,
      };

  factory SearchHistory.fromJson(Map<String, dynamic> json) => SearchHistory(
        id: json['id'] as String,
        searchType: json['search_type'] as String,
        displayAddress: json['display_address'] as String,
        roadAddress: json['road_address'] as String?,
        jibunAddress: json['jibun_address'] as String?,
        buildingName: json['building_name'] as String?,
        pnu: json['pnu'] as String?,
        bdMgtSn: json['bd_mgt_sn'] as String?,
        searchedAt: DateTime.parse(json['searched_at'] as String),
        dongName: json['dong_name'] as String?,
        hoName: json['ho_name'] as String?,
        buildingType: json['building_type'] as String?,
      );
}
