"""
ExcelWriterモジュール

Excelファイルの書き込み
"""

import sys
import os
from typing import List, Dict, Any
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger, ensure_directory
from src.data_structures import TruthTableData, IOTableData


class ExcelWriter:
    """Excelライター"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
    
    def write_truth_table(self, data: TruthTableData, filepath: str) -> None:
        """
        真偽表をExcelファイルに書き込み
        
        Args:
            data: 真偽表データ
            filepath: 出力ファイルパス
        """
        self.logger.info(f"真偽表をExcelに書き込み: {filepath}")
        
        # ディレクトリを確保
        ensure_directory(os.path.dirname(filepath))
        
        # Workbookを作成
        wb = Workbook()
        ws = wb.active
        ws.title = "真偽表"
        
        # Excel形式のデータを取得
        excel_data = data.to_excel_format()
        
        # ヘッダー行のスタイル
        header_font = Font(bold=True, size=11)
        header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
        
        # 罫線
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # データを書き込み
        for row_idx, row_data in enumerate(excel_data, 1):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # ヘッダー行のスタイル適用
                if row_idx == 1:
                    cell.font = header_font
                    cell.fill = header_fill
        
        # 列幅を調整
        ws.column_dimensions['A'].width = 8   # No.
        ws.column_dimensions['B'].width = 12  # 真偽
        ws.column_dimensions['C'].width = 50  # 判定文
        ws.column_dimensions['D'].width = 30  # 期待値
        
        # 保存
        wb.save(filepath)
        self.logger.info(f"真偽表の書き込みが完了: {len(data.test_cases)}行")
    
    def write_io_table(self, data: IOTableData, filepath: str) -> None:
        """
        I/O表をExcelファイルに書き込み
        
        Args:
            data: I/O表データ
            filepath: 出力ファイルパス
        """
        self.logger.info(f"I/O表をExcelに書き込み: {filepath}")
        
        # ディレクトリを確保
        ensure_directory(os.path.dirname(filepath))
        
        # Workbookを作成
        wb = Workbook()
        ws = wb.active
        ws.title = "IO表"
        
        # Excel形式のデータを取得
        excel_data = data.to_excel_format()
        
        if len(excel_data) < 2:
            self.logger.warning("I/O表のデータが不足しています")
            return
        
        # スタイル定義
        header_font = Font(bold=True, size=11)
        input_fill = PatternFill(start_color="E7F4FF", end_color="E7F4FF", fill_type="solid")
        output_fill = PatternFill(start_color="FFE7E7", end_color="FFE7E7", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # データを書き込み
        for row_idx, row_data in enumerate(excel_data, 1):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # ヘッダー行1（input/output）
                if row_idx == 1:
                    cell.font = header_font
                    if value == 'input':
                        cell.fill = input_fill
                    elif value == 'output':
                        cell.fill = output_fill
                
                # ヘッダー行2（変数名）
                elif row_idx == 2:
                    cell.font = header_font
                    
                    # input列かoutput列かを判定
                    if col_idx > 2:
                        header1_value = excel_data[0][col_idx - 1]
                        if header1_value == 'input':
                            cell.fill = input_fill
                        elif header1_value == 'output':
                            cell.fill = output_fill
        
        # 列幅を調整
        ws.column_dimensions['A'].width = 8   # No
        ws.column_dimensions['B'].width = 25  # テスト名
        
        # 入出力変数の列幅
        for col_idx in range(3, len(excel_data[0]) + 1):
            ws.column_dimensions[chr(64 + col_idx)].width = 12
        
        # 1行目と2行目をマージ（No、テスト名列）
        if len(excel_data) >= 2:
            ws.merge_cells('A1:A2')
            ws.merge_cells('B1:B2')
        
        # 保存
        wb.save(filepath)
        self.logger.info(f"I/O表の書き込みが完了: {len(data.test_data)}行")
    
    def format_cell(self, ws, row: int, col: int, style: Dict[str, Any]) -> None:
        """
        セルのフォーマットを設定
        
        Args:
            ws: ワークシート
            row: 行番号
            col: 列番号
            style: スタイル辞書
        """
        cell = ws.cell(row=row, column=col)
        
        if 'font' in style:
            cell.font = style['font']
        
        if 'fill' in style:
            cell.fill = style['fill']
        
        if 'border' in style:
            cell.border = style['border']
        
        if 'alignment' in style:
            cell.alignment = style['alignment']


if __name__ == "__main__":
    # ExcelWriterのテスト
    print("=== ExcelWriter のテスト ===\n")
    
    from src.data_structures import TruthTableData, TestCase, IOTableData
    
    # テスト1: 真偽表の書き込み
    print("1. 真偽表のテスト")
    
    # テストデータを作成
    truth_table = TruthTableData(
        function_name="test_func",
        test_cases=[
            TestCase(no=1, truth="T", condition="if (v10 > 30)", expected="v10 = 31"),
            TestCase(no=2, truth="F", condition="if (v10 > 30)", expected="v10 = 30"),
            TestCase(no=3, truth="TF", condition="if ((mx63 == m47) || (mx63 == m46))", expected="左辺が真"),
            TestCase(no=4, truth="FT", condition="if ((mx63 == m47) || (mx63 == m46))", expected="右辺が真"),
            TestCase(no=5, truth="FF", condition="if ((mx63 == m47) || (mx63 == m46))", expected="両方偽"),
        ],
        total_tests=5
    )
    
    writer = ExcelWriter()
    output_path = "/tmp/truth_table_test.xlsx"
    writer.write_truth_table(truth_table, output_path)
    print(f"   ✓ 真偽表を出力: {output_path}")
    print()
    
    # テスト2: I/O表の書き込み
    print("2. I/O表のテスト")
    
    # テストデータを作成
    io_table = IOTableData(
        input_variables=['v10', 'mx63', 'v9'],
        output_variables=['result', 'status'],
        test_data=[
            {
                'test_name': 'test_01_v10_gt_30_T',
                'inputs': {'v10': 31, 'mx63': 'm47', 'v9': 0},
                'outputs': {'result': 1, 'status': 'OK'}
            },
            {
                'test_name': 'test_02_v10_gt_30_F',
                'inputs': {'v10': 30, 'mx63': 'm47', 'v9': 0},
                'outputs': {'result': 0, 'status': 'NG'}
            },
            {
                'test_name': 'test_03_mx63_eq_m47_TF',
                'inputs': {'v10': '-', 'mx63': 'm47', 'v9': 1},
                'outputs': {'result': 1, 'status': '-'}
            }
        ]
    )
    
    output_path2 = "/tmp/io_table_test.xlsx"
    writer.write_io_table(io_table, output_path2)
    print(f"   ✓ I/O表を出力: {output_path2}")
    print()
    
    print("✓ ExcelWriterが正常に動作しました")
    print(f"\n生成されたファイル:")
    print(f"  - {output_path}")
    print(f"  - {output_path2}")
