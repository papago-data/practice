#include <stdio.h>
#include <stdlib.h>
#include "SeqList.h"

int main(int argc, char *argv[]) {
    printf("--- 开始测试顺序表 ---\n");

    // 1. 初始化
    SeqList *L = initList();
    printf("初始化成功，当前长度: %d\n\n", L->length);

    // 2. 测试尾部插入
    printf("尾部插入 10, 20, 30, 40:\n");
    appendElem(L, 10);
    appendElem(L, 20);
    appendElem(L, 30);
    appendElem(L, 40);
    ListElem(L); // 期望输出: 10 20 30 40
    printf("\n");

    // 3. 测试按位置插入
    printf("在第 2 个位置插入 15:\n");
    insertElem(L, 15, 2);
    ListElem(L); // 期望输出: 10 15 20 30 40
    printf("\n");

    // 4. 测试查找
    printf("查找元素 30 的位置:\n");
    int pos = FindElem(L, 30);
    if (pos > 0) {
        printf("元素 30 在第 %d 个位置\n\n", pos);
    } else {
        printf("未找到元素 30\n\n");
    }

    // 5. 测试删除
    printf("删除第 3 个位置的元素:\n");
    ElemType deletedData;
    if (deleteElem(L, 3, &deletedData)) {
        printf("成功删除，被删除的元素是: %d\n", deletedData);
    }
    printf("删除后的顺序表: ");
    ListElem(L); // 期望输出: 10 15 30 40
    printf("\n");

    // 6. 测试异常情况
    printf("尝试在第 10 个位置插入元素 (越界测试):\n");
    insertElem(L, 99, 10);

    // 7. 清理内存 (因为你用了 malloc，养成好习惯，用完要 free)
    free(L->data);
    free(L);
    printf("\n--- 测试结束，内存已释放 ---\n");

    return 0;
}
