from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common import action_chains, keys
import os
from os.path import isfile, join
import datetime

DOWNLOAD_FOLDER="/Users/XiangChen1/Downloads/"

def getAmexData(username, password):
    def cleanDownloadFolder():
        def isAmexData(f):
            if("ofx" in f or "Amex_" in f):
                return True
            else:
                return False

        path=DOWNLOAD_FOLDER
        onlyfiles = [f for f in os.listdir(path) if isfile(join(path, f))]
        amexDataFiles = [f for f in onlyfiles if isAmexData(f)]
        for f in amexDataFiles:
            os.remove(path + f)

    def clickLastStatement(driver, statements):
        action = action_chains.ActionChains(driver)
        action.move_to_element(statements)
        action.send_keys(keys.Keys.TAB)
        action.send_keys(keys.Keys.TAB)
        action.send_keys(keys.Keys.TAB)
        action.send_keys(keys.Keys.ENTER)
        action.perform()

    def logIn(driver):
        driver.get("https://www.americanexpress.com/")
        wait = WebDriverWait(driver, 5)
        inputElement = wait.until(EC.visibility_of_element_located((By.NAME, "UserID")))
        inputElement.send_keys(username)
        pwdElement = wait.until(EC.visibility_of_element_located((By.NAME, "Password")))
        pwdElement.send_keys(password)
        pwdElement.submit()

    def goToDownLoadPagePointToStatements(driver):
        driver.get("https://online.americanexpress.com/myca/ofxdl/us/domesticOptions.do?request_type=authreg_ofxdownload&Face=en_US&intlink=des_downloadcardact")
        csvButton = driver.find_element_by_id("nav_6").click()
        lastStatement = driver.find_element_by_id("download-list-0")
        statements = driver.find_element_by_id("downloadDates0")
        return statements

    def changeFileName(card="Cashback", bankName="Amex"):
        now = datetime.datetime.now()
        month = "%02d" % (now.month,)
        year = (str(now.year))[-2:]
        fileName = bankName + "_" + card + "_" + month + year + ".csv"
        os.rename(DOWNLOAD_FOLDER + "ofx.csv", DOWNLOAD_FOLDER + fileName)

    # cleanDownloadFolder()
    driver = webdriver.Chrome()
    logIn(driver)
    statements = goToDownLoadPagePointToStatements(driver)
    clickLastStatement(driver, statements)
    driver.find_element_by_id("downloadFormButton").click()
    time.sleep(5) # wait the data to be downloaded
    changeFileName()
    return driver


if __name__ == '__main__':
    import getpass

    uname = raw_input("Username for Amex: ")
    pwd = getpass.getpass()

    getAmexData(uname, pwd)
