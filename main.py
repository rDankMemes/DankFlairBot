import praw
import sqlite3


import time
import threading
import ThreadedServices
from DatabaseManager import DatabaseManager
from RedditManagerUtils import RedditManager
from DisplayManager import DisplayManager
from ruamel.yaml import YAML
import threading
import Rule
from RulesManager import RulesManager
import sys

SUBREDDIT = "dankmemes"

def main():

    DatabaseManager.init_connection('test.sqlite')

    DatabaseManager.create_tables()

    RedditManager.login_threads_from_file("config.yml")

    ThreadedServices.read_setting_from_file("settings.yml")

#    DisplayManager.addSubreddit("BotParty")


 #   for i in range(100):
  #      time.sleep(0.1)
   #     DisplayManager.update()

#     RedditManager.send_message("This is a test",
# """Wow!
#
# This is going ***MULTILINE***
#
# I hope it works.
#
# """, recipient="ELFAHBEHT_SOOP")

    #ThreadedServices.setup_threads("BotParty")

    ThreadedServices.setup_threads("CongratsLikeImFive")


    #    RedditManager.get_bans("BotParty")

 #   RedditManager.get_messages()

#    ThreadedServices.setup_threads(SUBREDDIT)

#    ThreadedServices.setup_threads("OnionHate")

#    ThreadedServices.setup_threads("OnionHate")

    time.sleep(10)

    while not ThreadedServices.threads_stopped:
        time.sleep(0)

    print(threading.enumerate())

    print("Dead.")


if __name__ == "__main__":
    main()