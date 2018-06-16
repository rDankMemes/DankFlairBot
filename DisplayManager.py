import sys
import os
import Constants


class DisplayManager():

    subredditDict = dict()

    update_locked = 0

    status_string = "OK"

    num_active_posts = 0
    num_active_comments = 0
    num_cur_post = 0
    num_cur_comment = 0

    @staticmethod
    def addSubreddit(subreddit):

        DisplayManager.subredditDict[subreddit] = {
                'num_moderators' : 0,
                'num_users' : 0,
                'num_flairs' : 0,
                'recent_user_updates' : [],
        }

    @staticmethod
    def update_lock():
        DisplayManager.update_locked += 1

    @staticmethod
    def update_unlock():
        DisplayManager.update_locked -= 1

    @staticmethod
    def update_cur_post(post_num):

        DisplayManager.num_cur_post = post_num

    @staticmethod
    def update_active_posts(num_active_posts):

        DisplayManager.num_active_posts = num_active_posts

    @staticmethod
    def update_cur_comment(num_cur_comment):

        DisplayManager.num_cur_comment = num_cur_comment

    @staticmethod
    def update_active_comments(num_active_comments):

        DisplayManager.num_active_comments = num_active_comments

    @staticmethod
    def update_num_mods(subreddit, num_mods):

        DisplayManager.subredditDict[subreddit]["num_moderators"] = num_mods

    @staticmethod
    def update_num_users(subreddit, num_users):

        DisplayManager.subredditDict[subreddit]["num_users"] = num_users

    @staticmethod
    def update_num_flairs(subreddit, num_flairs):

        DisplayManager.subredditDict[subreddit]["num_flairs"] = num_flairs

    @staticmethod
    def displayStatusString(status_string):
        DisplayManager.status_string = status_string


    @staticmethod
    def update():

        if DisplayManager.update_locked > 0:
            return

        DisplayManager.cls()

        sys.stdout.write(Constants.BOT_NAME + "_____\n\n")

        num_cur_comment = DisplayManager.num_cur_comment
        num_active_comments = DisplayManager.num_active_comments

        num_cur_post = DisplayManager.num_cur_post
        num_active_posts = DisplayManager.num_active_posts

        if num_active_comments != 0:
            comment_percent = num_cur_comment / num_active_comments
        else:
            comment_percent = 0

        if num_active_posts != 0:
            post_percent = num_cur_post / num_active_posts
        else:
            post_percent = 0

        comment_string = "\rUpdating {num_comments} Comments: ".format(num_comments=num_active_comments)

        formatted_comment_string = '{message: <26}'.format(message=comment_string)

        formatted_comment_percentage = '{message: <8}'.format(message="{percent}%".format(percent=round(comment_percent * 100, 1)))

        sys.stdout.write(formatted_comment_string + formatted_comment_percentage)

        # We now need to print dashes and spaces for the first progress bar.
        DisplayManager.progress(1, 20, comment_percent)

        sys.stdout.write("\n")

        post_string = "\rUpdating {num_posts} Posts: ".format(num_posts=num_active_posts)

        formatted_post_string = '{message: <26}'.format(message=post_string)

        formatted_post_percentage = '{message: <8}'.format(message="{percent}%".format(percent=round(post_percent * 100, 1)))

        sys.stdout.write(formatted_post_string + formatted_post_percentage)

        # We now need to print dashes and spaces for the first progress bar.
        DisplayManager.progress(1, 20, post_percent)

        sys.stdout.write("\n---\n")


        for sub_name, sub in DisplayManager.subredditDict.items():

            sys.stdout.write("Subreddit: r/{subname}\n"
                             .format(subname=sub_name))

            sys.stdout.write("\rCurrent Moderator Count: {mod_count}\n".format(mod_count=sub["num_moderators"]))
            sys.stdout.write("\rCurrent User Count: {user_count}\n".format(user_count=sub["num_users"]))
            sys.stdout.write("\rCurrent Flair Count: {flair_count}\n".format(flair_count=sub["num_flairs"]))

            sys.stdout.write("\r---\n")

        sys.stdout.write("\rStatus:\n\r {status_string}\n".format(status_string=DisplayManager.status_string))

        sys.stdout.flush()

    @staticmethod
    def progress(max_val, width, cur_val):

        sys.stdout.write("|")

        num_dash = int(cur_val/max_val * width)

        num_dash = min(width, num_dash)

        for i in range(0, num_dash):
            sys.stdout.write("-")

        for i in range(0, width - num_dash):
            sys.stdout.write(" ")

        sys.stdout.write("|")

    @staticmethod
    def cls():
        os.system('cls' if os.name == 'nt' else 'clear')
