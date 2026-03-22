// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'favorite.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class FavoriteAdapter extends TypeAdapter<Favorite> {
  @override
  final int typeId = 1;

  @override
  Favorite read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return Favorite(
      id: fields[0] as String,
      displayAddress: fields[1] as String,
      roadAddress: fields[2] as String?,
      jibunAddress: fields[3] as String?,
      buildingName: fields[4] as String?,
      pnu: fields[5] as String?,
      bdMgtSn: fields[6] as String?,
      createdAt: fields[7] as DateTime,
      dongName: fields[8] as String?,
      hoName: fields[9] as String?,
      buildingType: fields[10] as String?,
      memo: fields[11] as String?,
      serverId: fields[12] as int?,
    );
  }

  @override
  void write(BinaryWriter writer, Favorite obj) {
    writer
      ..writeByte(13)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.displayAddress)
      ..writeByte(2)
      ..write(obj.roadAddress)
      ..writeByte(3)
      ..write(obj.jibunAddress)
      ..writeByte(4)
      ..write(obj.buildingName)
      ..writeByte(5)
      ..write(obj.pnu)
      ..writeByte(6)
      ..write(obj.bdMgtSn)
      ..writeByte(7)
      ..write(obj.createdAt)
      ..writeByte(8)
      ..write(obj.dongName)
      ..writeByte(9)
      ..write(obj.hoName)
      ..writeByte(10)
      ..write(obj.buildingType)
      ..writeByte(11)
      ..write(obj.memo)
      ..writeByte(12)
      ..write(obj.serverId);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is FavoriteAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
