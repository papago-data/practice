#ifndef SEQLIST_H
#define SEQLIST_H

#define MAXSIZE 100

typedef int ElemType;

typedef struct {
    ElemType *data; // 修改为指针，配合动态内存分配
    int length;     // 元素个数
} SeqList;

SeqList* initList();
int appendElem(SeqList *L, ElemType e);
void ListElem(SeqList *L);
int insertElem(SeqList *L, ElemType e, int pos);
int deleteElem(SeqList *L, int pos, ElemType *e);
int FindElem(SeqList *L, ElemType e); // 修正拼写

#endif
