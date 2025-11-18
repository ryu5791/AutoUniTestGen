# MC/DC テスト実装 シーケンス図

## テスト実行フロー

```mermaid
sequenceDiagram
    participant Main as main()
    participant Unity as Unity Framework
    participant Setup as setUp()
    participant Test as Test Cases
    participant Eval as evaluate_condition()
    participant State as Global State
    participant Teardown as tearDown()

    Main->>Unity: UNITY_BEGIN()
    activate Unity

    loop For each test case (9 times)
        Unity->>Setup: Call setUp()
        activate Setup
        Setup->>State: Reset mState.dat = 0
        Setup->>State: Reset vHANDY_SET_POWERPON_SEQ = 0
        Setup->>State: Reset vHANDY_SET_OP_POWER_PUSH = 0
        Setup->>State: Reset test_condition_result = false
        Setup-->>Unity: Setup complete
        deactivate Setup

        Unity->>Test: RUN_TEST(test_mcdc_case_XX)
        activate Test

        Note over Test: Test Case Configuration
        Test->>State: Set mState.bit.act
        Test->>State: Set vHANDY_SET_POWERPON_SEQ
        Test->>State: Set vHANDY_SET_OP_POWER_PUSH

        Test->>Eval: evaluate_condition()
        activate Eval

        Eval->>State: Read mState.bit.act
        State-->>Eval: Return act value

        Eval->>State: Read vHANDY_SET_POWERPON_SEQ
        State-->>Eval: Return power-on sequence

        Eval->>State: Read vHANDY_SET_OP_POWER_PUSH
        State-->>Eval: Return power push value

        Note over Eval: Evaluate complex condition:<br/>(act == ACT_INIT) &&<br/>((seq == 1||2||3||6||7||8)) &&<br/>(push == 0)

        Eval-->>Test: Return boolean result
        deactivate Eval

        Test->>Test: TEST_ASSERT_TRUE/FALSE(result)

        Test-->>Unity: Test complete
        deactivate Test

        Unity->>Teardown: Call tearDown()
        activate Teardown
        Teardown->>State: Clean up (if needed)
        Teardown-->>Unity: Cleanup complete
        deactivate Teardown
    end

    Unity->>Main: Return test results
    deactivate Unity
    Main->>Main: UNITY_END()
```

## テストケース実行詳細

### Case 1: TTFFFFFT (Baseline)

```mermaid
sequenceDiagram
    participant Test as test_mcdc_case_01
    participant State as Global State
    participant Eval as evaluate_condition()

    Test->>State: mState.bit.act = ACT_INIT (2)
    Test->>State: vHANDY_SET_POWERPON_SEQ = 1
    Test->>State: vHANDY_SET_OP_POWER_PUSH = 0

    Test->>Eval: Call evaluate_condition()
    activate Eval

    Eval->>Eval: Check (mState.bit.act == ACT_INIT)<br/>✓ TRUE (2 == 2)
    Eval->>Eval: Check (seq == 1 || ... || 8)<br/>✓ TRUE (1 matches)
    Eval->>Eval: Check (push == 0)<br/>✓ TRUE (0 == 0)

    Eval->>Eval: Result: TRUE && TRUE && TRUE = TRUE
    Eval-->>Test: Return TRUE
    deactivate Eval

    Test->>Test: TEST_ASSERT_TRUE(TRUE)
    Note over Test: ✓ PASS
```

### Case 2: FTFFFFFT (C1 Independence)

```mermaid
sequenceDiagram
    participant Test as test_mcdc_case_02
    participant State as Global State
    participant Eval as evaluate_condition()

    Test->>State: mState.bit.act = ACT_NORMAL (0)
    Test->>State: vHANDY_SET_POWERPON_SEQ = 1
    Test->>State: vHANDY_SET_OP_POWER_PUSH = 0

    Test->>Eval: Call evaluate_condition()
    activate Eval

    Eval->>Eval: Check (mState.bit.act == ACT_INIT)<br/>✗ FALSE (0 != 2)
    Note over Eval: Short-circuit evaluation:<br/>First AND condition failed

    Eval->>Eval: Result: FALSE && ... && ... = FALSE
    Eval-->>Test: Return FALSE
    deactivate Eval

    Test->>Test: TEST_ASSERT_FALSE(FALSE)
    Note over Test: ✓ PASS<br/>Validates C1 independence
```

### Case 3: TFFFFFFT (OR Conditions)

```mermaid
sequenceDiagram
    participant Test as test_mcdc_case_03
    participant State as Global State
    participant Eval as evaluate_condition()

    Test->>State: mState.bit.act = ACT_INIT (2)
    Test->>State: vHANDY_SET_POWERPON_SEQ = 0
    Test->>State: vHANDY_SET_OP_POWER_PUSH = 0

    Test->>Eval: Call evaluate_condition()
    activate Eval

    Eval->>Eval: Check (mState.bit.act == ACT_INIT)<br/>✓ TRUE (2 == 2)
    Eval->>Eval: Check (seq == 1)<br/>✗ FALSE (0 != 1)
    Eval->>Eval: Check (seq == 2)<br/>✗ FALSE (0 != 2)
    Eval->>Eval: Check (seq == 3)<br/>✗ FALSE (0 != 3)
    Eval->>Eval: Check (seq == 6)<br/>✗ FALSE (0 != 6)
    Eval->>Eval: Check (seq == 7)<br/>✗ FALSE (0 != 7)
    Eval->>Eval: Check (seq == 8)<br/>✗ FALSE (0 != 8)
    Eval->>Eval: OR result: FALSE

    Eval->>Eval: Result: TRUE && FALSE && TRUE = FALSE
    Eval-->>Test: Return FALSE
    deactivate Eval

    Test->>Test: TEST_ASSERT_FALSE(FALSE)
    Note over Test: ✓ PASS<br/>Validates OR conditions
```

## MC/DC カバレッジ達成フロー

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Analyzer as Condition Analyzer
    participant Generator as Test Generator
    participant Validator as MC/DC Validator
    participant Report as Coverage Report

    Dev->>Analyzer: Provide condition:<br/>(C1) && (C2||C3||C4||C5||C6||C7) && (C8)
    activate Analyzer

    Analyzer->>Analyzer: Identify 8 atomic conditions
    Analyzer->>Analyzer: Map condition structure
    Analyzer-->>Generator: Condition breakdown
    deactivate Analyzer

    activate Generator
    Generator->>Generator: Generate truth table patterns
    Generator->>Generator: Create test case 1: TTFFFFFT
    Generator->>Generator: Create test case 2: FTFFFFFT (C1 toggle)
    Generator->>Generator: Create test case 3: TFFFFFFT (OR baseline)
    Generator->>Generator: Create test case 4: TTFFFFFF (C8 toggle)
    Generator->>Generator: Create test case 5: TFTFFFFT (C3 toggle)
    Generator->>Generator: Create test case 6: TFFTFFFT (C4 toggle)
    Generator->>Generator: Create test case 7: TFFFTFFT (C5 toggle)
    Generator->>Generator: Create test case 8: TFFFFTFT (C6 toggle)
    Generator->>Generator: Create test case 9: TFFFFFTT (C7 toggle)
    Generator-->>Validator: 9 test cases
    deactivate Generator

    activate Validator
    Validator->>Validator: Verify C1 independence<br/>(Case 1 vs Case 2)
    Validator->>Validator: Verify C2-C7 coverage<br/>(Cases 1,3,5,6,7,8,9)
    Validator->>Validator: Verify C8 independence<br/>(Case 1 vs Case 4)
    Validator->>Validator: Calculate coverage: 8/8 = 100%
    Validator-->>Report: MC/DC 100% achieved
    deactivate Validator

    activate Report
    Report->>Report: Generate truth table
    Report->>Report: Document independence proofs
    Report->>Report: Create test implementation
    Report-->>Dev: Complete MC/DC test suite
    deactivate Report
```

## テスト実行とカバレッジ検証

```mermaid
sequenceDiagram
    participant Runner as Test Runner
    participant Test1 as Test Case 1-9
    participant Coverage as Coverage Tool
    participant Validator as MC/DC Validator
    participant Report as Report Generator

    Runner->>Test1: Execute all 9 test cases
    activate Test1

    loop For each condition C1-C8
        Test1->>Coverage: Record condition evaluation
        Coverage->>Coverage: Track TRUE executions
        Coverage->>Coverage: Track FALSE executions
        Coverage->>Coverage: Track outcome changes
    end

    Test1-->>Runner: All tests PASS
    deactivate Test1

    Runner->>Coverage: Request coverage data
    activate Coverage
    Coverage->>Coverage: Analyze condition pairs
    Coverage-->>Validator: Coverage matrix
    deactivate Coverage

    activate Validator
    Validator->>Validator: Verify each condition toggles result independently
    Validator->>Validator: Confirm 100% MC/DC coverage
    Validator-->>Report: Coverage validated
    deactivate Validator

    activate Report
    Report->>Report: Generate MCDC_COVERAGE_REPORT.md
    Report->>Report: Document truth table
    Report->>Report: List all test cases
    Report-->>Runner: Final report
    deactivate Report
```

## まとめ

このシーケンス図は、MC/DC 100%カバレッジを達成するテスト実装の完全なフローを示しています：

1. **テスト実行フロー**: Unity フレームワークでの9つのテストケース実行
2. **個別テストケース**: 各テストケースの詳細な実行シーケンス
3. **MC/DC達成フロー**: 条件分析からテスト生成、カバレッジ検証まで
4. **検証フロー**: テスト実行後のカバレッジ検証とレポート生成

各シーケンスは、DO-178C規格のMC/DC要件を満たすために必要な全てのステップを含んでいます。
