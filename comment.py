import sqlite3
from databasable import databasable
import RedditManagerUtils

class comment(databasable):

    def __init__(self, comment_id, post_id=None, username=None, parent_comment=None, comment_karma=None,
                 comment_date=None, subreddit=None, cursor=None):

        super().__init__(cursor)

        self.comment_id = comment_id
        self.post_id = post_id
        self.username = username
        self.parent_comment = parent_comment
        self.comment_karma = comment_karma
        self.comment_date = comment_date
        self.subreddit = subreddit

    def fetch(self):
        # TODO: update the current values of this comment

        comment = RedditManagerUtils.RedditManager.fetchCommentMeta(self.comment_id)

        self.comment_id = comment.comment_id
        self.post_id = comment.post_id
        if self.username is not None:
            self.username = comment.username
        self.parent_comment = comment.parent_comment
        self.comment_karma = comment.comment_karma
        self.comment_date = comment.comment_date
        self.subreddit = comment.subreddit

        pass

    def update(self, cursor=None):

        # TODO: update the database representation, or insert.

        while True:

            try:

                active_cursor = None

                active_cursor = super().update(cursor)

                # TODO: update the database representation, or insert

                str = ''

                if self.parent_comment is not None:

                    str = 'INSERT OR REPLACE INTO comments(comment_id, post_id, username, parent_comment, comment_karma, comment_date, subreddit) ' \
                    'VALUES (\'{comment_id}\',' \
                    '\'{post_id}\',' \
                    '\'{username}\',' \
                    '\'{parent_comment}\',' \
                    '{comment_karma},' \
                    '{comment_date},'\
                    '\'{subreddit}\''\
                    ')'

                    query = str.format(comment_id=self.comment_id, post_id=self.post_id,
                                       username=self.username, parent_comment=self.parent_comment,
                                       comment_karma=self.comment_karma, comment_date=self.comment_date,
                                       subreddit=self.subreddit)


                else:

                    str = 'INSERT OR REPLACE INTO comments(comment_id, post_id, username, parent_comment, comment_karma, comment_date, subreddit) ' \
                    'VALUES (\'{comment_id}\',' \
                    '\'{post_id}\',' \
                    '\'{username}\',' \
                    'NULL,' \
                    '{comment_karma},' \
                    '{comment_date},'\
                    '\'{subreddit}\'' \
                    ')'

                    query = str.format(comment_id=self.comment_id, post_id=self.post_id,
                                       username=self.username,
                                       comment_karma=self.comment_karma, comment_date=self.comment_date,
                                       subreddit=self.subreddit)



                active_cursor.execute(
                    query
                )

                print("Updated " + self.comment_id)

                break

            except sqlite3.OperationalError:

                print("Database error. Trying again...")