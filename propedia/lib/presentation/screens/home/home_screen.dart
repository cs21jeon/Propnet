import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:kakao_map_plugin/kakao_map_plugin.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/core/update/in_app_update_service.dart';
import 'package:propedia/data/dto/building_dto.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:propedia/presentation/providers/building_provider.dart';
import 'package:propedia/presentation/providers/history_provider.dart';
import 'package:propedia/presentation/providers/favorites_provider.dart';
import 'package:propedia/presentation/providers/map_provider.dart';
import 'package:propedia/presentation/providers/notice_provider.dart';
import 'package:propedia/presentation/widgets/ads/banner_ad_widget.dart';
import 'package:propedia/presentation/widgets/common/app_drawer.dart';
import 'package:propedia/presentation/widgets/common/app_footer.dart';
import 'package:propedia/presentation/widgets/common/notice_dialog.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  Timer? _noticeTimer;

  // 지도 관련
  KakaoMapController? _mapController;
  Set<Polygon> _polygons = {};
  bool _isMapReady = false;

  // 검색 관련
  final _searchController = TextEditingController();
  final _searchFocusNode = FocusNode();
  Timer? _debounce;
  bool _showDropdown = false;

  // 기본 위치 (서울시청)
  static const _defaultLat = 37.5665;
  static const _defaultLng = 126.9780;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadData();
    });
    _noticeTimer = Timer.periodic(const Duration(minutes: 30), (_) {
      ref.read(noticeProvider.notifier).fetchNotices();
    });
  }

  @override
  void dispose() {
    _noticeTimer?.cancel();
    _debounce?.cancel();
    _searchController.dispose();
    _searchFocusNode.dispose();
    ref.read(mapSearchProvider.notifier).resetState();
    super.dispose();
  }

  void _loadData() {
    final authState = ref.read(authProvider);
    ref.read(historyProvider.notifier).loadLocalHistory();
    ref.read(favoritesProvider.notifier).loadLocalFavorites();
    if (authState.status == AuthStatus.authenticated) {
      ref.read(historyProvider.notifier).syncFromServer();
      ref.read(favoritesProvider.notifier).syncFromServer();
    }
    _checkForUpdate();
    ref.read(noticeProvider.notifier).fetchNotices();
  }

  Future<void> _checkForUpdate() async {
    final updateAvailable = await InAppUpdateService.checkForUpdate();
    if (!updateAvailable || !mounted) return;
    final downloaded = await InAppUpdateService.startFlexibleUpdate();
    if (!downloaded || !mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('업데이트가 다운로드되었습니다'),
        duration: const Duration(seconds: 10),
        action: SnackBarAction(
          label: '재시작',
          onPressed: () => InAppUpdateService.completeFlexibleUpdate(),
        ),
      ),
    );
  }

  // ==================== 검색 ====================

  void _onQueryChanged(String query) {
    _debounce?.cancel();
    setState(() {
      _showDropdown = query.trim().length >= 2;
    });
    if (query.trim().length < 2) {
      ref.read(unifiedSearchProvider.notifier).reset();
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 300), () {
      ref.read(unifiedSearchProvider.notifier).search(query);
    });
  }

  void _onSearchResultSelected(UnifiedSearchResultItem item) {
    _searchFocusNode.unfocus();
    _searchController.text = item.label;
    setState(() => _showDropdown = false);

    // 좌표가 있으면 지도 이동 + 역지오코딩
    double? lat, lon;
    if (item.center != null && item.center!.length >= 2) {
      lat = item.center![0];
      lon = item.center![1];
    } else if (item.coords != null && item.coords!.length >= 2) {
      lat = item.coords![0];
      lon = item.coords![1];
    }

    if (lat != null && lon != null && _isMapReady) {
      _moveToLocation(lat, lon);
      _mapController?.clearMarker();
      _mapController?.addMarker(
        markers: [Marker(markerId: 'search', latLng: LatLng(lat, lon))],
      );
      _mapController?.setLevel(item.type == 'complex' ? 3 : 2);
      // 역지오코딩으로 상세 정보 가져오기
      ref.read(mapSearchProvider.notifier).searchByCoordinate(lat, lon);
    } else {
      // 좌표 없음 — 직접 상세 조회로 이동
      _navigateToResultDirect(item);
    }
  }

  void _navigateToResultDirect(UnifiedSearchResultItem item) {
    final notifier = ref.read(buildingSearchProvider.notifier);
    if (item.bdMgtSn != null && item.bdMgtSn!.isNotEmpty) {
      notifier.searchByBdMgtSn(
        item.bdMgtSn!,
        lnbrMnnm: item.lnbrMnnm,
        lnbrSlno: item.lnbrSlno,
        admCd: item.admCd,
        searchType: 'unified',
      );
      context.push('/result');
    } else if (item.pnu != null && item.pnu!.length >= 11) {
      final bjdongCode = item.pnu!.substring(0, 10);
      // PNU: [법정동코드10][지목1][본번4][부번4] = 19자리. index 10은 지목이므로 건너뜀
      final bun = item.pnu!.length >= 15 ? item.pnu!.substring(11, 15) : item.pnu!.substring(11);
      final ji = item.pnu!.length >= 19 ? item.pnu!.substring(15, 19) : '0000';
      notifier.searchByJibun(bjdongCode: bjdongCode, bun: bun, ji: ji, searchType: 'unified');
      context.push('/result');
    }
  }

  // ==================== 지도 ====================

  void _onMapTap(LatLng latLng) async {
    _searchFocusNode.unfocus();
    setState(() => _showDropdown = false);

    if (_mapController != null) {
      await _mapController!.clearMarker();
      await _mapController!.addMarker(
        markers: [Marker(markerId: 'selected', latLng: latLng)],
      );
    }
    if (_polygons.isNotEmpty) {
      setState(() => _polygons = {});
    }
    _moveToLocation(latLng.latitude, latLng.longitude);
    ref.read(mapSearchProvider.notifier).searchByCoordinate(
          latLng.latitude,
          latLng.longitude,
        );
  }

  void _moveToLocation(double lat, double lng) {
    _mapController?.setCenter(LatLng(lat, lng));
  }

  void _moveToCurrentLocation() async {
    final location = ref.read(currentLocationProvider);
    location.whenData((position) {
      if (position != null) {
        _moveToLocation(position.latitude, position.longitude);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('현재 위치를 가져올 수 없습니다')),
        );
      }
    });
    ref.invalidate(currentLocationProvider);
  }

  void _updatePolygon(MapSearchState mapState) {
    if (mapState.parcelGeometry != null) {
      final geometry = mapState.parcelGeometry!;
      final coordinates = geometry.coordinates;
      List<LatLng> path = [];
      try {
        if (geometry.type == 'Polygon' && coordinates.isNotEmpty) {
          final ring = coordinates[0] as List;
          for (var coord in ring) {
            if (coord is List && coord.length >= 2) {
              path.add(LatLng((coord[1] as num).toDouble(), (coord[0] as num).toDouble()));
            }
          }
        } else if (geometry.type == 'MultiPolygon' && coordinates.isNotEmpty) {
          final firstPolygon = coordinates[0] as List;
          if (firstPolygon.isNotEmpty) {
            final ring = firstPolygon[0] as List;
            for (var coord in ring) {
              if (coord is List && coord.length >= 2) {
                path.add(LatLng((coord[1] as num).toDouble(), (coord[0] as num).toDouble()));
              }
            }
          }
        }
      } catch (e) {
        debugPrint('폴리곤 파싱 오류: $e');
      }
      if (path.isNotEmpty) {
        setState(() {
          _polygons = {
            Polygon(
              polygonId: 'parcel',
              points: path,
              strokeColor: AppColors.primary,
              strokeWidth: 3,
              fillColor: AppColors.primary.withValues(alpha: 0.2),
            ),
          };
        });
      }
    } else if (_polygons.isNotEmpty) {
      setState(() => _polygons = {});
    }
  }

  void _onSearchBuilding(dynamic jibunInfo) {
    ref.read(buildingSearchProvider.notifier).searchByJibun(
          bjdongCode: jibunInfo.bjdongCode,
          bun: jibunInfo.bun,
          ji: jibunInfo.ji,
          landType: jibunInfo.landType,
          searchType: 'map',
        );
    context.push('/result');
  }

  // ==================== Build ====================

  @override
  Widget build(BuildContext context) {
    final mapState = ref.watch(mapSearchProvider);
    final searchState = ref.watch(unifiedSearchProvider);
    final currentLocation = ref.watch(currentLocationProvider);

    // 공지사항 표시
    ref.listen<NoticeState>(noticeProvider, (previous, next) {
      if (!next.isLoading && !next.hasShown && next.visibleNotices.isNotEmpty) {
        ref.read(noticeProvider.notifier).markShown();
        final notice = next.visibleNotices.first;
        NoticeDialog.show(
          context,
          notice: notice,
          onDismiss: () => ref.read(noticeProvider.notifier).dismissNotice(notice.id),
          onDismissForToday: notice.isDismissible
              ? () => ref.read(noticeProvider.notifier).dismissForToday(notice.id)
              : null,
        );
      }
    });

    // 로그인 상태 변경 감지
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (previous?.status != next.status) {
        if (next.status == AuthStatus.authenticated) {
          ref.read(historyProvider.notifier).syncFromServer();
          ref.read(favoritesProvider.notifier).syncFromServer();
        } else if (next.status == AuthStatus.guest) {
          ref.read(historyProvider.notifier).loadLocalHistory();
          ref.read(favoritesProvider.notifier).loadLocalFavorites();
        }
      }
    });

    // 폴리곤 업데이트
    ref.listen<MapSearchState>(mapSearchProvider, (previous, next) {
      if (next.status == SearchStatus.success) {
        _updatePolygon(next);
      } else if (next.status == SearchStatus.initial || next.status == SearchStatus.error) {
        if (_polygons.isNotEmpty) setState(() => _polygons = {});
      }
    });

    // Web은 지도 미지원 — 검색만 제공
    if (kIsWeb) return _buildWebFallback(context, searchState);

    final showInfoCard = mapState.status == SearchStatus.success && mapState.jibunInfo != null;
    final showLoading = mapState.status == SearchStatus.loading;

    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 56,
        leading: Builder(
          builder: (context) => IconButton(
            icon: const Icon(Icons.menu),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset('assets/images/proppedia_logo.png', height: 36),
            const SizedBox(width: 8),
            Text(
              'Proppedia',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primary),
            ),
          ],
        ),
        centerTitle: true,
      ),
      drawer: const AppDrawer(currentApp: AppType.main),
      resizeToAvoidBottomInset: false,
      body: Stack(
        children: [
          // Layer 1: 전체 화면 카카오맵
          KakaoMap(
            onMapCreated: (controller) {
              _mapController = controller;
              setState(() => _isMapReady = true);
              currentLocation.whenData((position) {
                if (position != null) {
                  _moveToLocation(position.latitude, position.longitude);
                }
              });
            },
            onMapTap: _onMapTap,
            center: LatLng(_defaultLat, _defaultLng),
            polygons: _polygons.toList(),
          ),

          // 지도 로딩 중
          if (!_isMapReady)
            Container(
              color: Colors.grey[100],
              child: const Center(child: CircularProgressIndicator()),
            ),

          // Layer 2: 플로팅 검색바 + 드롭다운
          Positioned(
            top: 8,
            left: 12,
            right: 12,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // 검색바
                Material(
                  elevation: 4,
                  borderRadius: BorderRadius.circular(12),
                  child: TextField(
                    controller: _searchController,
                    focusNode: _searchFocusNode,
                    onChanged: _onQueryChanged,
                    onTap: () {
                      if (_searchController.text.trim().length >= 2) {
                        setState(() => _showDropdown = true);
                      }
                    },
                    decoration: InputDecoration(
                      hintText: '주소, 건물명, 단지명 검색',
                      hintStyle: TextStyle(color: Colors.grey[400], fontSize: 15),
                      prefixIcon: const Icon(Icons.search, color: Colors.grey),
                      suffixIcon: _searchController.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear, size: 20),
                              onPressed: () {
                                _searchController.clear();
                                ref.read(unifiedSearchProvider.notifier).reset();
                                setState(() => _showDropdown = false);
                              },
                            )
                          : null,
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    ),
                  ),
                ),

                // 드롭다운 결과
                if (_showDropdown && searchState.status != SearchStatus.initial)
                  Container(
                    margin: const EdgeInsets.only(top: 4),
                    constraints: const BoxConstraints(maxHeight: 360),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.15),
                          blurRadius: 16,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: _buildSearchDropdown(searchState),
                  ),
              ],
            ),
          ),

          // Layer 3: 안내 문구 (아무것도 선택되지 않았을 때)
          if (_isMapReady && !showLoading && !showInfoCard &&
              mapState.status != SearchStatus.error && !_showDropdown)
            Positioned(
              bottom: 24,
              left: 0,
              right: 0,
              child: IgnorePointer(
                child: Center(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Text(
                      '지도에서 직접 선택하세요',
                      style: TextStyle(color: Colors.white, fontSize: 13),
                    ),
                  ),
                ),
              ),
            ),

          // 하단 정보 카드
          if (showLoading)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
                      const SizedBox(width: 12),
                      Text('조회 중...', style: TextStyle(color: Colors.grey[600])),
                    ],
                  ),
                ),
              ),
            ),

          if (showInfoCard)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: _buildInfoCard(mapState),
            ),

          if (mapState.status == SearchStatus.error && mapState.errorMessage != null)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: Card(
                color: Colors.red[50],
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text(
                    mapState.errorMessage!,
                    style: TextStyle(color: Colors.red[700], fontSize: 13),
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
            ),

          // Layer 4: 현재 위치 FAB
          if (_isMapReady)
            Positioned(
              right: 12,
              bottom: showInfoCard ? 160 : 16,
              child: FloatingActionButton(
                heroTag: 'currentLocation',
                mini: true,
                backgroundColor: Colors.white,
                onPressed: _moveToCurrentLocation,
                child: const Icon(Icons.my_location, color: AppColors.primary),
              ),
            ),
        ],
      ),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (!kIsWeb) const BannerAdWidget(),
          _buildBottomNavigation(context),
          const AppFooterSimple(),
        ],
      ),
    );
  }

  Widget _buildSearchDropdown(UnifiedSearchState state) {
    if (state.status == SearchStatus.loading) {
      return const Padding(
        padding: EdgeInsets.all(16),
        child: Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))),
      );
    }
    if (state.results.isEmpty) {
      return Padding(
        padding: const EdgeInsets.all(16),
        child: Text(
          '"${state.query}"에 대한 결과 없음',
          style: TextStyle(color: Colors.grey[500], fontSize: 13),
          textAlign: TextAlign.center,
        ),
      );
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: ListView.separated(
        shrinkWrap: true,
        padding: EdgeInsets.zero,
        itemCount: state.results.length,
        separatorBuilder: (_, __) => Divider(height: 1, color: Colors.grey[200]),
        itemBuilder: (context, index) {
          final item = state.results[index];
          return _buildResultTile(item);
        },
      ),
    );
  }

  Widget _buildResultTile(UnifiedSearchResultItem item) {
    final typeIcon = switch (item.type) {
      'complex' => Icons.apartment,
      'road' => Icons.signpost_outlined,
      _ => Icons.location_on_outlined,
    };
    final typeColor = switch (item.type) {
      'complex' => AppColors.primary,
      'road' => AppColors.success,
      _ => AppColors.warning,
    };

    return ListTile(
      dense: true,
      leading: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: typeColor.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(typeIcon, color: typeColor, size: 20),
      ),
      title: Text(item.label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14), maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: item.sublabel != null
          ? Text(item.sublabel!, style: TextStyle(color: Colors.grey[500], fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis)
          : null,
      trailing: Icon(Icons.chevron_right, color: Colors.grey[400], size: 18),
      onTap: () => _onSearchResultSelected(item),
    );
  }

  Widget _buildInfoCard(MapSearchState mapState) {
    final jibunInfo = mapState.jibunInfo!;
    return Card(
      elevation: 6,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    jibunInfo.landTypeName ?? (jibunInfo.landType == '1' ? '대' : '임'),
                    style: const TextStyle(color: AppColors.primary, fontSize: 11, fontWeight: FontWeight.w600),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    jibunInfo.address,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                // 닫기 버튼
                InkWell(
                  onTap: () {
                    ref.read(mapSearchProvider.notifier).resetState();
                    _mapController?.clearMarker();
                  },
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.all(4),
                    child: Icon(Icons.close, size: 18, color: Colors.grey[400]),
                  ),
                ),
              ],
            ),
            if (jibunInfo.roadAddress != null && jibunInfo.roadAddress!.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                '도로명: ${jibunInfo.roadAddress!}',
                style: TextStyle(color: Colors.grey[600], fontSize: 12),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _onSearchBuilding(jibunInfo),
                icon: const Icon(Icons.search, size: 18),
                label: const Text('상세 조회'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 10),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomNavigation(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        border: Border(top: BorderSide(color: isDark ? Colors.grey[700]! : Colors.grey[200]!)),
      ),
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildNavItem(context: context, icon: Icons.home, label: '홈', isActive: true, onTap: () {}),
          _buildNavItem(context: context, icon: Icons.history, label: '검색기록', isActive: false, onTap: () => context.go('/history')),
          _buildNavItem(context: context, icon: Icons.star_outline, label: '즐겨찾기', isActive: false, onTap: () => context.go('/favorites')),
          _buildNavItem(context: context, icon: Icons.person_outline, label: '프로필', isActive: false, onTap: () => context.go('/profile')),
        ],
      ),
    );
  }

  Widget _buildNavItem({
    required BuildContext context,
    required IconData icon,
    required String label,
    required bool isActive,
    required VoidCallback onTap,
  }) {
    final color = isActive ? AppColors.primary : Colors.grey[400];
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: color, size: 26),
              const SizedBox(height: 4),
              Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color)),
            ],
          ),
        ),
      ),
    );
  }

  /// Web 폴백 (카카오맵 미지원)
  Widget _buildWebFallback(BuildContext context, UnifiedSearchState searchState) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset('assets/images/proppedia_logo.png', height: 36),
            const SizedBox(width: 8),
            Text('Proppedia', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primary)),
          ],
        ),
        centerTitle: true,
      ),
      drawer: const AppDrawer(currentApp: AppType.main),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _searchController,
              focusNode: _searchFocusNode,
              onChanged: _onQueryChanged,
              decoration: InputDecoration(
                hintText: '주소, 건물명, 단지명 검색',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(icon: const Icon(Icons.clear), onPressed: () {
                        _searchController.clear();
                        ref.read(unifiedSearchProvider.notifier).reset();
                        setState(() => _showDropdown = false);
                      })
                    : null,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 8),
            if (searchState.status == SearchStatus.loading)
              const Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()),
            if (searchState.results.isNotEmpty)
              Expanded(
                child: ListView.separated(
                  itemCount: searchState.results.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final item = searchState.results[index];
                    return ListTile(
                      title: Text(item.label),
                      subtitle: item.sublabel != null ? Text(item.sublabel!) : null,
                      onTap: () => _navigateToResultDirect(item),
                    );
                  },
                ),
              ),
          ],
        ),
      ),
      bottomNavigationBar: const AppFooterSimple(),
    );
  }
}
