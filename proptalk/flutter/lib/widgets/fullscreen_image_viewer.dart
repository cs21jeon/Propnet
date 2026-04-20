import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

/// 카카오톡 스타일 풀스크린 이미지 뷰어
/// - 검정 배경 + 핀치 줌/패닝
/// - 상단: 닫기(X) + 파일명 + 다운로드
class FullscreenImageViewer extends StatelessWidget {
  final String imageUrl;
  final Map<String, String> headers;
  final String? fileName;
  final String? driveUrl;

  const FullscreenImageViewer({
    super.key,
    required this.imageUrl,
    this.headers = const {},
    this.fileName,
    this.driveUrl,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.black54,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: fileName != null
            ? Text(
                fileName!,
                style: const TextStyle(color: Colors.white, fontSize: 14),
                overflow: TextOverflow.ellipsis,
              )
            : null,
        actions: [
          if (driveUrl != null && driveUrl!.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.open_in_new, color: Colors.white),
              tooltip: 'Drive에서 열기',
              onPressed: () async {
                final uri = Uri.parse(driveUrl!);
                await launchUrl(uri, mode: LaunchMode.externalApplication);
              },
            ),
        ],
      ),
      body: Center(
        child: InteractiveViewer(
          minScale: 0.5,
          maxScale: 4.0,
          child: Image.network(
            imageUrl,
            headers: headers,
            fit: BoxFit.contain,
            loadingBuilder: (ctx, child, progress) {
              if (progress == null) return child;
              return Center(
                child: CircularProgressIndicator(
                  value: progress.expectedTotalBytes != null
                      ? progress.cumulativeBytesLoaded /
                          progress.expectedTotalBytes!
                      : null,
                  color: Colors.white,
                ),
              );
            },
            errorBuilder: (ctx, err, stack) => const Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.broken_image, color: Colors.white54, size: 64),
                SizedBox(height: 16),
                Text('이미지를 불러올 수 없습니다',
                    style: TextStyle(color: Colors.white54)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
