import sqlite3
from databasable import databasable
import RedditManagerUtils

class post(databasable):

    def __init__(self, post_id, username=None, subreddit=None,
                 post_karma=None, post_date=None, max_sub_rank=None, max_all_rank=None, cursor=None):

        # Initialize the super class.
        super().__init__(cursor)

        self.post_id = post_id
        self.username = username
        self.subreddit = subreddit
        self.post_karma = post_karma
        self.post_date = post_date
        self.max_sub_rank = max_sub_rank
        self.max_all_rank = max_all_rank

    def fetchall(self):



        pass

    def fetch(self):

        post = RedditManagerUtils.RedditManager.fetchPostMeta(self.post_id)

        self.post_id = post.post_id

        if self.username is None:
            self.username = post.username
        self.subreddit = post.subreddit
        self.post_karma = post.post_karma
        self.post_date = post.post_date



        pass


    def update(self, cursor):

        # TODO: update the database representation, or insert.

        while True:

            try:

                active_cursor = None

                active_cursor = super().update(cursor)

                # TODO: update the database representation, or insert

                str = 'INSERT OR REPLACE INTO posts(post_id, username, subreddit, post_karma, post_date) ' \
                      'VALUES (\'{post_id}\',' \
                      '\'{username}\',' \
                      '\'{subreddit}\',' \
                      '{post_karma},' \
                      '{post_date}' \
                      ')'

                query = str.format(post_id=self.post_id, username=self.username, subreddit=self.subreddit,
                                   post_karma=self.post_karma, post_date=self.post_date)

                active_cursor.execute(
                    query
                )

                print("Updated Post " + self.post_id)

                break

            except sqlite3.OperationalError:

                print("Database error. Trying again...")