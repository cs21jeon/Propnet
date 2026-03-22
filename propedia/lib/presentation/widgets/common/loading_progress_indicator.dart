import 'dart:async';
import 'package:flutter/material.dart';
import 'skeleton_loading.dart';

/// 로딩 단계 정보
class _LoadingStep {
  final String message;
  final int startSeconds;

  const _LoadingStep({
    required this.message,
    required this.startSeconds,
  });
}

/// 시간 기반 로딩 프로그레스 위젯
/// 스켈레톤 UI와 단계별 메시지를 함께 표시
class LoadingProgressIndicator extends StatefulWidget {
  const LoadingProgressIndicator({super.key});

  @override
  State<LoadingProgressIndicator> createState() =>
      _LoadingProgressIndicatorState();
}

class _LoadingProgressIndicatorState extends State<LoadingProgressIndicator> {
  Timer? _timer;
  int _elapsedSeconds = 0;
  int _currentStep = 0;

  // 시간 기반 단계별 메시지 (서버 호출 없이 클라이언트에서만 처리)
  static const List<_LoadingStep> _steps = [
    _LoadingStep(
      message: '건축물 정보 조회 중...',
      startSeconds: 0,
    ),
    _LoadingStep(
      message: '토지 정보 확인 중...',
      startSeconds: 3,
    ),
    _LoadingStep(
      message: '전유부 정보 조회 중...',
      startSeconds: 8,
    ),
    _LoadingStep(
      message: '대지지분 계산 중...',
      startSeconds: 15,
    ),
    _LoadingStep(
      message: '데이터 정리 중...',
      startSeconds: 25,
    ),
    _LoadingStep(
      message: '거의 완료되었습니다...',
      startSeconds: 40,
    ),
  ];

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() {
        _elapsedSeconds = timer.tick;

        // 경과 시간에 따라 현재 단계 찾기
        for (int i = _steps.length - 1; i >= 0; i--) {
          if (_elapsedSeconds >= _steps[i].startSeconds) {
            _currentStep = i;
            break;
          }
        }
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // 스켈레톤 UI
        const Expanded(child: ResultScreenSkeleton()),

        // 하단 진행 상황 메시지
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 8,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: SafeArea(
            top: false,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  _steps[_currentStep].message,
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
