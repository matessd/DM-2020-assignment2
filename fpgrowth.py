# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 13:36:03 2020
这份代码有问题, apriori的才是正确结果, 
fpgrowth从headerTable转suppData的时候扫不全itemSet的数量

@author: sun
"""
import csv
import time
import cProfile
from memory_profiler import profile

class treeNode:
    def __init__(self, nameValue, numOccur, parentNode):
        self.name = nameValue
        self.count = numOccur
        self.nodeLink = None
        self.parent = parentNode
        self.children = {}
    
    def inc(self, numOccur):
        self.count += numOccur
    
    def disp(self, ind=1):
        #print '  '*ind, self.name, ' ', self.count
        for child in self.children.values():
            child.disp(ind+1)

def updateHeader(nodeToTest, targetNode):
    while nodeToTest.nodeLink != None:
        nodeToTest = nodeToTest.nodeLink
    nodeToTest.nodeLink = targetNode
def updateFPtree(items, inTree, headerTable, count):
    if items[0] in inTree.children:
        # 判断items的第一个结点是否已作为子结点
        inTree.children[items[0]].inc(count)
    else:
        # 创建新的分支
        inTree.children[items[0]] = treeNode(items[0], count, inTree)
        if headerTable[items[0]][1] == None:
            headerTable[items[0]][1] = inTree.children[items[0]]
        else:
            updateHeader(headerTable[items[0]][1], inTree.children[items[0]])
    # 递归
    if len(items) > 1:
        updateFPtree(items[1::], inTree.children[items[0]], headerTable, count)

def createFPtree(dataSet, minSup=1):
    headerTable = {}
    for trans in dataSet:
        for item in trans:
            headerTable[item] = headerTable.get(item, 0) + dataSet[trans]
    #print(headerTable)
    for k in list(headerTable.keys()):
        #print(k)
        if headerTable[k] < minSup:
            #print(headerTable[k])
            del(headerTable[k]) # 删除不满足最小支持度的元素
    #print(headerTable)
    freqItemSet = set(headerTable.keys()) # 满足最小支持度的频繁项集
    if len(freqItemSet) == 0:
        return None, None
    for k in headerTable:
        headerTable[k] = [headerTable[k], None] # element: [count, node]
    #print(headerTable)
    retTree = treeNode('Null Set', 1, None)
    for tranSet, count in dataSet.items():
        # dataSet：[element, count]
        localD = {}
        for item in tranSet:
            if item in freqItemSet: # 过滤，只取该样本中满足最小支持度的频繁项
                localD[item] = headerTable[item][0] # element : count
        if len(localD) > 0:
            # 根据全局频数从大到小对单样本排序
            #print(localD)
            # orderedItem = [v[0] for v in sorted(localD.iteritems(), key=lambda p:(p[1], -ord(p[0])), reverse=True)]
            orderedItem = [v[0] for v in sorted(localD.items(), key=lambda p:(p[1], p[0]), reverse=True)]
            # 用过滤且排序后的样本更新树
            updateFPtree(orderedItem, retTree, headerTable, count)
    return retTree, headerTable

# 回溯
def ascendFPtree(leafNode, prefixPath):
    if leafNode.parent != None:
        prefixPath.append(leafNode.name)
        ascendFPtree(leafNode.parent, prefixPath)
# 条件模式基
def findPrefixPath(basePat, myHeaderTab):
    treeNode = myHeaderTab[basePat][1] # basePat在FP树中的第一个结点
    condPats = {}
    while treeNode != None:
        prefixPath = []
        ascendFPtree(treeNode, prefixPath) # prefixPath是倒过来的，从treeNode开始到根
        if len(prefixPath) > 1:
            condPats[frozenset(prefixPath[1:])] = treeNode.count # 关联treeNode的计数
        treeNode = treeNode.nodeLink # 下一个basePat结点
    return condPats


def mineFPtree(inTree, headerTable, minSup, preFix, freqItemList):
    # 最开始的频繁项集是headerTable中的各元素
    #print("??",headerTable)
    #print("1")
    bigL = [v[0] for v in sorted(headerTable.items(), key=lambda p:p[1][0])] # 根据频繁项的总频次排序
    for basePat in bigL: # 对每个频繁项
        newFreqSet = preFix.copy()
        newFreqSet.add(basePat)
        freqItemList.append(newFreqSet)
        condPattBases = findPrefixPath(basePat, headerTable) # 当前频繁项集的条件模式基
        myCondTree, myHead = createFPtree(condPattBases, minSup) # 构造当前频繁项的条件FP树
        if myHead != None:
            # print 'conditional tree for: ', newFreqSet
            # myCondTree.disp(1)
            mineFPtree(myCondTree, myHead, minSup, newFreqSet, freqItemList) # 递归挖掘条件FP树

def createInitSet(dataSet):
    retDict={}
    for trans in dataSet:
	    key = frozenset(trans)
	    if key in retDict:
	        retDict[frozenset(trans)] += 1
	    else:
		    retDict[frozenset(trans)] = 1
    return retDict

def calSuppData(headerTable, freqItemList, total):
    suppData = {}
    for Item in freqItemList:
        # 找到最底下的结点
        Item = sorted(Item, key=lambda x:headerTable[x][0])
        base = findPrefixPath(Item[0], headerTable)
        # 计算支持度
        support = 0
        for B in base:
            if frozenset(Item[1:]).issubset(set(B)):
                support += base[B]
        # 对于根的儿子，没有条件模式基
        if len(base)==0 and len(Item)==1:
            support = headerTable[Item[0]][0]
            
        """if frozenset(Item)==frozenset({'curd'}):
            print(support)"""
        suppData[frozenset(Item)] = support/float(total)
    return suppData

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
         
        """t = frozenset({'curd','whole milk'})
        if t==freqSet:
            print(supportData[conseq],conseq)"""
        
        if conf >= minConf:
            print(str(list(freqSet - conseq))+'-->'+str(list(conseq)), 
                  'SUP:'+str(round(supportData[freqSet], 3)), 
                  'CONF:'+str(round(conf,2)),'LIFT:'+str(round(lift, 2)))
            ruleList.append((freqSet - conseq, conseq, conf))

# 生成规则
def gen_rule(freqSetList, supportData, minConf=0.7):
    bigRuleList = []
    for i in range(0, len(freqSetList)):  #所有频繁项集
            freqSet = freqSetList[i]
            H1 = list(freqSet)
            #print(H1, len(H1))
            if(len(H1)<=1):
                continue
            all_subset = []
            getSubset(H1, all_subset)  # 生成所有的子集
            calcConf(freqSet, all_subset, supportData, bigRuleList, minConf)
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
                    if(l[0] not in trans):
                        trans.append(l[0])
    return dataList


def topfun():
    dataList = loadDataList1()
    print(len(dataList))
    """cnt = 0
    t = frozenset({'curd'})
    print(t)
    for trans in dataList:
        #print(frozenset(trans))
        if t.issubset(frozenset(trans)):
            cnt+=1
    print(cnt,"test")
    return"""

    Start = time.perf_counter()
    initSet = createInitSet(dataList)
    minSupNum = 98
    myFPtree, myHeaderTab = createFPtree(initSet, minSupNum)
    freqItems = []
    mineFPtree(myFPtree, myHeaderTab, minSupNum, set([]), freqItems)
    suppData = calSuppData(myHeaderTab, freqItems, len(dataList))
    print(time.perf_counter()-Start)
    
    freqItems = [frozenset(x) for x in freqItems]
    #rule = generateRules(freqItems, suppData, minConf=0.5)
    rule = gen_rule(freqItems, suppData, minConf=0.5)
    #print(len(freqItems))
    print("FreqItemSet count:",len(freqItems))
    print("rule num:",len(rule)) 

if __name__ == '__main__':
    topfun()
    