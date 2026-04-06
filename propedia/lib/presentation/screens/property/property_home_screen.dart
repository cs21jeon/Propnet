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
import 'package:url_launcher/url_launcher.dart';

const _goldenRabbitLat = 37.4834458778777;
const _goldenRabbitLon = 126.970207234818;

enum _TabType { map, search, reconstruction, highYield, lowCost }

// 서브타입 옵션 (웹 map.html과 동일)
const _subtypeOptions = {
  'danil': ['주택', '건물', '토지'],
  'jibhap': ['아파트', '빌라', '오피스텔', '상가', '지산', '기타'],
  'bubun': ['원룸', '1.5룸', '투룸', '3룸', '4룸이상', '상가', '사무실'],
};

const _typeColors = {
  'danil': Color(0xFF1D4ED8),
  'jibhap': Color(0xFF15803D),
  'bubun': Color(0xFFEA580C),
};

const _txnColors = {
  '매매': Color(0xFF1e3a5f),
  '전세': Color(0xFF2563EB),
  '월세': Color(0xFFDC2626),
};

const _markerBgColors = {
  'danil-매매': '#1D4ED8', 'danil-전세': '#3B82F6', 'danil-월세': '#93C5FD',
  'jibhap-매매': '#15803D', 'jibhap-전세': '#22C55E', 'jibhap-월세': '#86EFAC',
  'bubun-매매': '#C2410C', 'bubun-전세': '#EA580C', 'bubun-월세': '#FB923C',
};

const _markerFgColors = {
  'danil-월세': '#1e3a5f', 'jibhap-월세': '#14532d', 'bubun-월세': '#431407',
};

class PropertyHomeScreen extends ConsumerStatefulWidget {
  const PropertyHomeScreen({super.key});
  @override
  ConsumerState<PropertyHomeScreen> createState() => _PropertyHomeScreenState();
}

class _PropertyHomeScreenState extends ConsumerState<PropertyHomeScreen> {
  _TabType _currentTab = _TabType.map;

  // 지도
  KakaoMapController? _mapController;
  bool _mapLoading = true;
  bool _markersAdded = false;
  PropertyMapMarker? _selectedMarker;
  int _mapKey = 0; // 지도 rebuild용

  // 지도 필터
  final _filterTypes = <String, bool>{'danil': true, 'jibhap': true, 'bubun': true};
  final _filterTxns = <String, bool>{'매매': true, '전세': true, '월세': true};
  final _filterSubtypes = <String, bool>{};
  String? _expandedFilterType;

  // 검색
  String _searchPropertyType = 'danil';
  final _searchSubtypes = <String, bool>{};
  final _priceCtrl = TextEditingController();
  final _yieldCtrl = TextEditingController();
  final _investCtrl = TextEditingController();
  final _areaCtrl = TextEditingController();
  final _depositCtrl = TextEditingController();
  final _rentCtrl = TextEditingController();
  String _priceCond = 'all', _yieldCond = 'all', _investCond = 'all';
  String _areaCond = 'all', _depositCond = 'all', _rentCond = 'all';

  @override
  void initState() {
    super.initState();
    // 서브타입 필터 초기화 (모두 활성)
    for (final e in _subtypeOptions.entries) {
      for (final st in e.value) {
        _filterSubtypes['${e.key}:$st'] = true;
        _searchSubtypes['${e.key}:$st'] = true;
      }
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.listenManual(mapDataProvider, (_, next) {
        next.whenData((_) => _tryAddMarkers());
      });
    });
  }

  @override
  void dispose() {
    _priceCtrl.dispose(); _yieldCtrl.dispose(); _investCtrl.dispose();
    _areaCtrl.dispose(); _depositCtrl.dispose(); _rentCtrl.dispose();
    super.dispose();
  }

  // ===== 필터 로직 =====
  bool _isTypeVisible(String type) {
    final opts = _subtypeOptions[type] ?? [];
    return opts.any((st) => _filterSubtypes['$type:$st'] == true);
  }

  bool _isMarkerVisible(PropertyMapMarker m) {
    final type = m.propertyType ?? 'danil';
    final txn = m.transactionType ?? '매매';
    if (_filterTxns[txn] != true) return false;
    final st = m.propertySubtype ?? '';
    if (st.isEmpty) return _isTypeVisible(type);
    return _filterSubtypes['$type:$st'] == true;
  }

  List<PropertyMapMarker> _filteredMarkers() {
    final mapData = ref.read(mapDataProvider).valueOrNull;
    if (mapData == null) return [];
    return mapData.markers.where(_isMarkerVisible).toList();
  }

  void _toggleType(String type) {
    final visible = _isTypeVisible(type);
    final opts = _subtypeOptions[type] ?? [];
    setState(() {
      for (final st in opts) {
        _filterSubtypes['$type:$st'] = !visible;
      }
      if (!visible) _expandedFilterType = type;
      else if (_expandedFilterType == type) _expandedFilterType = null;
    });
    _rebuildMapMarkers();
  }

  void _toggleTxn(String txn) {
    setState(() => _filterTxns[txn] = !(_filterTxns[txn] ?? true));
    _rebuildMapMarkers();
  }

  void _toggleSubtype(String key) {
    setState(() => _filterSubtypes[key] = !(_filterSubtypes[key] ?? true));
    _rebuildMapMarkers();
  }

  void _rebuildMapMarkers() {
    setState(() {
      _markersAdded = false;
      _mapController = null;
      _mapLoading = true;
      _mapKey++;
    });
  }

  // ===== 탭 전환 =====
  void _selectTab(_TabType tab) {
    if (_currentTab == _TabType.map && tab != _TabType.map) {
      _markersAdded = false;
      _mapController = null;
      _mapLoading = true;
    }
    setState(() { _currentTab = tab; _selectedMarker = null; });
    final cat = _tabToCategory(tab);
    if (cat != null) ref.read(propertyListProvider.notifier).changeCategory(cat);
  }

  PropertyCategory? _tabToCategory(_TabType t) => switch (t) {
    _TabType.reconstruction => PropertyCategory.reconstruction,
    _TabType.highYield => PropertyCategory.highYield,
    _TabType.lowCost => PropertyCategory.lowCost,
    _ => null,
  };

  // ===== BUILD =====
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 64,
        leading: Builder(builder: (ctx) => IconButton(icon: const Icon(Icons.menu), onPressed: () => Scaffold.of(ctx).openDrawer())),
        title: Row(mainAxisSize: MainAxisSize.min, children: [
          ClipRRect(borderRadius: BorderRadius.circular(8),
            child: Image.asset('assets/images/goldenrabbit_icon.png', height: 36, width: 36, fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => const Icon(Icons.home_work, color: Color(0xFFD4AF37), size: 36))),
          const SizedBox(width: 10),
          const Column(crossAxisAlignment: CrossAxisAlignment.center, mainAxisSize: MainAxisSize.min, children: [
            Text('금토끼부동산', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFFD4AF37))),
            Text('매물정보', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: Colors.grey)),
          ]),
        ]),
        centerTitle: true,
      ),
      drawer: const AppDrawer(currentApp: AppType.property),
      body: Column(children: [
        _buildTabButtons(),
        Expanded(child: _buildContent()),
      ]),
    );
  }

  // ===== 탭 버튼 =====
  Widget _buildTabButtons() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
      child: Column(children: [
        Row(children: [
          Expanded(child: _tabBtn(_TabType.map, '매물지도', Icons.map)),
          const SizedBox(width: 8),
          Expanded(child: _tabBtn(_TabType.search, '매물검색', Icons.search)),
        ]),
        const SizedBox(height: 8),
        Row(children: [
          Expanded(child: _catChip(_TabType.reconstruction, '재건축용토지')),
          const SizedBox(width: 6),
          Expanded(child: _catChip(_TabType.highYield, '고수익률건물')),
          const SizedBox(width: 6),
          Expanded(child: _catChip(_TabType.lowCost, '저가단독주택')),
        ]),
      ]),
    );
  }

  Widget _tabBtn(_TabType tab, String label, IconData icon) {
    final a = _currentTab == tab;
    return GestureDetector(onTap: () => _selectTab(tab), child: Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        color: a ? const Color(0xFF136dec) : Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: a ? null : Border.all(color: Colors.grey.shade300),
      ),
      child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(icon, size: 16, color: a ? Colors.white : Colors.grey.shade600),
        const SizedBox(width: 6),
        Text(label, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: a ? Colors.white : Colors.grey.shade600)),
      ]),
    ));
  }

  Widget _catChip(_TabType tab, String label) {
    final a = _currentTab == tab;
    return GestureDetector(onTap: () => _selectTab(tab), child: Container(
      padding: const EdgeInsets.symmetric(vertical: 9),
      decoration: BoxDecoration(
        color: a ? const Color(0xFF136dec) : Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: a ? null : Border.all(color: Colors.grey.shade300),
      ),
      child: Center(child: Text(label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: a ? Colors.white : Colors.grey.shade600))),
    ));
  }

  Widget _buildContent() => switch (_currentTab) {
    _TabType.map => _buildMapSection(),
    _TabType.search => _buildSearchSection(),
    _ => _buildCategorySection(),
  };

  // =========================================================================
  // 매물지도 섹션
  // =========================================================================
  Widget _buildMapSection() {
    if (kIsWeb) return Center(child: Text('지도 기능은 모바일 앱에서 사용할 수 있습니다', style: TextStyle(color: Colors.grey[600])));

    final mapDataAsync = ref.watch(mapDataProvider);
    return Column(children: [
      _buildMapFilterPanel(),
      if (_expandedFilterType != null) _buildSubtypePanel(_expandedFilterType!),
      Expanded(child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
        child: ClipRRect(borderRadius: BorderRadius.circular(16), child: Stack(children: [
          KakaoMap(
            key: ValueKey(_mapKey),
            onMapCreated: (c) { _mapController = c; setState(() => _mapLoading = false); _tryAddMarkers(); },
            center: LatLng(_goldenRabbitLat, _goldenRabbitLon),
            currentLevel: 8,
            onCustomOverlayTap: (id, _) => _onMarkerTap(id),
            onMarkerTap: (id, _, __) => _onMarkerTap(id),
          ),
          if (_mapLoading || mapDataAsync.isLoading) const Center(child: CircularProgressIndicator()),
        ])),
      )),
      if (_selectedMarker != null) _buildMapBottomSheet(_selectedMarker!),
      if (_selectedMarker == null) SizedBox(height: MediaQuery.of(context).padding.bottom + 8),
    ]);
  }

  // 필터 패널: 1줄 부동산유형 + 2줄 거래유형
  Widget _buildMapFilterPanel() {
    final mapData = ref.watch(mapDataProvider).valueOrNull;
    final allMarkers = mapData?.markers ?? [];
    int cDanil = 0, cJibhap = 0, cBubun = 0, cMaemae = 0, cJeonse = 0, cWolse = 0;
    for (final m in allMarkers) {
      if (!_isMarkerVisible(m)) continue;
      switch (m.propertyType) { case 'danil': cDanil++; case 'jibhap': cJibhap++; case 'bubun': cBubun++; }
      switch (m.transactionType) { case '매매': cMaemae++; case '전세': cJeonse++; case '월세': cWolse++; }
    }
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // 1줄: 부동산유형
        Row(children: [
          Text('유형', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.grey[500])),
          const SizedBox(width: 6),
          _typeFilterBtn('danil', '단일', cDanil),
          const SizedBox(width: 5),
          _typeFilterBtn('jibhap', '집합', cJibhap),
          const SizedBox(width: 5),
          _typeFilterBtn('bubun', '부분', cBubun),
        ]),
        const SizedBox(height: 4),
        // 2줄: 거래유형
        Row(children: [
          Text('거래', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.grey[500])),
          const SizedBox(width: 6),
          _txnFilterBtn('매매', cMaemae),
          const SizedBox(width: 5),
          _txnFilterBtn('전세', cJeonse),
          const SizedBox(width: 5),
          _txnFilterBtn('월세', cWolse),
          const Spacer(),
          Text('${cDanil + cJibhap + cBubun}건', style: TextStyle(fontSize: 10, color: Colors.grey[400])),
        ]),
      ]),
    );
  }

  Widget _typeFilterBtn(String type, String label, int count) {
    final visible = _isTypeVisible(type);
    final color = _typeColors[type]!;
    final expanded = _expandedFilterType == type;
    const h = 28.0;
    return SizedBox(
      height: h,
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        // 라벨: OFF면 클릭 시 ON+펼침, ON이면 펼침 토글
        GestureDetector(
          onTap: () {
            if (!visible) {
              // OFF → ON + 펼침
              final opts = _subtypeOptions[type] ?? [];
              setState(() {
                for (final st in opts) _filterSubtypes['$type:$st'] = true;
                _expandedFilterType = type;
              });
              _rebuildMapMarkers();
            } else {
              // ON → 펼침 토글만
              setState(() => _expandedFilterType = _expandedFilterType == type ? null : type);
            }
          },
          child: Container(
            height: h,
            padding: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(
              color: visible ? color : Colors.grey.shade200,
              borderRadius: const BorderRadius.horizontal(left: Radius.circular(6)),
              border: expanded ? Border(bottom: BorderSide(color: Colors.yellow, width: 2)) : null,
            ),
            alignment: Alignment.center,
            child: Text('$label $count', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: visible ? Colors.white : Colors.grey)),
          ),
        ),
        // X 버튼: 유형 OFF 토글
        GestureDetector(
          onTap: () => _toggleType(type),
          child: Container(
            height: h, width: h,
            decoration: BoxDecoration(
              color: visible ? color.withValues(alpha: 0.7) : Colors.grey.shade300,
              borderRadius: const BorderRadius.horizontal(right: Radius.circular(6)),
            ),
            alignment: Alignment.center,
            child: Icon(Icons.close, size: 14, color: visible ? Colors.white : Colors.grey.shade600),
          ),
        ),
      ]),
    );
  }

  Widget _txnFilterBtn(String txn, int count) {
    final active = _filterTxns[txn] == true;
    final color = _txnColors[txn] ?? Colors.grey;
    return GestureDetector(
      onTap: () => _toggleTxn(txn),
      child: Container(
        height: 28,
        padding: const EdgeInsets.symmetric(horizontal: 10),
        decoration: BoxDecoration(
          color: active ? color : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(6),
        ),
        alignment: Alignment.center,
        child: Text('$txn $count', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: active ? Colors.white : Colors.grey)),
      ),
    );
  }

  // 서브타입 패널 (펼침) - 왼쪽 정렬
  Widget _buildSubtypePanel(String type) {
    final opts = _subtypeOptions[type] ?? [];
    final color = _typeColors[type]!;
    final typeLabel = switch (type) { 'danil' => '단일', 'jibhap' => '집합', 'bubun' => '부분', _ => '' };
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(color: Colors.grey.shade50, borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.grey.shade200)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('$typeLabel부동산 세부유형', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey[600])),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerLeft,
            child: Wrap(spacing: 6, runSpacing: 6, children: opts.map((st) {
              final key = '$type:$st';
              final active = _filterSubtypes[key] == true;
              return GestureDetector(
                onTap: () => _toggleSubtype(key),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: active ? color : Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: active ? color : Colors.grey.shade300),
                  ),
                  child: Text(st, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: active ? Colors.white : Colors.grey.shade600)),
                ),
              );
            }).toList()),
          ),
        ]),
      ),
    );
  }

  void _tryAddMarkers() {
    if (_markersAdded || _mapController == null) return;
    final filtered = _filteredMarkers();
    if (filtered.isEmpty) { _markersAdded = true; return; }

    final overlays = <CustomOverlay>[];
    for (final m in filtered) {
      final key = '${m.propertyType ?? 'danil'}-${m.transactionType ?? '매매'}';
      final bg = _markerBgColors[key] ?? '#1D4ED8';
      final fg = _markerFgColors[key] ?? '#ffffff';
      final label = m.priceDisplay ?? m.displayPrice;
      overlays.add(CustomOverlay(
        customOverlayId: m.recordId ?? m.markerId,
        latLng: LatLng(m.lat, m.lon),
        content: '<div style="position:relative;background:$bg;border-radius:6px;padding:3px 7px;font-size:11px;font-weight:bold;color:$fg;white-space:nowrap;text-align:center;cursor:pointer;font-family:sans-serif;box-shadow:0 2px 4px rgba(0,0,0,0.25);">$label<div style="position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid $bg;"></div></div>',
        yAnchor: 1.5,
      ));
    }
    _mapController!.addCustomOverlay(customOverlays: overlays);
    _markersAdded = true;
    debugPrint('📍 ${overlays.length}개 마커 (필터 적용)');
  }

  void _onMarkerTap(String id) {
    final mapData = ref.read(mapDataProvider).valueOrNull;
    if (mapData == null) return;
    final found = mapData.markers.where((m) => (m.recordId ?? m.markerId) == id);
    if (found.isNotEmpty) setState(() => _selectedMarker = found.first);
  }

  Widget _buildMapBottomSheet(PropertyMapMarker m) {
    final key = '${m.propertyType ?? 'danil'}-${m.transactionType ?? '매매'}';
    final typeColor = Color(int.parse((_markerBgColors[key] ?? '#1D4ED8').replaceFirst('#', '0xFF')));
    final typeLabel = switch (m.propertyType) { 'danil' => '단일', 'jibhap' => '집합', 'bubun' => '부분', _ => '단일' };
    return Container(
      margin: EdgeInsets.fromLTRB(16, 8, 16, MediaQuery.of(context).padding.bottom + 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.12), blurRadius: 12, offset: const Offset(0, -2))]),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Row(children: [
          Container(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2), decoration: BoxDecoration(color: typeColor, borderRadius: BorderRadius.circular(4)),
            child: Text('$typeLabel ${m.transactionType ?? '매매'}', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Colors.white))),
          const SizedBox(width: 8),
          Expanded(child: Text(m.address ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13), maxLines: 1, overflow: TextOverflow.ellipsis)),
          GestureDetector(onTap: () => setState(() => _selectedMarker = null), child: const Icon(Icons.close, size: 18, color: Colors.grey)),
        ]),
        const SizedBox(height: 8),
        Row(children: [
          Text(m.priceDisplay ?? m.displayPrice, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: typeColor)),
          if (m.area != null) ...[const SizedBox(width: 10), Text('${(m.area! / 3.3058).round()}평', style: TextStyle(fontSize: 12, color: Colors.grey[600]))],
          if (m.floors != null) ...[const SizedBox(width: 8), Text('${m.floors}층', style: TextStyle(fontSize: 12, color: Colors.grey[600]))],
          if (m.yieldRate != null && m.yieldRate! > 0) ...[const SizedBox(width: 8), Text('${m.yieldRate!.toStringAsFixed(1)}%', style: TextStyle(fontSize: 12, color: Colors.green[700], fontWeight: FontWeight.w500))],
        ]),
        const SizedBox(height: 10),
        Row(children: [
          Expanded(child: OutlinedButton(
            onPressed: () { if (m.recordId != null) context.push('/property/detail/${m.recordId}?db_id=${m.dbId ?? 39}'); },
            style: OutlinedButton.styleFrom(foregroundColor: typeColor, side: BorderSide(color: typeColor), padding: const EdgeInsets.symmetric(vertical: 8)),
            child: const Text('상세보기', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)))),
          const SizedBox(width: 8),
          Expanded(child: ElevatedButton(
            onPressed: _showContactDialog,
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF136dec), foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 8)),
            child: const Text('문의하기', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)))),
        ]),
      ]),
    );
  }

  // =========================================================================
  // 매물검색 섹션
  // =========================================================================
  Widget _buildSearchSection() {
    final state = ref.watch(propertySearchProvider);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.grey.shade200)),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('조건 검색', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            // 부동산유형 탭
            Row(children: ['danil', 'jibhap', 'bubun'].map((t) => Expanded(child: Padding(
              padding: EdgeInsets.only(left: t == 'danil' ? 0 : 4),
              child: _searchTypeTab(t),
            ))).toList()),
            const SizedBox(height: 10),
            // 서브타입 체크박스
            _buildSearchSubtypes(),
            const SizedBox(height: 12),
            // 검색 필드
            ..._buildSearchFields(),
            const SizedBox(height: 14),
            Row(children: [
              Expanded(child: ElevatedButton.icon(onPressed: _doSearch, icon: const Icon(Icons.search, size: 16), label: const Text('검색', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF136dec), foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 12), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))))),
              const SizedBox(width: 8),
              OutlinedButton(onPressed: _resetSearch, style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))), child: const Text('초기화')),
            ]),
          ]),
        ),
        const SizedBox(height: 16),
        _buildSearchResults(state),
      ]),
    );
  }

  Widget _searchTypeTab(String type) {
    final a = _searchPropertyType == type;
    final color = _typeColors[type]!;
    final label = switch (type) { 'danil' => '단일', 'jibhap' => '집합', 'bubun' => '부분', _ => '' };
    return GestureDetector(
      onTap: () => setState(() => _searchPropertyType = type),
      child: Container(padding: const EdgeInsets.symmetric(vertical: 9),
        decoration: BoxDecoration(color: a ? color : Colors.grey.shade100, borderRadius: BorderRadius.circular(8)),
        child: Center(child: Text(label, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: a ? Colors.white : Colors.grey.shade500)))),
    );
  }

  Widget _buildSearchSubtypes() {
    final opts = _subtypeOptions[_searchPropertyType] ?? [];
    final color = _typeColors[_searchPropertyType]!;
    return Wrap(spacing: 4, runSpacing: 4, children: opts.map((st) {
      final key = '$_searchPropertyType:$st';
      final active = _searchSubtypes[key] == true;
      return GestureDetector(
        onTap: () => setState(() => _searchSubtypes[key] = !active),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: active ? color : Colors.white,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: active ? color : Colors.grey.shade300),
          ),
          child: Text(st, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: active ? Colors.white : Colors.grey.shade500)),
        ),
      );
    }).toList());
  }

  List<Widget> _buildSearchFields() => switch (_searchPropertyType) {
    'danil' => [
      _searchField('매가', '만원', '100000', _priceCtrl, _priceCond, (v) => setState(() => _priceCond = v)),
      const SizedBox(height: 10),
      _searchField('실투자금', '만원', '50000', _investCtrl, _investCond, (v) => setState(() => _investCond = v)),
      const SizedBox(height: 10),
      _searchField('수익률', '%', '5', _yieldCtrl, _yieldCond, (v) => setState(() => _yieldCond = v)),
      const SizedBox(height: 10),
      _searchField('토지면적', '㎡', '100', _areaCtrl, _areaCond, (v) => setState(() => _areaCond = v)),
    ],
    'jibhap' => [
      _searchField('매가', '만원', '100000', _priceCtrl, _priceCond, (v) => setState(() => _priceCond = v)),
      const SizedBox(height: 10),
      _searchField('보증금', '만원', '10000', _depositCtrl, _depositCond, (v) => setState(() => _depositCond = v)),
      const SizedBox(height: 10),
      _searchField('월세', '만원', '100', _rentCtrl, _rentCond, (v) => setState(() => _rentCond = v)),
      const SizedBox(height: 10),
      _searchField('전용면적', '㎡', '60', _areaCtrl, _areaCond, (v) => setState(() => _areaCond = v)),
    ],
    'bubun' => [
      _searchField('보증금', '만원', '5000', _depositCtrl, _depositCond, (v) => setState(() => _depositCond = v)),
      const SizedBox(height: 10),
      _searchField('월세', '만원', '50', _rentCtrl, _rentCond, (v) => setState(() => _rentCond = v)),
      const SizedBox(height: 10),
      _searchField('전용면적', '㎡', '30', _areaCtrl, _areaCond, (v) => setState(() => _areaCond = v)),
    ],
    _ => [],
  };

  Widget _searchField(String label, String unit, String hint, TextEditingController ctrl, String cond, ValueChanged<String> onCond) {
    return Row(children: [
      SizedBox(width: 60, child: Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500))),
      const SizedBox(width: 8),
      Expanded(flex: 5, child: TextField(controller: ctrl, keyboardType: TextInputType.number,
        decoration: InputDecoration(hintText: hint, suffixText: unit, contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10), border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)), isDense: true),
        onChanged: (v) { if (v.isNotEmpty && cond == 'all') onCond('lte'); })),
      const SizedBox(width: 8),
      Expanded(flex: 3, child: Container(height: 42, padding: const EdgeInsets.symmetric(horizontal: 10),
        decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade300), borderRadius: BorderRadius.circular(8)),
        child: DropdownButton<String>(value: cond, isExpanded: true, underline: const SizedBox(), isDense: true,
          items: const [DropdownMenuItem(value: 'all', child: Text('전체', style: TextStyle(fontSize: 13))), DropdownMenuItem(value: 'gte', child: Text('이상', style: TextStyle(fontSize: 13))), DropdownMenuItem(value: 'lte', child: Text('이하', style: TextStyle(fontSize: 13)))],
          onChanged: (v) { if (v != null) onCond(v); }))),
    ]);
  }

  void _doSearch() {
    ref.read(propertySearchProvider.notifier).search(
      priceValue: _priceCtrl.text.isNotEmpty ? _priceCtrl.text : null, priceCondition: _priceCond,
      yieldValue: _yieldCtrl.text.isNotEmpty ? _yieldCtrl.text : null, yieldCondition: _yieldCond,
      investmentValue: _investCtrl.text.isNotEmpty ? _investCtrl.text : null, investmentCondition: _investCond,
      areaValue: _areaCtrl.text.isNotEmpty ? _areaCtrl.text : null, areaCondition: _areaCond,
    );
  }

  void _resetSearch() {
    _priceCtrl.clear(); _yieldCtrl.clear(); _investCtrl.clear();
    _areaCtrl.clear(); _depositCtrl.clear(); _rentCtrl.clear();
    setState(() { _priceCond = 'all'; _yieldCond = 'all'; _investCond = 'all'; _areaCond = 'all'; _depositCond = 'all'; _rentCond = 'all';
      for (final k in _searchSubtypes.keys) _searchSubtypes[k] = true;
    });
    ref.read(propertySearchProvider.notifier).reset();
  }

  Widget _buildSearchResults(PropertySearchState state) => switch (state.status) {
    SearchStatus.initial => Padding(padding: const EdgeInsets.symmetric(vertical: 40), child: Center(child: Column(children: [Icon(Icons.search, size: 48, color: Colors.grey[300]), const SizedBox(height: 12), Text('조건을 설정하고 검색해주세요', style: TextStyle(color: Colors.grey[500], fontSize: 14))]))),
    SearchStatus.loading => const Padding(padding: EdgeInsets.symmetric(vertical: 40), child: Center(child: CircularProgressIndicator())),
    SearchStatus.error => Padding(padding: const EdgeInsets.symmetric(vertical: 40), child: Center(child: Text(state.errorMessage ?? '검색 오류', style: TextStyle(color: Colors.red[400])))),
    SearchStatus.success => state.markers.isEmpty
      ? Padding(padding: const EdgeInsets.symmetric(vertical: 40), child: Center(child: Text('조건에 맞는 매물이 없습니다', style: TextStyle(color: Colors.grey[500]))))
      : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text('검색결과: ${state.count}건', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            if (!kIsWeb) TextButton.icon(onPressed: () => context.push('/property/search-map', extra: state.markers), icon: const Icon(Icons.map, size: 16), label: const Text('지도보기', style: TextStyle(fontSize: 13))),
          ]),
          const SizedBox(height: 8),
          ...state.markers.map(_buildSearchResultCard),
        ]),
  };

  Widget _buildSearchResultCard(PropertyMapMarker m) {
    return GestureDetector(
      onTap: () { if (m.recordId != null) context.push('/property/detail/${m.recordId}?db_id=${m.dbId ?? 39}'); },
      child: Container(margin: const EdgeInsets.only(bottom: 10), padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), border: Border.all(color: Colors.grey.shade200)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(m.address ?? '', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13), maxLines: 1, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 6),
          Row(children: [
            Text(m.displayPrice, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF136dec))),
            if (m.area != null) ...[const SizedBox(width: 10), Text('${(m.area! / 3.3058).round()}평', style: TextStyle(fontSize: 12, color: Colors.grey[600]))],
            if (m.yieldRate != null) ...[const SizedBox(width: 10), Text('${m.yieldRate!.toStringAsFixed(1)}%', style: TextStyle(fontSize: 12, color: Colors.green[700], fontWeight: FontWeight.w500))],
          ]),
        ])),
    );
  }

  // =========================================================================
  // 카테고리 매물 섹션
  // =========================================================================
  Widget _buildCategorySection() {
    final state = ref.watch(propertyListProvider);
    final cat = _tabToCategory(_currentTab);
    final desc = switch (cat) {
      PropertyCategory.reconstruction => '대지 80평 이상 재건축용 매물',
      PropertyCategory.highYield => '수익률 6% 이상 (비용 제외)',
      PropertyCategory.lowCost => '단독의 꿈. 20억 이하 저가 단독주택',
      _ => null,
    };
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      if (desc != null) Padding(padding: const EdgeInsets.fromLTRB(16, 8, 16, 4), child: Text(desc, style: TextStyle(fontSize: 13, color: Colors.grey[500]))),
      Expanded(child: _buildCategoryBody(state)),
    ]);
  }

  Widget _buildCategoryBody(PropertyListState state) => switch (state.status) {
    SearchStatus.initial || SearchStatus.loading => const Center(child: CircularProgressIndicator()),
    SearchStatus.error => Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      Icon(Icons.error_outline, size: 48, color: Colors.grey[400]), const SizedBox(height: 12),
      Text(state.errorMessage ?? '오류', style: TextStyle(color: Colors.grey[600])), const SizedBox(height: 12),
      ElevatedButton(onPressed: () => ref.read(propertyListProvider.notifier).refresh(), child: const Text('다시 시도'))])),
    SearchStatus.success => state.properties.isEmpty
      ? Center(child: Text('매물이 없습니다', style: TextStyle(color: Colors.grey[500])))
      : RefreshIndicator(onRefresh: () => ref.read(propertyListProvider.notifier).refresh(),
          child: ListView.builder(
            padding: EdgeInsets.fromLTRB(16, 4, 16, MediaQuery.of(context).padding.bottom + 16),
            itemCount: state.properties.length,
            itemBuilder: (_, i) => _buildPropertyCard(state.properties[i]))),
  };

  Widget _buildPropertyCard(PropertyRecord property) {
    final f = property.fields;
    final imageUrl = _resolveImageUrl(property);
    return GestureDetector(
      onTap: () => context.push('/property/detail/${property.id}'),
      child: Container(margin: const EdgeInsets.only(bottom: 12), clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.grey.shade200),
          boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 8, offset: const Offset(0, 2))]),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          if (imageUrl != null) Image.network(imageUrl, height: 180, width: double.infinity, fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Container(height: 180, color: Colors.grey[200], child: Icon(Icons.home_outlined, size: 48, color: Colors.grey[400])))
          else Container(height: 180, color: Colors.grey[200], child: Icon(Icons.home_outlined, size: 48, color: Colors.grey[400])),
          Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(f.address ?? '', style: TextStyle(fontSize: 13, color: Colors.grey[500], fontWeight: FontWeight.w500), maxLines: 1, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Text(property.priceDisplay, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF136dec))),
            const SizedBox(height: 8),
            Wrap(spacing: 6, runSpacing: 4, children: [
              if (f.landArea != null) _chip('${property.landAreaPyung}평'),
              if (f.yieldRate != null && f.yieldRate! > 0) _chip('수익률 ${f.yieldRate!.toStringAsFixed(1)}%'),
              if (f.floors != null && f.floors!.isNotEmpty) _chip('${f.floors}층'),
              if (f.mainUsage != null && f.mainUsage!.isNotEmpty) _chip(f.mainUsage!),
            ].take(3).toList()),
          ])),
        ])),
    );
  }

  String? _resolveImageUrl(PropertyRecord p) {
    final photos = p.fields.representativePhoto;
    if (photos != null && photos.isNotEmpty) {
      final url = photos.first.url;
      if (url != null && url.isNotEmpty) return url.startsWith('/') ? '${ApiClient.baseUrl}$url' : url;
    }
    final link = p.fields.photoLink;
    if (link != null && link.isNotEmpty) { final u = link.split(',').first.trim(); return u.startsWith('/') ? '${ApiClient.baseUrl}$u' : u; }
    return null;
  }

  Widget _chip(String t) => Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(6)),
    child: Text(t, style: TextStyle(fontSize: 11, color: Colors.grey[600], fontWeight: FontWeight.w500)));

  void _showContactDialog() {
    const ph = '02-3471-7377';
    showDialog(context: context, builder: (ctx) => AlertDialog(
      title: const Text('금토끼부동산중개', style: TextStyle(fontSize: 17)),
      content: ListTile(leading: const Icon(Icons.phone, color: Color(0xFFD4AF37)), title: const Text(ph),
        onTap: () async { final u = Uri.parse('tel:${ph.replaceAll('-', '')}'); if (await canLaunchUrl(u)) await launchUrl(u); }),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('닫기'))],
    ));
  }
}
