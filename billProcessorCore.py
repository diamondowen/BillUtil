#!/usr/bin/python
from abc import ABCMeta, abstractmethod
import re
import categoryTree
import sqlite3
from transaction import TransactionInfo
import datetime


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
        if year is None:
            sqlDateFilter += "%"
        else:
            sqlDateFilter += str(year)
            if month is None:
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
            self.transData.append(TransactionInfo(date, bank, card, float(amount), desc ))

        conn.close

    def printStatistics(self, highlight_threshold):
        self.__getStatisticsFromData()

        print " ========== Spending: ========== "
        self.spending.printTree(spendingHighlightTh = highlight_threshold)

        print " ========== Earning and refund: ========== "
        self.income.printTree()

        for key, value in self.statistics.iteritems():
            if key != "Total Expense" and key != "Total Payment" and value > 0:
                print key, ":\t", value

    def __seperateTransData(self, transData):
        spendingTransData = filter(lambda x: x.amount < 0, transData)
        incomeTransData = filter(lambda x: x.amount > 0, transData)
        return spendingTransData, incomeTransData

    def __generateIncomeDataMap(self, incomeTransData):
        result = {}
        for td in incomeTransData:
            result[str(td.amount) +"#" + str(td.date)] = td
        return result

    def __findPossibleKeys(self, spendingTransData, incomeTransDataMap):
        result = []
        for key, value in incomeTransDataMap.iteritems():
            if float(value.amount) == -float(spendingTransData.amount):
                result.append(key)
        return result


    # Main logic of linking data
    def __getKeyOfTransFlow(self, incomeTransDataMap, spendingTransData):
        key = str(-spendingTransData.amount) + "#" + str(spendingTransData.date)
        if(key in incomeTransDataMap):
            return key
        else:
            keys = self.__findPossibleKeys(spendingTransData, incomeTransDataMap)
            for key in keys:
                incomeData = incomeTransDataMap[key]
                description_in = incomeData.description.lower()
                description_sp = spendingTransData.description.lower()
                if("payment" in description_in or "pmt" in description_in) and \
                        ("payment" in description_sp or "pmt" in description_sp):
                    return key

        return None


    def __getStatisticsFromData(self):
        statistics = {}

        unprocessedDesc = []
        linkedTransFlow = []

        spendingTransData, incomeTransData = self.__seperateTransData(self.transData)
        incomeTransDataMap = self.__generateIncomeDataMap(incomeTransData)

        # for key, value in incomeTransDataMap.iteritems():
        #     print key, value

        # Process spending data
        for td in spendingTransData:
            (date, bankSource, card, amount, desc) = td.getTuple()
            processedDesc = False

            for keyword, categoryPath in self.spending.keywordCategoryMapping.iteritems():
                if re.search(keyword, desc, re.IGNORECASE):
                    key = self.__getKeyOfTransFlow(incomeTransDataMap, td)
                    if(key is not None):
                        linkedTransFlow.append(td)
                        incomeTransDataMap.pop(key, None) # delete the linked transaction from income data
                    else:
                        self.spending.addTransaction(categoryPath, -amount, date, desc, bankSource, card) # amount is negative, convert it to positive number
                    processedDesc = True
                    break

            if processedDesc is False:
                key = self.__getKeyOfTransFlow(incomeTransDataMap, td)
                if(key is not None):
                    linkedTransFlow.append(td)
                    incomeTransDataMap.pop(key, None) # delete the linked transaction from income data
                else:
                    unprocessedDesc.append((date, amount, desc, bankSource, card))
                    self.spending.addTransaction("Other", -amount, date, desc, bankSource, card)

        # Process un-linked income data
        for key, td in incomeTransDataMap.iteritems():
            processedDesc = False
            (date, bankSource, card, amount, desc) = td.getTuple()
            for keyword, categoryPath in self.spending.keywordCategoryMapping.iteritems():
                if re.search(keyword, desc, re.IGNORECASE):
                    self.income.addTransaction(categoryPath, amount, date, desc, bankSource, card)
                    processedDesc = True
                    break

            if processedDesc is False:
                unprocessedDesc.append((date, amount, desc, bankSource, card))
                self.income.addTransaction("Other", amount, date, desc, bankSource, card)

        if len(linkedTransFlow) > 0:
            print "========== Linked transaction flow: =========="
            for td in linkedTransFlow:
                (date, bank, card, amount, desc) = td.getTuple()
                label = bank + " " + card + " " + date + " " + ' '.join(desc.split())
                print "{0:60} {1}".format(label, str(amount))

        if len(unprocessedDesc) > 0:
            print "========== Not classified transactions: =========="
            for date, amount, desc, bank, card in unprocessedDesc:
                label = bank + " " + card + " " + date + " " + ' '.join(desc.split())
                print "{0:60} {1}".format(label, str(-amount))

        # statistics['Total Payment'] = totalPayment

        return statistics

    def printAllTransData(self):
        for date, amount, desc, bank, card in self.transData:
            print date, ": ", bank, card, amount, "\t", desc
