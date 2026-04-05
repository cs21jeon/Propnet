import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:kakao_map_plugin/kakao_map_plugin.dart';
import 'package:propedia/core/network/api_client.dart';
import 'package:propedia/data/dto/property_dto.dart';
import 'package:propedia/presentation/providers/building_provider.dart';
import 'package:propedia/presentation/providers/property_provider.dart';
import 'package:propedia/presentation/widgets/common/app_drawer.dart';
import 'package:propedia/presentation/widgets/property/property_image.dart';
import 'package:url_launcher/url_launcher.dart';

/// 금토끼부동산 위치
const _goldenRabbitLat = 37.4834458778777;
const _goldenRabbitLon = 126.970207234818;

/// 탭 종류
enum _TabType { map, search, reconstruction, highYield, lowCost }

/// 금토끼부동산 홈 화면 (웹 레이아웃 반영 - 단일 페이지 탭 구조)
class PropertyHomeScreen extends ConsumerStatefulWidget {
  const PropertyHomeScreen({super.key});

  @override
  ConsumerState<PropertyHomeScreen> createState() => _PropertyHomeScreenState();
}

class _PropertyHomeScreenState extends ConsumerState<PropertyHomeScreen> {
  _TabType _currentTab = _TabType.map;

  // 지도 관련
  KakaoMapController? _mapController;
  bool _mapLoading = true;
  bool _markersAdded = false;
  PropertyRecord? _selectedProperty;

  // 검색 관련
  final _priceController = TextEditingController();
  final _yieldController = TextEditingController();
  final _investmentController = TextEditingController();
  final _areaController = TextEditingController();
  String _priceCondition = 'all';
  String _yieldCondition = 'all';
  String _investmentCondition = 'all';
  String _areaCondition = 'all';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _setupMapListeners();
    });
  }

  @override
  void dispose() {
    _priceController.dispose();
    _yieldController.dispose();
    _investmentController.dispose();
    _areaController.dispose();
    super.dispose();
  }

  void _setupMapListeners() {
    ref.listenManual(coordinatesProvider, (_, next) {
      next.whenData((_) => _tryAddMarkers());
    });
    ref.listenManual(allPropertiesProvider, (_, next) {
      next.whenData((_) => _tryAddMarkers());
    });
  }

  void _selectTab(_TabType tab) {
    setState(() {
      _currentTab = tab;
      _selectedProperty = null;
    });

    // 카테고리 탭이면 데이터 로드
    final category = _tabToCategory(tab);
    if (category != null) {
      ref.read(propertyListProvider.notifier).changeCategory(category);
    }
  }

  PropertyCategory? _tabToCategory(_TabType tab) {
    switch (tab) {
      case _TabType.reconstruction:
        return PropertyCategory.reconstruction;
      case _TabType.highYield:
        return PropertyCategory.highYield;
      case _TabType.lowCost:
        return PropertyCategory.lowCost;
      default:
        return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 64,
        leading: Builder(
          builder: (ctx) => IconButton(
            icon: const Icon(Icons.menu),
            onPressed: () => Scaffold.of(ctx).openDrawer(),
          ),
        ),
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.asset(
                'assets/images/goldenrabbit_icon.png',
                height: 36, width: 36, fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const Icon(Icons.home_work, color: Color(0xFFD4AF37), size: 36),
              ),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('금토끼부동산', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFFD4AF37))),
                Text('매물정보', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: Colors.grey)),
              ],
            ),
          ],
        ),
        centerTitle: true,
      ),
      drawer: const AppDrawer(currentApp: AppType.property),
      body: Column(
        children: [
          // 탭 버튼 영역
          _buildTabButtons(),
          // 콘텐츠 영역
          Expanded(child: _buildContent()),
        ],
      ),
    );
  }

  // ===== 탭 버튼 =====
  Widget _buildTabButtons() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 상단: 매물지도 / 매물검색
          Row(
            children: [
              Expanded(child: _buildTab(_TabType.map, '매물지도', Icons.map)),
              const SizedBox(width: 8),
              Expanded(child: _buildTab(_TabType.search, '매물검색', Icons.search)),
            ],
          ),
          const SizedBox(height: 8),
          // 하단: 카테고리 3개
          Row(
            children: [
              Expanded(child: _buildCategoryChip(_TabType.reconstruction, '재건축용토지')),
              const SizedBox(width: 6),
              Expanded(child: _buildCategoryChip(_TabType.highYield, '고수익률건물')),
              const SizedBox(width: 6),
              Expanded(child: _buildCategoryChip(_TabType.lowCost, '저가단독주택')),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTab(_TabType tab, String label, IconData icon) {
    final isActive = _currentTab == tab;
    return GestureDetector(
      onTap: () => _selectTab(tab),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: isActive ? const Color(0xFF136dec) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: isActive ? null : Border.all(color: Colors.grey.shade300),
          boxShadow: isActive ? [BoxShadow(color: const Color(0xFF136dec).withValues(alpha: 0.3), blurRadius: 8, offset: const Offset(0, 2))] : null,
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 16, color: isActive ? Colors.white : Colors.grey.shade600),
            const SizedBox(width: 6),
            Text(label, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: isActive ? Colors.white : Colors.grey.shade600)),
          ],
        ),
      ),
    );
  }

  Widget _buildCategoryChip(_TabType tab, String label) {
    final isActive = _currentTab == tab;
    return GestureDetector(
      onTap: () => _selectTab(tab),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 9),
        decoration: BoxDecoration(
          color: isActive ? const Color(0xFF136dec) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: isActive ? null : Border.all(color: Colors.grey.shade300),
        ),
        child: Center(
          child: Text(label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: isActive ? Colors.white : Colors.grey.shade600)),
        ),
      ),
    );
  }

  // ===== 콘텐츠 분기 =====
  Widget _buildContent() {
    switch (_currentTab) {
      case _TabType.map:
        return _buildMapSection();
      case _TabType.search:
        return _buildSearchSection();
      case _TabType.reconstruction:
      case _TabType.highYield:
      case _TabType.lowCost:
        return _buildCategorySection();
    }
  }

  // ===== 매물지도 섹션 =====
  Widget _buildMapSection() {
    if (kIsWeb) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.map_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text('지도 기능은 모바일 앱에서 사용할 수 있습니다', style: TextStyle(color: Colors.grey[600])),
          ],
        ),
      );
    }

    final coordsAsync = ref.watch(coordinatesProvider);
    final propertiesAsync = ref.watch(allPropertiesProvider);

    return Column(
      children: [
        Expanded(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Stack(
                children: [
                  KakaoMap(
                    onMapCreated: (controller) {
                      _mapController = controller;
                      setState(() => _mapLoading = false);
                      _tryAddMarkers();
                    },
                    center: LatLng(_goldenRabbitLat, _goldenRabbitLon),
                    currentLevel: 8,
                    onCustomOverlayTap: (markerId, _) => _onMarkerTap(markerId),
                    onMarkerTap: (markerId, _, __) => _onMarkerTap(markerId),
                  ),
                  if (_mapLoading || coordsAsync.isLoading || propertiesAsync.isLoading)
                    const Center(child: CircularProgressIndicator()),
                  if (propertiesAsync.hasError)
                    Center(child: Text('매물 로드 실패', style: TextStyle(color: Colors.red[400]))),
                ],
              ),
            ),
          ),
        ),
        if (_selectedProperty != null) _buildMapBottomSheet(_selectedProperty!),
        if (_selectedProperty == null) SizedBox(height: MediaQuery.of(context).padding.bottom + 8),
      ],
    );
  }

  void _tryAddMarkers() {
    if (_markersAdded || _mapController == null) return;
    final coords = ref.read(coordinatesProvider).valueOrNull;
    final props = ref.read(allPropertiesProvider).valueOrNull;
    if (coords == null || props == null || props.isEmpty) return;

    final overlays = <CustomOverlay>[];
    for (final p in props) {
      final c = coords[p.id];
      if (c != null) {
        overlays.add(CustomOverlay(
          customOverlayId: p.id,
          latLng: LatLng(c.lat, c.lon),
          content: '<div style="background:#fff;border:2px solid #e38000;border-radius:6px;box-shadow:0 2px 5px rgba(0,0,0,0.2);padding:3px 8px;font-size:12px;font-weight:bold;color:#e38000;white-space:nowrap;cursor:pointer;font-family:sans-serif;">${p.priceDisplay}</div>',
          yAnchor: 1.3,
        ));
      }
    }

    if (overlays.isNotEmpty) {
      _mapController!.addCustomOverlay(customOverlays: overlays);
      _markersAdded = true;
      debugPrint('📍 ${overlays.length}개 마커 추가');
    }
  }

  void _onMarkerTap(String markerId) {
    final props = ref.read(allPropertiesProvider).valueOrNull ?? [];
    final found = props.where((p) => p.id == markerId);
    if (found.isNotEmpty) {
      setState(() => _selectedProperty = found.first);
    }
  }

  Widget _buildMapBottomSheet(PropertyRecord property) {
    final f = property.fields;
    return Container(
      margin: EdgeInsets.fromLTRB(16, 8, 16, MediaQuery.of(context).padding.bottom + 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.12), blurRadius: 12, offset: const Offset(0, -2))],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Expanded(child: Text(f.address ?? '주소 없음', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14), maxLines: 1, overflow: TextOverflow.ellipsis)),
              GestureDetector(onTap: () => setState(() => _selectedProperty = null), child: const Icon(Icons.close, size: 18, color: Colors.grey)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(property.priceDisplay, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFFE38000))),
              const SizedBox(width: 12),
              if (f.landArea != null) Text('${property.landAreaPyung}평', style: TextStyle(fontSize: 13, color: Colors.grey[600])),
              if (f.floors != null) ...[const SizedBox(width: 8), Text('${f.floors}층', style: TextStyle(fontSize: 13, color: Colors.grey[600]))],
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => context.push('/property/detail/${property.id}'),
                  style: OutlinedButton.styleFrom(foregroundColor: const Color(0xFFE38000), side: const BorderSide(color: Color(0xFFE38000)), padding: const EdgeInsets.symmetric(vertical: 8)),
                  child: const Text('상세보기', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => _showContactDialog(),
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF136dec), foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 8)),
                  child: const Text('문의하기', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ===== 매물검색 섹션 =====
  Widget _buildSearchSection() {
    final state = ref.watch(propertySearchProvider);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 검색 폼
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey.shade200),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('조건 검색', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                _buildSearchField('매가', '만원', '100000', _priceController, _priceCondition, (v) => setState(() => _priceCondition = v)),
                const SizedBox(height: 10),
                _buildSearchField('수익률', '%', '5', _yieldController, _yieldCondition, (v) => setState(() => _yieldCondition = v)),
                const SizedBox(height: 10),
                _buildSearchField('투자금', '만원', '50000', _investmentController, _investmentCondition, (v) => setState(() => _investmentCondition = v)),
                const SizedBox(height: 10),
                _buildSearchField('토지면적', '평', '50', _areaController, _areaCondition, (v) => setState(() => _areaCondition = v)),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: _doSearch,
                        icon: const Icon(Icons.search, size: 16),
                        label: const Text('검색', style: TextStyle(fontWeight: FontWeight.bold)),
                        style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF136dec), foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 12), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                      ),
                    ),
                    const SizedBox(width: 8),
                    OutlinedButton(
                      onPressed: _resetSearch,
                      style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                      child: const Text('초기화'),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // 검색 결과
          _buildSearchResults(state),
        ],
      ),
    );
  }

  Widget _buildSearchField(String label, String unit, String hint, TextEditingController controller, String condition, ValueChanged<String> onConditionChanged) {
    return Row(
      children: [
        SizedBox(width: 60, child: Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500))),
        const SizedBox(width: 8),
        Expanded(
          flex: 5,
          child: TextField(
            controller: controller,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(hintText: hint, suffixText: unit, contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10), border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)), isDense: true),
            onChanged: (v) { if (v.isNotEmpty && condition == 'all') onConditionChanged('lte'); },
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          flex: 3,
          child: Container(
            height: 42,
            padding: const EdgeInsets.symmetric(horizontal: 10),
            decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade300), borderRadius: BorderRadius.circular(8)),
            child: DropdownButton<String>(
              value: condition, isExpanded: true, underline: const SizedBox(), isDense: true,
              items: const [DropdownMenuItem(value: 'all', child: Text('전체', style: TextStyle(fontSize: 13))), DropdownMenuItem(value: 'gte', child: Text('이상', style: TextStyle(fontSize: 13))), DropdownMenuItem(value: 'lte', child: Text('이하', style: TextStyle(fontSize: 13)))],
              onChanged: (v) { if (v != null) onConditionChanged(v); },
            ),
          ),
        ),
      ],
    );
  }

  void _doSearch() {
    ref.read(propertySearchProvider.notifier).search(
      priceValue: _priceController.text.isNotEmpty ? _priceController.text : null,
      priceCondition: _priceCondition,
      yieldValue: _yieldController.text.isNotEmpty ? _yieldController.text : null,
      yieldCondition: _yieldCondition,
      investmentValue: _investmentController.text.isNotEmpty ? _investmentController.text : null,
      investmentCondition: _investmentCondition,
      areaValue: _areaController.text.isNotEmpty ? _areaController.text : null,
      areaCondition: _areaCondition,
    );
  }

  void _resetSearch() {
    _priceController.clear(); _yieldController.clear();
    _investmentController.clear(); _areaController.clear();
    setState(() { _priceCondition = 'all'; _yieldCondition = 'all'; _investmentCondition = 'all'; _areaCondition = 'all'; });
    ref.read(propertySearchProvider.notifier).reset();
  }

  Widget _buildSearchResults(PropertySearchState state) {
    switch (state.status) {
      case SearchStatus.initial:
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 40),
          child: Center(child: Column(
            children: [
              Icon(Icons.search, size: 48, color: Colors.grey[300]),
              const SizedBox(height: 12),
              Text('조건을 설정하고 검색해주세요', style: TextStyle(color: Colors.grey[500], fontSize: 14)),
            ],
          )),
        );
      case SearchStatus.loading:
        return const Padding(padding: EdgeInsets.symmetric(vertical: 40), child: Center(child: CircularProgressIndicator()));
      case SearchStatus.error:
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 40),
          child: Center(child: Text(state.errorMessage ?? '검색 오류', style: TextStyle(color: Colors.red[400]))),
        );
      case SearchStatus.success:
        if (state.markers.isEmpty) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 40),
            child: Center(child: Text('조건에 맞는 매물이 없습니다', style: TextStyle(color: Colors.grey[500]))),
          );
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('검색결과: ${state.count}건', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                if (!kIsWeb)
                  TextButton.icon(
                    onPressed: () => context.push('/property/search-map', extra: state.markers),
                    icon: const Icon(Icons.map, size: 16),
                    label: const Text('지도보기', style: TextStyle(fontSize: 13)),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            ...state.markers.map((m) => _buildSearchResultCard(m)),
          ],
        );
    }
  }

  Widget _buildSearchResultCard(PropertyMapMarker marker) {
    return GestureDetector(
      onTap: () {
        if (marker.recordId != null) context.push('/property/detail/${marker.recordId}');
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white, borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(marker.address ?? '주소 없음', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13), maxLines: 1, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 6),
            Row(
              children: [
                Text(marker.displayPrice, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF136dec))),
                if (marker.area != null) ...[const SizedBox(width: 10), Text('${(marker.area! / 3.3058).round()}평', style: TextStyle(fontSize: 12, color: Colors.grey[600]))],
                if (marker.yieldRate != null) ...[const SizedBox(width: 10), Text('${marker.yieldRate!.toStringAsFixed(1)}%', style: TextStyle(fontSize: 12, color: Colors.green[700], fontWeight: FontWeight.w500))],
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ===== 카테고리 매물 섹션 =====
  Widget _buildCategorySection() {
    final state = ref.watch(propertyListProvider);
    final category = _tabToCategory(_currentTab);
    final description = _getCategoryDescription(category);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (description != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: Text(description, style: TextStyle(fontSize: 13, color: Colors.grey[500])),
          ),
        Expanded(child: _buildCategoryBody(state)),
      ],
    );
  }

  String? _getCategoryDescription(PropertyCategory? category) {
    switch (category) {
      case PropertyCategory.reconstruction: return '대지 80평 이상 재건축용 매물';
      case PropertyCategory.highYield: return '수익률 6% 이상 (비용 제외)';
      case PropertyCategory.lowCost: return '단독의 꿈. 20억 이하 저가 단독주택';
      default: return null;
    }
  }

  Widget _buildCategoryBody(PropertyListState state) {
    switch (state.status) {
      case SearchStatus.initial:
      case SearchStatus.loading:
        return const Center(child: CircularProgressIndicator());
      case SearchStatus.error:
        return Center(child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: Colors.grey[400]),
            const SizedBox(height: 12),
            Text(state.errorMessage ?? '오류가 발생했습니다', style: TextStyle(color: Colors.grey[600])),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: () => ref.read(propertyListProvider.notifier).refresh(), child: const Text('다시 시도')),
          ],
        ));
      case SearchStatus.success:
        if (state.properties.isEmpty) {
          return Center(child: Text('매물이 없습니다', style: TextStyle(color: Colors.grey[500])));
        }
        return RefreshIndicator(
          onRefresh: () => ref.read(propertyListProvider.notifier).refresh(),
          child: ListView.builder(
            padding: EdgeInsets.fromLTRB(16, 4, 16, MediaQuery.of(context).padding.bottom + 16),
            itemCount: state.properties.length,
            itemBuilder: (_, i) => _buildPropertyCard(state.properties[i]),
          ),
        );
    }
  }

  Widget _buildPropertyCard(PropertyRecord property) {
    final f = property.fields;
    final imageUrl = _resolveImageUrl(property);

    return GestureDetector(
      onTap: () => context.push('/property/detail/${property.id}'),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: Colors.white, borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.grey.shade200),
          boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 8, offset: const Offset(0, 2))],
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 이미지
            if (imageUrl != null)
              Image.network(imageUrl, height: 180, width: double.infinity, fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Container(height: 180, color: Colors.grey[200], child: Icon(Icons.home_outlined, size: 48, color: Colors.grey[400])))
            else
              Container(height: 180, color: Colors.grey[200], child: Icon(Icons.home_outlined, size: 48, color: Colors.grey[400])),
            // 정보
            Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(f.address ?? '주소 없음', style: TextStyle(fontSize: 13, color: Colors.grey[500], fontWeight: FontWeight.w500), maxLines: 1, overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 4),
                  Text(property.priceDisplay, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF136dec))),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 6, runSpacing: 4,
                    children: _buildInfoChips(property),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String? _resolveImageUrl(PropertyRecord property) {
    final photos = property.fields.representativePhoto;
    if (photos != null && photos.isNotEmpty) {
      final url = photos.first.url;
      if (url != null && url.isNotEmpty) {
        return url.startsWith('/') ? '${ApiClient.baseUrl}$url' : url;
      }
    }
    final link = property.fields.photoLink;
    if (link != null && link.isNotEmpty) {
      final first = link.split(',').first.trim();
      return first.startsWith('/') ? '${ApiClient.baseUrl}$first' : first;
    }
    return null;
  }

  List<Widget> _buildInfoChips(PropertyRecord property) {
    final f = property.fields;
    final chips = <Widget>[];

    if (f.landArea != null) chips.add(_chip('${property.landAreaPyung}평'));
    if (f.yieldRate != null && f.yieldRate! > 0) chips.add(_chip('수익률 ${f.yieldRate!.toStringAsFixed(1)}%'));
    if (f.floors != null && f.floors!.isNotEmpty) chips.add(_chip('${f.floors}층'));
    if (f.mainUsage != null && f.mainUsage!.isNotEmpty) chips.add(_chip(f.mainUsage!));

    return chips.take(3).toList();
  }

  Widget _chip(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(6)),
      child: Text(text, style: TextStyle(fontSize: 11, color: Colors.grey[600], fontWeight: FontWeight.w500)),
    );
  }

  // ===== 문의하기 다이얼로그 =====
  void _showContactDialog() {
    const phoneNumber = '02-3471-7377';
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('금토끼부동산중개', style: TextStyle(fontSize: 17)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.phone, color: Color(0xFFD4AF37)),
              title: const Text(phoneNumber),
              onTap: () async {
                final uri = Uri.parse('tel:${phoneNumber.replaceAll('-', '')}');
                if (await canLaunchUrl(uri)) await launchUrl(uri);
              },
            ),
          ],
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('닫기'))],
      ),
    );
  }
}
