#!/usr/bin/python
from abc import ABCMeta, abstractmethod
import csv, re
import categoryTree
import sqlite3
import datetime
from transaction import *

# Get the month from the date string in month/date/year format
def getMonthDateAndYearFromDate(date):
    # print date
    dateStr = re.findall('[0-9]+', date)
    month = int(dateStr[0])
    year = int(dateStr[2])
    date = int(dateStr[1])
    if(year < 2000):  # for year in short (e.g., 15), convert it to full length (e.g., 2015)
        year += 2000
    return month, date, year




class BillDataProcessor:
    # Description here

    # Month is an integer in the range of [1, 12]
    def __init__(self):
        self.transData = []
        self.errMessage = ""
        self.statistics = {}
        self.spending = categoryTree.CategoryTree()
        self.income = categoryTree.CategoryTree()
        self.sqlite_file = 'transactions_db.sqlite'
        self.trans_table_name = 'transactions'
        self.processed_data_files_table_name = 'processed_data_files'
        self.currentDate = datetime.date.today().strftime('%m/%d/%Y')


    def parseData(self, files):

        conn = sqlite3.connect(self.sqlite_file)
        c = conn.cursor()
        sql = 'create table if not exists ' + self.trans_table_name + ' (date text, bank text, card text, amount real, description text);'
        c.execute(sql)

        sql = 'create table if not exists ' + self.processed_data_files_table_name + ' ("file_name" text, "last_parsing_date" text);'
        c.execute(sql)

        sql = 'select file_name from ' + self.processed_data_files_table_name + ";"
        parsedFiles = [row[0] for row in c.execute(sql)]

        conn.close()


        for file in files:
            if(file.split('/')[-1] not in parsedFiles):
                if "Chase" in file:
                    transFile = self.__parseChaseData(file)
                    self.__saveDataToDB(transFile)
                elif "Amex" in file:
                    transFile = self.__parseAmexData(file)
                    self.__saveDataToDB(transFile)
                elif "BOA" in file:
                    transFile = self.__parseBOAData(file)
                    self.__saveDataToDB(transFile)
                else:
                    self.errMessage += "Non-recognized data: " + file

        if(len(self.errMessage) > 0):
            print self.errMessage


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
        self.spending.printTree(spendingHighlightTh = 100)

        print " ========== Payment and refund: ========== "
        self.income.printTree()

        for key, value in self.statistics.iteritems():
            if(key != "Total Expense" and key != "Total Payment" and value > 0):
                print key, ":\t", value

    def __formatDate(self, date):
        dateStrList = re.findall('[0-9]+', date)
        month = dateStrList[0]
        date = dateStrList[1]
        year = dateStrList[2]
        return '"' + year+"-"+month+"-"+date + '"'


    def __saveDataToDB(self, transFile):
        conn = sqlite3.connect(self.sqlite_file)
        c = conn.cursor()

        transData = transFile.transactions
        for transInfo in transData:
            date = transInfo.date
            amount = transInfo.amount
            desc = transInfo.description
            bankSource = transInfo.bank
            card = transInfo.card

            dateStr = self.__formatDate(date)
            data = c.execute('SELECT * FROM {table} WHERE date = {dateValue} AND bank = "{bankSourceValue}" AND card = "{cardValue}" AND amount = {amountValue} AND description = "{descValue}"'.\
            format(table=self.trans_table_name, dateValue=dateStr, bankSourceValue=bankSource, amountValue=amount, descValue=desc, cardValue=card))

            if(data.fetchone() is None):
                c.execute("""insert into {table} (date, bank, card, amount, description) values ({dateValue}, "{bankSource}", "{cardValue}", {amountValue}, "{descValue}")""".\
                format(table=self.trans_table_name, dateValue=dateStr, amountValue=amount, descValue=desc, bankSource=bankSource, cardValue=card))

        c.execute("""insert into {table} ("file_name", "last_parsing_date") values ("{filename}", "{parsingDate}")""".\
        format(table=self.processed_data_files_table_name, filename=transFile.filename, parsingDate=self.currentDate))
        conn.commit()
        conn.close()


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

    def __parseBOAData(self, file):
        print "Process BOA data:", file
        card = file.split("_")[1]
        transData = []

        with open(file, 'r') as csvFile:
            data = csv.DictReader(csvFile, delimiter = ',')
            for row in data:
                month, date, year = getMonthDateAndYearFromDate(row['Posted Date'])
                # print month, self.month, year, self.year
                transData.append(TransactionInfo(row['Posted Date'], "BOA", card, float(row['Amount']), row['Payee']))
        return TransactionFile(file, self.currentDate, transData)

    def __parseChaseData(self, file):
        print "Process Chase data:", file
        card = file.split("_")[1]
        transData = []

        with open(file, 'r') as csvFile:
            data = csv.DictReader(csvFile, delimiter = ',')
            for row in data:
                # print row['Type'], row['Trans Date'], row['Description'],row['Amount']
                month, date, year = getMonthDateAndYearFromDate(row['Trans Date'])
                transData.append(TransactionInfo(row['Trans Date'], "Chase", card, float(row['Amount']), row['Description']))
        return TransactionFile(file, self.currentDate, transData)

    def __parseAmexData(self, file):
        print "Process Amex data:", file
        card = file.split("_")[1]
        transData = []

        with open(file, 'r') as csvFile:
            data = csv.reader(csvFile, delimiter=',')
            for row in data:
                # print row
                if(len(row) > 4):
                    month, date, year = getMonthDateAndYearFromDate(row[0])
                    transData.append(TransactionInfo(row[0], "Amex", card, float(row[2]), row[3] ))
        return TransactionFile(file, self.currentDate, transData)

    def printAllTransData(self):
        for date, amount, desc, bank, card in self.transData:
            print date, ": ", bank, card, amount, "\t", desc
