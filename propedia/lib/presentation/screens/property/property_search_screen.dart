import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:propedia/data/dto/property_dto.dart';
import 'package:propedia/presentation/providers/building_provider.dart';
import 'package:propedia/presentation/providers/property_provider.dart';

/// 매물 검색 화면
class PropertySearchScreen extends ConsumerStatefulWidget {
  const PropertySearchScreen({super.key});

  @override
  ConsumerState<PropertySearchScreen> createState() =>
      _PropertySearchScreenState();
}

class _PropertySearchScreenState extends ConsumerState<PropertySearchScreen> {
  final _formKey = GlobalKey<FormState>();

  // 가격 조건
  String _priceCondition = 'all';
  final _priceController = TextEditingController();

  // 수익률 조건
  String _yieldCondition = 'all';
  final _yieldController = TextEditingController();

  // 투자금 조건
  String _investmentCondition = 'all';
  final _investmentController = TextEditingController();

  // 토지면적 조건
  String _areaCondition = 'all';
  final _areaController = TextEditingController();

  @override
  void dispose() {
    _priceController.dispose();
    _yieldController.dispose();
    _investmentController.dispose();
    _areaController.dispose();
    super.dispose();
  }

  void _search() {
    if (_formKey.currentState?.validate() ?? false) {
      ref.read(propertySearchProvider.notifier).search(
            priceValue: _priceController.text.isNotEmpty
                ? _priceController.text
                : null,
            priceCondition: _priceCondition,
            yieldValue: _yieldController.text.isNotEmpty
                ? _yieldController.text
                : null,
            yieldCondition: _yieldCondition,
            investmentValue: _investmentController.text.isNotEmpty
                ? _investmentController.text
                : null,
            investmentCondition: _investmentCondition,
            areaValue: _areaController.text.isNotEmpty
                ? _areaController.text
                : null,
            areaCondition: _areaCondition,
          );
    }
  }

  void _reset() {
    _priceController.clear();
    _yieldController.clear();
    _investmentController.clear();
    _areaController.clear();
    setState(() {
      _priceCondition = 'all';
      _yieldCondition = 'all';
      _investmentCondition = 'all';
      _areaCondition = 'all';
    });
    ref.read(propertySearchProvider.notifier).reset();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(propertySearchProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('매물 검색'),
        actions: [
          TextButton(
            onPressed: _reset,
            child: const Text('초기화'),
          ),
        ],
      ),
      body: Column(
          children: [
            // 검색 폼
            _buildSearchForm(isDark),

            // 검색 버튼
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: _search,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  child: const Text(
                    '검색하기',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),

            // 구분선
            const Divider(height: 1),

            // 검색 결과
            Expanded(
              child: _buildSearchResult(state),
            ),
          ],
        ),
    );
  }

  Widget _buildSearchForm(bool isDark) {
    return Form(
      key: _formKey,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 가격 조건
            _buildConditionRow(
              label: '매가',
              unit: '만원',
              hintText: '100000',
              controller: _priceController,
              condition: _priceCondition,
              onConditionChanged: (v) => setState(() => _priceCondition = v),
              isDark: isDark,
            ),

            const SizedBox(height: 12),

            // 수익률 조건
            _buildConditionRow(
              label: '수익률',
              unit: '%',
              hintText: '5',
              controller: _yieldController,
              condition: _yieldCondition,
              onConditionChanged: (v) => setState(() => _yieldCondition = v),
              isDark: isDark,
            ),

            const SizedBox(height: 12),

            // 투자금 조건
            _buildConditionRow(
              label: '투자금',
              unit: '만원',
              hintText: '50000',
              controller: _investmentController,
              condition: _investmentCondition,
              onConditionChanged: (v) =>
                  setState(() => _investmentCondition = v),
              isDark: isDark,
            ),

            const SizedBox(height: 12),

            // 토지면적 조건
            _buildConditionRow(
              label: '토지면적',
              unit: '평',
              hintText: '50',
              controller: _areaController,
              condition: _areaCondition,
              onConditionChanged: (v) => setState(() => _areaCondition = v),
              isDark: isDark,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildConditionRow({
    required String label,
    required String unit,
    required String hintText,
    required TextEditingController controller,
    required String condition,
    required ValueChanged<String> onConditionChanged,
    required bool isDark,
  }) {
    return Row(
      children: [
        // 라벨 (토지면적 4글자 수용)
        SizedBox(
          width: 70,
          child: Text(
            label,
            style: TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 14,
              color: isDark ? Colors.white : Colors.black87,
            ),
          ),
        ),

        const SizedBox(width: 8),

        // 값 입력 (flex 5)
        Flexible(
          flex: 5,
          child: TextFormField(
            controller: controller,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            maxLength: 7,
            onChanged: (value) {
              // 숫자 입력 시 자동으로 '이하'로 변경
              if (value.isNotEmpty && condition == 'all') {
                onConditionChanged('lte');
              }
            },
            decoration: InputDecoration(
              hintText: hintText,
              suffixText: unit,
              counterText: '',
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 10,
                vertical: 10,
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ),

        const SizedBox(width: 8),

        // 조건 선택 (flex 4)
        Flexible(
          flex: 4,
          child: Container(
            height: 48,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              border: Border.all(
                color: isDark ? Colors.grey[600]! : Colors.grey[300]!,
              ),
              borderRadius: BorderRadius.circular(8),
            ),
            child: DropdownButton<String>(
              value: condition,
              isExpanded: true,
              underline: const SizedBox(),
              items: const [
                DropdownMenuItem(value: 'all', child: Text('전체')),
                DropdownMenuItem(value: 'gte', child: Text('이상')),
                DropdownMenuItem(value: 'lte', child: Text('이하')),
              ],
              onChanged: (v) {
                if (v != null) onConditionChanged(v);
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSearchResult(PropertySearchState state) {
    switch (state.status) {
      case SearchStatus.initial:
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.search,
                size: 64,
                color: Colors.grey[400],
              ),
              const SizedBox(height: 16),
              Text(
                '조건을 설정하고 검색해주세요',
                style: TextStyle(
                  color: Colors.grey[600],
                ),
              ),
            ],
          ),
        );

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
                state.errorMessage ?? '검색 중 오류가 발생했습니다',
                style: TextStyle(
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _search,
                child: const Text('다시 시도'),
              ),
            ],
          ),
        );

      case SearchStatus.success:
        // markers를 사용하여 결과 표시 (서버가 properties 대신 markers를 반환)
        if (state.markers.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.home_outlined,
                  size: 64,
                  color: Colors.grey[400],
                ),
                const SizedBox(height: 16),
                Text(
                  '조건에 맞는 매물이 없습니다',
                  style: TextStyle(
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          );
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 결과 카운트 + 지도보기 버튼
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '검색결과: ${state.count}건',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  ElevatedButton.icon(
                    onPressed: () {
                      context.push('/property/search-map', extra: state.markers);
                    },
                    icon: const Icon(Icons.map, size: 18),
                    label: const Text('지도보기'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFE38000),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      visualDensity: VisualDensity.compact,
                    ),
                  ),
                ],
              ),
            ),

            // 결과 목록 (markers 사용)
            Expanded(
              child: ListView.builder(
                padding: EdgeInsets.only(
                  bottom: MediaQuery.of(context).padding.bottom + 16,
                ),
                itemCount: state.markers.length,
                itemBuilder: (context, index) {
                  final marker = state.markers[index];
                  return _buildMarkerCard(marker);
                },
              ),
            ),
          ],
        );
    }
  }

  Widget _buildMarkerCard(PropertyMapMarker marker) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: isDark ? Colors.grey[850] : Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            final recordId = marker.recordId;
            if (recordId != null) {
              context.push('/property/detail/$recordId');
            }
          },
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 주소
                Text(
                  marker.address ?? '주소 없음',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 8),

                // 가격
                Row(
                  children: [
                    const Text(
                      '매가: ',
                      style: TextStyle(fontSize: 13, color: Colors.grey),
                    ),
                    Text(
                      marker.displayPrice,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFFE38000),
                      ),
                    ),
                  ],
                ),

                // 면적 (있는 경우)
                if (marker.area != null) ...[
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Text(
                        '토지: ',
                        style: TextStyle(fontSize: 13, color: Colors.grey),
                      ),
                      Text(
                        '${(marker.area! / 3.3058).round()}평 (${marker.area!.toStringAsFixed(1)}㎡)',
                        style: const TextStyle(fontSize: 13),
                      ),
                    ],
                  ),
                ],

                // 수익률 (있는 경우)
                if (marker.yieldRate != null) ...[
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Text(
                        '수익률: ',
                        style: TextStyle(fontSize: 13, color: Colors.grey),
                      ),
                      Text(
                        '${marker.yieldRate!.toStringAsFixed(1)}%',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: Colors.green[700],
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
