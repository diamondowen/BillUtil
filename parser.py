#!/usr/bin/python
from abc import ABCMeta, abstractmethod
import sqlite3
from transaction import *
import datetime
import csv, re


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

class Parser:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.sqlite_file = 'transactions_db.sqlite'
        self.trans_table_name = 'transactions'
        self.processed_data_files_table_name = 'processed_data_files'
        self.currentDate = datetime.date.today().strftime('%m/%d/%Y')
        self.errMessage = ""

    # @abstractmethod doParseData(self): pass

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
                elif "Citi" in file:
                    transFile = self.__parseCitiData(file)
                    self.__saveDataToDB(transFile)
                else:
                    self.errMessage += "Non-recognized data: " + file

        if(len(self.errMessage) > 0):
            print self.errMessage

    def __saveDataToDB(self, transFile):
        conn = sqlite3.connect(self.sqlite_file)
        c = conn.cursor()

        transData = transFile.transactions
        for transInfo in transData:
            (date, bankSource, card, amount, desc) = transInfo.getTuple()

            dateStr = self.__formatDate(date)
            data = c.execute('SELECT * FROM {table} WHERE date = {dateValue} AND bank = "{bankSourceValue}" AND card = "{cardValue}" AND amount = {amountValue} AND description = "{descValue}"'. \
                             format(table=self.trans_table_name, dateValue=dateStr, bankSourceValue=bankSource, amountValue=amount, descValue=desc, cardValue=card))

            if(data.fetchone() is None):
                c.execute("""insert into {table} (date, bank, card, amount, description) values ({dateValue}, "{bankSource}", "{cardValue}", {amountValue}, "{descValue}")""". \
                          format(table=self.trans_table_name, dateValue=dateStr, amountValue=amount, descValue=desc, bankSource=bankSource, cardValue=card))

        c.execute("""insert into {table} ("file_name", "last_parsing_date") values ("{filename}", "{parsingDate}")""". \
                  format(table=self.processed_data_files_table_name, filename=transFile.filename, parsingDate=self.currentDate))
        conn.commit()
        conn.close()


    def __formatDate(self, date):
        dateStrList = re.findall('[0-9]+', date)
        month = dateStrList[0]
        date = dateStrList[1]
        year = dateStrList[2]
        return '"' + year+"-"+month+"-"+date + '"'


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

    def __parseCitiData(self, file):
        print "Process Citi data:", file
        card = file.split("_")[1]
        transData = []

        with open(file, 'r') as csvFile:
            data = csv.DictReader(csvFile, delimiter = ',')
            for row in data:
                month, date, year = getMonthDateAndYearFromDate(row['Date'])
                if(row['Debit'] == False):
                    amount = float(row['Credit']) #check plus or minus
                else:
                    amount = -float(row['Debit'])
                transData.append(TransactionInfo(row['Date'], "Citi", card, amount, row['Description']))
        return TransactionFile(file, self.currentDate, transData)


    def __parseChaseData(self, file):
        print "Process Chase data:", file
        card = file.split("_")[1]
        transData = []

        with open(file, 'r') as csvFile:
            data = csv.DictReader(csvFile, delimiter = ',')
            for row in data:
                # print row['Type'], row['Trans Date'], row['Description'],row['Amount']
                # month, date, year = getMonthDateAndYearFromDate(row['Trans Date'])
                if('Trans Date' in row):
                    transDate = row['Trans Date']
                elif('Posting Date' in row):
                    transDate = row['Posting Date']
                else:
                    raise Exception('Unknown transaction date in Chase data: ' + str(file))

                transData.append(TransactionInfo(transDate, "Chase", card, float(row['Amount']), row['Description']))
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