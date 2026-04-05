import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:propedia/core/network/api_client.dart';
import 'package:propedia/data/dto/property_dto.dart';

/// 매물 이미지 위젯
/// 1. PropSheet 업로드 이미지 (대표사진 필드)
/// 2. 사진링크 필드
/// 3. 기본 placeholder
class PropertyImage extends StatelessWidget {
  final PropertyRecord property;
  final double? height;
  final double? width;
  final BoxFit fit;
  final bool useThumbnail;

  const PropertyImage({
    super.key,
    required this.property,
    this.height,
    this.width,
    this.fit = BoxFit.cover,
    this.useThumbnail = true,
  });

  @override
  Widget build(BuildContext context) {
    final imageUrl = _resolveImageUrl();
    if (imageUrl != null) {
      return _buildCachedImage(
        context,
        imageUrl: imageUrl,
        fallbackBuilder: () => _buildPlaceholder(context),
      );
    }
    return _buildPlaceholder(context);
  }

  /// 이미지 URL 결정
  String? _resolveImageUrl() {
    final fields = property.fields;

    // 1순위: 대표사진 필드 (PropSheet uploads 경로)
    if (fields.representativePhoto != null && fields.representativePhoto!.isNotEmpty) {
      final photo = fields.representativePhoto!.first;
      final url = photo.url;
      if (url != null && url.isNotEmpty) {
        // 상대 경로면 baseUrl 붙이기
        if (url.startsWith('/')) {
          return '${ApiClient.baseUrl}$url';
        }
        return url;
      }
    }

    // 2순위: 사진링크 필드
    if (fields.photoLink != null && fields.photoLink!.isNotEmpty) {
      final links = fields.photoLink!.split(',');
      if (links.isNotEmpty) {
        final link = links.first.trim();
        if (link.startsWith('/')) {
          return '${ApiClient.baseUrl}$link';
        }
        return link;
      }
    }

    return null;
  }

  /// CachedNetworkImage 빌드
  Widget _buildCachedImage(
    BuildContext context, {
    required String imageUrl,
    required Widget Function() fallbackBuilder,
  }) {
    return SizedBox(
      height: height,
      width: width ?? double.infinity,
      child: CachedNetworkImage(
        imageUrl: imageUrl,
        fit: fit,
        // 성능 최적화: 메모리 캐시 크기 제한
        memCacheHeight: height != null ? (height! * 2).toInt() : 360,
        memCacheWidth: width != null ? (width! * 2).toInt() : 600,
        fadeInDuration: const Duration(milliseconds: 200),
        fadeOutDuration: const Duration(milliseconds: 200),
        placeholder: (context, url) => _buildPlaceholder(context, isLoading: true),
        errorWidget: (context, url, error) => fallbackBuilder(),
      ),
    );
  }

  /// Placeholder 빌드
  Widget _buildPlaceholder(BuildContext context, {bool isLoading = false}) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      height: height,
      width: width ?? double.infinity,
      color: isDark ? Colors.grey[800] : Colors.grey[200],
      child: Center(
        child: isLoading
            ? SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: isDark ? Colors.grey[600] : Colors.grey[400],
                ),
              )
            : Icon(
                Icons.home_outlined,
                size: height != null ? height! * 0.3 : 48,
                color: isDark ? Colors.grey[600] : Colors.grey[400],
              ),
      ),
    );
  }
}

/// 간단한 매물 이미지 (PropertyImage와 동일하게 동작)
class PropertyImageSimple extends PropertyImage {
  const PropertyImageSimple({
    super.key,
    required super.property,
    super.height,
    super.width,
    super.fit,
    String? backupFilename,
  });
}
