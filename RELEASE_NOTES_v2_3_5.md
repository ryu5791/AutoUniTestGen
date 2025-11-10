# AutoUniTestGen v2.3.5 リリースノート

## 🗓️ リリース日
2025年11月10日

## 🎯 概要
Windows環境でのImportError問題を修正

## 🐛 バグ修正

### 1. Windows環境でのImportError修正
**問題**: Windows環境で実行時に以下のエラーが発生していました：
```
Exception has occurred: ImportError
attempted relative import with no known parent package
```

**原因**: 
- 相対インポートと絶対インポートの混在
- Windows環境でのパス解決の問題
- PYTHONPATHの設定不足

**修正内容**:
1. **main.pyの改善**
   - より確実なパス設定処理を追加
   - Windows環境での動作を考慮したPYTHONPATH設定
   
2. **cli.pyのインポート処理改善**
   - 3段階のフォールバック処理を実装
   - 相対インポート → 直接インポート → 絶対インポート
   - SystemErrorも捕捉するように修正

3. **実行環境サポートの追加**
   - `run.bat`: Windows用実行バッチファイル
   - `debug_import.py`: インポート問題診断スクリプト
   - `src/__init__.py`: パッケージ定義の明確化

### 2. 構造体メンバー比較の初期化コード生成問題（v2.3.4から継続）
- 前バージョンの修正内容を維持

## 🆕 新機能

### デバッグサポートツール
- `debug_import.py`: インポートエラーの診断が可能
- 環境情報、パス情報、インポートテストを実行

## 📝 使用方法

### Windows環境での実行方法

#### 方法1: run.batを使用
```batch
run.bat -i your_file.c -f your_function -o output_dir
```

#### 方法2: main.pyを直接実行
```batch
python main.py -i your_file.c -f your_function -o output_dir
```

#### 方法3: cli.pyを直接実行（非推奨）
```batch
cd src
python cli.py -i your_file.c -f your_function -o output_dir
```

### インポートエラーが発生した場合
```batch
python debug_import.py
```
診断結果を確認して、必要に応じてPYTHONPATHを設定してください。

## 🔧 技術的詳細

### 修正ファイル
- `main.py`: パス設定処理の強化
- `src/cli.py`: インポート処理の改善
- `src/__init__.py`: パッケージ定義の追加

### 新規ファイル
- `run.bat`: Windows用実行スクリプト
- `debug_import.py`: デバッグ診断スクリプト

## ⚠️ 注意事項

### Python環境
- Python 3.8以上が必要
- Windows環境ではPython 3.13でテスト済み

### パス関連
- スペースを含むパスは避けることを推奨
- 日本語を含むパスでも動作しますが、エンコーディングに注意

## 📊 影響範囲
- すべてのWindows環境でのImportError問題が解決
- Linux/Mac環境での動作に影響なし

## 🙏 謝辞
Windows環境でのエラー報告と詳細なスタックトレースを提供していただいたユーザーの皆様に感謝いたします。

---

## 📚 関連ドキュメント
- [v2.3.4 リリースノート](RELEASE_NOTES_v2_3_4.md)
- [v2.3.3 リリースノート](RELEASE_NOTES_v2_3_3.md)
