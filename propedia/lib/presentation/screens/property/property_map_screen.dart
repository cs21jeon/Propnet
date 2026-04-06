import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:kakao_map_plugin/kakao_map_plugin.dart';
import 'package:propedia/data/dto/property_dto.dart';
import 'package:propedia/presentation/providers/property_provider.dart';

/// 금토끼부동산 위치 (관악구 봉천동)
const _goldenRabbitLat = 37.4834458778777;
const _goldenRabbitLon = 126.970207234818;

/// 매물 지도 화면
class PropertyMapScreen extends ConsumerStatefulWidget {
  const PropertyMapScreen({super.key});

  @override
  ConsumerState<PropertyMapScreen> createState() => _PropertyMapScreenState();
}

class _PropertyMapScreenState extends ConsumerState<PropertyMapScreen> {
  KakaoMapController? _mapController;
  PropertyRecord? _selectedProperty;
  bool _isLoading = true;
  bool _markersAdded = false;
  List<PropertyRecord> _allProperties = [];
  Map<String, int> _dbIdMap = {};
  Map<String, PropertyCoordinate>? _coordinates;

  @override
  void initState() {
    super.initState();
    // 데이터 변경 감지를 위해 listener 추가
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _setupDataListeners();
    });
  }

  void _setupDataListeners() {
    // 좌표와 매물 데이터 변경 감지
    ref.listenManual(coordinatesProvider, (previous, next) {
      next.whenData((coords) {
        _coordinates = coords;
        _tryAddMarkersWithData();
      });
    });

    ref.listenManual(mapDataProvider, (previous, next) {
      next.whenData((mapData) {
        final map = <String, int>{};
        for (final m in mapData.markers) {
          if (m.recordId != null && m.dbId != null) {
            map[m.recordId!] = m.dbId!;
          }
        }
        _dbIdMap = map;
      });
    });

    ref.listenManual(allPropertiesProvider, (previous, next) {
      next.whenData((properties) {
        _allProperties = properties;
        _tryAddMarkersWithData();
      });
    });
  }

  void _tryAddMarkersWithData() {
    if (_markersAdded || _mapController == null) return;
    if (_coordinates == null || _allProperties.isEmpty) return;

    _addPropertyMarkers(_allProperties, _coordinates!);
    _markersAdded = true;
  }

  @override
  Widget build(BuildContext context) {
    final coordsAsync = ref.watch(coordinatesProvider);
    final propertiesAsync = ref.watch(allPropertiesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('매물 지도'),
        actions: [
          IconButton(
            icon: const Icon(Icons.list),
            onPressed: () {
              context.push('/property/list');
            },
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
                          _buildMap(coordsAsync, propertiesAsync),

                          // 로딩 인디케이터
                          if (_isLoading ||
                              propertiesAsync.isLoading ||
                              coordsAsync.isLoading)
                            const Center(child: CircularProgressIndicator()),

                          // 에러 표시
                          if (propertiesAsync.hasError)
                            Center(
                              child: Text(
                                '매물 로드 실패: ${propertiesAsync.error}',
                                style: const TextStyle(color: Colors.red),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),

                // 선택된 매물 정보
                if (_selectedProperty != null)
                  _buildPropertyBottomSheet(_selectedProperty!),

                // 하단 여백
                if (_selectedProperty == null)
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
            onPressed: () => context.push('/property/list'),
            child: const Text('목록으로 보기'),
          ),
        ],
      ),
    );
  }

  Widget _buildMap(
    AsyncValue<Map<String, PropertyCoordinate>> coordsAsync,
    AsyncValue<List<PropertyRecord>> propertiesAsync,
  ) {
    return KakaoMap(
      onMapCreated: (controller) {
        _mapController = controller;
        setState(() {
          _isLoading = false;
        });

        // 좌표와 매물 데이터가 모두 로드되었으면 마커 추가
        _tryAddMarkers(coordsAsync, propertiesAsync);
        // 데이터가 이미 로드되어 있을 경우도 처리
        _tryAddMarkersWithData();
      },
      center: LatLng(_goldenRabbitLat, _goldenRabbitLon), // 금토끼부동산 위치
      currentLevel: 8,
      onMarkerTap: (markerId, latLng, zoomLevel) {
        _onMarkerTap(markerId);
      },
      onCustomOverlayTap: (markerId, latLng) {
        // 커스텀 오버레이(가격 마커) 클릭 시
        _onMarkerTap(markerId);
      },
    );
  }

  void _tryAddMarkers(
    AsyncValue<Map<String, PropertyCoordinate>> coordsAsync,
    AsyncValue<List<PropertyRecord>> propertiesAsync,
  ) {
    if (_markersAdded || _mapController == null) return;

    coordsAsync.whenData((coordinates) {
      _coordinates = coordinates;
      propertiesAsync.whenData((properties) {
        _allProperties = properties;
        _addPropertyMarkers(properties, coordinates);
        _markersAdded = true;
      });
    });
  }

  void _addPropertyMarkers(
    List<PropertyRecord> properties,
    Map<String, PropertyCoordinate> coordinates,
  ) async {
    if (_mapController == null) return;

    final customOverlays = <CustomOverlay>[];

    for (final property in properties) {
      final coord = coordinates[property.id];
      if (coord != null) {
        // 웹과 동일한 스타일의 가격 마커 HTML
        final priceMarkerHtml = '''
<div style="background-color:#fff;border:2px solid #e38000;border-radius:6px;box-shadow:0 2px 5px rgba(0,0,0,0.2);padding:3px 8px;font-size:12px;font-weight:bold;color:#e38000;white-space:nowrap;text-align:center;cursor:pointer;font-family:-apple-system,sans-serif;">${property.priceDisplay}</div>
''';

        customOverlays.add(
          CustomOverlay(
            customOverlayId: property.id,
            latLng: LatLng(coord.lat, coord.lon),
            content: priceMarkerHtml,
            yAnchor: 1.3,
          ),
        );
      }
    }

    if (customOverlays.isNotEmpty) {
      try {
        await _mapController!.addCustomOverlay(customOverlays: customOverlays);
        debugPrint('📍 ${customOverlays.length}개 마커 추가됨 (전체 매물, 가격표시)');
      } catch (e) {
        debugPrint('❌ 마커 추가 실패: $e');
      }
    } else {
      debugPrint('⚠️ 추가할 마커 없음');
    }
  }

  void _onMarkerTap(String markerId) {
    final property = _allProperties.firstWhere(
      (p) => p.id == markerId,
      orElse: () => _allProperties.first,
    );

    setState(() {
      _selectedProperty = property;
    });
  }

  Widget _buildPropertyBottomSheet(PropertyRecord property) {
    final fields = property.fields;
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    // 토지면적 평 계산
    final landAreaPyung = property.landAreaPyung;
    final landAreaSqm = fields.landArea?.toStringAsFixed(1) ?? '-';

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
                    fields.address ?? '주소 없음',
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: () => setState(() => _selectedProperty = null),
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
                  property.priceDisplay,
                  valueColor: const Color(0xFFE38000),
                  isBold: true,
                ),
                const SizedBox(height: 4),
                // 토지면적
                _buildInfoRow(
                  '토지',
                  '$landAreaPyung평 ($landAreaSqm㎡)',
                ),
                const SizedBox(height: 4),
                // 층수
                if (fields.floors != null && fields.floors!.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: _buildInfoRow('층수', fields.floors!),
                  ),
                // 용도
                if (fields.mainUsage != null && fields.mainUsage!.isNotEmpty)
                  _buildInfoRow('용도', fields.mainUsage!),
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
                      final dbId = _dbIdMap[property.id] ?? 39;
                      context.push('/property/detail/${property.id}?db_id=$dbId');
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
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // 문의하기 버튼
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      // 문의하기 기능 (추후 구현)
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
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
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

  Widget _buildInfoRow(String label, String value, {Color? valueColor, bool isBold = false}) {
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
