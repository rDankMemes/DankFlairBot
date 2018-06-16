import threading
from RedditManagerUtils import RedditManager
from DatabaseManager import DatabaseManager
import RulesManager
from user import user
import Constants
import time
import sys
import datetime
import prawcore
from DisplayManager import DisplayManager
from ruamel.yaml import YAML

global active_comment_duration
global active_post_duration

def read_setting_from_file(filename):

    global active_comment_duration
    global active_post_duration

    settings_file = open(filename)

    file_string = settings_file.read()

    yaml = YAML(typ='safe')

    output = list(yaml.load_all(file_string))

    active_post_duration = output[0]["active_post_duration"]

    active_comment_duration = output[0]["active_comment_duration"]

    print(output)


def setup_threads(subreddit):

    global active_comment_duration
    global active_post_duration

    mod_monitor = ModeratorsMonitorThread(subreddit)

    rule_maint = RuleMaintenanceThread(subreddit)

    hot_monitor = HotMonitorThread(subreddit)

    user_stream = UserStreamThread()

    user_maint = UserMaintenanceThread()

    RedditManager.fetchCommentMetaRecent(subreddit)

    post_maint = PostMaintenanceThread()

    post_stream = PostStreamThread(subreddit)

    comment_stream = CommentStreamThread(subreddit)

    comment_maint = CommentMaintenanceThread()

    flair_maint = FlairMantenanceThread(subreddit)

    ban_maint = BanMaintenanceThread(subreddit)

    message_monitor = MessageMonitorThread()

    display_manager = DisplayManagerThread(subreddit)

    mod_monitor.start()

    rule_maint.start()

    hot_monitor.start()

    post_maint.start()

    user_stream.start()

    user_maint.start()

    post_stream.start()

    comment_stream.start()

    comment_maint.start()

    flair_maint.start()

    ban_maint.start()

    message_monitor.start()

    display_manager.start()

class DisplayManagerThread(threading.Thread):

    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        DisplayManager.addSubreddit(subreddit)



        pass

    def run(self):

        while True:

            RedditManager.get_rate_limits()

            DisplayManager.update()

            time.sleep(0.1)

class MessageMonitorThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        pass

    def run(self):

        while True:

            try:

                messages = RedditManager.get_messages()

                for message in messages:

                    if message['subject'].startswith("invitation to moderate"):

                        # POW!
                        if not message['subreddit'] == 'None':
                            RedditManager.send_message(subject=Constants.ONBOARDING_SUBJECT,
                                                       content=Constants.ONBOARDING_MESSAGE,
                                                       recipient="r/{sub}".format(sub=message['subreddit']))

                            try:

                                RedditManager.accept_mod_invite(message['subreddit'])

                            except:
                                pass

                        RedditManager.mark_message_read(message['id'])

                    if message['author'] == "ELFAHBEHT_SOOP":

                        RedditManager.mark_message_read(message['id'])

                pass
            except:
                pass


class ModeratorsMonitorThread(threading.Thread):

    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        self.subreddit = subreddit

    def run(self):

        while True:

            userlist = RedditManager.get_subreddit_moderators(self.subreddit)

            DatabaseManager.update_moderators(userlist, self.subreddit)

            for mod in userlist:
                DatabaseManager.ensure_user_exists(mod.username, self.subreddit)

            #Sleep for 10 minutes
            time.sleep(10 * 60)


class FlairMantenanceThread(threading.Thread):

    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        self.subreddit = subreddit

    def run(self):

        while True:

            flair_list = RedditManager.get_flairs(subreddit=self.subreddit)

            DatabaseManager.update_flairs(flair_list)

            #Sleep for 10 minutes
            time.sleep(10 * 60)

class HotMonitorThread(threading.Thread):

    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        self.subreddit = subreddit

    def run(self):

        MINUTE_DELAY = 60

        while True:

            # Get the current hot posts from the subreddit.

            front_posts = RedditManager.getFrontPage(subreddit=self.subreddit)

            count = 0

            for post in front_posts:
                count += 1
                DatabaseManager.update_post_rank(post.post_id, sub_rank=count)

            # Get the current hot posts from r/all
            filtered_dict = RedditManager.getFrontPageFiltered(subreddit='all', filtersub=self.subreddit)

            for rank, ranked_post in filtered_dict.items():

                DatabaseManager.update_post_rank(ranked_post.post_id, all_rank=rank)

                print(rank)

            #Sleep for 5 minutes before checking again.
            time.sleep(10)

class RuleMaintenanceThread(threading.Thread):

    """
    This class ensures the current rule set is being imposed and updates users based on changing states.
    """

    rule_page = "dfb-config"

    def __init__(self, subreddit):

        threading.Thread.__init__(self)

        self.subreddit = subreddit

    def run(self):

        rule_page = RuleMaintenanceThread.rule_page

        while True:

            try:
                RulesManager.RulesManager.fetch_ruleset(subreddit=self.subreddit, page=rule_page)

                posts = DatabaseManager.get_all_posts(subreddit=self.subreddit)

                for a_post in posts:
                    RulesManager.RulesManager.evaluate_and_action(subreddit=self.subreddit, eval_post=a_post)

                users = DatabaseManager.get_all_users(subreddit=self.subreddit)

                for a_user in users:
                    RulesManager.RulesManager.evaluate_and_action(subreddit=self.subreddit, eval_user=a_user)

                RulesManager.RulesManager.commit_pending_batch_commands()

                pass

            except prawcore.exceptions.Forbidden as e:
                DisplayManager.displayStatusString("Need to be mod!")
                time.sleep(500)

class UserStreamThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):

        #print("User Stream Thread Started")

        while True:

            try:

                post_list = DatabaseManager.get_all_posts()

                for cur_post in post_list:

                    DatabaseManager.ensure_user_exists(cur_post.username, cur_post.subreddit)

                comment_list = DatabaseManager.get_all_comments()

                for cur_comment in comment_list:

                    DatabaseManager.ensure_user_exists(cur_comment.username, cur_comment.subreddit)


            except:

                DisplayManager.displayStatusString("User Stream Thread Exception: " + str(sys.exc_info()[0]))
                pass

class UserMaintenanceThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):

        #print("User Maintenance Thread Started")

        while True:

            try:

                user_list = DatabaseManager.get_all_users(limit=10)

                user_sub_list = []

                for cur_user in user_list:
                    if not cur_user.fetch():
                        DatabaseManager.remove_user(cur_user.username, cur_user.subreddit)
                        user_list.remove(cur_user)

                DatabaseManager.updateUserList(user_list)

            except:

                DisplayManager.displayStatusString("User Maintenance Thread Exception: " + str(sys.exc_info()[0]))

                pass

class PostStreamThread(threading.Thread):

    def __init__(self, subreddit=None):
        threading.Thread.__init__(self)

        self.sub = subreddit

    def run(self):

        #("Post Stream Thread Started")

        if self.sub is None:
            return

        while True:
            metaList = RedditManager.fetchPostMetaRecent(self.sub)

            DatabaseManager.updatePostList(metaList)

            for post_meta in metaList:
                DatabaseManager.ensure_user_exists(post_meta.username, post_meta.subreddit)

            time.sleep(10)

            pass

class CommentStreamThread(threading.Thread):

    def __init__(self, subreddit=None):
        threading.Thread.__init__(self)

        self.sub = subreddit

    def run(self):

        #DisplayManager.displayStatusString("Comment Stream Thread Started")

        if self.sub is None:
            return

        while True:
            metaList = RedditManager.fetchCommentMetaRecent(self.sub)

            DatabaseManager.updateCommentList(metaList)

            for post_meta in metaList:
                DatabaseManager.ensure_user_exists(post_meta.username, post_meta.subreddit)

            time.sleep(10)

            pass

class PostMaintenanceThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)


    def run(self):

        #print("Post Maintenance Thread Started")

        DAY_HALF_SECONDS = 60 * 60 * 24 * 1.5

        while True:

            try:

                current_time = datetime.datetime.utcnow().timestamp()

                post_list = DatabaseManager.get_all_posts(dateLimit=current_time - DAY_HALF_SECONDS)

                DisplayManager.update_lock()

                DisplayManager.update_active_posts(len(post_list))

                DisplayManager.update_cur_post(0)

                DisplayManager.update_unlock()

                post_sub_list = []

                count = 0

                while count < len(post_list):

                    cur_post = post_list[count]

                    cur_post.fetch()

                    if count % 10 == 0:

                        DatabaseManager.updatePostList(post_sub_list)

                        post_sub_list = []

                    post_sub_list.append(post_list[count])

                    DisplayManager.update_cur_post(count)

                    count += 1

            except:

                DisplayManager.displayStatusString("Post Main Thread Exception: " + str(sys.exc_info()[0]))

                pass

class CommentMaintenanceThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)


    def run(self):

        #print("Comment Maintenance Thread Started")

        DAY_HALF_SECONDS = 60 * 60 * 24 * 1.5

        while True:

            try:

                current_time = datetime.datetime.utcnow().timestamp()

                comment_list = DatabaseManager.get_all_comments(dateLimit=current_time - DAY_HALF_SECONDS)

                DisplayManager.update_lock()

                DisplayManager.update_active_comments(len(comment_list))

                DisplayManager.update_cur_comment(0)

                DisplayManager.update_unlock()

                comment_sub_list = []

                count = 0

                while count < len(comment_list):

                    comment_list[count].fetch()

                    if count % 10 == 0:

                        DatabaseManager.updateCommentList(comment_sub_list)

                        comment_sub_list = []

                    comment_sub_list.append(comment_list[count])

                    count += 1

                    DisplayManager.update_cur_comment(count)

            except:

                DisplayManager.displayStatusString("Comment Main Thread Exception: " + str(sys.exc_info()[0]))

                pass

class BanMaintenanceThread(threading.Thread):


    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        self.subreddit = subreddit


    def run(self):
        #TODO: change this by looking at changes in the modlog, and updating accordingly.
        #Currently, this simply pulls the entire mod list and updates it every 10 minutes.

        ban_list = RedditManager.get_bans(subreddit=self.subreddit)

        DatabaseManager.update_bans(ban_list=ban_list, subreddit=self.subreddit)

        # Sleep for 10 minutes
        time.sleep(10 * 60)