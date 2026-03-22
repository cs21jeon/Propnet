import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/dto/property_dto.dart';
import 'package:propedia/presentation/providers/building_provider.dart';
import 'package:propedia/presentation/providers/property_provider.dart';
import 'package:propedia/presentation/widgets/property/property_image.dart';
import 'package:url_launcher/url_launcher.dart';

/// 매물 상세 화면 (웹페이지 구조와 동일)
class PropertyDetailScreen extends ConsumerStatefulWidget {
  final String recordId;

  const PropertyDetailScreen({
    super.key,
    required this.recordId,
  });

  @override
  ConsumerState<PropertyDetailScreen> createState() =>
      _PropertyDetailScreenState();
}

class _PropertyDetailScreenState extends ConsumerState<PropertyDetailScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(propertyDetailProvider.notifier).loadDetail(widget.recordId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(propertyDetailProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('매물 상세'),
      ),
      body: _buildBody(state),
    );
  }

  Widget _buildBody(PropertyDetailState state) {
    switch (state.status) {
      case SearchStatus.initial:
      case SearchStatus.loading:
        return const Center(
          child: CircularProgressIndicator(),
        );

      case SearchStatus.error:
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                size: 64,
                color: Colors.grey[400],
              ),
              const SizedBox(height: 16),
              Text(
                state.errorMessage ?? '오류가 발생했습니다',
                style: TextStyle(
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  ref
                      .read(propertyDetailProvider.notifier)
                      .loadDetail(widget.recordId);
                },
                child: const Text('다시 시도'),
              ),
            ],
          ),
        );

      case SearchStatus.success:
        if (state.property == null) {
          return const Center(
            child: Text('매물을 찾을 수 없습니다'),
          );
        }

        return _buildDetailContent(state.property!);
    }
  }

  Widget _buildDetailContent(PropertyRecord property) {
    final fields = property.fields;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bottomPadding = MediaQuery.of(context).padding.bottom;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. 이미지
          PropertyImage(
            property: property,
            height: 300,
            useThumbnail: false,
          ),

          // 2. 지번/매매가
          _buildAddressAndPrice(property, isDark),

          const Divider(height: 1),

          // 3. 정보 행 (융자제외실투자금, 수익률, 평단가)
          _buildInfoRows(property, isDark),

          // 4. 상세정보
          if (fields.description != null && fields.description!.isNotEmpty)
            _buildDescriptionSection(fields.description!, isDark),

          const SizedBox(height: 16),

          // 5. 금토끼부동산 정보
          _buildCompanyInfo(isDark),

          const SizedBox(height: 16),

          // 6. 버튼들
          _buildActionButtons(property, isDark),

          // 하단 여백
          SizedBox(height: bottomPadding + 24),
        ],
      ),
    );
  }

  /// 2. 지번/매매가 섹션
  Widget _buildAddressAndPrice(PropertyRecord property, bool isDark) {
    final fields = property.fields;

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 지번 주소
          Text(
            fields.address ?? '주소 없음',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: isDark ? Colors.white : Colors.black87,
            ),
          ),
          const SizedBox(height: 12),
          // 매매가
          Text(
            property.priceDisplay,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFFD4AF37),
                ),
          ),
        ],
      ),
    );
  }

  /// 3. 정보 행 (융자제외실투자금, 수익률, 평단가)
  Widget _buildInfoRows(PropertyRecord property, bool isDark) {
    final fields = property.fields;
    final infoRows = <Widget>[];

    // 융자제외 실투자금
    if (fields.investment != null && fields.investment! > 0) {
      infoRows.add(_buildInfoRow(
        '융자제외 실투자금',
        formatPrice(fields.investment),
        isDark,
      ));
    }

    // 수익률
    if (fields.yieldRate != null && fields.yieldRate! > 0) {
      infoRows.add(_buildInfoRow(
        '수익률',
        '${fields.yieldRate!.toStringAsFixed(1)}%',
        isDark,
      ));
    }

    // 평단가 (매가 ÷ 토지면적평수)
    if (fields.price != null && fields.landArea != null && fields.landArea! > 0) {
      final landAreaPyung = fields.landArea! / 3.3058;
      final pricePerPyung = (fields.price! / landAreaPyung).round();
      infoRows.add(_buildInfoRow(
        '평단가',
        '${_formatNumber(pricePerPyung)}만원/평',
        isDark,
      ));
    }

    if (infoRows.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      children: infoRows,
    );
  }

  Widget _buildInfoRow(String label, String value, bool isDark) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: isDark ? Colors.grey[800]! : Colors.grey[200]!,
            width: 1,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 14,
              color: isDark ? Colors.grey[400] : Colors.grey[600],
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.white : Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  /// 4. 상세정보 섹션
  Widget _buildDescriptionSection(String description, bool isDark) {
    final cleanedDescription = _cleanDescription(description);

    if (cleanedDescription.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Text(
            '상세정보',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: isDark ? Colors.white : Colors.black87,
            ),
          ),
        ),
        const SizedBox(height: 12),
        Container(
          width: double.infinity,
          margin: const EdgeInsets.symmetric(horizontal: 16),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isDark ? Colors.grey[850] : Colors.grey[50],
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: isDark ? Colors.grey[700]! : Colors.grey[200]!,
            ),
          ),
          child: Text(
            cleanedDescription,
            style: TextStyle(
              fontSize: 12,
              height: 1.5,
              color: isDark ? Colors.grey[300] : Colors.grey[800],
            ),
          ),
        ),
      ],
    );
  }

  /// 5. 금토끼부동산 정보
  Widget _buildCompanyInfo(bool isDark) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? Colors.grey[850] : Colors.grey[100],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          // 회사명
          Text(
            '금토끼부동산중개',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: isDark ? Colors.white : Colors.black87,
            ),
          ),
          const SizedBox(height: 8),
          // 주소
          Text(
            '서울특별시 동작구 사당로16나길 55 1층',
            style: TextStyle(
              fontSize: 13,
              color: isDark ? Colors.grey[400] : Colors.grey[600],
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          // 전화번호
          Text(
            '02-3471-7377',
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: Color(0xFFD4AF37),
            ),
          ),
          const SizedBox(height: 12),
          // 사업자 정보
          Text(
            '대표: 전창성 | 사업자등록번호: 520-41-01170',
            style: TextStyle(
              fontSize: 11,
              color: isDark ? Colors.grey[500] : Colors.grey[600],
            ),
          ),
          const SizedBox(height: 2),
          Text(
            '중개사무소등록번호: 11590-2024-00048',
            style: TextStyle(
              fontSize: 11,
              color: isDark ? Colors.grey[500] : Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  /// 6. 버튼들 (웹페이지와 동일한 구조)
  Widget _buildActionButtons(PropertyRecord property, bool isDark) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          // 문의하기 + 지도보기 버튼 (나란히 - 웹페이지와 동일)
          Row(
            children: [
              // 문의하기
              Expanded(
                child: SizedBox(
                  height: 52,
                  child: ElevatedButton.icon(
                    onPressed: () => _makePhoneCall(),
                    icon: const Icon(Icons.phone, size: 18),
                    label: const Text('문의하기'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFD4AF37),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              // 지도보기
              Expanded(
                child: SizedBox(
                  height: 52,
                  child: OutlinedButton.icon(
                    onPressed: () => _openMap(property),
                    icon: const Icon(Icons.map_outlined, size: 18),
                    label: const Text('지도 보기'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: isDark ? Colors.grey[300] : Colors.grey[700],
                      side: BorderSide(
                        color: isDark ? Colors.grey[600]! : Colors.grey[300]!,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // 링크복사 버튼 (앱 전용 - 공유 기능)
          SizedBox(
            width: double.infinity,
            height: 52,
            child: OutlinedButton.icon(
              onPressed: () => _copyLink(property),
              icon: const Icon(Icons.link, size: 18),
              label: const Text('링크 복사'),
              style: OutlinedButton.styleFrom(
                foregroundColor: const Color(0xFF136dec),
                padding: const EdgeInsets.symmetric(vertical: 14),
                side: BorderSide(
                  color: const Color(0xFF136dec).withValues(alpha: 0.3),
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _cleanDescription(String description) {
    String content = description;

    // 1. '* 상세정보 *' 또는 '★ 상세정보 ★' 마커 이후 내용 추출
    final startMarker = RegExp(r'[\*★]\s*상세정보\s*[\*★]');
    final startMatch = startMarker.firstMatch(content);
    if (startMatch != null) {
      content = content.substring(startMatch.end);
    }

    // 2. '-----' 구분선 이전까지만 추출 (웹페이지와 동일)
    final dashIndex = content.indexOf(RegExp(r'-{5,}'));
    if (dashIndex != -1) {
      content = content.substring(0, dashIndex);
    }

    // 3. '⚛ 금토끼부동산은' 또는 '금토끼부동산은' 이전까지만 추출
    final footerPatterns = ['⚛ 금토끼부동산은', '금토끼부동산은', '⚛금토끼부동산'];
    for (final pattern in footerPatterns) {
      final footerIndex = content.indexOf(pattern);
      if (footerIndex != -1) {
        content = content.substring(0, footerIndex);
        break;
      }
    }

    // 4. 기타 정리
    content = content
        .replaceAll(RegExp(r'↑.*?↑'), '')
        .replaceAll(RegExp(r'\n{3,}'), '\n\n')
        .trim();

    // 5. 내용이 비어있으면 원본에서 다시 시도 (마커가 없는 경우)
    if (content.isEmpty && description.isNotEmpty) {
      content = description
          .replaceAll(RegExp(r'↑.*?↑'), '')
          .replaceAll(RegExp(r'\n{3,}'), '\n\n')
          .trim();

      // 다시 푸터 제거 시도
      for (final pattern in footerPatterns) {
        final footerIndex = content.indexOf(pattern);
        if (footerIndex != -1) {
          content = content.substring(0, footerIndex).trim();
          break;
        }
      }
    }

    return content;
  }

  String _formatNumber(int number) {
    return number.toString().replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (m) => '${m[1]},',
        );
  }

  /// 전화 걸기 (웹페이지와 동일 - 바로 전화)
  void _makePhoneCall() async {
    final uri = Uri.parse('tel:0234717377');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  /// 네이버 지도 열기 (웹페이지와 동일)
  void _openMap(PropertyRecord property) async {
    final fields = property.fields;
    final address = fields.address ?? '';

    if (address.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('주소 정보가 없습니다')),
      );
      return;
    }

    // 네이버 지도 링크로 열기 (웹페이지와 동일)
    final encodedAddress = Uri.encodeComponent(address);
    final naverMapUrl = 'https://map.naver.com/p/search/$encodedAddress';

    final uri = Uri.parse(naverMapUrl);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('지도를 열 수 없습니다')),
        );
      }
    }
  }

  void _copyLink(PropertyRecord property) {
    final link = 'https://goldenrabbit.biz/property/${property.id}';
    Clipboard.setData(ClipboardData(text: link));

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('링크가 복사되었습니다'),
        duration: Duration(seconds: 2),
      ),
    );
  }
}
