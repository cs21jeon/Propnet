import 'package:pdf/pdf.dart';

/// PDF 스타일 상수
class PdfStyles {
  PdfStyles._();

  // 색상
  static const PdfColor primary = PdfColor.fromInt(0xFF136dec);
  static const PdfColor dark = PdfColor.fromInt(0xFF334155);
  static const PdfColor gray = PdfColor.fromInt(0xFF64748b);
  static const PdfColor lightGray = PdfColor.fromInt(0xFF94a3b8);
  static const PdfColor bgLight = PdfColor.fromInt(0xFFf8fafc);
  static const PdfColor border = PdfColor.fromInt(0xFFe2e8f0);
  static const PdfColor blueBg = PdfColor.fromInt(0xFFeff6ff);
  static const PdfColor greenBg = PdfColor.fromInt(0xFFf0fdf4);
  static const PdfColor green = PdfColor.fromInt(0xFF22c55e);
  static const PdfColor purpleBg = PdfColor.fromInt(0xFFfaf5ff);
  static const PdfColor purple = PdfColor.fromInt(0xFF9333ea);
  static const PdfColor orangeBg = PdfColor.fromInt(0xFFfff7ed);
  static const PdfColor orange = PdfColor.fromInt(0xFFea580c);
  static const PdfColor white = PdfColors.white;
  static const PdfColor black = PdfColors.black;

  // 폰트 크기
  static const double fontSizeTitle = 18;
  static const double fontSizeSubtitle = 14;
  static const double fontSizeHeading = 12;
  static const double fontSizeBody = 10;
  static const double fontSizeSmall = 9;
  static const double fontSizeCaption = 8;

  // 간격
  static const double paddingSmall = 4;
  static const double paddingMedium = 8;
  static const double paddingLarge = 12;
  static const double paddingXLarge = 16;

  // 테이블
  static const double tableCellPadding = 6;
  static const double tableHeaderHeight = 24;
  static const double tableRowHeight = 20;
}
