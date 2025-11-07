#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

#define MAX_COMMAND_LEN 100
#define MAX_ARGS 10

// コマンドタイプの列挙型
typedef enum {
    CMD_FILE,
    CMD_USER,
    CMD_SYSTEM,
    CMD_NETWORK,
    CMD_UNKNOWN
} CommandType;

// 権限レベル
typedef enum {
    PERM_ADMIN = 3,
    PERM_USER = 2,
    PERM_GUEST = 1,
    PERM_NONE = 0
} PermissionLevel;

/**
 * 複雑なコマンド処理関数
 * - switch/case文による分岐
 * - 複雑な条件式(&&, ||使用)
 * - 3段以上のネスト構造
 */
int processCommand(const char* command, const char* arg1, const char* arg2, 
                   PermissionLevel userPerm, int isDebugMode) {
    CommandType cmdType = CMD_UNKNOWN;
    int result = 0;
    
    // コマンドタイプの判定(ネストレベル1)
    if (command != NULL && strlen(command) > 0) {
        // 最初の文字でコマンドカテゴリを判定
        switch (command[0]) {
            case 'f':  // fileコマンド系
                if (strcmp(command, "fopen") == 0 || strcmp(command, "fclose") == 0) {
                    cmdType = CMD_FILE;
                    
                    // 権限とデバッグモードの複雑な条件チェック(ネストレベル2)
                    if ((userPerm >= PERM_USER && arg1 != NULL) || 
                        (userPerm == PERM_ADMIN && isDebugMode)) {
                        
                        // ファイル操作の詳細処理(ネストレベル3)
                        if (strcmp(command, "fopen") == 0) {
                            // 引数の妥当性チェック(ネストレベル4)
                            if (arg1 != NULL && strlen(arg1) > 0 && 
                                arg2 != NULL && strlen(arg2) > 0) {
                                
                                printf("[FILE] Opening file: %s with mode: %s\n", arg1, arg2);
                                
                                // モードによる分岐
                                if (strcmp(arg2, "r") == 0 || strcmp(arg2, "rb") == 0) {
                                    printf("  -> Read mode\n");
                                    result = 1;
                                } else if (strcmp(arg2, "w") == 0 || strcmp(arg2, "wb") == 0) {
                                    if (userPerm >= PERM_ADMIN) {
                                        printf("  -> Write mode (admin)\n");
                                        result = 1;
                                    } else {
                                        printf("  -> ERROR: Write permission denied\n");
                                        result = -2;
                                    }
                                }
                            } else {
                                printf("[FILE] ERROR: Invalid arguments\n");
                                result = -1;
                            }
                        } else {  // fclose
                            printf("[FILE] Closing file: %s\n", arg1 ? arg1 : "NULL");
                            result = 1;
                        }
                    } else {
                        printf("[FILE] ERROR: Permission denied\n");
                        result = -2;
                    }
                }
                break;
                
            case 'u':  // userコマンド系
                if (strcmp(command, "uadd") == 0 || strcmp(command, "udel") == 0) {
                    cmdType = CMD_USER;
                    
                    // 管理者権限必須のチェック(ネストレベル2)
                    if (userPerm == PERM_ADMIN) {
                        
                        // ユーザー管理コマンドの処理(ネストレベル3)
                        if (strcmp(command, "uadd") == 0) {
                            if (arg1 != NULL && arg2 != NULL) {
                                int newUserPerm = atoi(arg2);
                                
                                // 新規ユーザーの権限妥当性チェック(ネストレベル4)
                                if ((newUserPerm >= PERM_GUEST && newUserPerm <= PERM_ADMIN) &&
                                    strlen(arg1) >= 3 && strlen(arg1) <= 20) {
                                    printf("[USER] Adding user: %s with permission: %d\n", 
                                           arg1, newUserPerm);
                                    result = 1;
                                } else {
                                    printf("[USER] ERROR: Invalid user parameters\n");
                                    result = -1;
                                }
                            }
                        } else {  // udel
                            printf("[USER] Deleting user: %s\n", arg1 ? arg1 : "NULL");
                            result = 1;
                        }
                    } else {
                        printf("[USER] ERROR: Admin permission required\n");
                        result = -2;
                    }
                }
                break;
                
            case 's':  // systemコマンド系
                if (strcmp(command, "status") == 0 || strcmp(command, "shutdown") == 0) {
                    cmdType = CMD_SYSTEM;
                    
                    // システムコマンドの処理(ネストレベル2)
                    if (strcmp(command, "status") == 0) {
                        // 誰でも実行可能
                        printf("[SYSTEM] Status check\n");
                        
                        // 詳細表示オプション(ネストレベル3)
                        if (arg1 != NULL && strcmp(arg1, "-v") == 0) {
                            if (isDebugMode || userPerm >= PERM_USER) {
                                printf("  -> Verbose mode enabled\n");
                                printf("  -> Debug: %s, Permission: %d\n", 
                                       isDebugMode ? "ON" : "OFF", userPerm);
                            }
                        }
                        result = 1;
                        
                    } else {  // shutdown
                        // 管理者のみ、かつデバッグモードでない場合のみ(ネストレベル3)
                        if (userPerm == PERM_ADMIN && !isDebugMode) {
                            if (arg1 != NULL && strcmp(arg1, "--force") == 0) {
                                printf("[SYSTEM] Force shutdown initiated\n");
                                result = 1;
                            } else {
                                printf("[SYSTEM] Normal shutdown initiated\n");
                                result = 1;
                            }
                        } else if (isDebugMode) {
                            printf("[SYSTEM] ERROR: Shutdown disabled in debug mode\n");
                            result = -3;
                        } else {
                            printf("[SYSTEM] ERROR: Admin permission required\n");
                            result = -2;
                        }
                    }
                }
                break;
                
            case 'n':  // networkコマンド系
                if (strcmp(command, "nping") == 0 || strcmp(command, "nconnect") == 0) {
                    cmdType = CMD_NETWORK;
                    
                    // ネットワークコマンドの処理(ネストレベル2)
                    if ((userPerm >= PERM_USER || isDebugMode) && arg1 != NULL) {
                        
                        if (strcmp(command, "nping") == 0) {
                            // IPアドレスの簡易検証(ネストレベル3)
                            int dotCount = 0;
                            for (int i = 0; arg1[i] != '\0'; i++) {
                                if (arg1[i] == '.') dotCount++;
                            }
                            
                            // IPv4形式チェック(ネストレベル4)
                            if (dotCount == 3 && strlen(arg1) >= 7) {
                                printf("[NETWORK] Pinging: %s\n", arg1);
                                result = 1;
                            } else {
                                printf("[NETWORK] ERROR: Invalid IP format\n");
                                result = -1;
                            }
                            
                        } else {  // nconnect
                            printf("[NETWORK] Connecting to: %s\n", arg1);
                            if (arg2 != NULL) {
                                int port = atoi(arg2);
                                if (port > 0 && port <= 65535) {
                                    printf("  -> Port: %d\n", port);
                                    result = 1;
                                } else {
                                    printf("  -> ERROR: Invalid port\n");
                                    result = -1;
                                }
                            }
                        }
                    } else {
                        printf("[NETWORK] ERROR: Permission denied or missing arguments\n");
                        result = -2;
                    }
                }
                break;
                
            default:
                printf("[ERROR] Unknown command: %s\n", command);
                cmdType = CMD_UNKNOWN;
                result = -1;
                break;
        }
    } else {
        printf("[ERROR] NULL or empty command\n");
        result = -1;
    }
    
    return result;
}

// メイン関数 - テスト用
int main() {
    printf("=== Complex C Sample Code Demo ===\n\n");
    
    // テストケース1: ファイル操作(管理者)
    printf("Test 1: File operation (Admin)\n");
    processCommand("fopen", "data.txt", "r", PERM_ADMIN, 0);
    printf("\n");
    
    // テストケース2: ユーザー追加(一般ユーザー - 失敗)
    printf("Test 2: User add (Regular user - should fail)\n");
    processCommand("uadd", "newuser", "2", PERM_USER, 0);
    printf("\n");
    
    // テストケース3: ユーザー追加(管理者 - 成功)
    printf("Test 3: User add (Admin - should succeed)\n");
    processCommand("uadd", "newuser", "2", PERM_ADMIN, 0);
    printf("\n");
    
    // テストケース4: システム状態確認(詳細表示)
    printf("Test 4: System status (verbose)\n");
    processCommand("status", "-v", NULL, PERM_USER, 1);
    printf("\n");
    
    // テストケース5: ネットワークping
    printf("Test 5: Network ping\n");
    processCommand("nping", "192.168.1.1", NULL, PERM_USER, 0);
    printf("\n");
    
    // テストケース6: シャットダウン(デバッグモード - 失敗)
    printf("Test 6: Shutdown (Debug mode - should fail)\n");
    processCommand("shutdown", "--force", NULL, PERM_ADMIN, 1);
    printf("\n");
    
    return 0;
}
