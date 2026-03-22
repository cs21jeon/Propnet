import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kakao_map_plugin/kakao_map_plugin.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/data/dto/building_dto.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:propedia/presentation/providers/building_provider.dart';
import 'package:propedia/presentation/providers/map_provider.dart';
import 'package:propedia/presentation/providers/pdf_provider.dart';
import 'package:propedia/presentation/providers/history_provider.dart';
import 'package:propedia/presentation/providers/favorites_provider.dart';
import 'package:propedia/presentation/widgets/ads/banner_ad_widget.dart';
import 'package:propedia/presentation/widgets/common/login_prompt_dialog.dart';
import 'package:propedia/presentation/widgets/common/loading_progress_indicator.dart';
import 'package:propedia/presentation/providers/airtable_provider.dart';

class ResultScreen extends ConsumerStatefulWidget {
  const ResultScreen({super.key});

  @override
  ConsumerState<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends ConsumerState<ResultScreen> {
  String? _selectedDong;
  String? _selectedHo;
  List<String> _hoList = [];
  bool _historySaved = false; // 검색 기록 저장 여부

  /// 시군구명 정규화 (화성시동탄구 → 화성시 동탄구)
  String _normalizeDistrictName(String? sigunguName) {
    if (sigunguName == null || sigunguName.isEmpty) return '';
    final pattern = RegExp(r'^(.+시)(.+구)$');
    final match = pattern.firstMatch(sigunguName);
    if (match != null) {
      return '${match.group(1)} ${match.group(2)}';
    }
    return sigunguName;
  }

  /// 주소에 구 이름 삽입 (신규 행정구역용)
  /// "화성시 오산동 988" → "화성시 동탄구 오산동 988"
  String _injectDistrictName(String address, String normalizedSigungu) {
    if (address.isEmpty || normalizedSigungu.isEmpty) return address;

    // "화성시 동탄구"에서 시, 구 분리
    final parts = normalizedSigungu.split(' ');
    if (parts.length < 2) return address;

    final city = parts[0];     // "화성시"
    final district = parts[1]; // "동탄구"

    // 이미 구 이름이 있으면 그대로 반환
    if (address.contains(district)) return address;

    // "화성시 " 뒤에 "동탄구 " 삽입
    return address.replaceFirst('$city ', '$city $district ');
  }

  /// 지도 마커 라벨 생성 (동+지번 형태)
  String _buildMarkerLabel(BuildingSearchResponse result) {
    final address = result.address;
    final codes = result.codes;

    // 동 이름
    String? dongName = address?.eupmyeondongName;

    // 지번 (PNU에서 추출)
    String? jibun;
    if (codes?.pnu != null && codes!.pnu!.length >= 19) {
      final pnu = codes.pnu!;
      final landType = pnu.substring(10, 11);
      final bun = int.tryParse(pnu.substring(11, 15))?.toString() ?? '';
      final ji = int.tryParse(pnu.substring(15, 19))?.toString() ?? '';

      if (bun.isNotEmpty) {
        final sanPrefix = landType == '2' ? '산 ' : '';
        jibun = (ji.isNotEmpty && ji != '0') ? '$sanPrefix$bun-$ji' : '$sanPrefix$bun';
      }
    }

    // "오산동 988" 형태
    if (dongName != null && jibun != null) {
      return '$dongName $jibun';
    }
    return jibun ?? '';
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(areaInfoProvider.notifier).reset();
      // 즐겨찾기 목록 로드
      ref.read(favoritesProvider.notifier).loadLocalFavorites();
      // 검색 상태 변화 감지하여 기록 저장
      _listenForSearchCompletion();
    });
  }

  /// 검색 완료 시 기록 저장
  void _listenForSearchCompletion() {
    // 현재 상태 체크
    final currentState = ref.read(buildingSearchProvider);
    if (currentState.status == SearchStatus.success) {
      _saveSearchHistory();
    } else {
      // 아직 로딩 중이면 상태 변화 감지
      ref.listenManual(buildingSearchProvider, (previous, next) {
        if (next.status == SearchStatus.success && !_historySaved) {
          _saveSearchHistory();
        }
      });
    }
  }

  /// 검색 기록 저장
  void _saveSearchHistory() {
    if (_historySaved) return;

    // 로그인 상태 확인 - 비로그인 시 기록 저장 안 함
    final authState = ref.read(authProvider);
    if (authState.status != AuthStatus.authenticated) return;

    final searchState = ref.read(buildingSearchProvider);
    if (searchState.status != SearchStatus.success || searchState.result == null) return;

    final result = searchState.result!;
    final address = result.address;
    final building = result.building;
    final pnu = result.codes?.pnu;

    // 표시용 주소 생성
    String displayAddress = address?.fullAddress ?? '';
    if (displayAddress.isEmpty) {
      displayAddress = building?.buildingInfo?.platPlc ?? '주소 없음';
    }

    // 검색 타입 (provider에서 가져옴)
    final searchType = searchState.searchType;

    ref.read(historyProvider.notifier).addHistory(
      searchType: searchType,
      displayAddress: displayAddress,
      roadAddress: building?.buildingInfo?.newPlatPlc,
      jibunAddress: building?.buildingInfo?.platPlc,
      buildingName: building?.buildingInfo?.buildingName,
      pnu: pnu,
      buildingType: building?.type,
    );

    _historySaved = true;
  }

  void _onDongSelected(String? dong, Map<String, dynamic> dongHoDict) {
    setState(() {
      _selectedDong = dong;
      _selectedHo = null;
      if (dong != null && dongHoDict.containsKey(dong)) {
        final hoData = dongHoDict[dong];
        if (hoData is List) {
          _hoList = hoData.map((e) {
            if (e is Map<String, dynamic>) {
              return e['ho_nm']?.toString() ?? '';
            }
            return e.toString();
          }).where((e) => e.isNotEmpty).toList().cast<String>();
        } else {
          _hoList = [];
        }
      } else {
        _hoList = [];
      }
    });
    ref.read(areaInfoProvider.notifier).selectDong(dong);
  }

  void _onHoSelected(String? ho) {
    setState(() {
      _selectedHo = ho;
    });
    ref.read(areaInfoProvider.notifier).selectHo(ho);
  }

  void _fetchAreaInfo() {
    final searchResult = ref.read(buildingSearchProvider).result;
    if (searchResult == null || _selectedDong == null || _selectedHo == null) return;

    final address = searchResult.address;
    final bjdongCode = address?.bjdongCode;
    if (bjdongCode == null) return;

    final pnu = searchResult.codes?.pnu;
    String bun = '0';
    String ji = '0000';
    if (pnu != null && pnu.length >= 19) {
      bun = pnu.substring(11, 15);
      ji = pnu.substring(15, 19);
    }

    ref.read(areaInfoProvider.notifier).fetchAreaInfo(
      bjdongCode: bjdongCode,
      bun: bun,
      ji: ji,
      dongNm: _selectedDong!,
      hoNm: _selectedHo!,
    );
  }

  /// 임야 여부 확인 (PNU의 11번째 자리가 2이면 임야)
  bool _isForestLand(String? pnu) {
    if (pnu == null || pnu.length < 11) return false;
    return pnu[10] == '2';
  }

  @override
  Widget build(BuildContext context) {
    final searchState = ref.watch(buildingSearchProvider);
    final pdfState = ref.watch(pdfProvider);
    final areaInfoState = ref.watch(areaInfoProvider);
    final favoritesState = ref.watch(favoritesProvider);
    final canSaveToAirtable = ref.watch(canSaveToAirtableProvider);
    final airtableSaveState = ref.watch(airtableSaveProvider);

    // 공동주택 여부 확인
    final isMultiUnit = searchState.result?.building?.type == 'multi_unit';
    // 공동주택이면 areaInfo가 있어야 PDF 가능
    final canShowPdf = searchState.status == SearchStatus.success &&
        searchState.result != null &&
        (!isMultiUnit || areaInfoState.status == SearchStatus.success);

    // 즐겨찾기 여부 확인 (PNU 기반)
    final pnu = searchState.result?.codes?.pnu;
    final isFavorite = pnu != null &&
        pnu.isNotEmpty &&
        favoritesState.localFavorites.any((f) =>
            f.pnu == pnu &&
            f.dongName == _selectedDong &&
            f.hoName == _selectedHo);

    return Scaffold(
      appBar: AppBar(
        title: const Text('검색 결과'),
        actions: [
          // Airtable 저장 버튼 (권한 있는 사용자만)
          if (canSaveToAirtable && searchState.status == SearchStatus.success && searchState.result != null)
            IconButton(
              icon: airtableSaveState.status == AirtableSaveStatus.saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(
                      airtableSaveState.status == AirtableSaveStatus.success
                          ? Icons.cloud_done
                          : Icons.cloud_upload_outlined,
                      color: airtableSaveState.status == AirtableSaveStatus.success
                          ? Colors.green
                          : null,
                    ),
              tooltip: 'Airtable에 저장',
              onPressed: airtableSaveState.status == AirtableSaveStatus.saving
                  ? null
                  : () => _saveToAirtable(searchState.result!),
            ),
          // 즐겨찾기 버튼
          if (searchState.status == SearchStatus.success && searchState.result != null)
            IconButton(
              icon: Icon(
                isFavorite ? Icons.star : Icons.star_border,
                color: isFavorite ? Colors.amber : null,
              ),
              tooltip: isFavorite ? '즐겨찾기 해제' : '즐겨찾기 등록',
              onPressed: () => _toggleFavorite(searchState.result!, isFavorite),
            ),
          // PDF 버튼 (공동주택은 동/호 선택 후에만 활성화)
          if (canShowPdf)
            IconButton(
              icon: pdfState.status == PdfStatus.loading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.picture_as_pdf),
              tooltip: 'PDF 저장',
              onPressed: pdfState.status == PdfStatus.loading
                  ? null
                  : () => _showPdfOptions(context, searchState.result!),
            ),
        ],
      ),
      body: _buildBody(context, searchState),
      // 배너 광고 (웹이 아닌 경우에만 표시)
      bottomNavigationBar: kIsWeb ? null : const BottomBannerAdWidget(),
    );
  }

  /// 표시용 주소 가져오기
  String _getDisplayAddress(BuildingSearchResponse? result) {
    if (result == null) return '';
    final address = result.address;
    final building = result.building;

    String displayAddress = address?.fullAddress ?? '';
    if (displayAddress.isEmpty) {
      displayAddress = building?.buildingInfo?.platPlc ?? '';
    }
    return displayAddress;
  }

  /// 즐겨찾기 토글
  Future<void> _toggleFavorite(BuildingSearchResponse result, bool isFavorite) async {
    // 로그인 상태 확인 - 비로그인 시 로그인 유도 다이얼로그 표시
    final authState = ref.read(authProvider);
    if (authState.status != AuthStatus.authenticated) {
      LoginPromptDialog.show(
        context,
        title: '즐겨찾기',
        message: '로그인하면 즐겨찾기를 등록하고 모든 기기에서 동기화할 수 있습니다.',
      );
      return;
    }

    final displayAddress = _getDisplayAddress(result);
    if (displayAddress.isEmpty) return;

    final building = result.building;
    final pnu = result.codes?.pnu;

    if (isFavorite) {
      // 즐겨찾기 해제
      final id = ref.read(favoritesProvider.notifier).findFavoriteId(
        displayAddress,
        dongName: _selectedDong,
        hoName: _selectedHo,
      );
      if (id != null) {
        await ref.read(favoritesProvider.notifier).deleteFavorite(id);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('즐겨찾기에서 삭제되었습니다'),
              duration: Duration(seconds: 2),
            ),
          );
        }
      }
    } else {
      // 즐겨찾기 등록
      await ref.read(favoritesProvider.notifier).addFavorite(
        displayAddress: displayAddress,
        roadAddress: building?.buildingInfo?.newPlatPlc,
        jibunAddress: building?.buildingInfo?.platPlc,
        buildingName: building?.buildingInfo?.buildingName,
        pnu: pnu,
        dongName: _selectedDong,
        hoName: _selectedHo,
        buildingType: building?.type,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('즐겨찾기에 등록되었습니다'),
            duration: Duration(seconds: 2),
          ),
        );
      }
    }
  }

  /// Airtable에 저장
  Future<void> _saveToAirtable(BuildingSearchResponse result) async {
    final areaInfoState = ref.read(areaInfoProvider);
    final areaInfo = areaInfoState.status == SearchStatus.success ? areaInfoState.areaInfo : null;

    final success = await ref.read(airtableSaveProvider.notifier).saveToAirtable(
      result,
      selectedDong: _selectedDong,
      selectedHo: _selectedHo,
      areaInfo: areaInfo,
    );

    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(success ? 'Airtable에 저장되었습니다' : '저장 실패: ${ref.read(airtableSaveProvider).errorMessage ?? "오류"}'),
        duration: const Duration(seconds: 2),
        backgroundColor: success ? Colors.green : Colors.red,
      ),
    );
  }

  /// PDF 옵션 Bottom Sheet
  void _showPdfOptions(BuildContext context, BuildingSearchResponse data) {
    // 로그인 상태 확인
    final authState = ref.read(authProvider);
    if (authState.status != AuthStatus.authenticated) {
      // 비로그인 시 로그인 유도 다이얼로그 표시
      LoginPromptDialog.show(
        context,
        title: 'PDF 저장',
        message: '로그인하면 건축물대장 정보를 PDF로 저장하고 공유할 수 있습니다.',
      );
      return;
    }

    final areaInfoState = ref.read(areaInfoProvider);
    final areaInfo = areaInfoState.status == SearchStatus.success ? areaInfoState.areaInfo : null;

    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // 핸들
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),

              // 제목
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    Icon(Icons.picture_as_pdf, color: AppColors.primary),
                    const SizedBox(width: 12),
                    Text(
                      'PDF 내보내기',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ],
                ),
              ),

              const Divider(),

              // 미리보기
              ListTile(
                leading: const Icon(Icons.preview),
                title: const Text('미리보기'),
                subtitle: const Text('PDF를 미리 확인합니다'),
                onTap: () {
                  Navigator.pop(context);
                  _previewPdf(data, areaInfo);
                },
              ),

              // 저장
              ListTile(
                leading: const Icon(Icons.save_alt),
                title: const Text('저장'),
                subtitle: const Text('기기에 PDF 파일을 저장합니다'),
                onTap: () {
                  Navigator.pop(context);
                  _savePdf(data, areaInfo);
                },
              ),

              // 공유
              ListTile(
                leading: const Icon(Icons.share),
                title: const Text('공유'),
                subtitle: const Text('다른 앱으로 PDF를 공유합니다'),
                onTap: () {
                  Navigator.pop(context);
                  _sharePdf(data, areaInfo);
                },
              ),

              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }

  /// PDF 미리보기
  Future<void> _previewPdf(BuildingSearchResponse data, AreaInfo? areaInfo) async {
    final notifier = ref.read(pdfProvider.notifier);

    // PDF 생성
    await notifier.generatePdf(data: data, areaInfo: areaInfo);

    final state = ref.read(pdfProvider);
    if (state.status == PdfStatus.success && state.pdfBytes != null) {
      // printing 패키지의 미리보기 사용
      await notifier.previewPdf();
    } else if (state.status == PdfStatus.error && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(state.errorMessage ?? 'PDF 생성 실패'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  /// PDF 저장
  Future<void> _savePdf(BuildingSearchResponse data, AreaInfo? areaInfo) async {
    final notifier = ref.read(pdfProvider.notifier);

    // PDF 생성
    await notifier.generatePdf(data: data, areaInfo: areaInfo);

    final state = ref.read(pdfProvider);
    if (state.status == PdfStatus.success) {
      final result = await notifier.savePdf();
      if (mounted) {
        if (result != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(kIsWeb ? result : 'PDF 저장 완료: $result'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 3),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('PDF 저장 실패'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } else if (state.status == PdfStatus.error && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(state.errorMessage ?? 'PDF 생성 실패'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  /// PDF 공유
  Future<void> _sharePdf(BuildingSearchResponse data, AreaInfo? areaInfo) async {
    final notifier = ref.read(pdfProvider.notifier);

    // PDF 생성
    await notifier.generatePdf(data: data, areaInfo: areaInfo);

    final state = ref.read(pdfProvider);
    if (state.status == PdfStatus.success) {
      await notifier.sharePdf();
    } else if (state.status == PdfStatus.error && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(state.errorMessage ?? 'PDF 생성 실패'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Widget _buildBody(BuildContext context, BuildingSearchState state) {
    switch (state.status) {
      case SearchStatus.initial:
        return const Center(child: Text('검색 결과가 없습니다'));
      case SearchStatus.loading:
        return const LoadingProgressIndicator();
      case SearchStatus.error:
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline, size: 64, color: Colors.grey[400]),
                const SizedBox(height: 16),
                Text(
                  state.errorMessage ?? '오류가 발생했습니다',
                  style: TextStyle(color: Colors.grey[600], fontSize: 16),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.refresh),
                  label: const Text('다시 시도'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 24,
                      vertical: 12,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  '네트워크 연결을 확인하고\n다시 시도해 보세요',
                  style: TextStyle(color: Colors.grey[500], fontSize: 13),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        );
      case SearchStatus.success:
        if (state.result == null) {
          return const Center(child: Text('검색 결과가 없습니다'));
        }
        return _buildResultContent(context, state.result!);
    }
  }

  Widget _buildResultContent(BuildContext context, BuildingSearchResponse result) {
    final building = result.building;
    final isMultiUnit = building?.type == 'multi_unit';
    final isLandWithHousePrice = building?.type == 'land_with_house_price';

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 1. 기본 정보
          _buildBasicInfoCard(context, result),

          const SizedBox(height: 16),

          // 2. 토지 정보
          if (result.land != null) _buildLandCard(context, result.land!),

          const SizedBox(height: 16),

          // 3. 건물 정보
          if (building != null && building.hasData && !isLandWithHousePrice)
            _buildBuildingInfoCard(context, building, result.land),

          // 3-1. 층별개요 (일반건축물일 경우)
          if (building != null && building.hasData && building.type == 'general' && building.floorInfo != null && building.floorInfo!.isNotEmpty) ...[
            const SizedBox(height: 16),
            _buildFloorInfoCard(context, building.floorInfo!),
          ],

          // 건물 정보 없음 (주택공시가격이 있는 경우 포함)
          if (building == null || !building.hasData || isLandWithHousePrice)
            _buildNoBuildingCard(context, housePrice: building?.buildingInfo?.housePrice, housePriceYear: building?.buildingInfo?.housePriceYear),

          // 4. 공동주택 동/호 선택
          if (isMultiUnit && building?.dongHoDict != null && building!.dongHoDict!.isNotEmpty) ...[
            const SizedBox(height: 16),
            _buildDongHoSelector(context, building.dongHoDict!),
          ],

          // 5. 지도
          const SizedBox(height: 16),
          _buildMapSection(context, result),

          // 6. 안내문구
          const SizedBox(height: 24),
          _buildDisclaimerSection(context),
        ],
        ),
      ),
    );
  }

  /// 6. 안내문구 섹션
  Widget _buildDisclaimerSection(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? Colors.grey[850] : Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: isDark ? Colors.grey[700]! : Colors.grey[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            '본 자료는 공공데이터포털 및\nVWorld를 기반으로 생성되었습니다.',
            style: TextStyle(fontSize: 11, color: Colors.grey[600]),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            '오류가 있을 수 있으니\n정확한 정보는 공적장부를 참고하세요.',
            style: TextStyle(fontSize: 11, color: Colors.grey[600]),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          // 로고 영역
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Image.asset(
                'assets/images/proppedia_icon.png',
                height: 14,
                errorBuilder: (context, error, stackTrace) =>
                    Icon(Icons.home, size: 14, color: Colors.grey[400]),
              ),
              const SizedBox(width: 4),
              Text(
                'Proppedia 제공',
                style: TextStyle(fontSize: 10, color: Colors.grey[700], fontWeight: FontWeight.w500),
              ),
              const SizedBox(width: 6),
              Text(
                '|',
                style: TextStyle(fontSize: 10, color: Colors.grey[400]),
              ),
              const SizedBox(width: 6),
              Image.asset(
                'assets/images/propnet_icon.png',
                height: 14,
                errorBuilder: (context, error, stackTrace) =>
                    Icon(Icons.language, size: 14, color: Colors.grey[400]),
              ),
              const SizedBox(width: 4),
              Text(
                '프롭넷 제작',
                style: TextStyle(fontSize: 10, color: Colors.grey[700], fontWeight: FontWeight.w500),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// 1. 기본 정보 카드
  Widget _buildBasicInfoCard(BuildContext context, BuildingSearchResponse result) {
    final buildingInfo = result.building?.buildingInfo;
    final recapTitleInfo = result.building?.recapTitleInfo;
    final address = result.address;
    final codes = result.codes;
    final isForest = _isForestLand(codes?.pnu);

    // 신규 행정구역 주소 보정용 시군구명 정규화
    final normalizedSigungu = _normalizeDistrictName(address?.sigunguName);
    final hasNewDistrict = normalizedSigungu.contains('구') &&
        normalizedSigungu.split(' ').length >= 2;

    // 지번 주소 (recapTitleInfo 우선 -> buildingInfo -> fallback 생성)
    String? platPlc = recapTitleInfo?['plat_plc'] as String?;
    if (platPlc == null || platPlc == '-' || platPlc.trim().isEmpty) {
      platPlc = buildingInfo?.platPlc;
    }

    // 지번 주소에 시도 추가 확인
    bool needsSidoPrefix = false;
    if (platPlc != null && platPlc.isNotEmpty && platPlc != '-') {
      // 시도로 시작하지 않으면 추가 필요
      if (address?.sidoName != null && !platPlc.startsWith(address!.sidoName!)) {
        needsSidoPrefix = true;
      }
    }

    if (platPlc == null || platPlc == '-' || platPlc.trim().isEmpty) {
      // Fallback 지번 생성 (정규화된 시군구명 사용)
      final parts = <String>[];
      if (address?.sidoName != null) parts.add(address!.sidoName!);
      if (normalizedSigungu.isNotEmpty) {
        parts.add(normalizedSigungu);
      }
      if (address?.eupmyeondongName != null) parts.add(address!.eupmyeondongName!);
      if (codes?.pnu != null && codes!.pnu!.length >= 19) {
        final bun = int.tryParse(codes.pnu!.substring(11, 15))?.toString() ?? '';
        final ji = int.tryParse(codes.pnu!.substring(15, 19))?.toString() ?? '';
        if (bun.isNotEmpty) {
          // 임야인 경우 '산' 추가
          final sanPrefix = isForest ? '산 ' : '';
          final jibun = (ji.isNotEmpty && ji != '0') ? '$sanPrefix$bun-$ji' : '$sanPrefix$bun';
          parts.add(jibun);
        }
      }
      if (parts.isNotEmpty) {
        platPlc = parts.join(' ');
      }
    } else if (needsSidoPrefix && address?.sidoName != null) {
      platPlc = '${address!.sidoName!} $platPlc';
    }

    // 신규 행정구역인 경우 구 이름 삽입
    if (platPlc != null && hasNewDistrict) {
      platPlc = _injectDistrictName(platPlc, normalizedSigungu);
    }

    // 번지 제거
    platPlc = platPlc?.replaceAll(RegExp(r'번지$'), '').trim();

    // 도로명 주소 (시도 포함 확인)
    String? newPlatPlc = recapTitleInfo?['new_plat_plc'] as String?;
    if (newPlatPlc == null || newPlatPlc == '-' || newPlatPlc.trim().isEmpty) {
      newPlatPlc = buildingInfo?.newPlatPlc;
    }
    if (newPlatPlc != null && newPlatPlc.isNotEmpty && newPlatPlc != '-') {
      if (address?.sidoName != null && !newPlatPlc.startsWith(address!.sidoName!)) {
        newPlatPlc = '${address.sidoName!} $newPlatPlc';
      }
      // 신규 행정구역인 경우 구 이름 삽입
      if (hasNewDistrict) {
        newPlatPlc = _injectDistrictName(newPlatPlc, normalizedSigungu);
      }
    }

    // 건물명
    String? buildingName = recapTitleInfo?['building_name'] as String?;
    if (buildingName == null || buildingName == '-' || buildingName.trim().isEmpty) {
      buildingName = buildingInfo?.buildingName;
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionHeader(context, Icons.info_outline, '기본 정보', Colors.blue),
            const Divider(height: 24),

            if (platPlc != null && platPlc.isNotEmpty)
              _buildInfoRow('지번', platPlc),

            if (newPlatPlc != null && newPlatPlc.isNotEmpty && newPlatPlc != '-')
              _buildInfoRow('도로명주소', newPlatPlc),

            if (buildingName != null && buildingName.isNotEmpty && buildingName != '-')
              _buildInfoRow('건물명', buildingName),
          ],
        ),
      ),
    );
  }

  /// 2. 토지 정보 카드
  Widget _buildLandCard(BuildContext context, LandInfo land) {
    // 공시지가(기준년도) 포맷
    String? publicLandPriceText;
    if (land.publicLandPrice != null) {
      publicLandPriceText = '${_formatPrice(land.publicLandPrice!)}원/㎡';
      if (land.priceYear != null) {
        publicLandPriceText += ' (${land.priceYear}년)';
      }
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionHeader(context, Icons.landscape, '토지 정보', Colors.green),
            const Divider(height: 24),

            // 지목
            if (land.landCategoryName != null && land.landCategoryName != '-')
              _buildInfoRow('지목', land.landCategoryName!),

            // 토지면적
            if (land.landArea != null) ...[
              _buildInfoRow(
                '토지면적',
                '${_formatNumber(land.landArea!)} ㎡ (${_sqmToPyeong(land.landArea!)} 평)'
                    '${land.parcelCount != null && land.parcelCount! > 1 ? ' [${land.parcelCount}필지 합계]' : ''}',
              ),
            ],

            // 용도지역
            if (land.zoneClassification != null && land.zoneClassification != '-')
              _buildInfoRow('용도지역', land.zoneClassification!),

            // 이용현황
            if (land.landUseSituationName != null && land.landUseSituationName != '-')
              _buildInfoRow('이용현황', land.landUseSituationName!),

            // 지형
            if (land.topographyHeightName != null && land.topographyHeightName != '-')
              _buildInfoRow('지형', '${land.topographyHeightName!}${land.topographyFormName != null && land.topographyFormName != '-' ? ' / ${land.topographyFormName}' : ''}'),

            // 도로접면
            if (land.roadSideName != null && land.roadSideName != '-')
              _buildInfoRow('도로접면', land.roadSideName!),

            // 공시지가(기준년도)
            if (publicLandPriceText != null)
              _buildInfoRow('공시지가', publicLandPriceText),
          ],
        ),
      ),
    );
  }

  /// 3. 건물 정보 카드
  Widget _buildBuildingInfoCard(BuildContext context, BuildingInfo building, LandInfo? land) {
    final info = building.buildingInfo;
    final recapTitleInfo = building.recapTitleInfo;
    final isMultiUnit = building.type == 'multi_unit';

    // 우선순위: recapTitleInfo > buildingInfo
    double? landArea = (recapTitleInfo?['land_area'] as num?)?.toDouble() ?? info?.landArea;
    double? buildingArea = (recapTitleInfo?['building_area'] as num?)?.toDouble() ?? info?.buildingArea;
    double? totalArea = (recapTitleInfo?['total_area'] as num?)?.toDouble() ?? info?.totalArea;
    double? vlRatEstmTotArea = (recapTitleInfo?['vl_rat_estm_tot_area'] as num?)?.toDouble() ?? info?.vlRatEstmTotArea;
    double? buildingCoverage = (recapTitleInfo?['building_coverage'] as num?)?.toDouble() ?? info?.buildingCoverage;
    double? floorAreaRatio = (recapTitleInfo?['floor_area_ratio'] as num?)?.toDouble() ?? info?.floorAreaRatio;
    double? height = (recapTitleInfo?['height'] as num?)?.toDouble() ?? info?.height;
    String? mainPurpose = recapTitleInfo?['main_purpose'] as String? ?? info?.mainPurpose;
    String? useApprovalDate = recapTitleInfo?['use_approval_date'] as String? ?? info?.useApprovalDate;
    String? totalParking = recapTitleInfo?['total_parking']?.toString() ?? info?.totalParking;
    int? elevatorCount = (recapTitleInfo?['elevator_count'] as num?)?.toInt() ?? info?.elevatorCount;

    // 총건물수 (공동주택)
    int mainBldCnt = (recapTitleInfo?['main_bld_cnt'] as int?) ?? 1;

    // 세대/가구/호
    int totalHhld = (recapTitleInfo?['total_hhld_cnt'] as int?) ?? (recapTitleInfo?['hhld_cnt'] as int?) ?? info?.hhldCnt ?? 0;
    int totalFmly = (recapTitleInfo?['total_fmly_cnt'] as int?) ?? (recapTitleInfo?['family_cnt'] as int?) ?? info?.familyCnt ?? 0;
    int totalHo = (recapTitleInfo?['total_ho_cnt'] as int?) ?? (recapTitleInfo?['ho_cnt'] as int?) ?? info?.hoCnt ?? 0;

    // 층수
    int? totalFloors = (recapTitleInfo?['total_floors'] as num?)?.toInt() ?? info?.totalFloors;
    int? basementFloors = (recapTitleInfo?['basement_floors'] as num?)?.toInt() ?? info?.basementFloors;
    String? mainStructure = info?.mainStructure;

    // 필지 수
    int? parcelCount = land?.parcelCount;

    // 대지면적 텍스트 (필지 수 포함)
    String? landAreaText;
    if (landArea != null) {
      landAreaText = '${_formatNumber(landArea)} ㎡ (${_sqmToPyeong(landArea)} 평)';
      if (parcelCount != null && parcelCount > 1) {
        landAreaText += ' [$parcelCount필지]';
      }
    }

    // 주택공시가격 포맷
    String housePriceText;
    if (info?.housePrice != null && info!.housePrice! > 0) {
      housePriceText = '${_formatPrice(info.housePrice!)}원';
      if (info.housePriceYear != null) {
        housePriceText += ' (${info.housePriceYear}년)';
      }
    } else {
      housePriceText = '해당사항 없음';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionHeader(
              context,
              Icons.apartment,
              '건물 정보',
              Colors.orange,
              subtitle: isMultiUnit ? '집합건축물 (공동주택)' : '일반건축물',
            ),
            const Divider(height: 24),

            if (landAreaText != null)
              _buildInfoRow('대지면적', landAreaText),
            if (buildingArea != null)
              _buildInfoRow('건축면적', '${_formatNumber(buildingArea)} ㎡ (${_sqmToPyeong(buildingArea)} 평)'),
            if (totalArea != null)
              _buildInfoRow('연면적', '${_formatNumber(totalArea)} ㎡ (${_sqmToPyeong(totalArea)} 평)'),
            if (vlRatEstmTotArea != null)
              _buildInfoRow('용적률산정용연면적', '${_formatNumber(vlRatEstmTotArea)} ㎡ (${_sqmToPyeong(vlRatEstmTotArea)} 평)'),

            if (buildingCoverage != null)
              _buildInfoRow('건폐율', '${buildingCoverage.toStringAsFixed(2)}%'),
            if (floorAreaRatio != null)
              _buildInfoRow('용적률', '${floorAreaRatio.toStringAsFixed(2)}%'),

            // 공동주택: 총건물수
            if (isMultiUnit)
              _buildInfoRow('총건물수', '$mainBldCnt개'),

            // 층수 (공동주택 여러동인 경우 숨김 - 해당동 정보에서 표시)
            if (!(isMultiUnit && mainBldCnt > 1) && (totalFloors != null || basementFloors != null))
              _buildInfoRow('층수', '지상 ${totalFloors ?? 0}층 / 지하 ${basementFloors ?? 0}층'),

            // 높이 (공동주택 여러동인 경우 숨김 - 해당동 정보에서 표시)
            if (!(isMultiUnit && mainBldCnt > 1) && height != null && height > 0)
              _buildInfoRow('높이', '${height}m'),

            // 세대/가구/호
            _buildInfoRow('세대/가구/호', _formatTotalUnits(totalHhld, totalFmly, totalHo)),

            if (!isMultiUnit && mainStructure != null && mainStructure != '-')
              _buildInfoRow('주구조', mainStructure),

            if (totalParking != null && totalParking != '-' && totalParking.isNotEmpty)
              _buildInfoRow('총주차대수', '$totalParking대'),

            // 승강기수 (공동주택 여러동인 경우 숨김 - 해당동 정보에서 표시)
            if (!(isMultiUnit && mainBldCnt > 1) && elevatorCount != null && elevatorCount > 0)
              _buildInfoRow('승강기수', '$elevatorCount기'),

            if (mainPurpose != null && mainPurpose != '-')
              _buildInfoRow('주용도', mainPurpose),

            if (useApprovalDate != null && useApprovalDate != '-' && useApprovalDate.isNotEmpty)
              _buildInfoRow('사용승인일', useApprovalDate),

            // 단독주택 주택공시가격
            if (!isMultiUnit)
              _buildInfoRow('주택공시가격', housePriceText),
          ],
        ),
      ),
    );
  }

  /// 건물 없음 카드
  Widget _buildNoBuildingCard(BuildContext context, {int? housePrice, String? housePriceYear}) {
    // 주택공시가격 포맷
    String housePriceText;
    if (housePrice != null && housePrice > 0) {
      housePriceText = '${_formatPrice(housePrice)}원';
      if (housePriceYear != null) {
        housePriceText += ' ($housePriceYear년)';
      }
    } else {
      housePriceText = '해당사항 없음';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.home_work_outlined, size: 48, color: Colors.grey[400]),
                const SizedBox(width: 12),
                Text(
                  '건물 정보 없음 (토지만 있음)',
                  style: TextStyle(color: Colors.red[600], fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 12),
            _buildInfoRow('주택공시가격', housePriceText),
          ],
        ),
      ),
    );
  }

  /// 층별개요 카드
  Widget _buildFloorInfoCard(BuildContext context, List<FloorInfo> floorInfoList) {
    // 정렬: 지하(높은순) → 지상(낮은순) → 옥탑(낮은순)
    // 예: 지하2층 → 지하1층 → 1층 → 2층 → ... → 8층 → 옥탑1층 → 옥탑2층
    final undergroundFloors = floorInfoList.where((f) => f.floorGb == '지하').toList();
    final aboveGroundFloors = floorInfoList.where((f) => f.floorGb == '지상').toList();
    final rooftopFloors = floorInfoList.where((f) => f.floorGb == '옥탑').toList();

    undergroundFloors.sort((a, b) => (b.floorNo ?? 0).compareTo(a.floorNo ?? 0)); // 내림차순 (2→1)
    aboveGroundFloors.sort((a, b) => (a.floorNo ?? 0).compareTo(b.floorNo ?? 0)); // 오름차순 (1→2→3)
    rooftopFloors.sort((a, b) => (a.floorNo ?? 0).compareTo(b.floorNo ?? 0)); // 오름차순 (1→2)

    final sortedFloors = [...undergroundFloors, ...aboveGroundFloors, ...rooftopFloors];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionHeader(context, Icons.layers, '층별개요', Colors.teal),
            const Divider(height: 24),

            // 테이블 헤더
            Container(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                children: [
                  _buildFloorTableCell(context, '층', flex: 2, isHeader: true),
                  _buildFloorTableCell(context, '구조', flex: 2, isHeader: true),
                  _buildFloorTableCell(context, '용도', flex: 3, isHeader: true),
                  _buildFloorTableCell(context, '면적', flex: 2, isHeader: true),
                ],
              ),
            ),

            // 테이블 내용
            ...sortedFloors.map((floor) {
              final floorName = floor.floorName ?? '${floor.floorGb ?? ''} ${floor.floorNo ?? ''}층';
              final structure = floor.structure ?? '-';
              final purpose = floor.purpose ?? floor.etcPurpose ?? '-';
              final areaText = floor.area != null ? '${_formatNumber(floor.area!)}㎡' : '-';

              return Container(
                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                decoration: BoxDecoration(
                  border: Border(bottom: BorderSide(color: Theme.of(context).dividerColor)),
                ),
                child: Row(
                  children: [
                    _buildFloorTableCell(context, floorName, flex: 2),
                    _buildFloorTableCell(context, structure, flex: 2),
                    _buildFloorTableCell(context, purpose, flex: 3),
                    _buildFloorTableCell(context, areaText, flex: 2),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  /// 층별개요 테이블 셀
  Widget _buildFloorTableCell(BuildContext context, String text, {int flex = 1, bool isHeader = false}) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Expanded(
      flex: flex,
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12,
          fontWeight: isHeader ? FontWeight.bold : FontWeight.normal,
          color: isHeader
              ? (isDark ? Colors.grey[300] : Colors.grey[700])
              : Theme.of(context).textTheme.bodyMedium?.color,
        ),
        textAlign: TextAlign.center,
        overflow: TextOverflow.ellipsis,
      ),
    );
  }

  /// 동/호 선택 위젯
  Widget _buildDongHoSelector(BuildContext context, Map<String, dynamic> dongHoDict) {
    final dongList = dongHoDict.keys.toList()..sort();
    final areaInfoState = ref.watch(areaInfoProvider);

    return Card(
      color: AppColors.primary.withValues(alpha: 0.05),
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionHeader(context, Icons.home, '동/호 선택', AppColors.primary),
            const SizedBox(height: 16),

            // 동 선택 드롭다운
            DropdownButtonFormField<String>(
              value: _selectedDong,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: '동 선택',
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                filled: true,
                fillColor: Theme.of(context).cardColor,
              ),
              dropdownColor: Theme.of(context).cardColor,
              items: dongList.map((dong) {
                final hoData = dongHoDict[dong];
                final hoCount = hoData is List ? hoData.length : 0;
                return DropdownMenuItem(value: dong, child: Text('$dong ($hoCount세대)'));
              }).toList(),
              onChanged: (value) => _onDongSelected(value, dongHoDict),
            ),

            const SizedBox(height: 12),

            // 호 선택 드롭다운
            DropdownButtonFormField<String>(
              value: _selectedHo,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: '호 선택',
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                filled: true,
                fillColor: Theme.of(context).cardColor,
              ),
              dropdownColor: Theme.of(context).cardColor,
              items: _hoList.map((ho) {
                final displayText = ho.endsWith('호') ? ho : '$ho호';
                return DropdownMenuItem(value: ho, child: Text(displayText));
              }).toList(),
              onChanged: _selectedDong != null ? _onHoSelected : null,
            ),

            const SizedBox(height: 12),

            // 조회 버튼
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: (_selectedDong != null && _selectedHo != null) ? _fetchAreaInfo : null,
                icon: areaInfoState.status == SearchStatus.loading
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.search, size: 18),
                label: Text(areaInfoState.status == SearchStatus.loading ? '조회 중...' : '상세 정보 조회'),
                style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 12)),
              ),
            ),

            // 4. 해당동 정보 + 5. 전유부 정보
            if (areaInfoState.status == SearchStatus.success && areaInfoState.areaInfo != null) ...[
              const SizedBox(height: 16),
              _buildDongTitleInfoSection(context, areaInfoState.areaInfo!),
              const SizedBox(height: 16),
              _buildExclusiveInfoSection(context, areaInfoState.areaInfo!),
            ],

            if (areaInfoState.status == SearchStatus.error) ...[
              const SizedBox(height: 12),
              Text(
                areaInfoState.errorMessage ?? '조회 중 오류가 발생했습니다',
                style: TextStyle(color: Colors.red[600], fontSize: 13),
              ),
            ],
          ],
        ),
      ),
    );
  }

  /// 4. 해당동 정보 섹션
  Widget _buildDongTitleInfoSection(BuildContext context, AreaInfo areaInfo) {
    final dongInfo = areaInfo.dongTitleInfo;
    if (dongInfo == null) return const SizedBox.shrink();

    final dongNm = dongInfo['dong_nm'] as String? ?? areaInfo.dongNm;
    final buildingArea = (dongInfo['building_area'] as num?)?.toDouble();
    final totalArea = (dongInfo['total_area'] as num?)?.toDouble();
    final hoCnt = dongInfo['ho_cnt'];
    final familyCnt = dongInfo['family_cnt'];
    final hhldCnt = dongInfo['hhld_cnt'];
    final height = (dongInfo['height'] as num?)?.toDouble();
    final totalFloors = dongInfo['total_floors'];
    final basementFloors = dongInfo['basement_floors'] ?? 0;
    final elevatorCount = dongInfo['elevator_count'];
    final emergencyElevatorCount = dongInfo['emergency_elevator_count'];

    // 해당동 세대/가구/호 포맷
    final dongHhldDisplay = (hhldCnt == null || hhldCnt == '-' || hhldCnt == 0) ? '-' : hhldCnt.toString();
    final dongFmlyDisplay = (familyCnt == null || familyCnt == '-' || familyCnt == 0) ? '-' : familyCnt.toString();
    final dongHoDisplay = (hoCnt == null || hoCnt == '-' || hoCnt == 0) ? '-' : hoCnt.toString();

    // 승강기 텍스트
    String elvText = '';
    if (elevatorCount != null && elevatorCount != '-' && int.tryParse(elevatorCount.toString()) != 0) {
      elvText = '일반 $elevatorCount대';
    }
    if (emergencyElevatorCount != null && emergencyElevatorCount != '-' && int.tryParse(emergencyElevatorCount.toString()) != 0) {
      elvText += (elvText.isNotEmpty ? ' / ' : '') + '비상 $emergencyElevatorCount대';
    }

    return SizedBox(
      width: double.infinity,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.blue.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.blue.withValues(alpha: 0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '해당동 정보',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Colors.blue[700],
                ),
          ),
          const SizedBox(height: 12),

          if (dongNm != null)
            _buildInfoRowHighlight('동', dongNm),

          if (buildingArea != null)
            _buildInfoRow('건축면적', '${_formatNumber(buildingArea)} ㎡ (${_sqmToPyeong(buildingArea)} 평)'),

          if (totalArea != null)
            _buildInfoRow('해당동연면적', '${_formatNumber(totalArea)} ㎡ (${_sqmToPyeong(totalArea)} 평)'),

          // 해당동 세대/가구/호
          _buildInfoRow('해당동 세대/가구/호', '$dongHhldDisplay/$dongFmlyDisplay/$dongHoDisplay'),

          if (height != null && height > 0)
            _buildInfoRow('높이', '${height}m'),

          if (totalFloors != null && totalFloors != '-')
            _buildInfoRow('해당동 층수', '지상 $totalFloors층 / 지하 $basementFloors층'),

          if (elvText.isNotEmpty)
            _buildInfoRow('해당동 승강기수', elvText),
        ],
        ),
      ),
    );
  }

  /// 5. 전유부 정보 섹션
  Widget _buildExclusiveInfoSection(BuildContext context, AreaInfo areaInfo) {
    // 주택공시가격 포맷
    String? housePriceText;
    if (areaInfo.housePrice != null && areaInfo.housePrice! > 0) {
      housePriceText = '${_formatPrice(areaInfo.housePrice!)}원';
      if (areaInfo.housePriceYear != null) {
        housePriceText += ' (${areaInfo.housePriceYear}년)';
      }
    }

    return SizedBox(
      width: double.infinity,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.purple.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.purple.withValues(alpha: 0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '전유부 정보',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Colors.purple[700],
                ),
          ),
          const SizedBox(height: 12),

          _buildInfoRowHighlight('호', areaInfo.hoNm ?? _selectedHo ?? '-'),

          if (areaInfo.exclusiveArea != null)
            _buildInfoRow('전용면적', '${_formatNumber(areaInfo.exclusiveArea!)} ㎡ (${_sqmToPyeong(areaInfo.exclusiveArea!)} 평)'),

          if (areaInfo.supplyArea != null)
            _buildInfoRow('공급면적', '${_formatNumber(areaInfo.supplyArea!)} ㎡ (${_sqmToPyeong(areaInfo.supplyArea!)} 평)'),

          if (areaInfo.landShare != null)
            _buildInfoRow('대지지분', '${_formatNumber(areaInfo.landShare!)} ㎡ (${_sqmToPyeong(areaInfo.landShare!)} 평)'),

          // 주택공시가격
          if (housePriceText != null)
            _buildInfoRow('주택공시가격', housePriceText),
        ],
        ),
      ),
    );
  }

  /// 섹션 헤더
  Widget _buildSectionHeader(BuildContext context, IconData icon, String title, Color color, {String? subtitle}) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: color),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
              if (subtitle != null)
                Text(subtitle, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
            ],
          ),
        ),
      ],
    );
  }

  /// 5. 지도 섹션
  Widget _buildMapSection(BuildContext context, BuildingSearchResponse result) {
    // Web은 미지원
    if (kIsWeb) {
      return const SizedBox.shrink();
    }

    // 주소 생성
    final buildingInfo = result.building?.buildingInfo;
    final recapTitleInfo = result.building?.recapTitleInfo;
    final address = result.address;
    final codes = result.codes;

    String? platPlc = recapTitleInfo?['plat_plc'] as String?;
    if (platPlc == null || platPlc == '-' || platPlc.trim().isEmpty) {
      platPlc = buildingInfo?.platPlc;
    }

    // 지번 주소가 없으면 fullAddress + PNU에서 추출한 번지 사용
    if (platPlc == null || platPlc == '-' || platPlc.trim().isEmpty) {
      platPlc = address?.fullAddress;

      // PNU에서 번지 추출하여 추가 (건물 없는 토지의 경우 필요)
      if (platPlc != null && codes?.pnu != null && codes!.pnu!.length >= 19) {
        final pnu = codes.pnu!;
        // PNU 구조: bjdong(10) + land_type(1) + bun(4) + ji(4)
        final landType = pnu.substring(10, 11);
        final bunStr = pnu.substring(11, 15);
        final jiStr = pnu.substring(15, 19);

        final bun = int.tryParse(bunStr) ?? 0;
        final ji = int.tryParse(jiStr) ?? 0;

        if (bun > 0) {
          final lotNumber = ji > 0 ? '$bun-$ji' : '$bun';
          final prefix = landType == '2' ? '산 ' : '';
          platPlc = '$platPlc $prefix$lotNumber';
        }
      }
    }

    // 주소가 없으면 지도 표시 안 함
    if (platPlc == null || platPlc.trim().isEmpty) {
      return const SizedBox.shrink();
    }

    // 시도명 추가
    if (address?.sidoName != null && !platPlc.startsWith(address!.sidoName!)) {
      platPlc = '${address.sidoName!} $platPlc';
    }

    // 번지 제거 (뒤에 "번지" 글자만 제거)
    platPlc = platPlc.replaceAll(RegExp(r'번지$'), '').trim();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionHeader(context, Icons.map, '위치', Colors.teal),
            const Divider(height: 24),
            SizedBox(
              height: 250,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: _ResultMapWidget(
                  address: platPlc,
                  pnu: codes?.pnu,
                  markerLabel: _buildMarkerLabel(result),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 정보 행 (세로 배치: 항목이 위, 값이 아래)
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(color: Colors.grey[600], fontSize: 12),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
          ),
        ],
      ),
    );
  }

  /// 정보 행 (강조, 세로 배치)
  Widget _buildInfoRowHighlight(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(color: Colors.grey[600], fontSize: 12),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.blue),
          ),
        ],
      ),
    );
  }

  String _formatNumber(double value) {
    if (value == value.toInt()) {
      return value.toInt().toString().replaceAllMapped(
            RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
            (Match m) => '${m[1]},',
          );
    }
    return value.toStringAsFixed(2).replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (Match m) => '${m[1]},',
        );
  }

  String _formatPrice(int value) {
    return value.toString().replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (Match m) => '${m[1]},',
        );
  }

  String _sqmToPyeong(double sqm) {
    final pyeong = sqm / 3.305785;
    return pyeong.toStringAsFixed(2);
  }

  String _formatTotalUnits(int hhld, int fmly, int ho) {
    // 0도 그대로 표시 (웹앱과 동일)
    return '$hhld/$fmly/$ho';
  }
}

/// 결과 화면용 지도 위젯
class _ResultMapWidget extends ConsumerStatefulWidget {
  final String address;
  final String? pnu;
  final String? markerLabel;

  const _ResultMapWidget({
    required this.address,
    this.pnu,
    this.markerLabel,
  });

  @override
  ConsumerState<_ResultMapWidget> createState() => _ResultMapWidgetState();
}

class _ResultMapWidgetState extends ConsumerState<_ResultMapWidget> {
  KakaoMapController? _mapController;
  bool _isMapReady = false;
  Set<Marker> _markers = {};

  @override
  Widget build(BuildContext context) {
    final geocoding = ref.watch(geocodingProvider(widget.address));

    return geocoding.when(
      loading: () => Container(
        color: Colors.grey[100],
        child: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 8),
              Text('지도 로딩 중...'),
            ],
          ),
        ),
      ),
      error: (error, stack) => Container(
        color: Colors.grey[100],
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.map_outlined, size: 48, color: Colors.grey[400]),
              const SizedBox(height: 8),
              Text(
                '위치 정보를 불러올 수 없습니다',
                style: TextStyle(color: Colors.grey[600]),
              ),
            ],
          ),
        ),
      ),
      data: (response) {
        if (!response.success || response.lat == null || response.lng == null) {
          return Container(
            color: Colors.grey[100],
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.map_outlined, size: 48, color: Colors.grey[400]),
                  const SizedBox(height: 8),
                  Text(
                    '위치 정보를 불러올 수 없습니다',
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                ],
              ),
            ),
          );
        }

        final lat = response.lat!;
        final lng = response.lng!;

        return Stack(
          children: [
            KakaoMap(
              onMapCreated: (controller) {
                _mapController = controller;
                setState(() {
                  _isMapReady = true;
                  _markers = {
                    Marker(
                      markerId: 'location',
                      latLng: LatLng(lat, lng),
                      infoWindowContent: widget.markerLabel ?? '',
                    ),
                  };
                });
              },
              center: LatLng(lat, lng),
              markers: _markers.toList(),
            ),
            if (!_isMapReady)
              Container(
                color: Colors.grey[100],
                child: const Center(
                  child: CircularProgressIndicator(),
                ),
              ),
          ],
        );
      },
    );
  }
}
