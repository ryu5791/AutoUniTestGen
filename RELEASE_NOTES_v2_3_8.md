# AutoUniTestGen v2.3.8 リリースノート

**リリース日**: 2025年11月12日

## 🎯 主な変更点

### 🐛 重大なバグ修正: "Directives not supported yet" エラーの完全修正

**問題**: pycparserがプリプロセッサディレクティブでエラーを出す

**修正内容**:
1. preprocessor.py: ディレクティブをコメント化ではなく完全削除
2. standard_types.h: ディレクティブとコメントを削除
3. ast_builder.py: 埋め込みマクロ定義を空文字列に変更

**結果**: ✅ AST解析が正常に動作

---
**作成者**: Claude  
**バージョン**: v2.3.8
