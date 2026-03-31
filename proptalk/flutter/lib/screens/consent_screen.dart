import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../constants/terms.dart';

class ConsentScreen extends StatefulWidget {
  const ConsentScreen({super.key});

  @override
  State<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends State<ConsentScreen> {
  /// 각 동의 항목의 체크 상태 (index 기반)
  late List<bool> _agreed;
  bool _isSubmitting = false;
  String? _error;

  /// 서버에서 받은 missing_consents 항목 리스트
  List<Map<String, dynamic>> get _consentItems {
    final auth = context.read<AuthService>();
    final items = auth.missingConsents;
    // 서버 응답이 비어있으면 기본 3개 항목으로 폴백
    if (items.isEmpty) {
      return [
        {'type': 'terms', 'version': AppTerms.currentVersion, 'label': '[필수] 서비스 이용약관', 'required': true},
        {'type': 'privacy', 'version': AppTerms.currentVersion, 'label': '[필수] 개인정보 수집 및 이용 동의', 'required': true},
        {'type': 'overseas_transfer', 'version': AppTerms.currentVersion, 'label': '[필수] 개인정보 국외 이전 동의', 'required': true},
      ];
    }
    return items;
  }

  bool get _allRequiredAgreed {
    final items = _consentItems;
    for (int i = 0; i < items.length; i++) {
      final isRequired = items[i]['required'] != false;
      if (isRequired && (i >= _agreed.length || !_agreed[i])) {
        return false;
      }
    }
    return true;
  }

  bool get _allAgreed {
    if (_agreed.length != _consentItems.length) return false;
    return _agreed.every((v) => v);
  }

  int get _agreedCount => _agreed.where((v) => v).length;

  @override
  void initState() {
    super.initState();
    // initState에서는 context.read 사용 불가하므로 didChangeDependencies에서 초기화
    _agreed = [];
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_agreed.isEmpty || _agreed.length != _consentItems.length) {
      _agreed = List.filled(_consentItems.length, false);
    }
  }

  Future<void> _submit() async {
    if (!_allRequiredAgreed) return;

    setState(() {
      _isSubmitting = true;
      _error = null;
    });

    try {
      final api = context.read<ApiService>();
      final items = _consentItems;

      // 동의한 항목만 서버에 전송
      final consents = <Map<String, String>>[];
      for (int i = 0; i < items.length; i++) {
        if (i < _agreed.length && _agreed[i]) {
          consents.add({
            'type': items[i]['type'] as String,
            'version': items[i]['version'] as String? ?? AppTerms.currentVersion,
          });
        }
      }

      await api.recordConsent(consents);

      if (mounted) {
        context.read<AuthService>().markConsentCompleted();
      }
    } catch (e) {
      debugPrint('[ConsentScreen] 동의 저장 실패: $e');
      if (mounted) {
        setState(() => _error = '동의 저장에 실패했습니다: $e');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('동의 저장 실패: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
            duration: const Duration(seconds: 5),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _openUrl(String url) async {
    final uri = Uri.parse(url);
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('[ConsentScreen] URL 열기 실패: $e');
    }
  }

  void _showFullText(String title, String content) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.85,
        maxChildSize: 0.95,
        minChildSize: 0.5,
        expand: false,
        builder: (context, scrollController) => Column(
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: SingleChildScrollView(
                controller: scrollController,
                padding: const EdgeInsets.all(16),
                child: Text(
                  content,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    height: 1.6,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final items = _consentItems;

    // _agreed 길이가 items와 맞지 않으면 재초기화
    if (_agreed.length != items.length) {
      _agreed = List.filled(items.length, false);
    }

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) {
          context.read<AuthService>().signOut();
        }
      },
      child: Scaffold(
      appBar: AppBar(
        title: const Text('서비스 이용 동의'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            context.read<AuthService>().signOut();
          },
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Proptalk 서비스 이용을 위해 아래 항목에 동의해 주세요.',
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '서비스 이용을 위해 필수 동의가 필요합니다.',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 16),

                    // 진행 표시
                    _buildProgressIndicator(theme, items.length),

                    const SizedBox(height: 20),

                    // 전체 동의
                    _buildAllAgreeCard(theme),

                    const SizedBox(height: 16),

                    // 동적 동의 항목
                    for (int i = 0; i < items.length; i++) ...[
                      if (i > 0) const SizedBox(height: 12),
                      _buildDynamicConsentItem(
                        theme: theme,
                        index: i,
                        item: items[i],
                      ),
                    ],

                    if (_error != null) ...[
                      const SizedBox(height: 16),
                      Text(
                        _error!,
                        style: TextStyle(color: theme.colorScheme.error),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            // 하단 버튼
            Padding(
              padding: const EdgeInsets.all(20),
              child: SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: _allRequiredAgreed && !_isSubmitting ? _submit : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: theme.colorScheme.primary,
                    foregroundColor: theme.colorScheme.onPrimary,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text(
                          '동의하고 시작하기',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                        ),
                ),
              ),
            ),
          ],
        ),
      ),
    ),
    );
  }

  Widget _buildProgressIndicator(ThemeData theme, int total) {
    return Row(
      children: [
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: total > 0 ? _agreedCount / total : 0,
              minHeight: 6,
              backgroundColor: theme.colorScheme.surfaceContainerHighest,
              color: theme.colorScheme.primary,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Text(
          '$_agreedCount/$total',
          style: theme.textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.primary,
          ),
        ),
      ],
    );
  }

  Widget _buildAllAgreeCard(ThemeData theme) {
    return Card(
      elevation: 0,
      color: theme.colorScheme.primaryContainer,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: CheckboxListTile(
        value: _allAgreed,
        onChanged: (v) {
          setState(() {
            final newValue = v ?? false;
            for (int i = 0; i < _agreed.length; i++) {
              _agreed[i] = newValue;
            }
          });
        },
        title: Text(
          '전체 동의',
          style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
        ),
        controlAffinity: ListTileControlAffinity.leading,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  /// 서버 missing_consents 항목을 동적으로 렌더링
  Widget _buildDynamicConsentItem({
    required ThemeData theme,
    required int index,
    required Map<String, dynamic> item,
  }) {
    final type = item['type'] as String;
    final label = item['label'] as String? ?? '[필수] $type';
    final isRequired = item['required'] != false;
    final subtitle = item['description'] as String? ?? AppTerms.getSubtitleForType(type);
    final fullText = AppTerms.getFullTextForType(type);
    final webUrl = AppTerms.getWebUrlForType(type);

    // 레이블에 [필수]/[선택] 이미 포함된 경우 그대로, 아니면 추가
    final displayLabel = label.startsWith('[') ? label : (isRequired ? '[필수] $label' : '[선택] $label');

    return _buildConsentItem(
      theme: theme,
      title: displayLabel,
      subtitle: subtitle,
      value: index < _agreed.length ? _agreed[index] : false,
      onChanged: (v) => setState(() {
        if (index < _agreed.length) {
          _agreed[index] = v ?? false;
        }
      }),
      onViewFull: fullText != null
          ? () => _showFullText(label.replaceAll(RegExp(r'\[.+?\]\s*'), ''), fullText)
          : null,
      onViewWeb: webUrl != null ? () => _openUrl(webUrl) : null,
    );
  }

  Widget _buildConsentItem({
    required ThemeData theme,
    required String title,
    String? subtitle,
    required bool value,
    required ValueChanged<bool?> onChanged,
    VoidCallback? onViewFull,
    VoidCallback? onViewWeb,
  }) {
    return Card(
      elevation: 0,
      color: theme.colorScheme.surfaceContainerHighest,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          CheckboxListTile(
            value: value,
            onChanged: onChanged,
            title: Text(
              title,
              style: theme.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w500),
            ),
            subtitle: subtitle != null
                ? Text(subtitle, style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ))
                : null,
            controlAffinity: ListTileControlAffinity.leading,
          ),
          if (onViewFull != null || onViewWeb != null)
            Padding(
              padding: const EdgeInsets.only(left: 16, right: 16, bottom: 8),
              child: Row(
                children: [
                  if (onViewFull != null)
                    TextButton.icon(
                      onPressed: onViewFull,
                      icon: const Icon(Icons.description_outlined, size: 16),
                      label: const Text('전문 보기'),
                      style: TextButton.styleFrom(
                        textStyle: const TextStyle(fontSize: 13),
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                      ),
                    ),
                  if (onViewWeb != null)
                    TextButton.icon(
                      onPressed: onViewWeb,
                      icon: const Icon(Icons.open_in_new, size: 16),
                      label: const Text('웹에서 보기'),
                      style: TextButton.styleFrom(
                        textStyle: const TextStyle(fontSize: 13),
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
