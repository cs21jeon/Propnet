// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'search_history.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class SearchHistoryAdapter extends TypeAdapter<SearchHistory> {
  @override
  final int typeId = 0;

  @override
  SearchHistory read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return SearchHistory(
      id: fields[0] as String,
      searchType: fields[1] as String,
      displayAddress: fields[2] as String,
      roadAddress: fields[3] as String?,
      jibunAddress: fields[4] as String?,
      buildingName: fields[5] as String?,
      pnu: fields[6] as String?,
      bdMgtSn: fields[7] as String?,
      searchedAt: fields[8] as DateTime,
      dongName: fields[9] as String?,
      hoName: fields[10] as String?,
      buildingType: fields[11] as String?,
    );
  }

  @override
  void write(BinaryWriter writer, SearchHistory obj) {
    writer
      ..writeByte(12)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.searchType)
      ..writeByte(2)
      ..write(obj.displayAddress)
      ..writeByte(3)
      ..write(obj.roadAddress)
      ..writeByte(4)
      ..write(obj.jibunAddress)
      ..writeByte(5)
      ..write(obj.buildingName)
      ..writeByte(6)
      ..write(obj.pnu)
      ..writeByte(7)
      ..write(obj.bdMgtSn)
      ..writeByte(8)
      ..write(obj.searchedAt)
      ..writeByte(9)
      ..write(obj.dongName)
      ..writeByte(10)
      ..write(obj.hoName)
      ..writeByte(11)
      ..write(obj.buildingType);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is SearchHistoryAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
