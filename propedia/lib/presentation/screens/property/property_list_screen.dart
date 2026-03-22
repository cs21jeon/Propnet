import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:propedia/data/dto/property_dto.dart';
import 'package:propedia/presentation/providers/building_provider.dart';
import 'package:propedia/presentation/providers/property_provider.dart';
import 'package:propedia/presentation/widgets/property/property_card.dart';

/// 매물 목록 화면
class PropertyListScreen extends ConsumerStatefulWidget {
  final String? initialCategory;

  const PropertyListScreen({
    super.key,
    this.initialCategory,
  });

  @override
  ConsumerState<PropertyListScreen> createState() => _PropertyListScreenState();
}

class _PropertyListScreenState extends ConsumerState<PropertyListScreen> {
  final _categories = PropertyCategory.values;
  late PropertyCategory _selectedCategory;

  @override
  void initState() {
    super.initState();

    // 초기 카테고리 결정
    _selectedCategory = PropertyCategory.reconstruction;
    if (widget.initialCategory != null) {
      final category = _categories.firstWhere(
        (c) => c.name == widget.initialCategory,
        orElse: () => PropertyCategory.reconstruction,
      );
      _selectedCategory = category;
    }

    // 초기 데이터 로드
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(selectedCategoryProvider.notifier).state = _selectedCategory;
      ref.read(propertyListProvider.notifier).loadProperties(category: _selectedCategory);
    });
  }

  void _onCategoryChanged(PropertyCategory category) {
    setState(() {
      _selectedCategory = category;
    });
    ref.read(selectedCategoryProvider.notifier).state = category;
    ref.read(propertyListProvider.notifier).changeCategory(category);
  }

  // 짧은 카테고리 레이블
  String _getShortLabel(PropertyCategory category) {
    switch (category) {
      case PropertyCategory.reconstruction:
        return '재건축토지';
      case PropertyCategory.highYield:
        return '고수익건물';
      case PropertyCategory.lowCost:
        return '단독주택';
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(propertyListProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            if (context.canPop()) {
              context.pop();
            } else {
              context.go('/property');
            }
          },
        ),
        title: const Text('추천매물'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              context.push('/property/search');
            },
            tooltip: '조건 검색',
          ),
          IconButton(
            icon: const Icon(Icons.map_outlined),
            onPressed: () {
              context.push('/property/map');
            },
            tooltip: '지도보기',
          ),
        ],
      ),
      body: Column(
        children: [
          // SegmentedButton 카테고리 선택
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: SizedBox(
              width: double.infinity,
              child: SegmentedButton<PropertyCategory>(
                showSelectedIcon: false,
                segments: _categories.map((category) {
                  return ButtonSegment<PropertyCategory>(
                    value: category,
                    label: Text(
                      _getShortLabel(category),
                      style: const TextStyle(fontSize: 13),
                    ),
                  );
                }).toList(),
                selected: {_selectedCategory},
                onSelectionChanged: (Set<PropertyCategory> selected) {
                  _onCategoryChanged(selected.first);
                },
                style: ButtonStyle(
                  backgroundColor: WidgetStateProperty.resolveWith((states) {
                    if (states.contains(WidgetState.selected)) {
                      return const Color(0xFFD4AF37);
                    }
                    return isDark ? Colors.grey[800] : Colors.grey[100];
                  }),
                  foregroundColor: WidgetStateProperty.resolveWith((states) {
                    if (states.contains(WidgetState.selected)) {
                      return Colors.white;
                    }
                    return isDark ? Colors.grey[300] : Colors.grey[700];
                  }),
                  side: WidgetStateProperty.all(
                    BorderSide(
                      color: isDark ? Colors.grey[700]! : Colors.grey[300]!,
                    ),
                  ),
                ),
              ),
            ),
          ),
          // 매물 목록
          Expanded(child: _buildBody(state)),
        ],
      ),
    );
  }

  Widget _buildBody(PropertyListState state) {
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
                  ref.read(propertyListProvider.notifier).refresh();
                },
                child: const Text('다시 시도'),
              ),
            ],
          ),
        );

      case SearchStatus.success:
        if (state.properties.isEmpty) {
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
                  '매물이 없습니다',
                  style: TextStyle(
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          );
        }

        final bottomPadding = MediaQuery.of(context).padding.bottom;
        final currentCategory = _selectedCategory;
        return RefreshIndicator(
          onRefresh: () async {
            await ref.read(propertyListProvider.notifier).refresh();
          },
          child: ListView.builder(
            padding: EdgeInsets.only(top: 8, bottom: bottomPadding + 16),
            itemCount: state.properties.length,
            itemBuilder: (context, index) {
              final property = state.properties[index];
              return PropertyCard(
                property: property,
                category: currentCategory,
                onTap: () {
                  context.push('/property/detail/${property.id}');
                },
              );
            },
          ),
        );
    }
  }
}
