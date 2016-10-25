#!/usr/bin/python
import csv
import re

class TransactionFile:
    def __init__(self, filename, parsingDate, transactions):
        self.filename = filename.split("/")[-1]
        self.parsingDate = parsingDate
        self.transactions = transactions




class TransactionInfo:
    def __init__(self, date, bank, card, amount, description):
        self.date = date
        self.bank = bank
        self.card = card
        self.amount = amount
        self.description = description
