#!/usr/bin/python
import csv,re

# Update the tree of category with input keyword and category list
# Input:
#       node: original category tree node
#       keyword: the keyword to be added
#       categoryList: category list in the format of [category1, sub-category, sub-sub-category, ...]
# Output:
#       node: updated category node
def updateCategoryTree(node, keyword, categoryList):

    if(len(categoryList) == 0):
        node.addKeyword(keyword)
    else:
        updatedNode = updateCategoryTree(node.getChild(categoryList[0]), keyword, categoryList[1:])
        node.updateChild(updatedNode)

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
        self.root = TreeNode("Total") # default category is "total"
        self.keywordCategoryMapping = {}
        self.root.addChildCategory(TreeNode("Other"))
        print "load category data"
        with open(file, 'r') as csvFile:
            data = csv.DictReader(csvFile, delimiter = ',')

            for row in data:
                keyword = row['Keyword']
                if(keyword not in self.keywordCategoryMapping.keys()):

                    categoryPath = row['Category']
                    self.keywordCategoryMapping[keyword] = categoryPath # avoid duplication
                    categories = re.findall("[^/]+", categoryPath)
                    self.root = updateCategoryTree(self.root, keyword, categories)
                else:
                    print "Warning: duplicated", keyword


    def addTransaction(self, categoryPath, expense):
        categoryList = re.findall("[^/]+", categoryPath)
        self.__addTransactionHelper(self.root, categoryList, expense)



    def printTree(self):
        self.__preOrderTraverse(self.root)

    def __addTransactionHelper(self, node, categoryList, expense):
        node.updateCost(expense)
        if(len(categoryList) > 0):
            self.__addTransactionHelper(getNodeOnPath(node, [categoryList[0]]), categoryList[1:], expense)

    def __preOrderTraverse(self, node):
        if(node.totalCost > 0):
            print "".join(['\t']*node.depth) + str(node)
        for childNode in node.childCategories.values():
            self.__preOrderTraverse(childNode)



class TreeNode:
    def __init__(self, categoryName):
        self.name = categoryName
        self.parentCategory = None
        self.childCategories = {}
        self.keywords = set()
        self.depth = 0 # record the depth to root
        self.totalCost = 0 # record the statistics

    def addParent(self, parentCategoryNode):
        self.parentCategory = parentCategoryNode

    def addChildCategory(self, childCategoryNode):
        childCategoryNode.addParent(self)
        childCategoryNode.depth = self.depth + 1
        self.childCategories[childCategoryNode.name] = childCategoryNode

    def addKeyword(self, keyword):
        self.keywords.add(keyword)

    def updateChild(self, updatedNode):
        self.childCategories[updatedNode.name] = updatedNode

    def __str__(self):
            return self.name + " "+str(self.totalCost)

    def updateCost(self, cost):
        self.totalCost += cost

    # Get the child node, if not exist, create new child
    def getChild(self, childName):
        node = self.childCategories.get(childName, None)
        if node is None:
            self.addChildCategory(TreeNode(childName))
            return self.getChild(childName)
        else:
            return node
