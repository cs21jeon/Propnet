import 'package:hive_flutter/hive_flutter.dart';

part 'favorite.g.dart';

@HiveType(typeId: 1)
class Favorite extends HiveObject {
  @HiveField(0)
  String id;

  @HiveField(1)
  String displayAddress; // 표시용 주소

  @HiveField(2)
  String? roadAddress; // 도로명주소

  @HiveField(3)
  String? jibunAddress; // 지번주소

  @HiveField(4)
  String? buildingName; // 건물명

  @HiveField(5)
  String? pnu; // PNU 코드

  @HiveField(6)
  String? bdMgtSn; // 건물관리번호

  @HiveField(7)
  DateTime createdAt;

  @HiveField(8)
  String? dongName; // 공동주택 동명

  @HiveField(9)
  String? hoName; // 공동주택 호명

  @HiveField(10)
  String? buildingType; // 'general', 'multi_unit', 'land_only'

  @HiveField(11)
  String? memo; // 사용자 메모

  @HiveField(12)
  int? serverId; // 서버 동기화 ID

  Favorite({
    required this.id,
    required this.displayAddress,
    this.roadAddress,
    this.jibunAddress,
    this.buildingName,
    this.pnu,
    this.bdMgtSn,
    required this.createdAt,
    this.dongName,
    this.hoName,
    this.buildingType,
    this.memo,
    this.serverId,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'display_address': displayAddress,
        'road_address': roadAddress,
        'jibun_address': jibunAddress,
        'building_name': buildingName,
        'pnu': pnu,
        'bd_mgt_sn': bdMgtSn,
        'created_at': createdAt.toIso8601String(),
        'dong_name': dongName,
        'ho_name': hoName,
        'building_type': buildingType,
        'memo': memo,
        'server_id': serverId,
      };

  factory Favorite.fromJson(Map<String, dynamic> json) => Favorite(
        id: json['id'] as String,
        displayAddress: json['display_address'] as String,
        roadAddress: json['road_address'] as String?,
        jibunAddress: json['jibun_address'] as String?,
        buildingName: json['building_name'] as String?,
        pnu: json['pnu'] as String?,
        bdMgtSn: json['bd_mgt_sn'] as String?,
        createdAt: DateTime.parse(json['created_at'] as String),
        dongName: json['dong_name'] as String?,
        hoName: json['ho_name'] as String?,
        buildingType: json['building_type'] as String?,
        memo: json['memo'] as String?,
        serverId: json['server_id'] as int?,
      );
}
