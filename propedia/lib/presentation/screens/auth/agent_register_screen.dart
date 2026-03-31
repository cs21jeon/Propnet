import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:file_picker/file_picker.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';

/// Agent 가입 신청 화면
///
/// 필수 입력: 상호, 영문이름(slug), 대표자, 연락처, 주소
/// 필수 첨부: 공인중개사 등록증
/// 선택 첨부: 사업자등록증
class AgentRegisterScreen extends ConsumerStatefulWidget {
  const AgentRegisterScreen({super.key});

  @override
  ConsumerState<AgentRegisterScreen> createState() =>
      _AgentRegisterScreenState();
}

class _AgentRegisterScreenState extends ConsumerState<AgentRegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _agentNameController = TextEditingController();
  final _slugController = TextEditingController();
  final _representativeController = TextEditingController();
  final _phoneController = TextEditingController();
  final _addressController = TextEditingController();

  String? _licenseFilePath;
  String? _licenseFileName;
  String? _businessRegFilePath;
  String? _businessRegFileName;

  bool _isSubmitting = false;
  bool _isCheckingSlug = false;
  bool? _slugAvailable;
  String? _slugError;

  @override
  void dispose() {
    _agentNameController.dispose();
    _slugController.dispose();
    _representativeController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    super.dispose();
  }

  Future<void> _checkSlug() async {
    final slug = _slugController.text.trim().toLowerCase();
    if (slug.isEmpty) {
      setState(() {
        _slugError = '영문 이름을 입력해주세요';
        _slugAvailable = null;
      });
      return;
    }

    if (!RegExp(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$').hasMatch(slug) &&
        slug.length > 1) {
      setState(() {
        _slugError = '영문 소문자, 숫자, 하이픈(-)만 사용 가능합니다';
        _slugAvailable = null;
      });
      return;
    }

    setState(() {
      _isCheckingSlug = true;
      _slugError = null;
    });

    try {
      final authRepo = ref.read(authRepositoryProvider);
      final result = await authRepo.checkSlug(slug);
      if (mounted) {
        setState(() {
          _slugAvailable = result['available'] == true;
          _slugError =
              _slugAvailable! ? null : '이미 사용 중인 이름입니다';
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _slugError = '확인에 실패했습니다';
          _slugAvailable = null;
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isCheckingSlug = false);
      }
    }
  }

  Future<void> _pickFile({required bool isLicense}) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['jpg', 'jpeg', 'png', 'pdf'],
    );

    if (result != null && result.files.isNotEmpty && mounted) {
      final file = result.files.first;
      setState(() {
        if (isLicense) {
          _licenseFilePath = file.path;
          _licenseFileName = file.name;
        } else {
          _businessRegFilePath = file.path;
          _businessRegFileName = file.name;
        }
      });
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (_slugAvailable != true) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('영문 이름 중복 확인을 해주세요'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    if (_licenseFilePath == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('공인중개사 등록증을 첨부해주세요'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final authRepo = ref.read(authRepositoryProvider);
      final result = await authRepo.submitAgentRequest(
        agentName: _agentNameController.text.trim(),
        agentSlug: _slugController.text.trim().toLowerCase(),
        representativeName: _representativeController.text.trim(),
        phone: _phoneController.text.trim(),
        officeAddress: _addressController.text.trim(),
        licenseFilePath: _licenseFilePath!,
        businessRegFilePath: _businessRegFilePath,
      );

      if (!mounted) return;

      if (result['success'] == true) {
        ref.read(authProvider.notifier).completeAgentRequest();
        _showSuccessDialog();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? '신청에 실패했습니다'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('신청에 실패했습니다: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  void _showSuccessDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('신청 완료'),
        content: const Text(
          '공인중개사 가입 신청이 접수되었습니다.\n'
          '관리자 승인 후 Agent 기능이 활성화됩니다.\n'
          '승인 결과는 앱 알림으로 안내드립니다.',
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              this.context.go('/home');
            },
            child: const Text('확인'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('공인중개사 가입 신청'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/user-type'),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  '중개사무소 정보를 입력해주세요',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '관리자 확인 후 승인이 완료됩니다.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 24),

                // 중개사무소 상호
                TextFormField(
                  controller: _agentNameController,
                  decoration: const InputDecoration(
                    labelText: '중개사무소 상호 *',
                    hintText: '예: 금토끼부동산',
                    prefixIcon: Icon(Icons.business),
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? '상호를 입력해주세요' : null,
                ),
                const SizedBox(height: 16),

                // 영문 이름 + 중복 확인
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _slugController,
                        decoration: InputDecoration(
                          labelText: '영문 이름 (URL용) *',
                          hintText: '예: goldenrabbit',
                          prefixIcon: const Icon(Icons.link),
                          border: const OutlineInputBorder(),
                          helperText: _slugAvailable == true
                              ? '사용 가능한 이름입니다'
                              : null,
                          helperStyle: const TextStyle(color: Colors.green),
                          errorText: _slugError,
                          suffixIcon: _slugAvailable == true
                              ? const Icon(Icons.check_circle,
                                  color: Colors.green)
                              : null,
                        ),
                        onChanged: (_) {
                          if (_slugAvailable != null) {
                            setState(() {
                              _slugAvailable = null;
                              _slugError = null;
                            });
                          }
                        },
                        validator: (v) {
                          if (v == null || v.trim().isEmpty) {
                            return '영문 이름을 입력해주세요';
                          }
                          if (v.trim().length < 2) {
                            return '2자 이상 입력해주세요';
                          }
                          return null;
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: ElevatedButton(
                        onPressed: _isCheckingSlug ? null : _checkSlug,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 18,
                          ),
                        ),
                        child: _isCheckingSlug
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2),
                              )
                            : const Text('중복확인'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // 대표자 성명
                TextFormField(
                  controller: _representativeController,
                  decoration: const InputDecoration(
                    labelText: '대표자 성명 *',
                    hintText: '예: 홍길동',
                    prefixIcon: Icon(Icons.person),
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? '성명을 입력해주세요' : null,
                ),
                const SizedBox(height: 16),

                // 연락처
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: '연락처 *',
                    hintText: '예: 02-3471-7377',
                    prefixIcon: Icon(Icons.phone),
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? '연락처를 입력해주세요' : null,
                ),
                const SizedBox(height: 16),

                // 사무소 주소
                TextFormField(
                  controller: _addressController,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: '사무소 주소 *',
                    hintText: '예: 서울특별시 동작구 사당로16나길 55, 1층',
                    prefixIcon: Icon(Icons.location_on),
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? '주소를 입력해주세요' : null,
                ),
                const SizedBox(height: 24),

                // 첨부 파일 섹션
                Text(
                  '첨부 서류',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),

                // 공인중개사 등록증
                _buildFilePickerTile(
                  theme: theme,
                  label: '공인중개사 등록증 *',
                  fileName: _licenseFileName,
                  isRequired: true,
                  onPick: () => _pickFile(isLicense: true),
                  onRemove: () => setState(() {
                    _licenseFilePath = null;
                    _licenseFileName = null;
                  }),
                ),
                const SizedBox(height: 8),

                // 사업자등록증 (선택)
                _buildFilePickerTile(
                  theme: theme,
                  label: '사업자등록증 (선택)',
                  fileName: _businessRegFileName,
                  isRequired: false,
                  onPick: () => _pickFile(isLicense: false),
                  onRemove: () => setState(() {
                    _businessRegFilePath = null;
                    _businessRegFileName = null;
                  }),
                ),

                const SizedBox(height: 32),

                // 제출 버튼
                SizedBox(
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _isSubmitting ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
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
                            '가입 신청',
                            style: TextStyle(
                                fontSize: 16, fontWeight: FontWeight.w600),
                          ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFilePickerTile({
    required ThemeData theme,
    required String label,
    required String? fileName,
    required bool isRequired,
    required VoidCallback onPick,
    required VoidCallback onRemove,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(
          color: isRequired && fileName == null
              ? AppColors.gray300
              : AppColors.gray200,
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(
            fileName != null ? Icons.description : Icons.upload_file,
            color: fileName != null ? AppColors.primary : AppColors.gray400,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                if (fileName != null)
                  Text(
                    fileName,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w500,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
          if (fileName != null)
            IconButton(
              icon: const Icon(Icons.close, size: 18),
              onPressed: onRemove,
            )
          else
            TextButton(
              onPressed: onPick,
              child: const Text('파일 선택'),
            ),
        ],
      ),
    );
  }
}
