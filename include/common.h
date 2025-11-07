/*
 * common.h - 共通定義ヘッダーファイル
 */
#ifndef COMMON_H
#define COMMON_H

/* 定数定義 */
#define MAX_BUFFER_SIZE 256
#define MIN_VALUE 0
#define MAX_VALUE 100

/* 関数マクロ */
#define CLAMP(val, min, max)  ((val) < (min) ? (min) : ((val) > (max) ? (max) : (val)))
#define IN_RANGE(val)  ((val) >= MIN_VALUE && (val) <= MAX_VALUE)

/* 型定義 */
typedef enum {
    STATUS_OK = 0,
    STATUS_ERROR = 1,
    STATUS_INVALID = 2
} status_t;

/* プロトタイプ宣言 */
int validate_input(int value);
int process_data(int data);

#endif /* COMMON_H */
