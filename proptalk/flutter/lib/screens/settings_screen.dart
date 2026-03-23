import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/billing_service.dart';
import '../constants/terms.dart';
import '../theme/app_colors.dart';
import '../theme/theme_provider.dart';
import '../widgets/propnet_footer.dart';
import 'billing_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Map<String, dynamic>? _consentStatus;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadConsentStatus();
  }

  Future<void> _loadConsentStatus() async {
    try {
      final api = context.read<ApiService>();
      _consentStatus = await api.getConsentStatus();
    } catch (_) {
      // API 미지원 서버 호환
    }
    if (mounted) setState(() => _isLoading = false);
  }

  Future<void> _openUrl(String url) async {
    final uri = Uri.parse(url);
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('[SettingsScreen] URL 열기 실패: $e');
    }
  }

  Future<void> _deleteAccount() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('계정 삭제'),
        content: const Text(
          '계정을 삭제하면 모든 개인정보와 데이터가 즉시 삭제되며 복구할 수 없습니다.\n\n'
          'Google Drive에 저장된 파일은 삭제되지 않습니다.\n\n'
          '정말 삭제하시겠습니까?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Theme.of(ctx).colorScheme.error,
              foregroundColor: Theme.of(ctx).colorScheme.onError,
            ),
            child: const Text('계정 삭제'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      final api = context.read<ApiService>();
      await api.deleteAccount();

      // 로컬 데이터 정리
      final prefs = await SharedPreferences.getInstance();
      await prefs.clear();

      if (mounted) {
        final auth = context.read<AuthService>();
        await auth.signOut();

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('계정이 삭제되었습니다.')),
          );
          Navigator.of(context).popUntil((route) => route.isFirst);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('계정 삭제 실패: $e')),
        );
      }
    }
  }

  void _showBillingSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.9,
        minChildSize: 0.4,
        expand: false,
        builder: (ctx, scrollController) => _BillingSheetContent(
          scrollController: scrollController,
        ),
      ),
    );
  }


  Future<void> _withdrawConsent(String type, String label) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('$label 동의 철회'),
        content: Text(
          '$label 동의를 철회하시겠습니까?\n\n'
          '철회 시 관련 기능을 사용할 수 없습니다.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('동의 철회'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      final api = context.read<ApiService>();
      await api.withdrawConsent(type);

      // audio_processing 철회 시 로컬 동의 상태도 초기화
      if (type == 'audio_processing') {
        final prefs = await SharedPreferences.getInstance();
        await prefs.remove('audio_consent_agreed');
      }

      await _loadConsentStatus();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$label 동의가 철회되었습니다.')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('동의 철회 실패: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final user = auth.currentUser;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('프로필')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: EdgeInsets.only(
                left: 16, right: 16, top: 8,
                bottom: MediaQuery.of(context).padding.bottom + 24,
              ),
              children: [
                // 프로필 카드
                if (user != null)
                  Card(
                    margin: const EdgeInsets.only(bottom: 16),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          CircleAvatar(
                            radius: 28,
                            backgroundImage: user['avatar_url'] != null
                                ? NetworkImage(user['avatar_url'])
                                : null,
                            child: user['avatar_url'] == null
                                ? Text(user['name']?[0] ?? '?',
                                    style: theme.textTheme.titleLarge)
                                : null,
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Flexible(
                                      child: Text(user['name'] ?? '',
                                          style: theme.textTheme.titleMedium
                                              ?.copyWith(fontWeight: FontWeight.w600)),
                                    ),
                                    const SizedBox(width: 4),
                                    InkWell(
                                      onTap: () => _showEditNameDialog(context),
                                      borderRadius: BorderRadius.circular(12),
                                      child: Padding(
                                        padding: const EdgeInsets.all(4),
                                        child: Icon(Icons.edit, size: 16,
                                            color: theme.colorScheme.outline),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 2),
                                Text(user['email'] ?? '',
                                    style: theme.textTheme.bodySmall?.copyWith(
                                        color: theme.colorScheme.outline)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                // 구독/결제 섹션
                _buildSectionHeader(theme, '구독/결제'),
                Consumer<BillingService>(
                  builder: (context, billing, _) {
                    return Card(
                      margin: const EdgeInsets.only(bottom: 16),
                      child: Column(
                        children: [
                          ListTile(
                            leading: const Icon(Icons.workspace_premium_outlined),
                            title: Text(billing.planName),
                            subtitle: Text('잔여 시간: ${billing.remainingTimeFormatted}'),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                  builder: (_) => const BillingScreen()),
                            ),
                          ),
                          const Divider(height: 1, indent: 56),
                          ListTile(
                            leading: const Icon(Icons.payment_outlined),
                            title: const Text('충전/요금제'),
                            subtitle: const Text('요금제 안내 및 충전 방법'),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: () => _showBillingSheet(),
                          ),
                        ],
                      ),
                    );
                  },
                ),

                // 앱 설정 섹션
                _buildSectionHeader(theme, '앱 설정'),
                Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Column(
                    children: [
                      _buildThemeTile(context, theme),
                    ],
                  ),
                ),

                // 법적 문서 섹션
                _buildSectionHeader(theme, '법적 문서'),
                Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Column(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.description_outlined),
                        title: const Text('이용약관'),
                        trailing: const Icon(Icons.open_in_new, size: 18),
                        onTap: () => _openUrl(AppTerms.termsOfServiceUrl),
                      ),
                      const Divider(height: 1, indent: 56),
                      ListTile(
                        leading: const Icon(Icons.privacy_tip_outlined),
                        title: const Text('개인정보 처리방침'),
                        trailing: const Icon(Icons.open_in_new, size: 18),
                        onTap: () => _openUrl(AppTerms.privacyPolicyUrl),
                      ),
                    ],
                  ),
                ),

                // 동의 관리 섹션
                _buildSectionHeader(theme, '동의 관리'),
                Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: _consentStatus != null
                      ? Column(children: _buildConsentItems(theme))
                      : const ListTile(
                          title: Text('동의 정보를 불러올 수 없습니다'),
                        ),
                ),

                // 관리자 (admin 계정만 표시)
                if (user?['email'] == 'cs21.jeon@gmail.com') ...[
                  _buildSectionHeader(theme, '관리자'),
                  Card(
                    margin: const EdgeInsets.only(bottom: 16),
                    child: ListTile(
                      leading: const Icon(Icons.admin_panel_settings),
                      title: const Text('관리자 대시보드'),
                      trailing: const Icon(Icons.open_in_new, size: 18),
                      onTap: () {
                        final api = context.read<ApiService>();
                        final token = api.token ?? '';
                        _openUrl('https://goldenrabbit.biz/proptalk/admin/login?token=$token');
                      },
                    ),
                  ),
                ],

                // 계정 섹션
                _buildSectionHeader(theme, '계정'),
                Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Column(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.logout),
                        title: const Text('로그아웃'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {
                          auth.signOut();
                          Navigator.of(context)
                              .popUntil((route) => route.isFirst);
                        },
                      ),
                      const Divider(height: 1, indent: 56),
                      ListTile(
                        leading: Icon(Icons.delete_forever,
                            color: theme.colorScheme.error),
                        title: Text('계정 삭제',
                            style:
                                TextStyle(color: theme.colorScheme.error)),
                        subtitle: const Text('모든 데이터가 즉시 삭제됩니다'),
                        onTap: _deleteAccount,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 8),

                // 앱 정보
                const PropnetFooter(),
                const SizedBox(height: 24),
              ],
            ),
    );
  }


  void _showEditNameDialog(BuildContext context) {
    final auth = context.read<AuthService>();
    final controller = TextEditingController(text: auth.currentUser?['name'] ?? '');
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('이름 변경'),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLength: 50,
          decoration: const InputDecoration(
            labelText: '이름',
            hintText: '표시할 이름을 입력하세요',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () async {
              final name = controller.text.trim();
              if (name.isEmpty) return;
              try {
                await auth.updateName(name);
                if (ctx.mounted) Navigator.pop(ctx);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('이름이 변경되었습니다'), duration: Duration(seconds: 1)),
                  );
                  setState(() {});
                }
              } catch (e) {
                if (ctx.mounted) Navigator.pop(ctx);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('이름 변경 실패: $e')),
                  );
                }
              }
            },
            child: const Text('변경'),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(ThemeData theme, String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(title,
          style: theme.textTheme.labelLarge?.copyWith(
            color: theme.colorScheme.primary,
            fontWeight: FontWeight.w600,
          )),
    );
  }

  Widget _buildThemeTile(BuildContext context, ThemeData theme) {
    final themeProvider = context.watch<ThemeProvider>();
    final isDark = themeProvider.themeMode == ThemeMode.dark;

    return SwitchListTile(
      secondary: Icon(isDark ? Icons.dark_mode : Icons.light_mode),
      title: const Text('다크 모드'),
      value: isDark,
      onChanged: (v) {
        themeProvider.setThemeMode(v ? ThemeMode.dark : ThemeMode.light);
      },
    );
  }

  List<Widget> _buildConsentItems(ThemeData theme) {
    final consents = (_consentStatus?['consents'] as List?) ?? [];
    final consentLabels = {
      'terms': '이용약관',
      'privacy': '개인정보 수집 및 이용',
      'overseas_transfer': '개인정보 국외 이전',
      'audio_processing': '음성 데이터 처리',
    };

    if (consents.isEmpty) {
      return [
        const ListTile(title: Text('동의 이력이 없습니다')),
      ];
    }

    return consents.map<Widget>((c) {
      final type = c['consent_type'] ?? c['type'] ?? '';
      final label = consentLabels[type] ?? type;
      final agreed = c['agreed'] == true && c['withdrawn_at'] == null;

      final appColors = theme.extension<AppColors>()!;
      return ListTile(
        leading: Icon(
          agreed ? Icons.check_circle : Icons.cancel,
          color: agreed ? appColors.success : theme.colorScheme.outline,
        ),
        title: Text(label),
        subtitle: Text(agreed ? '동의함' : '철회됨'),
        trailing: agreed
            ? TextButton(
                onPressed: () => _withdrawConsent(type, label),
                child: const Text('철회'),
              )
            : null,
      );
    }).toList();
  }
}

/// 서버에서 요금제를 불러와 표시하는 바텀시트 위젯
class _BillingSheetContent extends StatefulWidget {
  final ScrollController scrollController;
  const _BillingSheetContent({required this.scrollController});

  @override
  State<_BillingSheetContent> createState() => _BillingSheetContentState();
}

class _BillingSheetContentState extends State<_BillingSheetContent> {
  List<dynamic> _plans = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPlans();
  }

  Future<void> _loadPlans() async {
    try {
      final api = context.read<ApiService>();
      final data = await api.getBillingPlans();
      if (mounted) {
        setState(() {
          _plans = data['plans'] ?? [];
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  String _formatMinutes(dynamic mins) {
    if (mins == null) return '-';
    final m = (mins is int) ? mins : (mins as num).toInt();
    if (m >= 60) {
      final h = m ~/ 60;
      final rem = m % 60;
      return rem > 0 ? '${h}시간 ${rem}분' : '${h}시간';
    }
    return '${m}분';
  }

  String _formatPrice(dynamic price) {
    if (price == null || price == 0) return '무료';
    final p = (price is int) ? price : (price as num).toInt();
    final formatted = p.toString().replaceAllMapped(
        RegExp(r'(\d)(?=(\d{3})+(?!\d))'), (m) => '${m[1]},');
    return '${formatted}원';
  }

  String _buildSubtitle(Map<String, dynamic> plan) {
    final parts = <String>[];
    final type = plan['plan_type'] ?? '';

    if (type == 'free') {
      parts.add('계정당 평생 제공');
    } else if (type == 'time_pack') {
      parts.add('일회성 · 만료 없음');
    } else if (type == 'subscription') {
      parts.add('월 정기결제');
    }

    final mins = (plan['minutes_included'] as num?)?.toInt() ?? 0;
    if (mins > 0 && (plan['price'] as num?)?.toInt() != null) {
      final price = (plan['price'] as num).toInt();
      if (price > 0) {
        final hours = mins / 60;
        final perHour = (price / hours).round();
        parts.add('시간당 ${_formatPrice(perHour)}');
      }
    }

    final overage = plan['overage_rate'];
    if (overage != null && overage > 0) {
      parts.add('초과 시 ${overage}원/분');
    }

    return parts.join(' · ');
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SafeArea(
      child: ListView(
        controller: widget.scrollController,
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: theme.colorScheme.outline.withAlpha(60),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Text('요금제 안내',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),

          if (_isLoading)
            const Center(
                child: Padding(
              padding: EdgeInsets.all(32),
              child: CircularProgressIndicator(),
            ))
          else ...[
            // 일반 사용자 요금제 (free, time_pack, subscription 중 agent 아닌 것)
            ..._plans
                .where((p) => !(p['code']?.toString().startsWith('agent') ?? false))
                .map((plan) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _buildPlanCard(theme, plan),
                    )),

            // Agent 요금제가 있으면 섹션 분리
            if (_plans.any((p) => p['code']?.toString().startsWith('agent') ?? false)) ...[
              const SizedBox(height: 8),
              Text('중개사 (Agent)',
                  style: theme.textTheme.titleSmall
                      ?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.orange.withAlpha(25),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  'Agent 요금제에는 Propsheet(부동산 데이터베이스)가 포함되어 있습니다.',
                  style: TextStyle(fontSize: 12, color: Colors.deepOrange),
                ),
              ),
              ..._plans
                  .where((p) => p['code']?.toString().startsWith('agent') ?? false)
                  .map((plan) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: _buildPlanCard(theme, plan),
                      )),
            ],
          ],

          const SizedBox(height: 24),
          const Divider(),
          const SizedBox(height: 16),

          Text('충전 방법',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.bold)),
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
            '로그인 후 요금제를 선택하고 결제하면 앱에 자동으로 이용 시간이 충전됩니다.',
            style: TextStyle(fontSize: 12, color: theme.colorScheme.outline),
          ),
        ],
      ),
    );
  }

  Widget _buildPlanCard(ThemeData theme, Map<String, dynamic> plan) {
    final isSub = plan['plan_type'] == 'subscription';
    final priceStr = _formatPrice(plan['price']);
    final timeStr = _formatMinutes(plan['minutes_included']);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withAlpha(120),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(plan['name'] ?? '',
                    style: theme.textTheme.titleSmall
                        ?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(_buildSubtitle(plan),
                    style: TextStyle(
                        fontSize: 12, color: theme.colorScheme.outline)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(timeStr,
                  style: theme.textTheme.bodyMedium
                      ?.copyWith(fontWeight: FontWeight.w600)),
              Text(isSub ? '$priceStr/월' : priceStr,
                  style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: theme.colorScheme.primary)),
            ],
          ),
        ],
      ),
    );
  }
}
