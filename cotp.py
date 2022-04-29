##### - Skoden's COTP Script

from asyncio.windows_events import NULL
import copy
from glob import glob
import logging
import os
import requests
import socket
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException        

from time import sleep
import datetime as dt
from datetime import timezone, timedelta
from random import randint

# config imports
from config import *
licenseUrl = 'https://bit.ly/3iM9Xjv'

# helper functions
def get_number_of_elements(list):
    count = 0
    for element in list:
        count += 1
    return count

# set IFTTT variables
iftttBase = 'https://maker.ifttt.com/trigger/'
iftttMid = '/with/key/'
iftttEnd = '?value1='

#Global Profit Variables
dailyCycleProfit = 0
dailyRefProfit = 0
cycleStartBal = 0
cycleEndBal = 0

# set login and cycle parameters (in minutes)
loginBackoffList = [0, 0.1, 1, 4, 10, 15, 30] # 60 minutes
#loginBackoffList = [0, 1, 2] # testing
cycleBackoffList = [0, 1, 2, 3, 5, 9, 10, 15, 20, 20, 20, 20, 20] # 145 minutes
#cycleBackoffList = [0, 1, 2] # testing
cycleSuccessIntervalMin = 120
cycleSuccessIntervalMax = 125

# initialize Bot class
class Bot():

    def __init__(self) -> None:

        # set cycle loop variables
        cycleIndex = 0
        cycleIterations = get_number_of_elements(cycleBackoffList)

        # determine machine ID
        machineID = socket.gethostname()
        logging_info('Determine Machine ID from Hostname: %s', machineID)

        while True:
            try:
                logger = logging.getLogger()
                
                logging_info('Setting ChromeDriver options...')
                chrome_options = Options()
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument('--ignore-certificate-errors')
                chrome_options.add_argument('--ignore-ssl-errors')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options_headless = copy.deepcopy(chrome_options)
                chrome_options_headless.add_argument('--headless')
                
                logging_info('Initializing ChromeDriver...')
                self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options_headless)
    
                # check license URL (if applicable)
                # if licenseUrl != '':
                #     try:
                #         self.driver.get(licenseUrl)
                #         if self.driver.find_element(By.XPATH, "//*[contains(text(), '" + machineID + "')]"):
                #             logging_info('Machine ID licensed!')
                #             licensed = True
                #         else:
                #             logging_info('Machine ID not licensed!')
                #             licensed = False
                #     except:
                #         logging_info('Machine ID not licensed!')
                #         licensed = False
                # else:
                #     logging_info('Machine ID cannot be determined!')
                #     licensed = False
                licensed = True
                # if not licensed then terminate
                if licensed == False:
                    self.driver.quit()
                    sys.exit(1)

                # reinitialize chromedriver with UI (if applicable)
                headlessBool = str_to_bool(headless)
                if headlessBool == False and "IS_DOCKER_CONTAINER" not in os.environ:
                    logging_info('Reinitializing ChromeDriver with UI...')
                    self.driver.quit()
                    self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

                # set login loop variables
                logger.disabled = False
                loginSucess = False
                loginIndex = 0
                loginIterations = get_number_of_elements(loginBackoffList)

                # begin login loop
                while loginSucess == False and loginIndex <= loginIterations and licensed == True:
                    try:
                        if (loginIndex >= loginIterations):
                            logging_critical("Too many failed login attempts: %s", loginIndex)
                            logging_critical("Quitting application...")
                            self.driver.quit()
                            sys.exit(1)

                        sleepTime = loginBackoffList[loginIndex]
                        sleepTimeSeconds = sleepTime * 60 + 3
                        logging_info("Starting login attempt #%s", loginIndex+1,)
                        logging_info("Waiting %s minute(s) before attempting again", sleepTime)
                        sleep(sleepTimeSeconds)
                        loginSuccess = self.login(countryCode, phone, password)
                        if loginSuccess == True:
                            logging_info('Login succeeded!')
                            loginIndex = 0 # reset login index after success
                            break
                        elif loginSuccess == False:
                            if loginIndex > 1:
                                logging_critical('Login failed...')
                            loginIndex += 1
                    except Exception as e:
                        logging_critical('%s', e)
                        self.driver.close()
                        loginSuccess = False
                        if loginIndex > 1:
                            logging_critical('Login failed...')
                        loginIndex += 1
                        continue
                
                ready = self.cycleReady()       # adding in a cycle ready check so ref bonuses are only grabbed one time before cyclying trades.
                
                if ready == True:
                    # do referrals
                    if doReferral == True:
                        logging_info("Retrieve team bonuses before cycling trades...")
                        self.referrals()
                    
                    # do transaction cycle
                    if doCycle == True:    
                        cycled = self.cycleCheck()
                    else:
                        cycled = False  # adding in a condition so the app does not crash when doCycle is false. 
                else:
                    cycled = False  # adding in a condition so the app does not crash when doCycle is false
            
            # catch try exceptions
            except Exception as e:
                logging_critical('%s', e)
                if iftttEnabled == True:
                    get_url(self, iftttBase+iftttProblem+iftttMid+iftttKeyCode+iftttEnd+iftttNames)
                sleep(1)
                continue
            
            if cycled == True:
                cycleIndex = 0 # reset cycle index on success
                sleepTime = randint(cycleSuccessIntervalMin, cycleSuccessIntervalMax)
                sleepTimeSeconds = sleepTime * 60
                logging_info('All trades initialized - waiting %s minutes...', sleepTime)
                dataTimeDelta = (dt.datetime.now() + timedelta(seconds=sleepTimeSeconds)).strftime('%H:%M:%S')
                logging_info('Waiting until %s UTC before trying again...', dataTimeDelta)
                if iftttEnabled == True:
                    get_url(self, iftttBase+iftttProblem+iftttMid+iftttKeyCode+iftttEnd+iftttNames)
                    sleep(2)
            else:
                logging_info('Trades not initialized...')
                cycleIndex += 1
                if (cycleIndex >= cycleIterations):
                    logging_critical("Too many failed cycle attempts: %s", cycleIndex)
                    logging_critical("Quitting application...")
                    self.driver.quit()
                    sys.exit(1)
                sleepTime = cycleBackoffList[cycleIndex]
                sleepTimeSeconds = sleepTime * 60
                dateTimeDelta = (dt.datetime.now() + timedelta(seconds=sleepTimeSeconds)).strftime('%H:%M:%S')
                logging_info("Restarting cycle attempt: %s", cycleIndex+1)
                logging_info("Wait before cycle attempt: %s minute(s)", sleepTime)
                logging_info('Waiting until %s UTC before trying again...', dateTimeDelta)

            # close driver before next cycle (why?)
            self.driver.close()
            sleep(sleepTimeSeconds)
    
    def clickThis(self, element):
        try:
            wait = WebDriverWait(self.driver, 60)
            clickBtn = wait.until(EC.presence_of_element_located((By.XPATH, element)))
            clickBtn.click()
            #logging_info('Clicked element: %s', element)
        except Exception as e:
            pass
            #logging_warning('%s', e)

    def login(self, countryCode, phone, password):

        currentUrl = self.driver.current_url
        if 'pages/userCenter/userCenter' in currentUrl:
            loginSuccess = True
        else:
            currentUrl = get_url(self, 'https://www.cotps.com/#/pages/phonecode/phonecode?from=login') # load phone code 
            
            # handle country code
            try:
                if WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[1]/uni-view/uni-input/div/input'))):
                    self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[1]/uni-view/uni-input/div/input').send_keys(countryCode)
                    self.clickThis('/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[1]/uni-button') # Submit Country Code     
                    sleep(2)
                    currentUrl = self.driver.current_url
                    logging_info("Current driver URL: %s", currentUrl)
                    if 'phonecode' in currentUrl:
                        self.clickThis('/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[1]/uni-button') # Submit Country Code        
            except Exception as e:
                logging_critical('%s', e)
                logging_critical('Could not enter country code!')
                loginSuccess = False         
            
            # handle phone + password
            try:
                if WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[5]/uni-input/div/input')))   \
                        and WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[7]/uni-input/div/input'))):
                    self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[5]/uni-input/div/input').send_keys(phone)      # send Phone Number
                    self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[7]/uni-input/div/input').send_keys(password)     # send Password
                    sleep(2)
                    self.clickThis('/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-button') # Click Login Button
                    sleep(5)
                    currentUrl = self.driver.current_url
                    logging_info("Current driver URL: %s", currentUrl)
                    if 'login' in currentUrl:
                        loginSuccess = False
                    else:
                        loginSuccess = True
            except Exception as e:
                logging_critical('%s', e)
                logging_critical('Could not enter phone or email!')
                loginSuccess = False                

        return loginSuccess

    def referrals(self):
        global dailyRefProfit
        sleep(1)
        get_url(self, 'https://www.cotps.com/#/pages/userCenter/myTeam') # Open My Team
        refLevelElement1 = '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[1]/uni-view[1]' # Level 1
        refLevelElement2 = '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[1]/uni-view[2]' # Level 2
        refLevelElement3 = '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[1]/uni-view[3]' # Level 3
        refLevelReceive = '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[2]/uni-view/uni-button' # Receive Button
        refSleepDelay = 3 # seconds
        ref1 = ref2 = ref3 = 0.0

        # Team: Level 1
        try:  
            sleep(refSleepDelay)
            self.clickThis(refLevelElement1)
            ref1 = str_to_float(self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[2]/uni-view/uni-view[1]/uni-view[2]/uni-view[2]').text)
            logging_info("Received Level 1 team balance %s", ref1)
            sleep(refSleepDelay)
            self.clickThis(refLevelReceive)
            sleep(refSleepDelay)
        except:
            logging_warning('No team bonus to claim at Level 1...')

        # Team: Level 2
        try:
            sleep(refSleepDelay)
            self.clickThis(refLevelElement2)
            sleep(refSleepDelay)
            ref2 = str_to_float(self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[2]/uni-view/uni-view[1]/uni-view[2]/uni-view[2]').text)
            logging_info("Received Level 2 team balance %s", ref2)
            self.clickThis(refLevelReceive)
            sleep(refSleepDelay)
        except:
            logging_warning('No team bonus to claim at Level 2...')

        # Team: Level 3
        try:
            sleep(refSleepDelay)
            self.clickThis(refLevelElement3)
            sleep(refSleepDelay)
            ref3 = str_to_float(self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[2]/uni-view/uni-view[1]/uni-view[2]/uni-view[2]').text)
            logging_info("Received Level 3 team balance %s", ref3)
            self.clickThis(refLevelReceive)
            sleep(refSleepDelay)
        except:
            logging_warning('No team bonus to claim at Level 3...')
        
        logging_info("Total team bonus this round %s", (ref1+ref2+ref3))
        dailyRefProfit += (ref1+ref2+ref3)
        logging_info("Daily Team Bonus so far: %s", dailyRefProfit)
        


    # Transactions
    def cycleCheck(self):
        global cycleEndBal, cycleStartBal, dailyCycleProfit, dailyRefProfit
        get_url(self, 'https://www.cotps.com/#/pages/transaction/transaction') # Transaction Hall
        sleep(2)
        tBalance = str_to_float(self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[3]/uni-view[1]/uni-view[2]').text)
        wBalance = str_to_float(self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[3]/uni-view[2]/uni-view[2]').text)
        logging_info("Transaction balance: %s", tBalance)
        logging_info("Wallet balance: %s", wBalance)
        
        # set threshold based on daily profit
        currentTime = dt.datetime.now(timezone.utc).hour
        if minTimeForProfits < currentTime < maxTimeForProfits:
            txThreshold = 5
            logging_critical("Script stopping for Profit window. you have %s seconds", dailyProfit)
            sleep(dailyProfit)
        else:
            txThreshold = 5

        # ensure threshold is greater than 5 (as a fallback)
        if txThreshold < 5:
            txThreshold = 5

        if tBalance == 0:
            
            #determine previous cycle profits
            cycleStartBal = wBalance
            logging_info("Start of cycle account balance: %s", cycleStartBal)
            cycleProfit = cycleStartBal-cycleEndBal
            logging_info("Profits from last cycle: %s", cycleProfit)

            dailyCycleProfit += cycleProfit
            logging_info("Daily Profits so far: %s", dailyCycleProfit)
            if 1 < currentTime < 3:
                logging_info("Today's Total Cycle Profits: %s", dailyCycleProfit)
                dailyCycleProfit = dailyRefProfit = 0
                logging_info("Resetting daily profit running total to %s", dailyCycleProfit)

            
            # do transactions
            logging_info("Starting new transaction cycle!")
            while wBalance > float(txThreshold):
                self.clickThis('/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[4]/uni-button')     # start transaction                
                self.clickThis('/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[7]/uni-view/uni-view/uni-view[6]/uni-button[2]')     # Transaction Sell Button
                self.clickThis('/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[8]/uni-view/uni-view/uni-button')        #Transaction Confirmation Button
                sleep(2)
                wBalance = str_to_float(self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[3]/uni-view[2]/uni-view[2]').text)
            logging_info("Finished transactions!")            

            if iftttEnabled == True and txThreshold > 5:
                get_url(self, iftttBase+iftttProblem+iftttMid+iftttKeyCode+iftttEnd+iftttNames)
                sleep(2)
            cycled = True
            tBalance = str_to_float(self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[3]/uni-view[1]/uni-view[2]').text)
            wBalance = str_to_float(self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[3]/uni-view[2]/uni-view[2]').text)
            cycleEndBal = float(wBalance) + float(tBalance)
            logging_info("End of cycle account balance: %s", cycleStartBal)
        else:
            cycled = False
            
        return cycled
    
    def cycleReady(self):
        get_url(self, 'https://www.cotps.com/#/pages/transaction/transaction') # Transaction Hall
        sleep(2)
        tBalance = str_to_float(self.driver.find_element(By.XPATH, '/html/body/uni-app/uni-page/uni-page-wrapper/uni-page-body/uni-view/uni-view[3]/uni-view[1]/uni-view[2]').text)
        
        if tBalance == 0:
            ready = True
            logging_info("Transaction balance: %s - ready to cycle trades!", tBalance)
        else:
            ready = False
            logging_info("Transaction balance: %s - not ready to cycle trades yet...", tBalance)
        
        return ready

def get_url(self, url):
    logging_info("Requesting URL: %s", url)
    self.driver.get(url)
    currentUrl = self.driver.current_url
    logging_info("Current driver URL: %s", currentUrl)
    return currentUrl

def str_to_float(str):
    if str != '':
        flt = float(str)
        #logging_info("Converted string to float: %s", flt)
        return flt  
    else:
        flt = '0'
        #logging_info("Converted empty string to float: %s", flt)
        return flt

def logging_info(message, var = ''):
    if (var == ''):
        logging.info(message)
    else:
        logging.info(message, var)
    message = message.replace('%s', str(var))
    data = {
        "content" : "INFO:" + message,
        "username" : "4045905239"
    }
    print(data)
    if discordWebhook != "":
        requests.post(discordWebhook, json = data)

def logging_critical(message, var = ''):
    if (var == ''):
        logging.critical(message)
    else:
        logging.critical(message, var)
    message = message.replace('%s', str(var))
    data = {
        "content" : "<@" + discordPingID + "> CRITICAL:" + message,
        "username" : "4045905239"
    }
    print(data)
    if discordWebhook != "":
        requests.post(discordWebhook, json = data)

def logging_warning(message, var = ''):
    if (var == ''):
        logging.warning(message)
    else:
        logging.warning(message, var)
    message = message.replace('%s', str(var))
    data = {
        "content" : "<@" + discordPingID + "> WARNING:" + message,
        "username" : "4045905239"
    }
    print(data)
    if discordWebhook != "":
        requests.post(discordWebhook, json = data)

def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         return False # assume all other values are false

def main():
    while True:
        logging.basicConfig(stream=sys.stdout, level=logLevel)
        logging_info('-- STARTING COTPS DRIVER -- ')
        delayStartTimer = cycleBackoffList[0]
        logging_info('Waiting %s seconds before starting the script...', delayStartTimer)
        sleep(delayStartTimer)
        my_bot = Bot()
       

if __name__ == '__main__':
    main()