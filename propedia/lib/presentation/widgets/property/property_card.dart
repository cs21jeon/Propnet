import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/dto/property_dto.dart';
import 'package:propedia/presentation/widgets/property/property_image.dart';

/// 매물 카드 위젯 (백업 이미지 우선 사용)
class PropertyCard extends ConsumerWidget {
  final PropertyRecord property;
  final VoidCallback? onTap;
  final PropertyCategory? category;

  const PropertyCard({
    super.key,
    required this.property,
    this.onTap,
    this.category,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final fields = property.fields;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Card(
      key: ValueKey(property.id), // 성능 최적화: 고유 키 지정
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      clipBehavior: Clip.antiAlias,
      elevation: isDark ? 0 : 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isDark
            ? BorderSide(color: Colors.grey[700]!, width: 1)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 이미지 (백업 서버 우선)
            PropertyImage(
              property: property,
              height: 180,
            ),

            // 정보
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 주소
                  Text(
                    fields.address ?? '주소 없음',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: isDark ? Colors.grey[400] : Colors.grey[600],
                        ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),

                  const SizedBox(height: 4),

                  // 가격
                  Text(
                    property.priceDisplay,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                  ),

                  const SizedBox(height: 8),

                  // 정보 칩 (카테고리별로 다른 정보 표시)
                  _buildInfoChips(context, category),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoChips(BuildContext context, PropertyCategory? category) {
    final fields = property.fields;
    final chips = <Widget>[];

    // 카테고리별로 다른 정보 표시
    // 재건축용 토지: 대지면적, 용도지역
    // 고수익률 건물: 대지면적, 수익률, 사용승인일
    // 저가단독주택: 대지면적, 층수, 사용승인일

    // 1. 대지면적 (모든 카테고리 공통)
    if (fields.landArea != null && fields.landArea! > 0) {
      chips.add(_buildChip(
        context,
        '${property.landAreaPyung}평',
        Icons.straighten_outlined,
      ));
    }

    // 2. 카테고리별 추가 정보
    switch (category) {
      case PropertyCategory.reconstruction:
        // 재건축용 토지: 용도지역
        if (fields.zoning != null && fields.zoning!.isNotEmpty) {
          chips.add(_buildChip(
            context,
            _shortenText(fields.zoning!, 8),
            Icons.map_outlined,
          ));
        }
        break;

      case PropertyCategory.highYield:
        // 고수익률 건물: 수익률, 사용승인일
        if (fields.yieldRate != null && fields.yieldRate! > 0) {
          chips.add(_buildChip(
            context,
            '${fields.yieldRate!.toStringAsFixed(1)}%',
            Icons.trending_up_outlined,
          ));
        }
        if (fields.approvalDate != null && fields.approvalDate!.isNotEmpty) {
          chips.add(_buildChip(
            context,
            fields.approvalDate!,
            Icons.calendar_today_outlined,
          ));
        }
        break;

      case PropertyCategory.lowCost:
        // 저가단독주택: 층수, 사용승인일
        if (fields.floors != null && fields.floors!.isNotEmpty) {
          chips.add(_buildChip(
            context,
            fields.floors!,
            Icons.layers_outlined,
          ));
        }
        if (fields.approvalDate != null && fields.approvalDate!.isNotEmpty) {
          chips.add(_buildChip(
            context,
            fields.approvalDate!,
            Icons.calendar_today_outlined,
          ));
        }
        break;

      case null:
        // 카테고리 없음 (검색 결과 등): 기본 정보 표시
        if (fields.yieldRate != null && fields.yieldRate! > 0) {
          chips.add(_buildChip(
            context,
            '${fields.yieldRate!.toStringAsFixed(1)}%',
            Icons.trending_up_outlined,
          ));
        }
        if (fields.floors != null && fields.floors!.isNotEmpty) {
          chips.add(_buildChip(
            context,
            fields.floors!,
            Icons.layers_outlined,
          ));
        }
        break;
    }

    if (chips.isEmpty) {
      return const SizedBox.shrink();
    }

    return Wrap(
      spacing: 8,
      runSpacing: 4,
      children: chips,
    );
  }

  Widget _buildChip(BuildContext context, String label, IconData icon) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isDark ? Colors.grey[700] : Colors.grey[100],
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 14,
            color: isDark ? Colors.grey[400] : Colors.grey[600],
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: isDark ? Colors.grey[300] : Colors.grey[700],
            ),
          ),
        ],
      ),
    );
  }

  /// 문자열 줄이기
  String _shortenText(String text, int maxLength) {
    if (text.length > maxLength) {
      return '${text.substring(0, maxLength)}...';
    }
    return text;
  }
}

/// 매물 목록용 간략 카드 (그리드뷰용)
class PropertyCardCompact extends ConsumerWidget {
  final PropertyRecord property;
  final VoidCallback? onTap;

  const PropertyCardCompact({
    super.key,
    required this.property,
    this.onTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final fields = property.fields;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Card(
      key: ValueKey(property.id),
      clipBehavior: Clip.antiAlias,
      elevation: isDark ? 0 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: isDark
            ? BorderSide(color: Colors.grey[700]!, width: 1)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 이미지 (백업 서버 우선)
            Expanded(
              child: PropertyImage(
                property: property,
                useThumbnail: true,
              ),
            ),

            // 정보
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    fields.address ?? '주소 없음',
                    style: const TextStyle(fontSize: 11),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    property.priceDisplay,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
