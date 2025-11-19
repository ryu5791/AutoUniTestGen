/*
 * サンプルC言語ファイル
 * テスト対象: calculate関数
 */

/**
 * 簡単な計算を行う関数
 * 
 * @param a 第1引数
 * @param b 第2引数
 * @param c 第3引数
 * @return 計算結果
 */
int calculate(int a, int b, int c) {
    if (a > 10) {
        if (b < 20) {
            return c * 2;
        } else {
            return c + 10;
        }
    } else {
        return c - 5;
    }
}
