#!/usr/bin/env python
"""
This tool processes the data from BOA, Chase and Amex.
Usage: ./test.py -m 9
NOTE: when changing the "category.csv" file, save it as "windows comma spread sheet"
"""
import csv, glob
import billProcessorCore
import click
import parser

def loadData(month, year, highlight_threshold, root_folder = "Data"):
    # Find all .csv files in the data folder
    fileList = glob.glob(root_folder + "/*.csv") + glob.glob(root_folder + "/*.CSV")

    # Process each file
    billProcessor = billProcessorCore.BillDataProcessor()
    parser.Parser().parseData(fileList)
    billProcessor.loadData(year, month)
    billProcessor.printStatistics(float(highlight_threshold))

    # billProcessor.printAllTransData()


@click.command()
@click.option('-m','--month',type=click.IntRange(1, 12),
                help='Month of interest')
@click.option('-y','--year',type=click.IntRange(2000, 3000),
                help='Year of interest')
@click.option('-t', '--highlight_threshold', type=click.FLOAT,
                default=100,
                help='Threshold of highlight spending in result')
def processDataOnMonthAndYear(month, year, highlight_threshold):
    print "Month of interst:", month, "/", year
    loadData(month, year, highlight_threshold)


if __name__ == '__main__':
    processDataOnMonthAndYear()
