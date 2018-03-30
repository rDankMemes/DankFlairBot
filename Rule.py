
import DatabaseManager

import RedditManagerUtils

import RulesManager

def less(value_one, value_two):

    return value_one < value_two

def less_equal(value_one, value_two):

    return value_one <= value_two

def equal(value_one, value_two):

    return value_one == value_two

def greater_equal(value_one, value_two):

    return value_one >= value_two

def greater(value_one, value_two):

    return value_one > value_two

def not_equal(value_one, value_two):

    return value_one != value_two

conditions = dict([('less', less),
                  ('less_equal', less_equal),
                  ('equal', equal),
                  ('greater_equal', greater_equal),
                  ('greater', greater),
                  ('not_equal', not_equal)])

class Input():


    def __init__(self, context=None):

        self.context = context

        pass

    def evaluate(self):

        return False

class ValuedInput(Input):

    def __init__(self, range=None, value=None, condition=None, occurrences=None, context=None):

        super().__init__(context)

        # Tuple range
        self.range = range

        # Integer value
        self.value = value

        # The condition in which to activate
        self.condition = condition

        # How many times does the condition need to occur to activate?
        if occurrences is None:
            self.occurrences = 1
        else:
            self.occurrences = occurrences

    def init_with_dict(self, dict):

        if 'value' in dict:
            self.value = dict['value']
        if 'context' in dict:
            self.context = dict['context']
        if 'condition' in dict:
            self.condition = dict['condition']
        if 'occurances' in dict:
            self.occurrences = dict['occurances']
        if 'range' in dict and isinstance(dict['range'], list) and len(dict['range']) == 2:
            list_range = dict['range']
            self.range = (list_range[0],list_range[1])

        # TODO: Finish

    def evaluate(self, value=None, value_list=None):

        final_list = []

        if value is not None:
            final_list.append(value)

        if value_list is not None:
            final_list.extend(value_list)

        count = 0

        for cur_value in final_list:

            if self.range is not None:

                if cur_value in range(self.range[0],self.range[1]):
                    count += 1

            elif conditions[self.condition](cur_value, self.value):
                count += 1

            if count >= self.occurrences:

                return True

        return False

class BooleanInput(Input):

    def __init__(self, value=None, context = None):

        super().__init__(context)

        self.value = value

    def init_with_dict(self, dict):

        if 'value' in dict:
            self.value = dict['value']
        if 'context' in dict:
            self.context = dict['context']

    def evaluate(self, eval_value=None):

        return eval_value == self.value

class maximum_all_rank(ValuedInput):

    def __init__(self, range=None, value=None, condition=None, occurrences=None, context=None):

        super().__init__(range, value, condition, occurrences, context)

    def evaluate(self, eval_post=None, eval_user=None):

        if eval_post is not None:

            return super().evaluate(value=eval_post.max_all_rank)

        elif eval_user is not None:

            post_list = DatabaseManager.DatabaseManager.get_all_user_posts(eval_user.username)

            value_list = []

            for a_post in post_list:

                if a_post.max_all_rank is not None and a_post.subreddit == self.context:
                    value_list.append(a_post.max_all_rank)

            return super().evaluate(value_list=value_list)

class maximum_sub_rank(ValuedInput):

    def __init__(self, range=None, value=None, condition=None, occurrences=None, context=None):

        super().__init__(range, value, condition, occurrences, context)

    def evaluate(self, eval_post=None, eval_user=None):

        if eval_post is not None:

            return super().evaluate(value=eval_post.max_sub_rank)

        elif eval_user is not None:

            post_list = DatabaseManager.DatabaseManager.get_all_user_posts(eval_user.username)

            value_list = []

            for a_post in post_list:

                if a_post.max_sub_rank is not None and a_post.subreddit == self.context:
                    value_list.append(a_post.max_sub_rank)

            return super().evaluate(value_list=value_list)

class link_score(ValuedInput):

    def __init__(self, range=None, value=None, condition=None, occurrences=None, context=None):

        super().__init__(range, value, condition, occurrences, context)

    def evaluate(self, eval_post=None, eval_user=None):

        if eval_post is not None:

            return super().evaluate(value=eval_post.post_karma)

        elif eval_user is not None:

            post_list = DatabaseManager.DatabaseManager.get_all_user_posts(eval_user.username)

            value_list = []

            for a_post in post_list:

                if a_post.post_karma is not None and a_post.subreddit == self.context:
                    value_list.append(a_post.post_karma)

            return super().evaluate(value_list=value_list)

class comment_score(ValuedInput):

    def __init__(self, range=None, value=None, condition=None, occurrences=None, context=None):

        super().__init__(range, value, condition, occurrences, context)

    def evaluate(self, eval_comment=None, eval_user=None):

        if eval_comment is not None:

            return super().evaluate(value=eval_comment.post_karma)

        elif eval_user is not None:

            comment_list = DatabaseManager.DatabaseManager.get_all_user_comments(eval_user.username)

            value_list = []

            for a_comment in comment_list:

                if a_comment.comment_karma is not None and a_comment.subreddit == self.context:
                    value_list.append(a_comment.comment_karma)

            return super().evaluate(value_list=value_list)

class total_link_score(ValuedInput):

    def __init__(self, range=None, value=None, condition=None, occurrences=None, context=None):

        super().__init__(range, value, condition, occurrences, context)

    def evaluate(self, eval_post=None, eval_user=None):

        if eval_post is not None:

            # TODO: This shouldn't be used for posts. But what-if it is?
            return super().evaluate(value=eval_post.post_karma)

        elif eval_user is not None:

            post_score = DatabaseManager.DatabaseManager.get_user_post_score(eval_user.username, self.context)

            return super().evaluate(value=post_score)

class total_comment_score(ValuedInput):

    def __init__(self, range=None, value=None, condition=None, occurrences=None, context=None):

        super().__init__(range, value, condition, occurrences, context)

    def evaluate(self, eval_post=None, eval_user=None):

        if eval_post is not None:

            # TODO: lol wut
            pass

        elif eval_user is not None:

            comment_score = DatabaseManager.DatabaseManager.get_user_comment_score(eval_user.username, self.context)

            return super().evaluate(value=comment_score)


class banned(BooleanInput):

    def __init__(self, value=None, context=None):

        super().__init__(value, context)

    def evaluate(self, eval_post=None, eval_user=None):

        if eval_post is not None:

            return super().evaluate(
                eval_value=DatabaseManager.DatabaseManager.is_banned(username=eval_post.username, subreddit=self.context)
            )

        elif eval_user is not None:

            return super().evaluate(
                eval_value=DatabaseManager.DatabaseManager.is_banned(username=eval_user.username, subreddit=self.context)
            )

        return False

class moderator(BooleanInput):

    def __init__(self, value=None, context=None):

        super().__init__(value, context)

    def evaluate(self, eval_post=None, eval_user=None):

        if eval_post is not None:

            return super().evaluate(
                eval_value=DatabaseManager.DatabaseManager.is_moderator(eval_post.username, self.context))

        elif eval_user is not None:

            return super().evaluate(
                eval_value=DatabaseManager.DatabaseManager.is_moderator(eval_user.username, self.context))

        return False

class Output():

    def __init__(self, context):

        self.context = context

        pass

    def perform_action(self):

        pass

class ban(Output):

    def __init__(self, value=None, length=None, context=None):

        super().__init__(context)

        self.value = value
        self.length = length

    def perform_action(self, eval_post=None, eval_user=None):

        pass


class flair(Output):

    def __init__(self, managed=None, user_text=None, user_class=None,
                 submission_text=None, submission_class=None,
                 context=None):

        super().__init__(context)

        self.managed = managed

        self.user_text = user_text
        self.user_class = user_class

        self.submission_text = submission_text
        self.submission_class = submission_class

    def init_with_dict(self, dict):

        try:
            if 'managed' in dict:
                self.managed = bool(dict['managed'])
            if 'user_text' in dict:
                self.user_text = dict['user_text']
            if 'user_class' in dict:
                self.user_class = dict['user_class']
            if 'submission_text' in dict:
                self.submission_text = dict['submission_text']
            if 'submission_class' in dict:
                self.submission_class = dict['submission_class']

        except Exception as e:
            print(e)

    def perform_action(self, eval_post=None, eval_user=None):

        if self.managed is not None and not self.managed:
            return  # Don't do anything to this flair.

        if eval_post is not None:

            RedditManagerUtils.RedditManager.give_post_flair(post_id=eval_post.post_id,
                                                                  flair_text=self.submission_text,
                                                                  flair_class=self.submission_class)


            if self.user_text is not None:
                # TODO: Also needs to update the user's flair if the user flair params are set.
                pass

            pass

        elif eval_user is not None:

            #RedditManager.RedditManager.give_user_flair(eval_user.username, self.context, self.user_text, self.user_class)


            RulesManager.RulesManager.add_to_batch_flair(RedditManagerUtils.user_flair_struct(username=eval_user.username,
                                                                                              subreddit=self.context,
                                                                                              flair_text=self.user_text,
                                                                                              flair_class=self.user_class))

            pass

