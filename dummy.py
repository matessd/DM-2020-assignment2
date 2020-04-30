# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 16:29:58 2020

@author: sun
"""
import csv
import time
import cProfile
from memory_profiler import profile

def createC1(dataSet):
    C1 = []
    for transaction in dataSet:
        for item in transaction:
            if not [item] in C1:
                C1.append([item])
    # 映射为frozenset唯一性的，可使用其构造字典
    return list(map(frozenset, C1))      
 
 
# 从候选K项集到频繁K项集（支持度计算）
def scanD(D, Ck, minSupport):
    ssCnt = {}
    for tid in D:
        for can in Ck:
            if can.issubset(tid):
                if not can in ssCnt:
                    ssCnt[can] = 1
                else:
                    ssCnt[can] += 1
    numItems = float(len(D))
    retList = []
    supportData = {}
    for key in ssCnt:
        support = ssCnt[key] / numItems
        if support >= minSupport:
            retList.insert(0, key)
            supportData[key] = support  
    return retList, supportData
 

def calSupport(D, Ck, min_support):
    dict_sup = {}
    for i in D:
        for j in Ck:
            if j.issubset(i):
                if not j in dict_sup:
                    dict_sup[j] = 1
                else:
                    dict_sup[j] += 1
    sumCount = float(len(D))
    supportData = {}
    relist = []
    for i in dict_sup:
        temp_sup = dict_sup[i] / sumCount
        if temp_sup >= min_support:
            relist.append(i)
            supportData[i] = temp_sup  # 此处可设置返回全部的支持度数据（或者频繁项集的支持度数据）
    return relist, supportData
 

# 改进剪枝算法
def aprioriGen(Lk, k):  # 创建候选K项集 ##LK为频繁K项集
    retList = []
    lenLk = len(Lk)
    for i in range(lenLk):
        for j in range(i + 1, lenLk):
            L1 = Lk[i]
            L2 = Lk[j]
            L = L1 | L2
            if len(L)==k:
                if(L not in retList):
                    retList.append(L)
    return retList


def apriori(dataList, minSupport=0.2):
    C1 = createC1(dataList)
    D = list(map(set, dataList))  # 使用list()转换为列表
    L1, supportData = calSupport(D, C1, minSupport)
    L = [L1]  # 加列表框，使得1项集为一个单独元素
    k = 2
    while (len(L[k - 2]) > 0):
        Ck = aprioriGen(L[k - 2], k)
        Lk, supK = scanD(D, Ck, minSupport)  # scan DB to get Lk
        supportData.update(supK)
        L.append(Lk)  # L最后一个值为空集
        k += 1
    del L[-1]  # 删除最后一个空集
    return L, supportData  # L为频繁项集，为一个列表，1，2，3项集分别为一个元素。
 
 
# 生成集合的所有子集
def getSubset(fromList, toList):
    for i in range(len(fromList)):
        t = [fromList[i]]
        tt = frozenset(set(fromList) - set(t))
        if not tt in toList:
            toList.append(tt)
            tt = list(tt)
            if len(tt) > 1:
                getSubset(tt, toList)
 
 
def calcConf(freqSet, H, supportData, ruleList, minConf=0.7):
    for conseq in H:
        conf = supportData[freqSet] / supportData[freqSet - conseq]  # 计算置信度
        # 提升度lift计算lift = p(a & b) / p(a)*p(b)
        lift = supportData[freqSet] / (supportData[conseq] * supportData[freqSet - conseq])
 
        if conf >= minConf:
            print(str(list(freqSet - conseq))+'-->'+str(list(conseq)), 
                  'SUP:'+str(round(supportData[freqSet], 3)), 
                  'CONF:'+str(round(conf,2)),'LIFT:'+str(round(lift, 2)))
            ruleList.append((freqSet - conseq, conseq, conf))
 
# 生成规则
def gen_rule(L, supportData, minConf=0.7):
    bigRuleList = []
    cnt = 0
    for i in range(1, len(L)):  # 从二项集开始计算
        for freqSet in L[i]:  # freqSet为所有的k项集
            cnt+=1
            # 求该三项集的所有非空子集，1项集，2项集，直到k-1项集，用H1表示，为list类型,里面为frozenset类型，
            H1 = list(freqSet)
            all_subset = []
            getSubset(H1, all_subset)  # 生成所有的子集
            calcConf(freqSet, all_subset, supportData, bigRuleList, minConf)
    print("FreqItemSet count:",cnt)
    return bigRuleList


def loadDataList1():
    with open('GroceryStore/Groceries.csv', 'r',encoding='utf-8') as f:
       reader = csv.reader(f)
       leng = 0
       datalist=[]
       for row in reader:
           if leng==0:
               leng+=1
               continue
           strlen = len(row[1])
           trans = row[1][1:strlen-1].split(",")
           datalist.append(trans)
           leng+=1
       leng -= 1
       #print(leng)
       return datalist 
   
def loadDataList2(i):
    filename1 = "UNIX_usage\\USER"
    dataList = []
    trans = []
    with open(filename1+str(i)+'\\sanitized_all.981115184025', 'r',encoding='utf-8') as f:   
        for line in f:
            if "**SOF**" in line:
                trans = []
            elif "**EOF**" in line:
                dataList.append(trans)
            else:
                #print(line)
                l = line.split()
                if(l==[]):
                    continue
                trans.append(l[0])
    #print(dataList)
    return dataList

def loadDataList3():
    filename1 = "UNIX_usage\\USER"
    dataList = []
    trans = []
    for i in range(9):
        with open(filename1+str(i)+'\\sanitized_all.981115184025', 'r',encoding='utf-8') as f:   
            for line in f:
                if "**SOF**" in line:
                    trans = []
                elif "**EOF**" in line:
                    dataList.append(trans)
                else:
                    #print(line)
                    l = line.split()
                    if(l==[]):
                        continue
                    #print(l, i)
                    #print("2",s)
                    if(l[0] not in trans):
                        trans.append(l[0])
    return dataList


def topfun():
    dataList = loadDataList1()
    """import pyfpgrowth
    freq_patterns = pyfpgrowth.find_frequent_patterns(dataList, 98)
    print(len(freq_patterns))
    return """

    Start = time.perf_counter()
    L, supportData = apriori(dataList, minSupport=0.01)
    #print(len(L))
    print(time.perf_counter()-Start)
    rule = gen_rule(L, supportData, minConf=0.5)
    print("rule num:",len(rule))
    #cProfile.run("apriori(dataSet, minSupport=0.01)")   

if __name__ == '__main__':
    topfun()
