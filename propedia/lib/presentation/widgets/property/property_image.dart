import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/dto/property_dto.dart';
import 'package:propedia/presentation/providers/property_provider.dart';

/// 백업 이미지 서버 Base URL
const String _backupImageBaseUrl = 'https://goldenrabbit.biz/airtable_backup/images';

/// 매물 이미지 위젯 (3단 Fallback)
/// 1. 백업 서버 이미지 (한국 서버, 빠름)
/// 2. Airtable 이미지 (미국 서버)
/// 3. 기본 placeholder
class PropertyImage extends ConsumerWidget {
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
  Widget build(BuildContext context, WidgetRef ref) {
    // 백업 이미지 확인
    final imageCheckAsync = ref.watch(propertyImageProvider(property.id));

    return imageCheckAsync.when(
      loading: () => _buildPlaceholder(context, isLoading: true),
      error: (_, __) => _buildAirtableImage(context),
      data: (imageCheck) {
        if (imageCheck.hasImage && imageCheck.filename != null) {
          // 1순위: 백업 이미지 사용
          final backupUrl = '$_backupImageBaseUrl/${property.id}/${imageCheck.filename}';
          return _buildCachedImage(
            context,
            imageUrl: backupUrl,
            fallbackBuilder: () => _buildAirtableImage(context),
          );
        } else {
          // 백업 이미지 없음 → Airtable 이미지
          return _buildAirtableImage(context);
        }
      },
    );
  }

  /// Airtable 이미지 빌드
  Widget _buildAirtableImage(BuildContext context) {
    final fields = property.fields;
    String? imageUrl;

    // 대표사진에서 URL 추출
    if (fields.representativePhoto != null && fields.representativePhoto!.isNotEmpty) {
      final photo = fields.representativePhoto!.first;
      if (useThumbnail) {
        imageUrl = photo.thumbnails?.large?.url ?? photo.url;
      } else {
        imageUrl = photo.url;
      }
    }

    // 사진링크 필드 확인
    if (imageUrl == null && fields.photoLink != null) {
      final links = fields.photoLink!.split(',');
      if (links.isNotEmpty) {
        imageUrl = links.first.trim();
      }
    }

    if (imageUrl != null) {
      return _buildCachedImage(
        context,
        imageUrl: imageUrl,
        fallbackBuilder: () => _buildPlaceholder(context),
      );
    }

    return _buildPlaceholder(context);
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

/// 간단한 백업 이미지 URL 생성 (API 호출 없이)
/// check-image API를 호출하지 않고 바로 URL 구성
/// 이미지가 없으면 CachedNetworkImage의 errorWidget이 fallback 처리
class PropertyImageSimple extends StatelessWidget {
  final PropertyRecord property;
  final double? height;
  final double? width;
  final BoxFit fit;
  final String? backupFilename;

  const PropertyImageSimple({
    super.key,
    required this.property,
    this.height,
    this.width,
    this.fit = BoxFit.cover,
    this.backupFilename,
  });

  @override
  Widget build(BuildContext context) {
    // 백업 이미지 URL 시도 (파일명이 있는 경우)
    if (backupFilename != null) {
      final backupUrl = '$_backupImageBaseUrl/${property.id}/$backupFilename';
      return _buildWithFallback(context, backupUrl);
    }

    // Airtable 이미지 사용
    return _buildAirtableOnly(context);
  }

  Widget _buildWithFallback(BuildContext context, String backupUrl) {
    return SizedBox(
      height: height,
      width: width ?? double.infinity,
      child: CachedNetworkImage(
        imageUrl: backupUrl,
        fit: fit,
        memCacheHeight: height != null ? (height! * 2).toInt() : 360,
        memCacheWidth: width != null ? (width! * 2).toInt() : 600,
        placeholder: (context, url) => _buildPlaceholder(context, isLoading: true),
        errorWidget: (context, url, error) => _buildAirtableOnly(context),
      ),
    );
  }

  Widget _buildAirtableOnly(BuildContext context) {
    final fields = property.fields;
    String? imageUrl;

    if (fields.representativePhoto != null && fields.representativePhoto!.isNotEmpty) {
      final photo = fields.representativePhoto!.first;
      imageUrl = photo.thumbnails?.large?.url ?? photo.url;
    }

    if (imageUrl == null && fields.photoLink != null) {
      final links = fields.photoLink!.split(',');
      if (links.isNotEmpty) {
        imageUrl = links.first.trim();
      }
    }

    if (imageUrl == null) {
      return _buildPlaceholder(context);
    }

    return SizedBox(
      height: height,
      width: width ?? double.infinity,
      child: CachedNetworkImage(
        imageUrl: imageUrl,
        fit: fit,
        memCacheHeight: height != null ? (height! * 2).toInt() : 360,
        memCacheWidth: width != null ? (width! * 2).toInt() : 600,
        placeholder: (context, url) => _buildPlaceholder(context, isLoading: true),
        errorWidget: (context, url, error) => _buildPlaceholder(context),
      ),
    );
  }

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
