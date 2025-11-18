# MC/DC テスト実装 クラス図

## 全体構造

```mermaid
classDiagram
    class UnityFramework {
        +UNITY_BEGIN() void
        +RUN_TEST(func) void
        +UNITY_END() int
        +TEST_ASSERT_TRUE(condition) void
        +TEST_ASSERT_FALSE(condition) void
    }

    class TestSuite {
        +setUp() void
        +tearDown() void
        +test_mcdc_case_01_TTFFFFFT() void
        +test_mcdc_case_02_FTFFFFFT() void
        +test_mcdc_case_03_TFFFFFFT() void
        +test_mcdc_case_04_TTFFFFFF() void
        +test_mcdc_case_05_TFTFFFFT() void
        +test_mcdc_case_06_TFFTFFFT() void
        +test_mcdc_case_07_TFFFTFFT() void
        +test_mcdc_case_08_TFFFFTFT() void
        +test_mcdc_case_09_TFFFFFTT() void
        +main() int
    }

    class StateDefinition {
        +uint16_t dat
        +StateBitfield bit
    }

    class StateBitfield {
        +uint16_t state : 3
        +uint16_t act : 2
        +uint16_t half : 1
        +uint16_t rvs : 1
        +uint16_t handmv : 1
        +uint16_t stopsw : 1
        +uint16_t init : 1
        +uint16_t strk : 3
        +uint16_t test : 1
        +uint16_t error : 1
        +uint16_t safestop : 1
    }

    class HandyData {
        +HandyDataInfo info
    }

    class HandyDataInfo {
        +SpecialInfo special
        +DoorInfo door
        +NetlinkInfo netlink
    }

    class SpecialInfo {
        +SpecialInfoDetail info
    }

    class SpecialInfoDetail {
        +uint8_t af_power_on
    }

    class DoorInfo {
        +DoorInfoDetail info
    }

    class DoorInfoDetail {
        +uint8_t op_power_push
    }

    class NetlinkInfo {
        +NetlinkInfoDetail info
    }

    class NetlinkInfoDetail {
        +uint8_t unlock
    }

    class GlobalState {
        <<static>>
        +StateDefinition mState
        +HandyData mHandyData
        +bool test_condition_result
    }

    class ConditionEvaluator {
        +evaluate_condition() bool
    }

    class Constants {
        <<enumeration>>
        ACT_INIT = 2
        ACT_NORMAL = 0
        ACT_SETTING = 1
        ACT_GLITCH = 3
    }

    class Macros {
        <<define>>
        +vHANDY_SET_POWERPON_SEQ
        +vHANDY_SET_OP_POWER_PUSH
    }

    UnityFramework <|.. TestSuite : uses
    TestSuite --> GlobalState : modifies
    TestSuite --> ConditionEvaluator : calls
    GlobalState --> StateDefinition : contains
    GlobalState --> HandyData : contains
    StateDefinition --> StateBitfield : contains
    HandyData --> HandyDataInfo : contains
    HandyDataInfo --> SpecialInfo : contains
    HandyDataInfo --> DoorInfo : contains
    HandyDataInfo --> NetlinkInfo : contains
    SpecialInfo --> SpecialInfoDetail : contains
    DoorInfo --> DoorInfoDetail : contains
    NetlinkInfo --> NetlinkInfoDetail : contains
    ConditionEvaluator --> GlobalState : reads
    ConditionEvaluator --> Constants : uses
    ConditionEvaluator --> Macros : uses
```

## テストケースクラス階層

```mermaid
classDiagram
    class TestCase {
        <<abstract>>
        +pattern String
        +expected_result bool
        +execute() void
        +validate() void
    }

    class BaselineTest {
        +pattern "TTFFFFFT"
        +expected_result true
        +description "Baseline case: all conditions satisfied"
        +execute() void
    }

    class C1IndependenceTest {
        +pattern "FTFFFFFT"
        +expected_result false
        +description "Validates C1 (act) independence"
        +execute() void
    }

    class ORConditionsTest {
        +pattern "TFFFFFFT"
        +expected_result false
        +description "Validates OR conditions requirement"
        +execute() void
    }

    class C8IndependenceTest {
        +pattern "TTFFFFFF"
        +expected_result false
        +description "Validates C8 (power_push) independence"
        +execute() void
    }

    class C3IndependenceTest {
        +pattern "TFTFFFFT"
        +expected_result true
        +description "Validates C3 (seq==2) independence"
        +execute() void
    }

    class C4IndependenceTest {
        +pattern "TFFTFFFT"
        +expected_result true
        +description "Validates C4 (seq==3) independence"
        +execute() void
    }

    class C5IndependenceTest {
        +pattern "TFFFTFFT"
        +expected_result true
        +description "Validates C5 (seq==6) independence"
        +execute() void
    }

    class C6IndependenceTest {
        +pattern "TFFFFTFT"
        +expected_result true
        +description "Validates C6 (seq==7) independence"
        +execute() void
    }

    class C7IndependenceTest {
        +pattern "TFFFFFTT"
        +expected_result true
        +description "Validates C7 (seq==8) independence"
        +execute() void
    }

    TestCase <|-- BaselineTest
    TestCase <|-- C1IndependenceTest
    TestCase <|-- ORConditionsTest
    TestCase <|-- C8IndependenceTest
    TestCase <|-- C3IndependenceTest
    TestCase <|-- C4IndependenceTest
    TestCase <|-- C5IndependenceTest
    TestCase <|-- C6IndependenceTest
    TestCase <|-- C7IndependenceTest
```

## 条件評価構造

```mermaid
classDiagram
    class Condition {
        <<abstract>>
        +id String
        +evaluate() bool
        +toString() String
    }

    class ANDCondition {
        +List~Condition~ conditions
        +evaluate() bool
        +toString() String
    }

    class ORCondition {
        +List~Condition~ conditions
        +evaluate() bool
        +toString() String
    }

    class AtomicCondition {
        +variable String
        +operator String
        +value Any
        +evaluate() bool
        +toString() String
    }

    class C1_ActInit {
        +variable "mState.bit.act"
        +operator "=="
        +value ACT_INIT
        +evaluate() bool
    }

    class C2_Seq1 {
        +variable "vHANDY_SET_POWERPON_SEQ"
        +operator "=="
        +value 1
        +evaluate() bool
    }

    class C3_Seq2 {
        +variable "vHANDY_SET_POWERPON_SEQ"
        +operator "=="
        +value 2
        +evaluate() bool
    }

    class C4_Seq3 {
        +variable "vHANDY_SET_POWERPON_SEQ"
        +operator "=="
        +value 3
        +evaluate() bool
    }

    class C5_Seq6 {
        +variable "vHANDY_SET_POWERPON_SEQ"
        +operator "=="
        +value 6
        +evaluate() bool
    }

    class C6_Seq7 {
        +variable "vHANDY_SET_POWERPON_SEQ"
        +operator "=="
        +value 7
        +evaluate() bool
    }

    class C7_Seq8 {
        +variable "vHANDY_SET_POWERPON_SEQ"
        +operator "=="
        +value 8
        +evaluate() bool
    }

    class C8_PowerPush0 {
        +variable "vHANDY_SET_OP_POWER_PUSH"
        +operator "=="
        +value 0
        +evaluate() bool
    }

    class ComplexCondition {
        +rootCondition ANDCondition
        +evaluate() bool
        +getCoverage() float
    }

    Condition <|-- ANDCondition
    Condition <|-- ORCondition
    Condition <|-- AtomicCondition
    AtomicCondition <|-- C1_ActInit
    AtomicCondition <|-- C2_Seq1
    AtomicCondition <|-- C3_Seq2
    AtomicCondition <|-- C4_Seq3
    AtomicCondition <|-- C5_Seq6
    AtomicCondition <|-- C6_Seq7
    AtomicCondition <|-- C7_Seq8
    AtomicCondition <|-- C8_PowerPush0
    ANDCondition "1" *-- "3" Condition : contains
    ORCondition "1" *-- "6" AtomicCondition : contains C2-C7
    ComplexCondition --> ANDCondition : uses
```

## MC/DC カバレッジ分析構造

```mermaid
classDiagram
    class MCDCAnalyzer {
        +List~Condition~ conditions
        +List~TestCase~ testCases
        +analyzeIndependence() Map
        +calculateCoverage() float
        +generateReport() String
    }

    class ConditionPair {
        +TestCase trueCase
        +TestCase falseCase
        +Condition targetCondition
        +bool isIndependent
        +validate() bool
    }

    class CoverageMatrix {
        +int[8][9] matrix
        +recordEvaluation(condId, testId, value) void
        +getConditionCoverage(condId) float
        +getTotalCoverage() float
    }

    class IndependenceProof {
        +String conditionId
        +TestCase pairA
        +TestCase pairB
        +bool resultDiffers
        +bool otherConditionsSame
        +bool isValid
        +verify() bool
        +toString() String
    }

    class TruthTable {
        +int rows
        +int columns
        +bool[][] values
        +bool[] results
        +addRow(values, result) void
        +verify() bool
        +toString() String
    }

    class CoverageReport {
        +TruthTable table
        +List~IndependenceProof~ proofs
        +float coverage
        +generateMarkdown() String
        +exportToFile(path) void
    }

    MCDCAnalyzer --> ConditionPair : creates
    MCDCAnalyzer --> CoverageMatrix : uses
    MCDCAnalyzer --> IndependenceProof : generates
    MCDCAnalyzer --> TruthTable : builds
    MCDCAnalyzer --> CoverageReport : produces
    ConditionPair --> IndependenceProof : validates
    CoverageMatrix --> TruthTable : populates
    CoverageReport --> TruthTable : includes
    CoverageReport --> IndependenceProof : documents
```

## データフロー構造

```mermaid
classDiagram
    class TestInput {
        +uint8_t act_value
        +uint8_t powerpon_seq
        +uint8_t op_power_push
        +applyToState() void
    }

    class TestOutput {
        +bool condition_result
        +bool assertion_passed
        +String error_message
        +validate() bool
    }

    class TestContext {
        +TestInput input
        +TestOutput output
        +StateDefinition snapshot_before
        +StateDefinition snapshot_after
        +setup() void
        +execute() void
        +teardown() void
    }

    class TestResult {
        +String test_name
        +String pattern
        +bool passed
        +long execution_time_ms
        +String details
    }

    class TestReport {
        +List~TestResult~ results
        +int total_tests
        +int passed_tests
        +int failed_tests
        +float coverage_percentage
        +generateSummary() String
    }

    TestContext --> TestInput : contains
    TestContext --> TestOutput : contains
    TestContext --> StateDefinition : snapshots
    TestContext --> TestResult : produces
    TestReport "1" *-- "*" TestResult : aggregates
```

## 関係図の説明

### 1. 全体構造
- **UnityFramework**: テストフレームワークの基盤
- **TestSuite**: 9つのテストケースを実装
- **GlobalState**: テスト対象の状態を保持
- **ConditionEvaluator**: 条件式を評価

### 2. テストケースクラス階層
- 各テストケースは抽象クラス `TestCase` を継承
- 9つの具体的なテストケースがそれぞれの独立性を検証

### 3. 条件評価構造
- **ComplexCondition**: 複合条件全体を表現
- **ANDCondition**: AND演算子でつながる条件
- **ORCondition**: OR演算子でつながる6つの条件 (C2-C7)
- **AtomicCondition**: 8つの原子的条件 (C1-C8)

### 4. MC/DC カバレッジ分析構造
- **MCDCAnalyzer**: カバレッジ分析のコア
- **ConditionPair**: 条件の独立性を検証するペア
- **CoverageMatrix**: 各条件の評価結果を記録
- **IndependenceProof**: 各条件の独立性証明
- **TruthTable**: 真偽表の表現
- **CoverageReport**: 最終レポート生成

### 5. データフロー構造
- **TestInput**: テストケースの入力データ
- **TestOutput**: テスト実行結果
- **TestContext**: テスト実行のコンテキスト
- **TestResult**: 個別テスト結果
- **TestReport**: 全体のテストレポート

## クラス間の主要な関係

1. **使用関係 (uses)**
   - TestSuite は UnityFramework を使用
   - ConditionEvaluator は GlobalState を読み取り

2. **包含関係 (contains)**
   - GlobalState は StateDefinition と HandyData を包含
   - StateDefinition は StateBitfield を包含
   - HandyData は複数の情報構造を階層的に包含

3. **継承関係 (inherits)**
   - 9つのテストケースは TestCase を継承
   - 8つの原子条件は AtomicCondition を継承

4. **生成関係 (creates/produces)**
   - MCDCAnalyzer は各種分析オブジェクトを生成
   - TestContext は TestResult を生成

## まとめ

この構造により、以下が達成されています：

- **明確な責任分離**: 各クラスが明確な役割を持つ
- **拡張性**: 新しいテストケースや条件を容易に追加可能
- **保守性**: 階層化により変更の影響範囲が限定的
- **テスト性**: 各コンポーネントを独立してテスト可能
- **MC/DC準拠**: DO-178C規格のMC/DC要件を満たす設計
