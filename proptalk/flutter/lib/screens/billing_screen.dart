import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/billing_service.dart';
import '../constants/terms.dart';

class BillingScreen extends StatefulWidget {
  const BillingScreen({super.key});

  @override
  State<BillingScreen> createState() => _BillingScreenState();
}

class _BillingScreenState extends State<BillingScreen> {
  List<dynamic> _usageHistory = [];
  bool _isLoadingHistory = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadData());
  }

  Future<void> _loadData() async {
    final billing = context.read<BillingService>();
    await billing.loadBillingStatus();
    await _loadUsageHistory();
  }

  Future<void> _loadUsageHistory() async {
    try {
      final api = context.read<ApiService>();
      final data = await api.getUsageHistory(limit: 10);
      if (mounted) {
        setState(() {
          _usageHistory = data['usage_logs'] ?? [];
          _isLoadingHistory = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoadingHistory = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('구독/결제')),
      body: Consumer<BillingService>(
        builder: (context, billing, _) {
          if (billing.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          return RefreshIndicator(
            onRefresh: _loadData,
            child: ListView(
              padding: EdgeInsets.only(
                left: 16, right: 16, top: 8,
                bottom: MediaQuery.of(context).padding.bottom + 24,
              ),
              children: [
                // 현재 플랜 카드
                Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(billing.planName,
                                style: theme.textTheme.titleLarge
                                    ?.copyWith(fontWeight: FontWeight.w700)),
                            _buildStatusBadge(theme, billing),
                          ],
                        ),
                        const SizedBox(height: 16),
                        // 잔여 시간 프로그레스
                        _buildRemainingTimeBar(theme, billing),
                        const SizedBox(height: 8),
                        Text(
                          '잔여 시간: ${billing.remainingTimeFormatted}',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        if (billing.subscriptionExpiresAt != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            '갱신일: ${_formatDate(billing.subscriptionExpiresAt!)}',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.outline,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),

                // 웹 결제 안내
                Card(
                  margin: const EdgeInsets.only(bottom: 0),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('충전/구독',
                            style: theme.textTheme.titleSmall
                                ?.copyWith(fontWeight: FontWeight.w600)),
                        const SizedBox(height: 8),
                        const Text(
                          '모바일 또는 PC 브라우저에서 아래 주소로 접속하여 충전할 수 있습니다.',
                          style: TextStyle(fontSize: 13),
                        ),
                        const SizedBox(height: 12),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: theme.colorScheme.surfaceContainerHighest,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: SelectableText(
                            BillingService.billingWebUrl,
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: theme.colorScheme.primary,
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '로그인 후 요금제를 선택하고 결제하면 자동으로 이용 시간이 충전됩니다.',
                          style: TextStyle(fontSize: 12, color: theme.colorScheme.outline),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // 사용량 이력
                Text('최근 사용 이력',
                    style: theme.textTheme.labelLarge?.copyWith(
                      color: theme.colorScheme.primary,
                      fontWeight: FontWeight.w600,
                    )),
                const SizedBox(height: 8),
                if (_isLoadingHistory)
                  const Center(
                      child: Padding(
                    padding: EdgeInsets.all(16),
                    child: CircularProgressIndicator(),
                  ))
                else if (_usageHistory.isEmpty)
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Center(
                        child: Text('사용 이력이 없습니다',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.outline,
                            )),
                      ),
                    ),
                  )
                else
                  Card(
                    child: Column(
                      children: _usageHistory.map<Widget>((log) {
                        final seconds = (log['seconds_used'] as num?) ?? 0;
                        final mins = (seconds / 60).ceil();
                        final date = log['created_at'] ?? '';
                        return ListTile(
                          dense: true,
                          leading: const Icon(Icons.mic, size: 20),
                          title: Text('${mins}분 사용'),
                          trailing: Text(
                            _formatDateTime(date),
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.outline,
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),

                const SizedBox(height: 16),

                // 결제 약관 링크
                TextButton(
                  onPressed: () => _showBillingTerms(context),
                  child: const Text('결제/환불 약관 보기'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildStatusBadge(ThemeData theme, BillingService billing) {
    final labels = {
      'free': '무료',
      'active': '이용 중',
      'cancelled': '해지 예정',
      'expired': '만료',
      'past_due': '결제 실패',
    };
    final colors = {
      'free': theme.colorScheme.outline,
      'active': Colors.green,
      'cancelled': Colors.orange,
      'expired': theme.colorScheme.outline,
      'past_due': theme.colorScheme.error,
    };
    final status = billing.subscriptionStatus;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: (colors[status] ?? theme.colorScheme.outline).withAlpha(25),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: (colors[status] ?? theme.colorScheme.outline).withAlpha(80),
        ),
      ),
      child: Text(
        labels[status] ?? status,
        style: theme.textTheme.labelSmall?.copyWith(
          color: colors[status] ?? theme.colorScheme.outline,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _buildRemainingTimeBar(ThemeData theme, BillingService billing) {
    // 프로그레스 바 (무료=10분, 그 외는 플랜 기준으로 추정)
    double progress;
    if (billing.isFree) {
      progress = billing.remainingSeconds / 600; // 10분 기준
    } else {
      // 일반적으로 잔여 비율을 정확히 알기 어려우므로 대략적으로 표시
      final totalMinutes = billing.planCode.contains('30h')
          ? 1800
          : billing.planCode.contains('90h')
              ? 5400
              : billing.remainingSeconds > 0
                  ? billing.remainingSeconds
                  : 1;
      progress = billing.remainingSeconds / (totalMinutes * 60);
    }
    progress = progress.clamp(0.0, 1.0);

    Color barColor;
    if (progress > 0.3) {
      barColor = Colors.green;
    } else if (progress > 0.1) {
      barColor = Colors.orange;
    } else {
      barColor = theme.colorScheme.error;
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(4),
      child: LinearProgressIndicator(
        value: progress,
        minHeight: 8,
        backgroundColor: theme.colorScheme.surfaceContainerHighest,
        valueColor: AlwaysStoppedAnimation<Color>(barColor),
      ),
    );
  }

  String _formatDate(String isoDate) {
    try {
      final d = DateTime.parse(isoDate);
      return '${d.year}.${d.month}.${d.day}';
    } catch (_) {
      return isoDate;
    }
  }

  String _formatDateTime(String isoDate) {
    try {
      final d = DateTime.parse(isoDate);
      return '${d.month}/${d.day} ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return isoDate;
    }
  }

  void _showBillingTerms(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('결제/환불 약관'),
        content: const SingleChildScrollView(
          child: Text(AppTerms.billingTermsSummary, style: TextStyle(fontSize: 13)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('닫기'),
          ),
        ],
      ),
    );
  }
}
