import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:kakao_map_plugin/kakao_map_plugin.dart';
import 'package:propedia/data/dto/property_dto.dart';

/// 금토끼부동산 위치 (관악구 봉천동)
const _goldenRabbitLat = 37.4834458778777;
const _goldenRabbitLon = 126.970207234818;

/// 검색 결과 지도 화면
class PropertySearchMapScreen extends ConsumerStatefulWidget {
  final List<PropertyMapMarker> markers;

  const PropertySearchMapScreen({
    super.key,
    required this.markers,
  });

  @override
  ConsumerState<PropertySearchMapScreen> createState() =>
      _PropertySearchMapScreenState();
}

class _PropertySearchMapScreenState
    extends ConsumerState<PropertySearchMapScreen> {
  KakaoMapController? _mapController;
  PropertyMapMarker? _selectedMarker;
  bool _isLoading = true;
  bool _markersAdded = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('검색결과 ${widget.markers.length}건'),
        actions: [
          IconButton(
            icon: const Icon(Icons.list),
            onPressed: () => context.pop(),
            tooltip: '목록보기',
          ),
        ],
      ),
      body: kIsWeb
          ? _buildWebMessage()
          : Column(
              children: [
                // 지도 영역
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: Stack(
                        children: [
                          // 지도
                          _buildMap(),

                          // 로딩 인디케이터
                          if (_isLoading)
                            const Center(child: CircularProgressIndicator()),
                        ],
                      ),
                    ),
                  ),
                ),

                // 선택된 매물 정보
                if (_selectedMarker != null)
                  _buildMarkerBottomSheet(_selectedMarker!),

                // 하단 여백
                if (_selectedMarker == null)
                  SizedBox(height: MediaQuery.of(context).padding.bottom),
              ],
            ),
    );
  }

  Widget _buildWebMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.map_outlined, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            '지도 기능은 모바일 앱에서 사용할 수 있습니다',
            style: TextStyle(color: Colors.grey[600], fontSize: 16),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () => context.pop(),
            child: const Text('목록으로 돌아가기'),
          ),
        ],
      ),
    );
  }

  Widget _buildMap() {
    // 첫 번째 마커의 위치를 중심으로 설정
    final centerLat = widget.markers.isNotEmpty
        ? widget.markers.first.lat
        : _goldenRabbitLat;
    final centerLon = widget.markers.isNotEmpty
        ? widget.markers.first.lon
        : _goldenRabbitLon;

    return KakaoMap(
      onMapCreated: (controller) {
        _mapController = controller;
        setState(() {
          _isLoading = false;
        });
        _addSearchMarkers();
      },
      center: LatLng(centerLat, centerLon),
      currentLevel: 8,
      onCustomOverlayTap: (markerId, latLng) {
        _onMarkerTap(markerId);
      },
    );
  }

  void _addSearchMarkers() async {
    if (_markersAdded || _mapController == null) return;
    _markersAdded = true;

    final customOverlays = <CustomOverlay>[];

    for (final marker in widget.markers) {
      // 웹과 동일한 스타일의 가격 마커 HTML
      final priceMarkerHtml = '''
<div style="background-color:#fff;border:2px solid #e38000;border-radius:6px;box-shadow:0 2px 5px rgba(0,0,0,0.2);padding:3px 8px;font-size:12px;font-weight:bold;color:#e38000;white-space:nowrap;text-align:center;cursor:pointer;font-family:-apple-system,sans-serif;">${marker.displayPrice}</div>
''';

      customOverlays.add(
        CustomOverlay(
          customOverlayId: marker.markerId,
          latLng: LatLng(marker.lat, marker.lon),
          content: priceMarkerHtml,
          yAnchor: 1.3,
        ),
      );
    }

    if (customOverlays.isNotEmpty) {
      try {
        await _mapController!.addCustomOverlay(customOverlays: customOverlays);
        debugPrint('📍 ${customOverlays.length}개 검색결과 마커 추가됨');
      } catch (e) {
        debugPrint('❌ 마커 추가 실패: $e');
      }
    }
  }

  void _onMarkerTap(String markerId) {
    final marker = widget.markers.firstWhere(
      (m) => m.markerId == markerId,
      orElse: () => widget.markers.first,
    );

    setState(() {
      _selectedMarker = marker;
    });
  }

  Widget _buildMarkerBottomSheet(PropertyMapMarker marker) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    // 토지면적 평 계산
    final areaText = marker.area != null
        ? '${(marker.area! / 3.3058).round()}평 (${marker.area!.toStringAsFixed(1)}㎡)'
        : '-';

    return Container(
      margin: EdgeInsets.fromLTRB(
        16, 0, 16, MediaQuery.of(context).padding.bottom + 16,
      ),
      decoration: BoxDecoration(
        color: isDark ? Colors.grey[850] : Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.15),
            blurRadius: 12,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 헤더 (주소 + 닫기 버튼)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 8, 0),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    marker.address ?? '주소 없음',
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: () => setState(() => _selectedMarker = null),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
          ),

          // 정보 그리드
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: Column(
              children: [
                // 매가
                _buildInfoRow(
                  '매가',
                  marker.displayPrice,
                  valueColor: const Color(0xFFE38000),
                  isBold: true,
                ),
                const SizedBox(height: 4),
                // 토지면적
                if (marker.area != null) ...[
                  _buildInfoRow('토지', areaText),
                  const SizedBox(height: 4),
                ],
                // 수익률
                if (marker.yieldRate != null)
                  _buildInfoRow(
                    '수익률',
                    '${marker.yieldRate!.toStringAsFixed(1)}%',
                    valueColor: Colors.green[700],
                  ),
              ],
            ),
          ),

          // 버튼들
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: Row(
              children: [
                // 상세보기 버튼
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      final recordId = marker.recordId;
                      if (recordId != null) {
                        context.push('/property/detail/$recordId');
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.grey[100],
                      foregroundColor: const Color(0xFFE38000),
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text(
                      '상세내역보기',
                      style:
                          TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // 문의하기 버튼
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('문의하기 기능은 준비 중입니다')),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF2962FF),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text(
                      '이 매물 문의하기',
                      style:
                          TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value,
      {Color? valueColor, bool isBold = false}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 40,
          child: Text(
            '$label:',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
              color: valueColor,
            ),
          ),
        ),
      ],
    );
  }
}
