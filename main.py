#!/usr/bin/env python
"""
This tool processes the data from BOA, Chase and Amex.
Usage: ./test.py -m 9 -v yes
NOTE: when changing the "category.csv" file, save it as "windows comma spread sheet"
"""
import csv, glob
import billProcessorCore
import click

def loadData(month, year, visualization = False, root_folder = "Data"):
    # Find all .csv files in the data folder
    fileList = glob.glob(root_folder + "/*.csv") + glob.glob(root_folder + "/*.CSV")

    # Process each file
    billProcessor = billProcessorCore.BillDataProcessor(month, year)
    billProcessor.processData(fileList)
    billProcessor.printStatistics()

    visualize(visualization)

    # billProcessor.printAllTransData()

def visualize(flag):
    print "Visualization: ", flag

@click.command()
@click.option('-m','--month',type=click.IntRange(1, 12),
                help='Month of interest')
@click.option('-y','--year',type=click.IntRange(2000, 3000),
                help='Year of interest')
@click.option('-v','--visualization',type=click.BOOL, default=0, help='Visualize result')
def processDataOnMonth(month, year, visualization):
    print "Month of interst:", month, "/", year
    loadData(month, year, visualization)


if __name__ == '__main__':
    processDataOnMonth()
