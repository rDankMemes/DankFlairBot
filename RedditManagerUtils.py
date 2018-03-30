import praw
import Constants

from DatabaseManager import DatabaseManager

from user import user

from post import post
from comment import comment


import time

import threading

from ruamel.yaml import YAML

class RedditManager():

    __praw_reddit = None

    _praw_dict = dict()

    # List of praw instances that don't have mod privileges
    _worker_reddits = []

    # List of praw instances that do have mod privileges
    _mod_reddits = []

    mod_index = 0

    worker_index = 0

    _thread_lock = False

    def __init__(self, username=None, password=None, client_id=None, client_secret=None):

        RedditManager.__praw_reddit = None

        if(username is not None
           and password is not None
           and client_id is not None
           and client_secret is not None):
            self.login(username, password, client_id, client_secret)

        pass

    @staticmethod
    def login_threads_from_file(file_path):

        login_file = open(file_path)

        file_string = login_file.read()

        yaml = YAML(typ='safe')

        output = list(yaml.load_all(file_string))

        for login in output:
            new_reddit = praw.Reddit(client_id=login['client-id'],
                        client_secret=login['client-secret'],
                        user_agent=Constants.USER_AGENT,
                        username=login['username'],
                        password=login['password'])

            if login['type'] == 'mod':
                RedditManager._mod_reddits.append(new_reddit)
            else:
                RedditManager._worker_reddits.append(new_reddit)

        print(output)

    @staticmethod
    def get_connection(moderator=False):

        while RedditManager._thread_lock:
            time.sleep(0)

        RedditManager._thread_lock = True

        returned_connection = None

        if moderator:
            returned_connection = RedditManager._mod_reddits[RedditManager.mod_index]

            RedditManager.mod_index += 1

            if RedditManager.mod_index >= len(RedditManager._mod_reddits):
                RedditManager.mod_index = 0

        else:
            returned_connection = RedditManager._worker_reddits[RedditManager.worker_index]

            RedditManager.worker_index += 1

            if RedditManager.worker_index >= len(RedditManager._worker_reddits):
                RedditManager.worker_index = 0

        RedditManager._thread_lock = False

        return returned_connection

        # if threading.current_thread().ident in RedditManager._praw_dict:
        #
        #     return RedditManager._praw_dict[threading.current_thread().ident]
        #
        # else:
        #
        #     # Use the fallback reddit instance if there isn't a thread specific one.
        #
        #     return RedditManager.__praw_reddit

    @staticmethod
    def _add_worker(reddit):
        RedditManager._worker_reddits.append(reddit)

    @staticmethod
    def _add_mod(reddit):
        RedditManager._mod_reddits.append(reddit)

    @staticmethod
    def login_thread(username, password, client_id, client_secret):

        RedditManager._praw_dict[threading.current_thread().ident] = praw.Reddit(client_id=client_id,
                                                                                 client_secret=client_secret,
                                                                                 user_agent=Constants.USER_AGENT,
                                                                                 username=username,
                                                                                 password=password)


    @staticmethod
    def login(username, password, client_id, client_secret):

        RedditManager.__praw_reddit = praw.Reddit(client_id=client_id,
                                                  client_secret=client_secret,
                                                  user_agent=Constants.USER_AGENT,
                                                  username=username,
                                                  password=password)

    @staticmethod
    def fetchCommentMeta(id):


        reddit_comment = RedditManager.get_connection().comment(id=id)

        comment_id = reddit_comment.id

        post_id = reddit_comment.submission.id

        if reddit_comment.author is None:
            username = "[deleted]"
        else:
            username = reddit_comment.author.name

        parent_comment = None

        # We need to split here, because the incoming id uses the fullname syntax
        if reddit_comment.parent_id.split('_')[0] == 't1':
            parent_comment = reddit_comment.parent_id.split('_')[1]

        comment_karma = reddit_comment.score

        comment_date = reddit_comment.created_utc

        subreddit = str(reddit_comment.subreddit)

        new_comment = comment(comment_id=comment_id, post_id=post_id, username=username,
                              parent_comment=parent_comment, comment_karma=comment_karma,
                              comment_date=comment_date, subreddit=subreddit)


        return new_comment



        pass

    @staticmethod
    def fetchUserMeta(username, subreddit):

        reddit_user = RedditManager.get_connection().redditor(name=username)

        new_user = RedditManager._usertouser(reddit_user, subreddit)

        return new_user

        pass

    @staticmethod
    def fetchPostMeta(id):

        reddit_post = RedditManager.get_connection().submission(id=id)

        new_post = RedditManager._subtopost(reddit_post)

        return new_post


    @staticmethod
    def fetchCommentMetaRecent(subreddit, limit=100):

        sub = RedditManager.get_connection().subreddit(subreddit)

        commentlist = sub.comments(limit=limit)

        meta_list = []

        try:

            for temp_comment in commentlist:

                comment_id = temp_comment.id

                post_id = temp_comment.submission.id

                username = temp_comment.author.name

                parent_comment = None

                # We need to split here, because the incoming id uses the fullname syntax
                if temp_comment.parent_id.split('_')[0] == 't1':
                    parent_comment = temp_comment.parent_id.split('_')[1]

                comment_karma = temp_comment.score

                comment_date = temp_comment.created_utc

                subreddit = str(temp_comment.subreddit)

                new_comment = comment(comment_id=comment_id, post_id=post_id, username=username,
                                      parent_comment=parent_comment, comment_karma=comment_karma,
                                      comment_date=comment_date, subreddit=subreddit)

                meta_list.append(new_comment)

        except:

            pass

        return meta_list


    @staticmethod
    def fetchPostMetaRecent(subreddit, limit=100):
        sub = RedditManager.get_connection().subreddit(subreddit)

        submission_list = sub.new(limit=limit)

        meta_list = []

        try:

            for temp_post in submission_list:

                new_post = RedditManager._subtopost(temp_post)

                meta_list.append(new_post)

        except:

            pass

        return meta_list

    @staticmethod
    def getWikiContent(subreddit, page):

        r = RedditManager.get_connection(moderator=True)

        page = r.subreddit(subreddit).wiki[page]

        return page.content_md

    @staticmethod
    def getFrontPage(subreddit):

        r = RedditManager.get_connection()

        sub = r.subreddit(subreddit)

        submissions = sub.hot(limit=100)

        sub_post_list = []

        for cur_post in submissions:
            sub_post_list.append(RedditManager._subtopost(cur_post))

        return sub_post_list

    @staticmethod
    def getFrontPageFiltered(subreddit, filtersub):

        # Gets the top 100 posts on subreddit, and filters for only posts in 'filtersub'.

        r = RedditManager.get_connection()

        sub = r.subreddit(subreddit)

        submissions = sub.hot(limit=100)

        sub_post_list = dict()

        count = 0

        for cur_post in submissions:
            count += 1
            if str(cur_post.subreddit) == filtersub:
                sub_post_list[count] = RedditManager._subtopost(cur_post)

        return sub_post_list

        pass

    @staticmethod
    def get_subreddit_moderators(sub):

        r = RedditManager.get_connection()

        subreddit = r.subreddit(sub)

        print(subreddit)

        user_list = []

        for moderator in subreddit.moderator():

            new_user = RedditManager._usertouser(moderator)

            user_list.append(new_user)

        return user_list

    @staticmethod
    def _subtopost(submission):

        post_id = submission.id

        username = str(submission.author)

        subreddit = str(submission.subreddit)

        post_karma = submission.score

        post_date = submission.created_utc

        new_post = post(post_id=post_id, username=username, subreddit=subreddit,
                        post_karma=post_karma, post_date=post_date)

        return new_post

    @staticmethod
    def ban_user(username, subreddit):

        #Todo: Implement
        pass

    @staticmethod
    def get_flairs(subreddit):

        try:

            r = RedditManager.get_connection(moderator=True)

            flair_list = []

            for flair in r.subreddit(subreddit).flair(limit=None):
                a_flair = user_flair_struct(username=flair['user'].name,
                                            subreddit=subreddit,
                                            flair_class=flair['flair_css_class'],
                                            flair_text=flair['flair_text'])

                flair_list.append(a_flair)

            return flair_list

        except:

            pass


    @staticmethod
    def give_post_flair(post_id, flair_text, flair_class):

        try:

            r = RedditManager.get_connection(moderator=True)

            this_post = r.submission(id=post_id)

            if this_post.flair.submission.link_flair_text is not None and \
                this_post.flair.submission.link_flair_css_class is not None and\
                this_post.flair.submission.link_flair_text == flair_text and \
                this_post.flair.submission.link_flair_css_class == flair_class:
                return # The flair has already been set.

            flair_choice = this_post.flair.choices()

            flair_template_choice = None

            for choice in flair_choice:
                if choice['flair_css_class'] == flair_class:
                    flair_template_choice = choice['flair_template_id']
                    this_post.flair.select(flair_template_choice, flair_text)
                    return

            if flair_template_choice is None:
                # We have to make the flair template now.
                this_post.subreddit.flair.link_templates.add(text=flair_text, text_editable=False, css_class=flair_class)
                # Okay, now what is the ID for this flair?
                flair_choice = this_post.flair.choices()
                for choice in flair_choice:
                    if choice['flair_css_class'] == flair_class:
                        flair_template_choice = choice['flair_template_id']
                        this_post.flair.select(flair_template_choice, flair_text)
                        # If we don't delete, this will cut down on requests made in future flair sets.
                        #this_post.subreddit.flair.link_templates.delete(flair_template_choice)
                        return

        except:

            pass

    @staticmethod
    def give_user_flair(username, subreddit, flair_text, flair_class=None):

        try:

            r = RedditManager.get_connection(moderator=True)

            r.subreddit(subreddit).flair.set(redditor=username, text=flair_text, css_class=flair_class)

        except:

            pass

    @staticmethod
    def give_user_flair_list(flair_struct_list):

        final_mapping = dict()

        for flair_struct in flair_struct_list:

            if flair_struct.subreddit not in final_mapping:
                final_mapping[flair_struct.subreddit] = []

            if flair_struct.flair_text is None:
                continue

            if not DatabaseManager.is_flair(flair_struct.subreddit,
                                            flair_struct.username,
                                            flair_struct.flair_text,
                                            flair_struct.flair_class):
                final_mapping[flair_struct.subreddit]\
                    .append(dict([('user', flair_struct.username),
                                  ('flair_text', flair_struct.flair_text),
                                  ('flair_css_class', flair_struct.flair_class)]))

        r = RedditManager.get_connection(moderator=True)

        for key, value in final_mapping.items():
            r.subreddit(key).flair.update(value)

        # If everything updated successfully, update in the database
        DatabaseManager.update_flairs(flair_struct_list)

    @staticmethod
    def _usertouser(reddit_user, subreddit=None):

        new_user = None

        try:

            new_user = user(username=reddit_user.name, subreddit=subreddit, user_id=reddit_user.id)

        except:

            pass

        return new_user

    @staticmethod
    def get_messages():

        conn = RedditManager.get_connection(moderator=True)

        message_list = []

        for message in conn.inbox.unread():
            message_list.append(dict([('author', str(message.author)),
                                      ('subject', message.subject),
                                      ('body',message.body)]))


        return message_list

    @staticmethod
    def get_bans(subreddit):

        conn = RedditManager.get_connection(moderator=True)

        ban_list = []

        for ban in conn.subreddit(subreddit).banned(limit=None):
            a_ban = user_ban_struct(ban.name, subreddit, ban.date, ban.note)

            ban_list.append(a_ban)

        return ban_list


class user_ban_struct():

    def __init__(self, username, subreddit, time, note):

        self.username = username
        self.subreddit = subreddit
        self.time = time
        self.note = note



class user_flair_struct():

    def __init__(self, username, subreddit, flair_text, flair_class=None):

        self.username = username
        self.subreddit = subreddit
        self.flair_text = flair_text
        self.flair_class = flair_class




