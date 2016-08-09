#!/usr/bin/python
from abc import ABCMeta, abstractmethod
import csv, re
import categoryTree
import sqlite3

# Get the month from the date string in month/date/year format
def getMonthAndYearFromDate(date):
    # print date
    date = re.findall('[0-9]+', date)
    month = int(date[0])
    year = int(date[2])
    if(year < 2000):  # for year in short (e.g., 15), convert it to full length (e.g., 2015)
        year += 2000
    return month, year


class BillDataProcessor:
    # Description here

    # Month is an integer in the range of [1, 12]
    def __init__(self, month, year, spendingHighlightTh):
        self.transData = []
        self.errMessage = ""
        self.month = int(month)
        self.year = int(year)
        self.spendingHighlightTh = int(spendingHighlightTh)
        self.statistics = {}
        self.trans = set()  # used to avoid duplicated transactions
        self.spending = categoryTree.CategoryTree()
        self.income = categoryTree.CategoryTree()
        self.sqlite_file = 'transactions_db.sqlite'
        self.trans_table_name = 'transactions'


    def processData(self, files):
        conn = sqlite3.connect(self.sqlite_file)
        c = conn.cursor()
        sql = 'create table if not exists ' + self.trans_table_name + ' (date text, amount real, description text)'
        c.execute(sql)

        for file in files:
            if "Chase" in file:
                self.__processChaseData(file)
            elif "Amex" in file:
                self.__processAmexData(file)
            elif "BOA" in file:
                self.__processBOAData(file)
            else:
                self.errMessage += "Non-recognized data: " + file

        self.statistics = self.__getStatisticsFromData()


        if(len(self.errMessage) > 0):
            print self.errMessage

        self.__saveDataToDB(c, self.transData)

        conn.commit()
        conn.close()

    def printStatistics(self):

        print " ========== Spending: ========== "
        self.spending.printTree()

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


    def __saveDataToDB(self, c, transData):
        for date, amount, desc in transData:
            dateStr = self.__formatDate(date)
            print dateStr
            c.execute("""insert into {table} (date, amount, description) values ({dateValue}, {amountValue}, "{descValue}")""".\
            format(table=self.trans_table_name, dateValue=dateStr, amountValue=amount, descValue=desc))


    def __getStatisticsFromData(self):
        statistics = {}

        totalPayment = 0

        unprocessedDesc = []
        for date, amount, desc in self.transData:
            processedDesc = False
            for keyword, categoryPath in self.spending.keywordCategoryMapping.iteritems():
                if(re.search(keyword, desc, re.IGNORECASE)):
                    if(amount < 0):
                        if(amount < -self.spendingHighlightTh):
                            self.spending.addTransaction(categoryPath + "/" + desc, -amount)
                        else:
                            self.spending.addTransaction(categoryPath, -amount) # amount is negative, convert it to positive number
                        processedDesc = True
                        break;
                    else:
                        self.income.addTransaction(categoryPath, amount)
                        processedDesc = True
                        break;
            if(processedDesc is False):
                unprocessedDesc.append((date, amount, desc))
                if(amount < 0):
                    self.spending.addTransaction("Other", -amount)
                else:
                    self.income.addTransaction("Other", amount)


        if(len(unprocessedDesc) > 0):
            print "Not classified transactions:"
            for date, amount, desc in unprocessedDesc:
                print date, ": ", amount , "\t", desc

        # statistics['Total Payment'] = totalPayment

        return statistics



    def __processBOAData(self, file):
        print "Process BOA data:", file
        with open(file, 'r') as csvFile:
            data = csv.DictReader(csvFile, delimiter = ',')
            for row in data:
                month, year = getMonthAndYearFromDate(row['Posted Date'])
                # print month, self.month, year, self.year
                if(month == self.month and year == self.year and str(row) not in self.trans):
                    self.trans.add(str(row))
                    self.transData.append((row['Posted Date'], float(row['Amount']), row['Payee']))


    def __processChaseData(self, file):
        print "Process Chase data:", file
        with open(file, 'r') as csvFile:
            data = csv.DictReader(csvFile, delimiter = ',')
            for row in data:
                # print row['Type'], row['Trans Date'], row['Description'],row['Amount']
                month, year = getMonthAndYearFromDate(row['Trans Date'])
                if(month == self.month and year == self.year and str(row) not in self.trans):
                    self.trans.add(str(row))
                    self.transData.append((row['Trans Date'], float(row['Amount']), row['Description']))


    def __processAmexData(self, file):
        print "Process Amex data:", file
        with open(file, 'r') as csvFile:
            data = csv.reader(csvFile, delimiter=',')
            for row in data:
                # print row
                if(len(row) > 4):
                    month, year = getMonthAndYearFromDate(row[0])
                    if(month == self.month and year == self.year and str(row) not in self.trans):
                        self.transData.append((row[0], float(row[2]), row[3]))
                        self.trans.add(str(row))


    def printAllTransData(self):
        for date, amount, desc in self.transData:
            print date, ": ", amount, "\t", desc
