import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/core/constants/terms.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';

/// 서비스 이용 동의 화면
///
/// 서버에서 받은 missing_consents 목록으로 동적 구성.
/// 모든 필수 동의 완료 후 서버에 기록하고 홈 화면으로 이동.
class ConsentScreen extends ConsumerStatefulWidget {
  const ConsentScreen({super.key});

  @override
  ConsumerState<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends ConsumerState<ConsentScreen> {
  /// 각 동의 항목의 체크 상태 (consent_type -> agreed)
  final Map<String, bool> _agreements = {};
  bool _isSubmitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    // 서버에서 받은 missing_consents로 초기 상태 설정
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final consents = ref.read(authProvider).missingConsents;
      for (final consent in consents) {
        final type = consent['type'] as String? ?? '';
        if (type.isNotEmpty) {
          _agreements[type] = false;
        }
      }
      // 서버 응답이 비어있을 경우 기본 3개 항목
      if (_agreements.isEmpty) {
        _agreements['terms'] = false;
        _agreements['privacy'] = false;
        _agreements['overseas_transfer'] = false;
      }
      setState(() {});
    });
  }

  List<Map<String, dynamic>> get _consentItems {
    final serverConsents = ref.read(authProvider).missingConsents;
    if (serverConsents.isNotEmpty) {
      return serverConsents;
    }
    // 서버 응답이 없을 경우 기본 동의 항목
    return [
      {
        'type': 'terms',
        'label': '[필수] 서비스 이용약관',
        'version': '2026-04-01',
        'required': true,
      },
      {
        'type': 'privacy',
        'label': '[필수] 개인정보 수집 및 이용 동의',
        'version': '2026-04-01',
        'required': true,
      },
      {
        'type': 'overseas_transfer',
        'label': '[필수] 개인정보 국외 이전 동의',
        'version': '2026-04-01',
        'required': true,
      },
    ];
  }

  bool get _allRequiredAgreed {
    for (final consent in _consentItems) {
      final type = consent['type'] as String? ?? '';
      final required = consent['required'] as bool? ?? true;
      if (required && _agreements[type] != true) {
        return false;
      }
    }
    return _agreements.isNotEmpty;
  }

  bool get _allAgreed {
    if (_agreements.isEmpty) return false;
    return _agreements.values.every((v) => v);
  }

  int get _agreedCount => _agreements.values.where((v) => v).length;

  void _toggleAll(bool? value) {
    setState(() {
      for (final key in _agreements.keys) {
        _agreements[key] = value ?? false;
      }
    });
  }

  Future<void> _submit() async {
    if (!_allRequiredAgreed) return;

    setState(() {
      _isSubmitting = true;
      _error = null;
    });

    try {
      // 동의 항목 구성
      final consents = <Map<String, dynamic>>[];
      for (final consent in _consentItems) {
        final type = consent['type'] as String? ?? '';
        if (_agreements[type] == true) {
          consents.add({
            'type': type,
            'version': consent['version'] ?? '2026-04-01',
          });
        }
      }

      await ref.read(authProvider.notifier).submitConsent(consents);
      // submitConsent이 성공하면 authProvider 상태가 authenticated로 변경되고
      // GoRouter redirect가 /home으로 보냄
    } catch (e) {
      debugPrint('[ConsentScreen] 동의 저장 실패: $e');
      if (mounted) {
        setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('동의 저장 실패: $_error'),
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

  /// 약관 전문을 바텀시트로 표시
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
            // 드래그 핸들
            Container(
              margin: const EdgeInsets.only(top: 12),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
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

  /// 동의 유형에 따라 전문 내용 반환
  String _getFullTextForType(String type) {
    switch (type) {
      case 'terms':
        return Terms.termsOfService;
      case 'privacy':
        return Terms.privacyPolicy;
      case 'overseas_transfer':
        return _overseasTransferText;
      default:
        return '약관 내용을 불러올 수 없습니다.';
    }
  }

  /// 동의 유형에 따라 전문 제목 반환
  String _getTitleForType(String type) {
    switch (type) {
      case 'terms':
        return '서비스 이용약관';
      case 'privacy':
        return '개인정보 처리방침';
      case 'overseas_transfer':
        return '개인정보 국외 이전 동의';
      default:
        return '약관';
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final items = _consentItems;
    final totalCount = items.length;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('서비스 이용 동의'),
        automaticallyImplyLeading: false,
        actions: [
          // 로그아웃 (동의 거부 시 뒤로가기)
          TextButton(
            onPressed: () {
              ref.read(authProvider.notifier).logout();
              context.go('/login');
            },
            child: Text(
              '취소',
              style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
            ),
          ),
        ],
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
                    // 헤더 텍스트
                    Text(
                      'PropNet 서비스 이용을 위해 아래 항목에 동의해 주세요.',
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
                    _buildProgressIndicator(theme, totalCount),

                    const SizedBox(height: 20),

                    // 전체 동의
                    _buildAllAgreeCard(theme),

                    const SizedBox(height: 16),

                    // 개별 동의 항목
                    ...items.map((consent) {
                      final type = consent['type'] as String? ?? '';
                      final label = consent['label'] as String? ?? type;
                      final description = consent['description'] as String?;

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: _buildConsentItem(
                          theme: theme,
                          title: label,
                          subtitle: description,
                          value: _agreements[type] ?? false,
                          onChanged: (v) {
                            setState(() => _agreements[type] = v ?? false);
                          },
                          onViewFull: () {
                            _showFullText(
                              _getTitleForType(type),
                              _getFullTextForType(type),
                            );
                          },
                        ),
                      );
                    }),

                    if (_error != null) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.error.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline,
                                color: AppColors.error, size: 20),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _error!,
                                style: const TextStyle(
                                  color: AppColors.error,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            // 하단 버튼
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: theme.scaffoldBackgroundColor,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.05),
                    blurRadius: 10,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: _allRequiredAgreed && !_isSubmitting ? _submit : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    disabledBackgroundColor: AppColors.gray300,
                    disabledForegroundColor: AppColors.gray500,
                    elevation: 0,
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
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                ),
              ),
            ),
          ],
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
              backgroundColor: AppColors.gray200,
              color: AppColors.primary,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Text(
          '$_agreedCount/$total',
          style: theme.textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w600,
            color: AppColors.primary,
          ),
        ),
      ],
    );
  }

  Widget _buildAllAgreeCard(ThemeData theme) {
    return Card(
      elevation: 0,
      color: AppColors.primary.withValues(alpha: 0.08),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: CheckboxListTile(
        value: _allAgreed,
        onChanged: _toggleAll,
        title: Text(
          '전체 동의',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        controlAffinity: ListTileControlAffinity.leading,
        activeColor: AppColors.primary,
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
  }) {
    return Card(
      elevation: 0,
      color: AppColors.gray100,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          CheckboxListTile(
            value: value,
            onChanged: onChanged,
            title: Text(
              title,
              style: theme.textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            subtitle: subtitle != null
                ? Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      subtitle,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  )
                : null,
            controlAffinity: ListTileControlAffinity.leading,
            activeColor: AppColors.primary,
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
                    foregroundColor: AppColors.textSecondary,
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

  static const String _overseasTransferText = '''
개인정보 국외 이전 동의

Proppedia 서비스 제공을 위해 아래와 같이 개인정보를 국외로 이전합니다.

1. Google LLC (미국)
   - 이전 항목: 인증 정보 (이메일, 이름, 프로필 사진)
   - 이전 목적: Google OAuth 로그인 인증
   - 보유 기간: 회원 탈퇴 시까지

2. 공공데이터 포털 (한국)
   - 이전 항목: 검색 주소 정보
   - 이전 목적: 건축물대장, 토지대장, 공시가격 등 부동산 정보 조회
   - 보유 기간: 처리 즉시 (API 호출 시에만 전송)

위 업체들은 각각의 보안 체계(TLS 암호화, 접근 통제 등)를 통해 데이터를 보호합니다.

동의를 거부하실 수 있으나, 거부 시 서비스의 핵심 기능(로그인, 부동산 정보 조회)을 이용할 수 없습니다.

문의: cs21.jeon@gmail.com
''';
}
