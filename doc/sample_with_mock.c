/*
 * 外部関数を含むサンプルC言語ファイル
 */

// 外部関数の宣言
extern int get_sensor_value(void);
extern int calculate_threshold(int base);

/**
 * センサー値を評価する関数
 */
int evaluate_sensor(int base_threshold) {
    int sensor_val = get_sensor_value();
    int threshold = calculate_threshold(base_threshold);
    
    if (sensor_val > threshold) {
        return 1;  // 正常
    } else {
        return 0;  // 異常
    }
}
