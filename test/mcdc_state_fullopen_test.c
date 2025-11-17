#include "unity.h"
#include <limits.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* Constants from original source */
#define ACT_INIT 2
#define ACT_NORMAL 0
#define ACT_SETTING 1
#define ACT_GLITCH 3

/* Global variables */
static struct {
    struct {
        uint16_t state : 3;
        uint16_t act : 2;
        uint16_t half : 1;
        uint16_t rvs : 1;
        uint16_t handmv : 1;
        uint16_t stopsw : 1;
        uint16_t init : 1;
        uint16_t strk : 3;
        uint16_t test : 1;
        uint16_t error : 1;
        uint16_t safestop : 1;
    } bit;
    uint16_t dat;
} mState = {0};

static struct {
    struct {
        struct {
            struct {
                uint8_t af_power_on;
            } info;
        } special;
        struct {
            struct {
                uint8_t op_power_push;
            } info;
        } door;
        struct {
            struct {
                uint8_t unlock;
            } info;
        } netlink;
    } info;
} mHandyData = {0};

/* Macro definitions */
#define vHANDY_SET_POWERPON_SEQ mHandyData.info.special.info.af_power_on
#define vHANDY_SET_OP_POWER_PUSH mHandyData.info.door.info.op_power_push

/* Mock functions */
bool test_condition_result = false;

void setUp(void) {
    /* Reset global variables before each test */
    mState.dat = 0;
    mHandyData.info.special.info.af_power_on = 0;
    mHandyData.info.door.info.op_power_push = 0;
    test_condition_result = false;
}

void tearDown(void) {
    /* Clean up after each test */
}

/* Function to evaluate the condition */
bool evaluate_condition(void) {
    return ((mState.bit.act == ACT_INIT) &&
            ((vHANDY_SET_POWERPON_SEQ == 1) || (vHANDY_SET_POWERPON_SEQ == 2) || (vHANDY_SET_POWERPON_SEQ == 3) ||
             (vHANDY_SET_POWERPON_SEQ == 6) || (vHANDY_SET_POWERPON_SEQ == 7) || (vHANDY_SET_POWERPON_SEQ == 8)) &&
            (vHANDY_SET_OP_POWER_PUSH == 0));
}

/*
 * MC/DC 100% Coverage Test Cases
 * Truth Table Pattern (8 conditions, 9 test cases):
 *
 * Condition mapping:
 * C1: mState.bit.act == ACT_INIT
 * C2: vHANDY_SET_POWERPON_SEQ == 1
 * C3: vHANDY_SET_POWERPON_SEQ == 2
 * C4: vHANDY_SET_POWERPON_SEQ == 3
 * C5: vHANDY_SET_POWERPON_SEQ == 6
 * C6: vHANDY_SET_POWERPON_SEQ == 7
 * C7: vHANDY_SET_POWERPON_SEQ == 8
 * C8: vHANDY_SET_OP_POWER_PUSH == 0
 *
 * Pattern: C1 C2 C3 C4 C5 C6 C7 C8 -> Expected Result
 */

/* Test Case 1: TTFFFFFT -> TRUE
 * C1=T, C2=T, C3=F, C4=F, C5=F, C6=F, C7=F, C8=T
 * mState.bit.act == ACT_INIT (T)
 * vHANDY_SET_POWERPON_SEQ == 1 (T)
 * vHANDY_SET_OP_POWER_PUSH == 0 (T)
 */
void test_mcdc_case_01_TTFFFFFT(void) {
    mState.bit.act = ACT_INIT;           /* C1 = True */
    vHANDY_SET_POWERPON_SEQ = 1;         /* C2 = True, C3-C7 = False */
    vHANDY_SET_OP_POWER_PUSH = 0;        /* C8 = True */

    TEST_ASSERT_TRUE(evaluate_condition());
}

/* Test Case 2: FTFFFFFT -> FALSE
 * C1=F, C2=T, C3=F, C4=F, C5=F, C6=F, C7=F, C8=T
 * mState.bit.act != ACT_INIT (F)
 * vHANDY_SET_POWERPON_SEQ == 1 (T)
 * vHANDY_SET_OP_POWER_PUSH == 0 (T)
 * Tests independence of C1
 */
void test_mcdc_case_02_FTFFFFFT(void) {
    mState.bit.act = ACT_NORMAL;         /* C1 = False */
    vHANDY_SET_POWERPON_SEQ = 1;         /* C2 = True, C3-C7 = False */
    vHANDY_SET_OP_POWER_PUSH = 0;        /* C8 = True */

    TEST_ASSERT_FALSE(evaluate_condition());
}

/* Test Case 3: TFFFFFFT -> FALSE
 * C1=T, C2=F, C3=F, C4=F, C5=F, C6=F, C7=F, C8=T
 * mState.bit.act == ACT_INIT (T)
 * vHANDY_SET_POWERPON_SEQ is none of valid values (all F)
 * vHANDY_SET_OP_POWER_PUSH == 0 (T)
 * Tests that at least one of C2-C7 must be true
 */
void test_mcdc_case_03_TFFFFFFT(void) {
    mState.bit.act = ACT_INIT;           /* C1 = True */
    vHANDY_SET_POWERPON_SEQ = 0;         /* C2-C7 = False (value is not 1,2,3,6,7,8) */
    vHANDY_SET_OP_POWER_PUSH = 0;        /* C8 = True */

    TEST_ASSERT_FALSE(evaluate_condition());
}

/* Test Case 4: TTFFFFFF -> FALSE
 * C1=T, C2=T, C3=F, C4=F, C5=F, C6=F, C7=F, C8=F
 * mState.bit.act == ACT_INIT (T)
 * vHANDY_SET_POWERPON_SEQ == 1 (T)
 * vHANDY_SET_OP_POWER_PUSH != 0 (F)
 * Tests independence of C8
 */
void test_mcdc_case_04_TTFFFFFF(void) {
    mState.bit.act = ACT_INIT;           /* C1 = True */
    vHANDY_SET_POWERPON_SEQ = 1;         /* C2 = True, C3-C7 = False */
    vHANDY_SET_OP_POWER_PUSH = 1;        /* C8 = False */

    TEST_ASSERT_FALSE(evaluate_condition());
}

/* Test Case 5: TFTFFFFT -> TRUE
 * C1=T, C2=F, C3=T, C4=F, C5=F, C6=F, C7=F, C8=T
 * mState.bit.act == ACT_INIT (T)
 * vHANDY_SET_POWERPON_SEQ == 2 (C3=T)
 * vHANDY_SET_OP_POWER_PUSH == 0 (T)
 * Tests independence of C3
 */
void test_mcdc_case_05_TFTFFFFT(void) {
    mState.bit.act = ACT_INIT;           /* C1 = True */
    vHANDY_SET_POWERPON_SEQ = 2;         /* C2 = False, C3 = True, C4-C7 = False */
    vHANDY_SET_OP_POWER_PUSH = 0;        /* C8 = True */

    TEST_ASSERT_TRUE(evaluate_condition());
}

/* Test Case 6: TFFTFFFT -> TRUE
 * C1=T, C2=F, C3=F, C4=T, C5=F, C6=F, C7=F, C8=T
 * mState.bit.act == ACT_INIT (T)
 * vHANDY_SET_POWERPON_SEQ == 3 (C4=T)
 * vHANDY_SET_OP_POWER_PUSH == 0 (T)
 * Tests independence of C4
 */
void test_mcdc_case_06_TFFTFFFT(void) {
    mState.bit.act = ACT_INIT;           /* C1 = True */
    vHANDY_SET_POWERPON_SEQ = 3;         /* C2-C3 = False, C4 = True, C5-C7 = False */
    vHANDY_SET_OP_POWER_PUSH = 0;        /* C8 = True */

    TEST_ASSERT_TRUE(evaluate_condition());
}

/* Test Case 7: TFFFTFFT -> TRUE
 * C1=T, C2=F, C3=F, C4=F, C5=T, C6=F, C7=F, C8=T
 * mState.bit.act == ACT_INIT (T)
 * vHANDY_SET_POWERPON_SEQ == 6 (C5=T)
 * vHANDY_SET_OP_POWER_PUSH == 0 (T)
 * Tests independence of C5
 */
void test_mcdc_case_07_TFFFTFFT(void) {
    mState.bit.act = ACT_INIT;           /* C1 = True */
    vHANDY_SET_POWERPON_SEQ = 6;         /* C2-C4 = False, C5 = True, C6-C7 = False */
    vHANDY_SET_OP_POWER_PUSH = 0;        /* C8 = True */

    TEST_ASSERT_TRUE(evaluate_condition());
}

/* Test Case 8: TFFFFTFT -> TRUE
 * C1=T, C2=F, C3=F, C4=F, C5=F, C6=T, C7=F, C8=T
 * mState.bit.act == ACT_INIT (T)
 * vHANDY_SET_POWERPON_SEQ == 7 (C6=T)
 * vHANDY_SET_OP_POWER_PUSH == 0 (T)
 * Tests independence of C6
 */
void test_mcdc_case_08_TFFFFTFT(void) {
    mState.bit.act = ACT_INIT;           /* C1 = True */
    vHANDY_SET_POWERPON_SEQ = 7;         /* C2-C5 = False, C6 = True, C7 = False */
    vHANDY_SET_OP_POWER_PUSH = 0;        /* C8 = True */

    TEST_ASSERT_TRUE(evaluate_condition());
}

/* Test Case 9: TFFFFFTT -> TRUE
 * C1=T, C2=F, C3=F, C4=F, C5=F, C6=F, C7=T, C8=T
 * mState.bit.act == ACT_INIT (T)
 * vHANDY_SET_POWERPON_SEQ == 8 (C7=T)
 * vHANDY_SET_OP_POWER_PUSH == 0 (T)
 * Tests independence of C7
 */
void test_mcdc_case_09_TFFFFFTT(void) {
    mState.bit.act = ACT_INIT;           /* C1 = True */
    vHANDY_SET_POWERPON_SEQ = 8;         /* C2-C6 = False, C7 = True */
    vHANDY_SET_OP_POWER_PUSH = 0;        /* C8 = True */

    TEST_ASSERT_TRUE(evaluate_condition());
}

/* Main function for Unity test runner */
int main(void) {
    UNITY_BEGIN();

    /* MC/DC Coverage Tests */
    RUN_TEST(test_mcdc_case_01_TTFFFFFT);
    RUN_TEST(test_mcdc_case_02_FTFFFFFT);
    RUN_TEST(test_mcdc_case_03_TFFFFFFT);
    RUN_TEST(test_mcdc_case_04_TTFFFFFF);
    RUN_TEST(test_mcdc_case_05_TFTFFFFT);
    RUN_TEST(test_mcdc_case_06_TFFTFFFT);
    RUN_TEST(test_mcdc_case_07_TFFFTFFT);
    RUN_TEST(test_mcdc_case_08_TFFFFTFT);
    RUN_TEST(test_mcdc_case_09_TFFFFFTT);

    return UNITY_END();
}
