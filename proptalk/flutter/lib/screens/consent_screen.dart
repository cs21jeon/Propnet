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
  bool _termsAgreed = false;
  bool _privacyAgreed = false;
  bool _overseasAgreed = false;
  bool _isSubmitting = false;
  String? _error;

  bool get _allAgreed => _termsAgreed && _privacyAgreed && _overseasAgreed;

  Future<void> _submit() async {
    if (!_allAgreed) return;

    setState(() {
      _isSubmitting = true;
      _error = null;
    });

    try {
      final api = context.read<ApiService>();
      await api.recordConsent([
        {'type': 'terms', 'version': '2026-03-01'},
        {'type': 'privacy', 'version': '2026-03-01'},
        {'type': 'overseas_transfer', 'version': '2026-03-01'},
      ]);

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

    return Scaffold(
      appBar: AppBar(
        title: const Text('서비스 이용 동의'),
        automaticallyImplyLeading: false,
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
                      'Proptalk 서비스를 이용하시려면\n아래 항목에 동의해 주세요.',
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
                    _buildProgressIndicator(theme),

                    const SizedBox(height: 20),

                    // 전체 동의
                    _buildAllAgreeCard(theme),

                    const SizedBox(height: 16),

                    // 개별 동의 항목
                    _buildConsentItem(
                      theme: theme,
                      title: '[필수] 서비스 이용약관',
                      value: _termsAgreed,
                      onChanged: (v) => setState(() => _termsAgreed = v ?? false),
                      onViewFull: () => _showFullText('서비스 이용약관', AppTerms.termsOfServiceFull),
                      onViewWeb: () => _openUrl(AppTerms.termsOfServiceUrl),
                    ),
                    const SizedBox(height: 12),

                    _buildConsentItem(
                      theme: theme,
                      title: '[필수] 개인정보 수집 및 이용 동의',
                      subtitle: '음성 파일, STT 변환 텍스트, AI 요약 결과 등',
                      value: _privacyAgreed,
                      onChanged: (v) => setState(() => _privacyAgreed = v ?? false),
                      onViewFull: () => _showFullText('개인정보 처리방침', AppTerms.privacyPolicyFull),
                      onViewWeb: () => _openUrl(AppTerms.privacyPolicyUrl),
                    ),
                    const SizedBox(height: 12),

                    _buildConsentItem(
                      theme: theme,
                      title: '[필수] 개인정보 국외 이전 동의',
                      subtitle: 'OpenAI(미국), Anthropic(미국), Google(미국)에 데이터 전송',
                      value: _overseasAgreed,
                      onChanged: (v) => setState(() => _overseasAgreed = v ?? false),
                      onViewFull: () => _showOverseasDetail(),
                    ),

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
                  onPressed: _allAgreed && !_isSubmitting ? _submit : null,
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
    );
  }

  Widget _buildProgressIndicator(ThemeData theme) {
    final count = [_termsAgreed, _privacyAgreed, _overseasAgreed]
        .where((v) => v)
        .length;
    return Row(
      children: [
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: count / 3,
              minHeight: 6,
              backgroundColor: theme.colorScheme.surfaceContainerHighest,
              color: theme.colorScheme.primary,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Text(
          '$count/3',
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
            _termsAgreed = v ?? false;
            _privacyAgreed = v ?? false;
            _overseasAgreed = v ?? false;
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

  Widget _buildConsentItem({
    required ThemeData theme,
    required String title,
    String? subtitle,
    required bool value,
    required ValueChanged<bool?> onChanged,
    required VoidCallback onViewFull,
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
          Padding(
            padding: const EdgeInsets.only(left: 16, right: 16, bottom: 8),
            child: Row(
              children: [
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

  void _showOverseasDetail() {
    _showFullText('개인정보 국외 이전 동의', '''
개인정보 국외 이전 동의

Proptalk 서비스 제공을 위해 아래와 같이 개인정보를 국외로 이전합니다.

1. OpenAI, Inc. (미국)
   - 이전 항목: 음성 파일
   - 이전 목적: Whisper API를 통한 음성-텍스트 변환(STT)
   - 보유 기간: 처리 즉시 삭제 (OpenAI는 API 데이터를 학습에 사용하지 않음)

2. Anthropic, PBC (미국)
   - 이전 항목: STT 변환 텍스트
   - 이전 목적: Claude API를 통한 대화 내용 AI 요약
   - 보유 기간: 처리 즉시 삭제

3. Google LLC (미국)
   - 이전 항목: 인증 정보, 음성 파일 (Drive 백업 시)
   - 이전 목적: OAuth 로그인 인증, Google Drive 파일 백업
   - 보유 기간: Drive 백업 파일은 사용자가 직접 관리

위 업체들은 각각의 보안 체계(TLS 암호화, 접근 통제 등)를 통해 데이터를 보호합니다.

동의를 거부하실 수 있으나, 거부 시 음성 변환 및 AI 요약 기능을 이용할 수 없습니다.

문의: cs21.jeon@gmail.com
''');
  }
}
