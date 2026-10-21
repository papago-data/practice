#include <stdio.h>
#include <stdlib.h> // 必须包含，因为用到了 malloc
#include "SeqList.h"

// 初始化
SeqList* initList()
{
    SeqList *L = (SeqList*)malloc(sizeof(SeqList));
    L->data = (ElemType*)malloc(sizeof(ElemType) * MAXSIZE);
    L->length = 0;
    return L; // 修正拼写 retuen -> return
}

// 在尾部加入元素
int appendElem(SeqList *L, ElemType e)
{
    if(L->length >= MAXSIZE)
    {
        printf("顺序表已满。\n");
        return 0;
    }
    L->data[L->length] = e;
    L->length++;
    return 1;
}

// 遍历
void ListElem(SeqList *L)
{
    for(int i = 0; i < L->length; i++) // 修复越界问题：< 而不是 <=
    {
        printf("%d ", L->data[i]);     // 修复换行符：\n 而不是 /n，这里为了好看我改成空格了
    }
    printf("\n");
}

// 插入
int insertElem(SeqList *L, ElemType e, int pos)
{
    if(L->length >= MAXSIZE)
    {
        printf("表已经满了\n");
        return 0;
    }

    if(pos < 1 || pos > L->length + 1) // 可以在 length+1 的位置插入
    {
        printf("插入位置错误\n");
        return 0;
    }

    // 元素后移
    for(int i = L->length - 1; i >= pos - 1; i--) // 修复死循环：i++ 改为 i--
    {
        L->data[i+1] = L->data[i];
    }
    L->data[pos-1] = e;
    L->length++;
    return 1;
}

// 删除元素
int deleteElem(SeqList *L, int pos, ElemType *e)
{
    if(L->length == 0)
    {
        printf("空表\n");
        return 0;
    }
    if(pos < 1 || pos > L->length)
    {
        printf("删除数据位置错误\n");
        return 0;
    }
    *e = L->data[pos-1]; // 保存被删除的元素

    // 元素前移
    for(int i = pos - 1; i < L->length - 1; i++) // 修正了 length 变量名
    {
        L->data[i] = L->data[i+1];
    }
    L->length--;
    return 1;
}

// 查找
int FindElem(SeqList *L, ElemType e) // 修正拼写
{
    if(L->length == 0)
    {
        printf("空表\n");
        return 0;
    }
    for(int i = 0; i < L->length; i++) // 修正了 length 变量名
    {
        if(L->data[i] == e)
        {
            return i + 1; // 返回逻辑位置（1开始）
        }
    }
    return 0; // 找不到返回 0
}
