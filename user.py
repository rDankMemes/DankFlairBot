import sqlite3
from databasable import databasable
from InfoNotFetchedError import InfoNotFetchedError
#from MissingCursorError import MissingCursorError

from DisplayManager import DisplayManager

import RedditManagerUtils
import time


class user(databasable):

    #
    #
    def __init__(self, username, subreddit, user_id=None, user_comment_karma=0, user_post_karma=0, cursor=None):

        #Initialize the super class.
        super().__init__(cursor)

        self.username = username
        self.subreddit  = subreddit
        self.userid = user_id
        self.last_update = -1
        self.user_comment_karma = user_comment_karma
        self.user_post_karma = user_post_karma


    def fetchall(self):

        # TODO: Fetch the object representation for a user from reddit.
        # TODO: Fetch new karma counts for applicable comments
        # TODO: Recalculate user comment karma
        # TODO:
        # TODO:

        pass

    def fetch(self):

        # TODO: Fetch the object representation from reddit

        new_user = RedditManagerUtils.RedditManager.fetchUserMeta(self.username, self.subreddit)

        if new_user is None:
            return False

        self.username = new_user.username
        self.subreddit = new_user.subreddit
        self.userid = new_user.userid

        self.last_update = int(time.time())

        return True

        pass


    def update(self, cursor = None):

        while True:

            try:
                active_cursor = None

                if(self.username is None or self.subreddit is None):
                    raise InfoNotFetchedError

                active_cursor = super().update(cursor)

                str = 'INSERT OR REPLACE INTO users(username, subreddit, user_id, last_update) ' \
                    'VALUES (\'{username}\',' \
                    '\'{subreddit}\',' \
                    '\'{userid}\',' \
                    '{update_time}' \
                    ')'

                query = str.format(username=self.username, subreddit=self.subreddit, userid=self.userid,
                                   update_time=self.last_update)

                active_cursor.execute(
                    query
                )

                #print("Updated user " + self.username)

                # Break the loop because it works.
                break

            except sqlite3.OperationalError:

                DisplayManager.displayStatusString("Database error. Trying again...")

    def __str__(self):

        return 'user(username=\'{username}\')'.format(username=self.username)

