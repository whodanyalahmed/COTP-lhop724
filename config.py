# COTP Automation Config File
#
# Please adjust the settings to match your account.
# Please keep the '' and "" in the code, do not remove them.

# The script will cycle trades then wait between 7300 and 7500 second before trying to cyle again
# If it does not cycle, then it will wait between 30 and 120 seconds before trying again.

# Single Account only.


countryCode = '1'        # - Do not add a + here. Just the number
phone = '4045905239'     # - No spaces or punctuation
username = '4045905239'
password ='COTPS2022!'     # - Dont have spaces between the '' - should look like: ='P4ssW0rd!'
doCycle = True          # Cycle Trades
doReferral = False       # Collect Referral Bonuses. 
doReferral = False       # Collect Referral Bonuses.

headless = 'True'       # Options: Auto/True/False



#IF This Then That -  Webhooks and Profit Timings
# IF This Then That -  Webhooks and Profit Timings
# If you know what IFTTT is, you can set up an account for free and receive email notifications when your script runs.

iftttEnabled = False

iftttKeyCode = 'xxxxxx'

iftttSuccess = 'COTPCylced'    #Notification when trades have been cycled
iftttSuccess = 'COTPCylced'  # Notification when trades have been cycled
iftttProblem = 'COTPProblem'  # There was an issue with the script, please check it
iftttProfit = 'COTPCylced'  # Profits are ready to be collected
iftttNames = 'Main'

discordWebhook = ''     # See the walkthrough guide in the Google Drive on how to set this up
# See the walkthrough guide in the Google Drive on how to set this up
discordWebhook = ''


dailyProfitSleepTimer = 0        # - the amount of time the script will sleep for when it tries to cycle trades in the below defined window
# - the amount of time the script will sleep for when it tries to cycle trades in the below defined window
dailyProfitSleepTimer = 0
# the min time window of day Profits will be available to withdraw ***IN UTC*** - Hour Only - no minutes
minTimeForProfits = 0
# the max time window of day Profits will be available to withdraw ***IN UTC***
maxTimeForProfits = 0
logLevel = 'INFO'       # Sets the logging level of the application
                        # - CRITICAL [50]
# - CRITICAL [50]
# - ERROR [40]
# - WARNING [30]
# - INFO [20]
# - DEBUG [10]
# - NOTSET [0]
