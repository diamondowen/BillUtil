# BillUtil
This project is a bill utility to process statements from banks and analyze income and spending. The motivation of this project is to create self-organized income and spending analytics without using other tools such as "mint.com" so that the risk of unfolding the bank account information can be reduced. This project is written in Python.

1. Bill data:
Credit card bill statements from BOA, Chase and American Express are supported in the current version. The bills should be saved as "csv" format in the "Data" folder. The file name of BOA statement should contain the keyword "BOA". The file name of Chase statement should contain "Chase" and the file name of American Express statement should contain the keyword "Amex".

2. Categories:
A self-specified csv file called "categories.csv" is used to setup the categories for each transactions. There are two columns in this file. The first column is the keywords of the transaction. The second column is the category for the transaction. The format of the category input should be: main category/ sub-category/ sub-sub-category... Note that the categories.csv file should be saved as "windows comma seperated (csv)" if you are using Mac.

3. Visualization:
Not supported in the current version

4. Usage:
In the folder containing "main.py", type: ./main.py -m 1, -y 2016, -v true


Need to install Selenium: http://selenium-python.readthedocs.io/installation.html
