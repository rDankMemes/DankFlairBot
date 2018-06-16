
from ruamel.yaml import YAML

import RedditManagerUtils
import DatabaseManager
import Rule
import time


class RulesManager():

    _internal_ruleset = []

    __input_string_to_type = dict([
                            ('maximum_all_rank', Rule.maximum_all_rank),
                            ('maximum_sub_rank', Rule.maximum_sub_rank),
                            ('link_score', Rule.link_score),
                            ('comment_score', Rule.comment_score),
                            ('total_comment_score', Rule.total_comment_score),
                            ('total_link_score', Rule.total_link_score),
                            ('banned', Rule.banned),
                            ('moderator', Rule.moderator)])

    __output_string_to_type = dict([('flair', Rule.flair)])

    __subreddit_rulesets = dict()

    __batch_flair = []

    __flair_lock = False

    # def __init__(self, subreddit, page):
    #
    #     self.subreddit = subreddit
    #     self.page = page

    @staticmethod
    def fetch_ruleset(subreddit, page):

        raw_content = RedditManagerUtils.RedditManager.getWikiContent(subreddit, page)

        yaml = YAML(typ='safe')

        output = list(yaml.load_all(raw_content))

        new_ruleset = RulesManager._parse_rules(output, subreddit)

        RulesManager.__subreddit_rulesets[subreddit] = new_ruleset

    @staticmethod
    def _parse_rules(raw_dict, subreddit):

        #print(raw_dict)

        ruleset = []

        for input_output in raw_dict:

            if input_output is None:
                continue

            rule_type = None

            rule_priority = None

            if 'type' in input_output:
                rule_type = input_output['type']

            if 'priority' in input_output:
                rule_priority = input_output['priority']

            inputs = []

            outputs = []

            for rule, params in input_output.items():

                input_class = RulesManager._input_name_to_type(rule)

                if input_class is not None and isinstance(params, dict):

                    new_input = input_class(context=subreddit)

                    new_input.init_with_dict(params)

                    inputs.append(new_input)

                    #print(input_class)

                output_class = RulesManager._output_name_to_type(rule)

                if output_class is not None and isinstance(params, dict):

                    new_output = output_class(context=subreddit)

                    new_output.init_with_dict(params)

                    outputs.append(new_output)

            new_ruleset = Ruleset(inputs=inputs, outputs=outputs, priority=rule_priority, type=rule_type)

            ruleset.append(new_ruleset)

        new_collection = RulesetCollection(ruleset)

        return new_collection

    @staticmethod
    def evaluate_and_action(subreddit, eval_post=None, eval_user=None):

        active_rulesets = None

        if subreddit in RulesManager.__subreddit_rulesets:
            active_rulesets = RulesManager.__subreddit_rulesets[subreddit]
        else:
            return

        active_rulesets.evaluate_and_action(eval_post=eval_post, eval_user=eval_user)

        # for ruleset in active_rulesets:
        #     if ruleset.type == 'submission' and ruleset.evaluate(eval_post=eval_post) and eval_post is not None:
        #             ruleset.perform_action(eval_post=eval_post)
        #
        #     elif ruleset.type == 'user' and ruleset.evaluate(eval_user=eval_user) and eval_user is not None:
        #         ruleset.perform_action(eval_user=eval_user)

    @staticmethod
    def add_to_batch_flair(new_flair):

        while RulesManager.__flair_lock:
            time.sleep(0)

        a_list = RulesManager.__batch_flair

        index_list = [i for i in range(len(RulesManager.__batch_flair))
                      if a_list[i].username==new_flair.username
                      and a_list[i].subreddit == new_flair.subreddit]

        if len(index_list) > 0:
            RulesManager.__batch_flair[index_list[0]] = new_flair
        else:
            RulesManager.__batch_flair.append(new_flair)

    @staticmethod
    def commit_pending_batch_commands():

        RulesManager.__flair_lock = True

        RedditManagerUtils.RedditManager.give_user_flair_list(RulesManager.__batch_flair)

        RulesManager.__flair_lock = False

    @staticmethod
    def _input_name_to_type(name):

        if name in RulesManager.__input_string_to_type:
            return RulesManager.__input_string_to_type[name]
        else:
            return None

    @staticmethod
    def _output_name_to_type(name):

        if name in RulesManager.__output_string_to_type:
            return RulesManager.__output_string_to_type[name]
        else:
            return None

class Ruleset():

    def __init__(self, inputs=None, outputs=None, priority=None, type=None):

        if outputs is None:
            outputs = []
        if inputs is None:
            inputs = []
        self.inputs = inputs
        self.outputs = outputs

        self.priority = 0

        if priority is not None:
            self.priority = priority

        self.type = type

    def evaluate(self, eval_post=None, eval_user=None):

        cur_eval = True

        for input in self.inputs:

            if eval_post is not None:
                cur_eval = cur_eval and input.evaluate(eval_post=eval_post)

            elif eval_user is not None:
                cur_eval = cur_eval and input.evaluate(eval_user=eval_user)

            if not cur_eval:
                break

        return cur_eval

    def perform_action(self, eval_post=None, eval_user=None):

        for output in self.outputs:
            output.perform_action(eval_post=eval_post, eval_user=eval_user)

    def __eq__(self, other):
        return self.priority == other.priority

    def __ne__(self, other):
        return self.priority != other.priority

    def __lt__(self, other):
        # Is the priority -1?
        if self.priority == -1 and other.priority != -1:
            # Then, no. Priority is higher than any other priority
            return False
        elif self.priority != -1 and other.priority == -1:
            return True

        return self.priority < other.priority

    def __le__(self, other):
        # Is the priority -1?
        if self.priority == -1 and other.priority != -1:
            # Then, no. Priority is higher than any other priority
            return False
        elif self.priority != -1 and other.priority == -1:
            return True

        return self.priority <= other.priority

    def __gt__(self, other):
        # Is the priority -1?
        if self.priority == -1 and other.priority != -1:
            # Then, yes. Priority is higher than any other priority
            return True
        elif self.priority != -1 and other.priority == -1:
            return False

        return self.priority > other.priority

    def __ge__(self, other):
        # Is the priority -1?
        if self.priority == -1 and other.priority != -1:
            # Then, yes. Priority is higher than any other priority
            return True
        elif self.priority != -1 and other.priority == -1:
            return False

        return self.priority >= other.priority


class RulesetCollection():

    def __init__(self, rulesets):

        # Ensure the rulesets are sorted by priority
        self.sorted_rulesets = sorted(rulesets, reverse=True)

        self._rulesets = self.sorted_rulesets

    def evaluate_and_action(self, eval_post=None, eval_user=None):

        action_list = []

        for ruleset in self.sorted_rulesets:

            new_action_list = []

            if ruleset.type == 'submission' and eval_post is not None and ruleset.evaluate(eval_post=eval_post):
                new_action_list.extend(ruleset.outputs)
            elif ruleset.type == 'user' and eval_user is not None and ruleset.evaluate(eval_user=eval_user):
                new_action_list.extend(ruleset.outputs)


            for action in new_action_list:
                index_list = [i for i in range(len(action_list))
                              if isinstance(action_list[i], action.__class__)]

                if len(index_list) == 0:
                    action_list.append(action)

        for action in action_list:
            action.perform_action(eval_post=eval_post, eval_user=eval_user)
