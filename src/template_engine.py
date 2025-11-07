"""
テンプレートエンジンモジュール

カスタムテンプレートを使用してテストコードを生成する機能を提供します。
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from string import Template
from dataclasses import dataclass


@dataclass
class TemplateConfig:
    """テンプレート設定"""
    name: str
    description: str
    template_file: str
    variables: Dict[str, str]


class TemplateEngine:
    """テンプレートエンジンクラス"""
    
    # デフォルトテンプレート
    DEFAULT_TEST_TEMPLATE = """/* 
 * テストファイル: ${test_file_name}
 * 生成日時: ${generation_time}
 * テスト対象関数: ${function_name}
 */

#include "unity.h"
#include "${source_header}"

void setUp(void) {
    /* テスト前の初期化処理 */
${setup_code}
}

void tearDown(void) {
    /* テスト後のクリーンアップ処理 */
${teardown_code}
}

${test_cases}

int main(void) {
    UNITY_BEGIN();
${test_calls}
    return UNITY_END();
}
"""
    
    DEFAULT_TEST_CASE_TEMPLATE = """void ${test_function_name}(void) {
    /* テストケース: ${test_case_description} */
${test_body}
}
"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            template_dir: テンプレートディレクトリ
        """
        self.template_dir = Path(template_dir) if template_dir else None
        self.templates: Dict[str, str] = {}
        self.template_configs: Dict[str, TemplateConfig] = {}
        
        # デフォルトテンプレートを登録
        self.register_template('default_test', self.DEFAULT_TEST_TEMPLATE)
        self.register_template('default_test_case', self.DEFAULT_TEST_CASE_TEMPLATE)
    
    def register_template(self, name: str, template_str: str):
        """
        テンプレートを登録
        
        Args:
            name: テンプレート名
            template_str: テンプレート文字列
        """
        self.templates[name] = template_str
    
    def load_template(self, name: str, file_path: Optional[str] = None) -> str:
        """
        テンプレートを読み込む
        
        Args:
            name: テンプレート名
            file_path: テンプレートファイルパス（Noneの場合は登録済みテンプレートを使用）
        
        Returns:
            テンプレート文字列
        """
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_str = f.read()
            self.register_template(name, template_str)
            return template_str
        
        return self.templates.get(name, '')
    
    def render(self, template_name: str, variables: Dict[str, Any]) -> str:
        """
        テンプレートをレンダリング
        
        Args:
            template_name: テンプレート名
            variables: 変数の辞書
        
        Returns:
            レンダリング結果
        """
        template_str = self.templates.get(template_name)
        if not template_str:
            raise ValueError(f"テンプレート '{template_name}' が見つかりません")
        
        template = Template(template_str)
        
        # 変数を文字列に変換
        str_variables = {k: str(v) for k, v in variables.items()}
        
        try:
            return template.safe_substitute(**str_variables)
        except Exception as e:
            raise ValueError(f"テンプレートのレンダリングに失敗: {str(e)}")
    
    def load_template_config(self, config_file: str) -> TemplateConfig:
        """
        テンプレート設定ファイルを読み込む
        
        Args:
            config_file: 設定ファイルパス（JSON形式）
        
        Returns:
            テンプレート設定
        """
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = TemplateConfig(
            name=data['name'],
            description=data.get('description', ''),
            template_file=data['template_file'],
            variables=data.get('variables', {})
        )
        
        # テンプレートファイルを読み込む
        if self.template_dir:
            template_path = self.template_dir / config.template_file
        else:
            template_path = Path(config.template_file)
        
        self.load_template(config.name, str(template_path))
        self.template_configs[config.name] = config
        
        return config
    
    def list_templates(self) -> List[str]:
        """登録されているテンプレートのリストを取得"""
        return list(self.templates.keys())
    
    def get_template_variables(self, template_name: str) -> List[str]:
        """
        テンプレートで使用されている変数のリストを取得
        
        Args:
            template_name: テンプレート名
        
        Returns:
            変数名のリスト
        """
        template_str = self.templates.get(template_name, '')
        
        # ${}で囲まれた変数を抽出
        import re
        pattern = r'\$\{(\w+)\}'
        variables = re.findall(pattern, template_str)
        
        return list(set(variables))
    
    @staticmethod
    def create_template_config_file(
        output_file: str = "template_config.json",
        name: str = "custom_template",
        template_file: str = "custom_template.txt"
    ):
        """
        テンプレート設定ファイルのサンプルを作成
        
        Args:
            output_file: 出力ファイルパス
            name: テンプレート名
            template_file: テンプレートファイル名
        """
        config = {
            "name": name,
            "description": "カスタムテンプレートの説明",
            "template_file": template_file,
            "variables": {
                "test_file_name": "テストファイル名",
                "generation_time": "生成日時",
                "function_name": "テスト対象関数名",
                "source_header": "ソースヘッダーファイル",
                "setup_code": "セットアップコード",
                "teardown_code": "クリーンアップコード",
                "test_cases": "テストケース",
                "test_calls": "テスト呼び出し"
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"テンプレート設定ファイルを作成しました: {output_file}")
    
    @staticmethod
    def create_sample_template(output_file: str = "sample_template.txt"):
        """
        サンプルテンプレートファイルを作成
        
        Args:
            output_file: 出力ファイルパス
        """
        sample = """/*
 * ============================================================================
 * テストファイル: ${test_file_name}
 * 生成日時: ${generation_time}
 * ============================================================================
 */

#include "unity.h"
#include "${source_header}"

/* グローバル変数 */
${global_variables}

/* セットアップ関数 */
void setUp(void) {
${setup_code}
}

/* クリーンアップ関数 */
void tearDown(void) {
${teardown_code}
}

/* ============================================================================
 * テストケース - ${function_name}
 * ============================================================================
 */

${test_cases}

/* ============================================================================
 * メイン関数
 * ============================================================================
 */
int main(void) {
    UNITY_BEGIN();
${test_calls}
    return UNITY_END();
}
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sample)
        
        print(f"サンプルテンプレートファイルを作成しました: {output_file}")


class CustomTestGenerator:
    """カスタムテンプレートを使用したテストジェネレータ"""
    
    def __init__(self, template_engine: Optional[TemplateEngine] = None):
        """
        初期化
        
        Args:
            template_engine: テンプレートエンジン
        """
        self.template_engine = template_engine or TemplateEngine()
    
    def generate_with_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> str:
        """
        テンプレートを使用してテストコードを生成
        
        Args:
            template_name: テンプレート名
            variables: 変数の辞書
            output_file: 出力ファイルパス（Noneの場合は文字列として返す）
        
        Returns:
            生成されたテストコード
        """
        # テンプレートをレンダリング
        code = self.template_engine.render(template_name, variables)
        
        # ファイルに保存
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(code)
            print(f"テストコードを生成しました: {output_file}")
        
        return code
    
    def generate_test_case(
        self,
        test_name: str,
        description: str,
        test_body: str,
        template_name: str = 'default_test_case'
    ) -> str:
        """
        単一のテストケースを生成
        
        Args:
            test_name: テスト関数名
            description: テストケースの説明
            test_body: テスト本体
            template_name: 使用するテンプレート名
        
        Returns:
            生成されたテストケースコード
        """
        variables = {
            'test_function_name': test_name,
            'test_case_description': description,
            'test_body': test_body
        }
        
        return self.template_engine.render(template_name, variables)
    
    def generate_full_test_file(
        self,
        function_name: str,
        source_header: str,
        test_cases: List[Dict[str, str]],
        setup_code: str = "",
        teardown_code: str = "",
        template_name: str = 'default_test'
    ) -> str:
        """
        完全なテストファイルを生成
        
        Args:
            function_name: テスト対象関数名
            source_header: ソースヘッダーファイル名
            test_cases: テストケースのリスト（各要素は name, description, body を含む辞書）
            setup_code: セットアップコード
            teardown_code: クリーンアップコード
            template_name: 使用するテンプレート名
        
        Returns:
            生成されたテストファイルコード
        """
        from datetime import datetime
        
        # テストケースコードを生成
        test_cases_code = []
        test_calls_code = []
        
        for i, test_case in enumerate(test_cases, 1):
            case_code = self.generate_test_case(
                test_name=test_case.get('name', f'test_{function_name}_{i}'),
                description=test_case.get('description', f'Test case {i}'),
                test_body=test_case.get('body', '    TEST_FAIL_MESSAGE("Not implemented");')
            )
            test_cases_code.append(case_code)
            test_calls_code.append(f"    RUN_TEST({test_case.get('name', f'test_{function_name}_{i}')});")
        
        # 変数を設定
        variables = {
            'test_file_name': f'test_{function_name}.c',
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'function_name': function_name,
            'source_header': source_header,
            'setup_code': setup_code or '    /* 初期化なし */',
            'teardown_code': teardown_code or '    /* クリーンアップなし */',
            'test_cases': '\n'.join(test_cases_code),
            'test_calls': '\n'.join(test_calls_code),
            'global_variables': '/* グローバル変数なし */'
        }
        
        return self.template_engine.render(template_name, variables)


def create_template_files(output_dir: str = "templates"):
    """
    テンプレート関連のサンプルファイルを作成
    
    Args:
        output_dir: 出力ディレクトリ
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # テンプレートファイルを作成
    TemplateEngine.create_sample_template(str(output_path / "sample_template.txt"))
    
    # 設定ファイルを作成
    TemplateEngine.create_template_config_file(
        output_file=str(output_path / "template_config.json"),
        name="sample",
        template_file="sample_template.txt"
    )
    
    print(f"\nテンプレートファイルを作成しました: {output_dir}/")
    print("  - sample_template.txt")
    print("  - template_config.json")
