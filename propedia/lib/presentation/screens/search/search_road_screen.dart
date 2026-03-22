import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/presentation/providers/building_provider.dart';
import 'package:propedia/presentation/widgets/common/app_footer.dart';

class SearchRoadScreen extends ConsumerStatefulWidget {
  const SearchRoadScreen({super.key});

  @override
  ConsumerState<SearchRoadScreen> createState() => _SearchRoadScreenState();
}

class _SearchRoadScreenState extends ConsumerState<SearchRoadScreen> {
  final _searchController = TextEditingController();
  final _focusNode = FocusNode();

  @override
  void dispose() {
    _searchController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _search() {
    final query = _searchController.text.trim();
    if (query.isNotEmpty) {
      ref.read(roadSearchProvider.notifier).search(query);
    }
  }

  @override
  Widget build(BuildContext context) {
    final searchState = ref.watch(roadSearchProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('도로명 주소 검색'),
      ),
      body: Column(
        children: [
          // 검색 입력
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              focusNode: _focusNode,
              decoration: InputDecoration(
                hintText: '도로명 또는 건물명을 입력하세요',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _searchController.clear();
                    ref.read(roadSearchProvider.notifier).reset();
                  },
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => _search(),
            ),
          ),

          // 검색 버튼
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _search,
                child: const Text('검색'),
              ),
            ),
          ),

          const SizedBox(height: 16),

          // 검색 결과
          Expanded(
            child: _buildSearchResults(searchState),
          ),
        ],
      ),
      bottomNavigationBar: const AppFooterSimple(),
    );
  }

  Widget _buildSearchResults(RoadSearchState state) {
    switch (state.status) {
      case SearchStatus.initial:
        return _buildInitialHint();
      case SearchStatus.loading:
        return const Center(child: CircularProgressIndicator());
      case SearchStatus.error:
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 48, color: Colors.grey[400]),
              const SizedBox(height: 16),
              Text(
                state.errorMessage ?? '오류가 발생했습니다',
                style: TextStyle(color: Colors.grey[600]),
              ),
            ],
          ),
        );
      case SearchStatus.success:
        if (state.results.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.search_off, size: 48, color: Colors.grey[400]),
                const SizedBox(height: 16),
                Text(
                  '검색 결과가 없습니다',
                  style: TextStyle(color: Colors.grey[600]),
                ),
              ],
            ),
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: state.results.length,
          separatorBuilder: (_, __) => const SizedBox(height: 8),
          itemBuilder: (context, index) {
            final item = state.results[index];
            return _buildResultCard(item);
          },
        );
    }
  }

  Widget _buildInitialHint() {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.signpost_outlined, size: 64, color: Colors.grey[300]),
            const SizedBox(height: 24),
            Text(
              '도로명 또는 건물명을 입력하여\n건축물을 검색하세요',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 16),
            Text(
              '예: 테헤란로 123, 강남대로 456',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[400],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard(item) {
    return Card(
      child: InkWell(
        onTap: () {
          // 건물관리번호로 상세 검색 후 결과 화면으로 이동
          // lnbrMnnm, lnbrSlno: 토지 지번 본번/부번 (bdMgtSn의 본번/부번과 다름!)
          ref.read(buildingSearchProvider.notifier).searchByBdMgtSn(
            item.bdMgtSn,
            lnbrMnnm: item.lnbrMnnm,
            lnbrSlno: item.lnbrSlno,
            admCd: item.admCd,
          );
          context.push('/result');
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 건물명
              if (item.bdNm != null && item.bdNm!.isNotEmpty) ...[
                Text(
                  item.bdNm!,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 8),
              ],
              // 도로명 주소
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      '도로명',
                      style: TextStyle(
                        fontSize: 12,
                        color: AppColors.primary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      item.roadAddr,
                      style: const TextStyle(fontSize: 14),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              // 지번 주소
              Builder(
                builder: (context) {
                  final isDark = Theme.of(context).brightness == Brightness.dark;
                  return Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: isDark ? Colors.grey[700] : Colors.grey[200],
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          '지번',
                          style: TextStyle(
                            fontSize: 12,
                            color: isDark ? Colors.grey[300] : Colors.grey[600],
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          item.jibunAddr,
                          style: TextStyle(
                            fontSize: 14,
                            color: isDark ? Colors.grey[400] : Colors.grey[600],
                          ),
                        ),
                      ),
                    ],
                  );
                },
              ),
              // 우편번호
              if (item.zipNo != null && item.zipNo!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  '우편번호: ${item.zipNo}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[500],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
