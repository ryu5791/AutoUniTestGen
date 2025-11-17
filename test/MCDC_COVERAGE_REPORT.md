# MC/DC カバレッジレポート

## 対象条件式

```c
if ((mState.bit.act == ACT_INIT) &&
    ((vHANDY_SET_POWERPON_SEQ == 1) || (vHANDY_SET_POWERPON_SEQ == 2) || (vHANDY_SET_POWERPON_SEQ == 3) ||
     (vHANDY_SET_POWERPON_SEQ == 6) || (vHANDY_SET_POWERPON_SEQ == 7) || (vHANDY_SET_POWERPON_SEQ == 8)) &&
    (vHANDY_SET_OP_POWER_PUSH == 0))
```

## 条件の分解

| 条件番号 | 条件式 | 説明 |
|---------|--------|------|
| C1 | `mState.bit.act == ACT_INIT` | 状態がACT_INITであること |
| C2 | `vHANDY_SET_POWERPON_SEQ == 1` | パワーオンシーケンスが1 |
| C3 | `vHANDY_SET_POWERPON_SEQ == 2` | パワーオンシーケンスが2 |
| C4 | `vHANDY_SET_POWERPON_SEQ == 3` | パワーオンシーケンスが3 |
| C5 | `vHANDY_SET_POWERPON_SEQ == 6` | パワーオンシーケンスが6 |
| C6 | `vHANDY_SET_POWERPON_SEQ == 7` | パワーオンシーケンスが7 |
| C7 | `vHANDY_SET_POWERPON_SEQ == 8` | パワーオンシーケンスが8 |
| C8 | `vHANDY_SET_OP_POWER_PUSH == 0` | オープンパワープッシュが0 |

## MC/DC 100% カバレッジ真偽表

| テストケース | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | 期待結果 | 検証内容 |
|-------------|----|----|----|----|----|----|----|----|---------|----------|
| Case 1 | T | T | F | F | F | F | F | T | **TRUE** | 基本パターン（全条件満足） |
| Case 2 | **F** | T | F | F | F | F | F | T | **FALSE** | **C1の独立性を検証** |
| Case 3 | T | **F** | **F** | **F** | **F** | **F** | **F** | T | **FALSE** | **C2-C7のOR条件を検証** |
| Case 4 | T | T | F | F | F | F | F | **F** | **FALSE** | **C8の独立性を検証** |
| Case 5 | T | F | **T** | F | F | F | F | T | **TRUE** | **C3の独立性を検証** |
| Case 6 | T | F | F | **T** | F | F | F | T | **TRUE** | **C4の独立性を検証** |
| Case 7 | T | F | F | F | **T** | F | F | T | **TRUE** | **C5の独立性を検証** |
| Case 8 | T | F | F | F | F | **T** | F | T | **TRUE** | **C6の独立性を検証** |
| Case 9 | T | F | F | F | F | F | **T** | T | **TRUE** | **C7の独立性を検証** |

## MC/DC要件の達成状況

### ✅ カバレッジ達成項目

1. **C1 (mState.bit.act == ACT_INIT) の独立性**
   - Case 1 (T) vs Case 2 (F): 結果が TRUE → FALSE に変化
   - C1が独立して結果に影響することを証明

2. **C2 (vHANDY_SET_POWERPON_SEQ == 1) の独立性**
   - Case 1 (C2=T, 他のOR条件=F) vs Case 3 (全OR条件=F): 結果が TRUE → FALSE に変化
   - C2が独立して結果に影響することを証明

3. **C3 (vHANDY_SET_POWERPON_SEQ == 2) の独立性**
   - Case 5 (C3=T, 他のOR条件=F) vs Case 3 (全OR条件=F): 結果が TRUE → FALSE に変化
   - C3が独立して結果に影響することを証明

4. **C4 (vHANDY_SET_POWERPON_SEQ == 3) の独立性**
   - Case 6 (C4=T, 他のOR条件=F) vs Case 3 (全OR条件=F): 結果が TRUE → FALSE に変化
   - C4が独立して結果に影響することを証明

5. **C5 (vHANDY_SET_POWERPON_SEQ == 6) の独立性**
   - Case 7 (C5=T, 他のOR条件=F) vs Case 3 (全OR条件=F): 結果が TRUE → FALSE に変化
   - C5が独立して結果に影響することを証明

6. **C6 (vHANDY_SET_POWERPON_SEQ == 7) の独立性**
   - Case 8 (C6=T, 他のOR条件=F) vs Case 3 (全OR条件=F): 結果が TRUE → FALSE に変化
   - C6が独立して結果に影響することを証明

7. **C7 (vHANDY_SET_POWERPON_SEQ == 8) の独立性**
   - Case 9 (C7=T, 他のOR条件=F) vs Case 3 (全OR条件=F): 結果が TRUE → FALSE に変化
   - C7が独立して結果に影響することを証明

8. **C8 (vHANDY_SET_OP_POWER_PUSH == 0) の独立性**
   - Case 1 (C8=T) vs Case 4 (C8=F): 結果が TRUE → FALSE に変化
   - C8が独立して結果に影響することを証明

## テスト実装

テストケースは `test_state_fullopen_func.c` に実装されています。

### テストケース関数名

1. `test_mcdc_case_01_TTFFFFFT()` - TTFFFFFT → TRUE
2. `test_mcdc_case_02_FTFFFFFT()` - FTFFFFFT → FALSE
3. `test_mcdc_case_03_TFFFFFFT()` - TFFFFFFT → FALSE
4. `test_mcdc_case_04_TTFFFFFF()` - TTFFFFFF → FALSE
5. `test_mcdc_case_05_TFTFFFFT()` - TFTFFFFT → TRUE
6. `test_mcdc_case_06_TFFTFFFT()` - TFFTFFFT → TRUE
7. `test_mcdc_case_07_TFFFTFFT()` - TFFFTFFT → TRUE
8. `test_mcdc_case_08_TFFFFTFT()` - TFFFFTFT → TRUE
9. `test_mcdc_case_09_TFFFFFTT()` - TFFFFFTT → TRUE

## MC/DCカバレッジ: 100%

全ての条件（C1～C8）が独立して結果に影響を与えることを検証できています。

## テスト実行方法

```bash
# Unity テストフレームワークでコンパイル
gcc -I/path/to/unity/src \
    test_state_fullopen_func.c \
    /path/to/unity/src/unity.c \
    -o test_state_fullopen_func

# テスト実行
./test_state_fullopen_func
```

## 参考資料

- MC/DC (Modified Condition/Decision Coverage): 各条件が独立して結果に影響を与えることを検証するカバレッジ基準
- 航空宇宙規格 DO-178C で要求されるカバレッジレベル
