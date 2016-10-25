#!/usr/bin/python
import csv
import re
from transaction import TransactionInfo

# Update the tree of category with input keyword and category list
# Input:
#       node: original category tree node
#       keyword: the keyword to be added
#       categoryList: category list in the format of [category1,
#                   sub-category, sub-sub-category, ...]
# Output:
#       node: updated category node
def updateCategoryTree(node, keyword, categoryList):

    if(len(categoryList) == 0):
        node.addKeyword(keyword)
    else:
        updatedNode = updateCategoryTree(node.getChild(
                        categoryList[0]), keyword, categoryList[1:])
        node.updateChild(updatedNode)

    node.setIsCategory(True)
    return node

# Get the node of category
# Input:
#       node: original category tree node
#       categoryList: category list in the format of [category1, sub-category, sub-sub-category, ...]
# Output:
#       node: target category node
def getNodeOnPath(node, categoryList):
    if(len(categoryList) == 0):
        return node
    else:
        return getNodeOnPath(node.getChild(categoryList[0]), categoryList[1:])


class CategoryTree:
    def __init__(self, file="categories.csv"):
        self.root = TreeNode("Total")  # default category is "total"
        self.keywordCategoryMapping = {}
        self.root.addChildCategory(TreeNode("Other"))
        #print "load category data"
        with open(file, 'r') as csvFile:
            data = csv.DictReader(csvFile, delimiter=',')

            for row in data:
                keyword = row['Keyword']
                if(keyword not in self.keywordCategoryMapping.keys()):

                    categoryPath = row['Category']
                    self.keywordCategoryMapping[keyword] = categoryPath  # avoid duplication
                    categories = re.findall("[^/]+", categoryPath)
                    self.root = updateCategoryTree(self.root, keyword, categories)
                else:
                    print "Warning: duplicated", keyword


    def addTransaction(self, categoryPath, expense, date, desc, bankSource, card):
        categoryList = re.findall("[^/]+", categoryPath)
        self.__addTransactionHelper(self.root, categoryList, expense, date, desc, bankSource, card)


    def printTree(self, spendingHighlightTh = 1):
        self.__preOrderTraverse(self.root, spendingHighlightTh)

    def __addTransactionHelper(self, node, categoryList, expense, date, desc, bankSource, card):
        node.updateCost(expense)
        if(len(categoryList) > 0):
            self.__addTransactionHelper(getNodeOnPath(node, [categoryList[0]]), categoryList[1:], expense, date, desc, bankSource, card)
        else:
            node.addChildTransaction(date, expense, desc, bankSource, card)


    def __preOrderTraverse(self, node, spendingHighlightTh):
        if((node.totalCost > 0 and node.isCategory) or (node.transactionInfo != None and node.transactionInfo.amount >= spendingHighlightTh)):
            print "".join(['\t']*node.depth) + str(node)
        for childNode in node.childCategories.values():
            self.__preOrderTraverse(childNode, spendingHighlightTh)


class TreeNode:
    def __init__(self, categoryName):
        self.name = categoryName
        self.parentCategory = None
        self.childCategories = {}
        self.keywords = set()
        self.depth = 0  # record the depth to root
        self.totalCost = 0  # record the statistics
        self.isCategory = False
        self.transactionInfo = None

    def addParent(self, parentCategoryNode):
        self.parentCategory = parentCategoryNode

    def addChildCategory(self, childCategoryNode):
        childCategoryNode.addParent(self)
        childCategoryNode.depth = self.depth + 1
        self.isCategory = True
        childCategoryNode.setIsCategory(True)
        self.childCategories[childCategoryNode.name] = childCategoryNode

    def addChildTransaction(self, date, expense, desc, bankSource, card):
        transactionNode = TreeNode(desc)
        transactionNode.transactionInfo = TransactionInfo(date, bankSource, card, expense, desc)
        transactionNode.depth = self.depth + 1
        self.childCategories[date+"#"+bankSource+"#"+card+"#"+desc+"#"+str(expense)] = transactionNode

    def addKeyword(self, keyword):
        self.keywords.add(keyword)

    def updateChild(self, updatedNode):
        self.childCategories[updatedNode.name] = updatedNode

    def __str__(self):
        if(not self.isCategory):
            label = self.transactionInfo.bank + " " + self.transactionInfo.card + " " + self.transactionInfo.date + " " + \
            ' '.join(self.transactionInfo.description.split())
            return "{0:55} {1}".format(label, str(self.transactionInfo.amount))
        else:
            return self.name + " "+str(self.totalCost)

    def updateCost(self, cost):
        self.totalCost += cost

    def updateDate(self, date):
        self.transDate = date

    def setIsCategory(self, isCategory):
        self.isCategory = isCategory

    # Get the child node, if not exist, create new child
    def getChild(self, childName):
        node = self.childCategories.get(childName, None)
        if node is None:
            self.addChildCategory(TreeNode(childName))
            return self.getChild(childName)
        else:
            return node
