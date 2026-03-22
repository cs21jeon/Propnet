import 'package:flutter/services.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

/// PDF 폰트 로딩 유틸리티
class PdfFonts {
  pw.Font? _regular;
  pw.Font? _bold;

  pw.Font get regular => _regular ?? pw.Font.helvetica();
  pw.Font get bold => _bold ?? pw.Font.helveticaBold();

  bool _isLoaded = false;
  bool get isLoaded => _isLoaded;

  /// 폰트를 로드합니다.
  Future<void> load() async {
    if (_isLoaded) return;

    try {
      final regularData =
          await rootBundle.load('assets/fonts/NotoSansKR-Regular.ttf');
      final boldData =
          await rootBundle.load('assets/fonts/NotoSansKR-Bold.ttf');

      _regular = pw.Font.ttf(regularData);
      _bold = pw.Font.ttf(boldData);
      _isLoaded = true;
    } catch (e) {
      print('Failed to load fonts: $e');
      // 기본 폰트 사용 (fallback)
      _regular = pw.Font.helvetica();
      _bold = pw.Font.helveticaBold();
      _isLoaded = true;
    }
  }

  /// 텍스트 스타일을 생성합니다.
  pw.TextStyle style({
    double fontSize = 10,
    bool isBold = false,
    PdfColor? color,
  }) {
    return pw.TextStyle(
      font: isBold ? bold : regular,
      fontBold: bold,
      fontSize: fontSize,
      color: color,
    );
  }
}
