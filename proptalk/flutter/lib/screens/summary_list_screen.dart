import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';

/// Step 1: 채팅방 선택 화면
class SummaryListScreen extends StatefulWidget {
  const SummaryListScreen({super.key});

  @override
  State<SummaryListScreen> createState() => _SummaryListScreenState();
}

class _SummaryListScreenState extends State<SummaryListScreen> {
  List<dynamic> _rooms = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRooms();
  }

  Future<void> _loadRooms() async {
    setState(() => _isLoading = true);
    try {
      final api = context.read<ApiService>();
      _rooms = await api.getRooms();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('목록 로딩 실패: $e')),
        );
      }
    }
    if (mounted) setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('음성파일 요약'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _rooms.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.summarize_outlined,
                          size: 64,
                          color: theme.colorScheme.onSurfaceVariant
                              .withOpacity(0.4)),
                      const SizedBox(height: 16),
                      Text('참여 중인 채팅방이 없습니다',
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          )),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadRooms,
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 8),
                    itemCount: _rooms.length,
                    itemBuilder: (context, index) {
                      final room = _rooms[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12)),
                        child: ListTile(
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12)),
                          leading: CircleAvatar(
                            backgroundColor:
                                theme.colorScheme.secondaryContainer,
                            child: Icon(Icons.summarize_outlined,
                                color: theme.colorScheme.secondary),
                          ),
                          title: Text(room['name'] ?? ''),
                          subtitle: Text(
                            '${room['member_count'] ?? 0}명 참여중',
                            style: TextStyle(
                              color: theme.colorScheme.onSurfaceVariant,
                              fontSize: 12,
                            ),
                          ),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => RoomSummaryScreen(
                                roomId: room['id'],
                                roomName: room['name'] ?? '',
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}

/// Step 2: 방별 요약 화면
class RoomSummaryScreen extends StatefulWidget {
  final int roomId;
  final String roomName;

  const RoomSummaryScreen({
    super.key,
    required this.roomId,
    required this.roomName,
  });

  @override
  State<RoomSummaryScreen> createState() => _RoomSummaryScreenState();
}

class _RoomSummaryScreenState extends State<RoomSummaryScreen> {
  List<dynamic> _summaries = [];
  bool _isLoading = true;
  bool _isLoadingMore = false;
  int _page = 1;
  int _total = 0;
  final int _perPage = 30;

  final _phoneController = TextEditingController();
  final _nameController = TextEditingController();
  final _searchController = TextEditingController();
  String? _dateFrom;
  String? _dateTo;
  bool _showFilters = false;

  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _loadSummaries();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _nameController.dispose();
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
            _scrollController.position.maxScrollExtent - 200 &&
        !_isLoadingMore &&
        _summaries.length < _total) {
      _loadMore();
    }
  }

  Future<void> _loadSummaries() async {
    setState(() {
      _isLoading = true;
      _page = 1;
    });

    try {
      final api = context.read<ApiService>();
      final result = await api.getAudioSummaries(
        roomId: widget.roomId,
        phone: _phoneController.text,
        name: _nameController.text,
        dateFrom: _dateFrom,
        dateTo: _dateTo,
        query: _searchController.text,
        page: 1,
        perPage: _perPage,
      );
      _summaries = result['audio_files'] ?? [];
      _total = result['total'] ?? 0;
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('로딩 실패: $e')),
        );
      }
    }

    if (mounted) setState(() => _isLoading = false);
  }

  Future<void> _loadMore() async {
    if (_isLoadingMore) return;
    setState(() => _isLoadingMore = true);

    try {
      final api = context.read<ApiService>();
      final result = await api.getAudioSummaries(
        roomId: widget.roomId,
        phone: _phoneController.text,
        name: _nameController.text,
        dateFrom: _dateFrom,
        dateTo: _dateTo,
        query: _searchController.text,
        page: _page + 1,
        perPage: _perPage,
      );
      final newItems = result['audio_files'] ?? [];
      if (newItems.isNotEmpty) {
        _page++;
        _summaries.addAll(newItems);
      }
    } catch (_) {}

    if (mounted) setState(() => _isLoadingMore = false);
  }

  void _clearFilters() {
    _phoneController.clear();
    _nameController.clear();
    _searchController.clear();
    _dateFrom = null;
    _dateTo = null;
    _loadSummaries();
  }

  Future<void> _pickDate(bool isFrom) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
    );
    if (picked != null) {
      final formatted =
          '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
      setState(() {
        if (isFrom) {
          _dateFrom = formatted;
        } else {
          _dateTo = formatted;
        }
      });
    }
  }

  String _formatDuration(dynamic seconds) {
    if (seconds == null) return '-';
    final s = (seconds is int) ? seconds : (seconds as num).toInt();
    final min = s ~/ 60;
    final sec = s % 60;
    return '${min}분 ${sec}초';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.roomName),
        actions: [
          IconButton(
            icon: Icon(
                _showFilters ? Icons.filter_list_off : Icons.filter_list),
            tooltip: '필터',
            onPressed: () => setState(() => _showFilters = !_showFilters),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildSearchBar(theme),
          if (_showFilters) _buildFilterBar(theme),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _summaries.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.summarize_outlined,
                                size: 64,
                                color: theme.colorScheme.onSurfaceVariant
                                    .withOpacity(0.4)),
                            const SizedBox(height: 16),
                            Text('음성파일 요약이 없습니다',
                                style: theme.textTheme.bodyLarge?.copyWith(
                                  color: theme.colorScheme.onSurfaceVariant,
                                )),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadSummaries,
                        child: ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 8),
                          itemCount:
                              _summaries.length + (_isLoadingMore ? 1 : 0),
                          itemBuilder: (context, index) {
                            if (index == _summaries.length) {
                              return const Center(
                                  child: Padding(
                                padding: EdgeInsets.all(16),
                                child: CircularProgressIndicator(),
                              ));
                            }
                            return _SummaryCard(
                              summary: _summaries[index],
                              formatDuration: _formatDuration,
                            );
                          },
                        ),
                      ),
          ),
          if (!_isLoading && _summaries.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Text(
                '${_summaries.length} / $_total건',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildSearchBar(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withOpacity(0.3),
        border: Border(
          bottom: BorderSide(color: theme.dividerColor),
        ),
      ),
      child: TextField(
        controller: _searchController,
        decoration: InputDecoration(
          hintText: '요약 내용 검색...',
          isDense: true,
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          prefixIcon: const Icon(Icons.search, size: 20),
          suffixIcon: _searchController.text.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear, size: 18),
                  onPressed: () {
                    _searchController.clear();
                    _loadSummaries();
                  },
                )
              : null,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        textInputAction: TextInputAction.search,
        onSubmitted: (_) => _loadSummaries(),
        onChanged: (_) => setState(() {}),
      ),
    );
  }

  Widget _buildFilterBar(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withOpacity(0.3),
        border: Border(
          bottom: BorderSide(color: theme.dividerColor),
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _phoneController,
                  decoration: const InputDecoration(
                    labelText: '전화번호',
                    isDense: true,
                    contentPadding:
                        EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                  keyboardType: TextInputType.phone,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                    labelText: '이름',
                    isDense: true,
                    contentPadding:
                        EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: InkWell(
                  onTap: () => _pickDate(true),
                  child: InputDecorator(
                    decoration: const InputDecoration(
                      labelText: '시작일',
                      isDense: true,
                      contentPadding:
                          EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                    child: Text(_dateFrom ?? '선택'),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: InkWell(
                  onTap: () => _pickDate(false),
                  child: InputDecorator(
                    decoration: const InputDecoration(
                      labelText: '종료일',
                      isDense: true,
                      contentPadding:
                          EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                    child: Text(_dateTo ?? '선택'),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: _loadSummaries,
                  icon: const Icon(Icons.search, size: 18),
                  label: const Text('검색'),
                ),
              ),
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: _clearFilters,
                child: const Text('초기화'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// 요약 카드 위젯
class _SummaryCard extends StatefulWidget {
  final Map<String, dynamic> summary;
  final String Function(dynamic) formatDuration;

  const _SummaryCard({
    required this.summary,
    required this.formatDuration,
  });

  @override
  State<_SummaryCard> createState() => _SummaryCardState();
}

class _SummaryCardState extends State<_SummaryCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final s = widget.summary;
    final theme = Theme.of(context);
    final hasDrive = s['drive_url'] != null && s['drive_url'] != '';
    final summary = s['transcript_summary'] ?? '';

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => setState(() => _expanded = !_expanded),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            if (s['parsed_name'] != null)
                              Flexible(
                                child: Text(s['parsed_name'],
                                    overflow: TextOverflow.ellipsis,
                                    style:
                                        theme.textTheme.titleSmall?.copyWith(
                                      fontWeight: FontWeight.w600,
                                    )),
                              ),
                            if (s['parsed_name'] != null &&
                                s['phone_number'] != null)
                              const SizedBox(width: 8),
                            if (s['phone_number'] != null)
                              Flexible(
                                child: Text(s['phone_number'],
                                    overflow: TextOverflow.ellipsis,
                                    style:
                                        theme.textTheme.bodySmall?.copyWith(
                                      color: theme.colorScheme.primary,
                                    )),
                              ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${s['record_date'] ?? s['created_at']?.toString().substring(0, 10) ?? ''} · ${widget.formatDuration(s['duration_seconds'])}',
                          overflow: TextOverflow.ellipsis,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (hasDrive)
                    IconButton(
                      icon: const Icon(Icons.open_in_new, size: 20),
                      tooltip: 'Drive에서 열기',
                      onPressed: () async {
                        final url = Uri.parse(s['drive_url']);
                        if (await canLaunchUrl(url)) {
                          await launchUrl(url,
                              mode: LaunchMode.externalApplication);
                        }
                      },
                    ),
                  Icon(
                    _expanded ? Icons.expand_less : Icons.expand_more,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ],
              ),
              if (summary.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  summary,
                  maxLines: _expanded ? null : 3,
                  overflow: _expanded ? null : TextOverflow.ellipsis,
                  style: theme.textTheme.bodyMedium,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
