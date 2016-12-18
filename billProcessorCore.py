#!/usr/bin/python
from abc import ABCMeta, abstractmethod
import re
import categoryTree
import sqlite3


class BillDataProcessor:
    # Description here

    # Month is an integer in the range of [1, 12]
    def __init__(self):
        self.transData = []
        self.statistics = {}
        self.spending = categoryTree.CategoryTree()
        self.income = categoryTree.CategoryTree()
        self.sqlite_file = 'transactions_db.sqlite'
        self.trans_table_name = 'transactions'


    def loadData(self, year, month):
        conn = sqlite3.connect(self.sqlite_file)
        c = conn.cursor()
        sqlDateFilter = ""
        if (year is None):
            sqlDateFilter += "%"
        else:
            sqlDateFilter += str(year)
            if(month is None):
                sqlDateFilter += "%"
            else:

                sqlDateFilter += "-" + str(month).zfill(2) + "%"

        data = c.execute("SELECT * FROM " + self.trans_table_name + ' WHERE date like "' + sqlDateFilter + '";')
        for transData in data:
            date = transData[0]
            bank = transData[1]
            card = transData[2]
            amount = transData[3]
            desc = transData[4]
            self.transData.append((date, float(amount), desc, bank, card))

        conn.close

    def printStatistics(self, highlight_threshold):
        self.__getStatisticsFromData()

        print " ========== Spending: ========== "
        self.spending.printTree(spendingHighlightTh = highlight_threshold)

        print " ========== Payment and refund: ========== "
        self.income.printTree()

        for key, value in self.statistics.iteritems():
            if(key != "Total Expense" and key != "Total Payment" and value > 0):
                print key, ":\t", value


    def __getStatisticsFromData(self):
        statistics = {}

        totalPayment = 0

        unprocessedDesc = []
        for date, amount, desc, bankSource, card in self.transData:
            processedDesc = False
            for keyword, categoryPath in self.spending.keywordCategoryMapping.iteritems():
                if(re.search(keyword, desc, re.IGNORECASE)):
                    if(amount < 0):
                        self.spending.addTransaction(categoryPath, -amount, date, desc, bankSource, card) # amount is negative, convert it to positive number
                        processedDesc = True
                        break;
                    else:
                        self.income.addTransaction(categoryPath, amount, date, desc, bankSource, card)
                        processedDesc = True
                        break;
            if(processedDesc is False):
                unprocessedDesc.append((date, amount, desc, bankSource, card))
                if(amount < 0):
                    self.spending.addTransaction("Other", -amount, date, desc, bankSource, card)
                else:
                    self.income.addTransaction("Other", amount, date, desc, bankSource, card)


        if(len(unprocessedDesc) > 0):
            print "Not classified transactions:"
            for date, amount, desc, bank, card in unprocessedDesc:
                label = bank + " " + card + " " + date + " " + ' '.join(desc.split())
                print  "{0:60} {1}".format(label, str(-amount))

        # statistics['Total Payment'] = totalPayment

        return statistics



    def printAllTransData(self):
        for date, amount, desc, bank, card in self.transData:
            print date, ": ", bank, card, amount, "\t", desc
