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
import traceback

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

threads_stopped = False

# All of the monitor threads. 

mod_monitor = None
rule_maint  = None
hot_monitor = None
user_stream = None
user_maint  = None
post_stream = None
comment_stream = None
flair_maint = None
ban_maint = None
message_monitor = None
display_manager = None

post_comment_maint = None

kill_lock = threading.Lock()

def setup_threads(subreddit):

    global active_comment_duration
    global active_post_duration

    global mod_monitor 
    global rule_maint  
    global hot_monitor 
    global user_stream 
    global user_maint  
    global post_stream 
    global comment_stream 
    global flair_maint 
    global ban_maint 
    global message_monitor 
    global display_manager 
    global post_comment_maint

    mod_monitor = ModeratorsMonitorThread(subreddit)

    rule_maint = RuleMaintenanceThread(subreddit)

    hot_monitor = HotMonitorThread(subreddit)

    user_stream = UserStreamThread()

    user_maint = UserMaintenanceThread()

    RedditManager.fetchCommentMetaRecent(subreddit)

    #post_maint = PostMaintenanceThread()

    post_stream = PostStreamThread(subreddit)

    comment_stream = CommentStreamThread(subreddit)

    #comment_maint = CommentMaintenanceThread()

    flair_maint = FlairMaintenanceThread(subreddit)

    ban_maint = BanMaintenanceThread(subreddit)

    message_monitor = MessageMonitorThread()

    display_manager = DisplayManagerThread(subreddit)

    mod_monitor.start()

    rule_maint.start()

    hot_monitor.start()

    #post_maint.start()

    user_stream.start()

    user_maint.start()

    post_stream.start()

    comment_stream.start()

    #comment_maint.start()

    flair_maint.start()

    ban_maint.start()

    message_monitor.start()

    display_manager.start()

    post_comment_maint = PostCommentMaintenanceThread()

    post_comment_maint.start()

def stop_threads():

    global kill_lock

    acq_res = kill_lock.acquire(blocking = False)

    if not acq_res:
        return

    killing_threads = True

    killer = KillThread()

    killer.start()

class KillThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.name = "Kill Thread"

    def run(self):

        global threads_stopped

        display_manager.join()
        mod_monitor.join()
        rule_maint.join()
        hot_monitor.join() 
        user_stream.join()
        user_maint.join()
        post_stream.join()
        comment_stream.join()
        flair_maint.join()
        ban_maint.join()
        message_monitor.join()
        post_comment_maint.join()

        print(threading.enumerate())

        threads_stopped = True
        
        return

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class DisplayManagerThread(threading.Thread):

    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        DisplayManager.addSubreddit(subreddit)

        self.name = "Display Manager Thread"

        self.stop = False

        pass

    def run(self):

        try:

            while not self.stop:

                RedditManager.get_rate_limits()

                DisplayManager.update()

                time.sleep(0.1)

        except:

            traceback.print_exc()
            stop_threads()

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name) 

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class MessageMonitorThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.name = "Message Monitor Thread"

        self.stop = False

        self.stoppable = False

    def run(self):

        while not self.stop:

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
                                traceback.print_exc()
                                stop_threads()

                        RedditManager.mark_message_read(message['id'])

                    if message['author'] == "ELFAHBEHT_SOOP":

                        RedditManager.mark_message_read(message['id'])

            except:
                traceback.print_exc()
                stop_threads()
            
            self.stoppable = True

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)                


class ModeratorsMonitorThread(threading.Thread):

    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        self.subreddit = subreddit

        self.name = "Moderators Monitor Thread"

        self.stop = False

    def run(self):

        loop_pause_time = 60 * 10

        try:

            while not self.stop:

                userlist = RedditManager.get_subreddit_moderators(self.subreddit)

                DatabaseManager.update_moderators(userlist, self.subreddit)

                for mod in userlist:
                    DatabaseManager.ensure_user_exists(mod.username, self.subreddit)

                DisplayManager.update_num_mods(self.subreddit, len(userlist))

                current_time = time.time()

                while current_time + loop_pause_time > time.time() and not self.stop:
                    time.sleep(0)
        except:
            traceback.print_exc()
            stop_threads()

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)


class FlairMaintenanceThread(threading.Thread):

    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        self.subreddit = subreddit

        self.name = "Flair Maintenance Thread"

        self.stop = False

    def run(self):

        loop_pause_time = 60

        try:

            while not self.stop:

                flair_list = RedditManager.get_flairs(subreddit=self.subreddit)

                DisplayManager.update_num_flairs(self.subreddit, len(flair_list))

                DatabaseManager.update_flairs(flair_list)

                current_time = time.time()

                while current_time + loop_pause_time > time.time() and not self.stop:
                    time.sleep(0)

        except:
            traceback.print_exc()
            stop_threads()

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)


class HotMonitorThread(threading.Thread):

    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        self.subreddit = subreddit

        self.name = "Hot Monitor Thread"

        self.stop = False

    def run(self):

        MINUTE_DELAY = 60

        loop_pause_time = MINUTE_DELAY * 5

        try:

            while not self.stop:

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

                current_time = time.time()

                while current_time + loop_pause_time > time.time() and not self.stop:
                    time.sleep(0)

        except:
            traceback.print_exc()
            stop_threads()


    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)    

class RuleMaintenanceThread(threading.Thread):

    """
    This class ensures the current rule set is being imposed and updates users based on changing states.
    """

    rule_page = "dfb-config"

    def __init__(self, subreddit):

        threading.Thread.__init__(self)

        self.subreddit = subreddit

        self.name = "Rule Maintenance Thread"

        self.stop = False

    def run(self):

        rule_page = RuleMaintenanceThread.rule_page

        loop_pause_time = 500

        while not self.stop:

            try:
                RulesManager.RulesManager.fetch_ruleset(subreddit=self.subreddit, page=rule_page)

                posts = DatabaseManager.get_all_posts(subreddit=self.subreddit)

                if self.stop:
                    return

                for a_post in posts:

                    if self.stop:
                        return

                    RulesManager.RulesManager.evaluate_and_action(subreddit=self.subreddit, eval_post=a_post)

                users = DatabaseManager.get_all_users(subreddit=self.subreddit)

                for a_user in users:

                    if self.stop:
                        return

                    print("Evaluating {}...".format(a_user.username))

                    RulesManager.RulesManager.evaluate_and_action(subreddit=self.subreddit, eval_user=a_user)

                RulesManager.RulesManager.commit_pending_batch_commands()

                pass

            except prawcore.exceptions.Forbidden as e:
                DisplayManager.displayStatusString("Need to be mod!")

                current_time = time.time()

                while current_time + loop_pause_time > time.time() and not self.stop:
                    time.sleep(0)

            except:
                traceback.print_exc()
                stop_threads()

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class UserStreamThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.name = "User Stream Thread"

        self.stop = False

    def run(self):

        #print("User Stream Thread Started")

        while not self.stop:

            try:

                post_list = DatabaseManager.get_all_posts()

                for cur_post in post_list:

                    DatabaseManager.ensure_user_exists(cur_post.username, cur_post.subreddit)

                comment_list = DatabaseManager.get_all_comments()

                for cur_comment in comment_list:

                    DatabaseManager.ensure_user_exists(cur_comment.username, cur_comment.subreddit)




            except:

                DisplayManager.displayStatusString("User Stream Thread Exception: " + str(sys.exc_info()))

                

                traceback.print_exc()
                stop_threads()


    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class UserMaintenanceThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.name = "User Maintenance Thread"

        self.stop = False

    def run(self):

        #print("User Maintenance Thread Started")

        loop_pause_time = 10

        while not self.stop:

            try:

                user_list = DatabaseManager.get_all_users(limit=10)

                user_sub_list = []

                for cur_user in user_list:
                    if not cur_user.fetch():
                        DatabaseManager.remove_user(cur_user.username, cur_user.subreddit)
                        user_list.remove(cur_user)

                DatabaseManager.updateUserList(user_list)

                current_time = time.time()

                while current_time + loop_pause_time > time.time() and not self.stop:
                    time.sleep(0)

            except:

                DisplayManager.displayStatusString("User Maintenance Thread Exception: " + str(sys.exc_info()[0]))

                traceback.print_exc()
                stop_threads()

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class PostStreamThread(threading.Thread):

    def __init__(self, subreddit=None):
        threading.Thread.__init__(self)

        self.sub = subreddit

        self.name = "Post Stream Thread"

        self.stop = False

    def run(self):

        loop_pause_time = 10

        #("Post Stream Thread Started")
        try:

            if self.sub is None:
                return

            while not self.stop:
                metaList = RedditManager.fetchPostMetaRecent(self.sub)

                DatabaseManager.updatePostList(metaList)

                for post_meta in metaList:
                    DatabaseManager.ensure_user_exists(post_meta.username, post_meta.subreddit)

                current_time = time.time()

                while current_time + loop_pause_time > time.time() and not self.stop:
                    time.sleep(0)

        except:
            traceback.print_exc()
            stop_threads()

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class CommentStreamThread(threading.Thread):

    def __init__(self, subreddit=None):
        threading.Thread.__init__(self)

        self.sub = subreddit

        self.name = "Comment Stream Thread"

        self.stop = False

    def run(self):

        #DisplayManager.displayStatusString("Comment Stream Thread Started")

        loop_pause_time = 10

        try:

            if self.sub is None:
                return

            while not self.stop:
                metaList = RedditManager.fetchCommentMetaRecent(self.sub)

                DatabaseManager.updateCommentList(metaList)

                for post_meta in metaList:
                    DatabaseManager.ensure_user_exists(post_meta.username, post_meta.subreddit)

                num_users = DatabaseManager.get_count_all_users(self.sub)

                DisplayManager.update_num_users(self.sub, num_users)

                current_time = time.time()

                while current_time + loop_pause_time > time.time() and not self.stop:
                    time.sleep(0)

                pass

        except:
            traceback.print_exc()
            stop_threads()

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class PostMaintenanceThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.name = "Post Maintenance Thread"

    def run(self):

        #print("Post Maintenance Thread Started")

        DAY_HALF_SECONDS = 60 * 60 * 24 * 1.5

        while not self.stop:

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

                traceback.print_exc()
                stop_threads()

                pass

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class CommentMaintenanceThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.name = "Comment Maintenance Thread"

    def run(self):

        #print("Comment Maintenance Thread Started")

        DAY_HALF_SECONDS = 60 * 60 * 24 * 1.5

        while not self.stop:

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

                DisplayManager.displayStatusString("Comment Main Thread Exception: " + str(sys.exc_info()))
                
                traceback.print_exc()
                stop_threads()
                pass

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class PostCommentMaintenanceThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.name = "Post/Comment Maintenance Thread"

        self.stop = False

    def run(self):

        global active_comment_duration
        global active_post_duration

        #print("Comment Maintenance Thread Started")

        DAY_HALF_SECONDS = 60 * 60 * 24 * 1.5        

        while not self.stop:

            try:

                # First, get the current time!

                current_time = datetime.datetime.utcnow().timestamp()

                # Then, get all the posts we have stored that have been posted in the last
                # duration where we are updating posts. Default 1.5 days.
                post_list = DatabaseManager.get_all_posts(dateLimit=current_time - active_post_duration)

                # Get the comments as well.
                comment_list = DatabaseManager.get_all_comments(dateLimit=current_time - active_comment_duration)

                # Resetting the display to show the number of active posts.

                # We have to lock the display from updating so we don't show weird info.
                DisplayManager.update_lock()

                # Update the number of active posts
                DisplayManager.update_active_posts(len(post_list))

                # Update the current post we are on to the 0th post.
                DisplayManager.update_cur_post(0)

                # Update the number of active comments.
                DisplayManager.update_active_comments(len(comment_list))

                # Update the current comment number.
                DisplayManager.update_cur_comment(0)

                # unlock the display now that we have finished updating.
                DisplayManager.update_unlock()

                post_sub_list = []

                comment_sub_list = []

                post_count = 0

                comment_count_display = 0

                while post_count < len(post_list):

                    cur_post = post_list[post_count]

                    post_comments = RedditManager.fetchAllPostComments(cur_post.post_id)

                    cur_post.fetch()

                    DatabaseManager.updateCommentList(post_comments)

                    comment_count_display += len(post_comments)

                    DisplayManager.update_cur_comment(comment_count_display)

                    # Prune all of the comments we have just processed.
                    for comment in post_comments:
                        if comment in comment_list:
                            comment_list.remove(comment)

                    if post_count % 10 == 0:

                        # Every 10 posts we process are commited to the database together.

                        DatabaseManager.updatePostList(post_sub_list)


                        post_sub_list = []

                    #Add the current post to the post_sub_list.

                    post_sub_list.append(post_list[post_count])

                    post_count += 1

                    # Update the display manager with the number of posts processed.
                    DisplayManager.update_cur_post(post_count)

                # Commit what's left.
                DatabaseManager.updatePostList(post_sub_list)

                comment_count = 0

                while comment_count < len(comment_list):

                    comment_list[comment_count].fetch()

                    if comment_count % 10 == 0:

                        DatabaseManager.updateCommentList(comment_sub_list)

                        comment_sub_list = []

                    comment_sub_list.append(comment_list[comment_count])

                    comment_count += 1
                    comment_count_display += 1

                    DisplayManager.update_cur_comment(comment_count_display)

                # Commit what's left.
                DatabaseManager.updateCommentList(comment_sub_list)

            except:

                DisplayManager.displayStatusString("Comment Main Thread Exception: " + str(sys.exc_info()[0]))
                
                traceback.print_exc()
                stop_threads()
                pass

    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)

class BanMaintenanceThread(threading.Thread):


    def __init__(self, subreddit):
        threading.Thread.__init__(self)

        self.subreddit = subreddit

        self.name = "Ban Maintenance Thread"

        self.stop = False

    def run(self):
        #TODO: change this by looking at changes in the modlog, and updating accordingly.
        #Currently, this simply pulls the entire mod list and updates it every 10 minutes.

        loop_pause_time = 10 * 60

        try:

            while not self.stop:

                ban_list = RedditManager.get_bans(subreddit=self.subreddit)

                DatabaseManager.update_bans(ban_list=ban_list, subreddit=self.subreddit)

                current_time = time.time()

                while current_time + loop_pause_time > time.time() and not self.stop:
                    time.sleep(0)

        except:

            traceback.print_exc()
            stop_threads()


    def join(self, timeout=None):
        """
        Join the thread using underlying threading.Thread join()
        This method is over-ridden to tell the thread to stop.

        :param timeout: The amount of time to wait for join (Default value = None)

        """

        print("Killing " + self.name)

        # Tell the thread to stop.
        self.stop = True

        # Pass control to the internal join implementation.
        super(type(self), self).join(timeout)            