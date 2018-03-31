## What is DankFlairBot?

DankFlairBot (DFB) is a bot designed from the ground up to actively manage flairs on any subreddit _in real time_. This means it actively scans through a subreddit in order to keep an updated state of every user's contributions. Unlike Automoderator, this is happening all the time, it doesn't need an API driven event in order to react. 

### How do I use it?

DFB uses synax similar to Automoderator, which is based off YAML. The concept is also the same, where there are inputs that lead to outputs. A collection of inputs and outputs is called a _rule_. Rules can be processed on posts or users, this will be noted as the _type_ of the rule. Inputs that are user specific, but processed on a post, will apply the output to the post.  

Currently, only a small amount of inputs and outputs are supported, but more inputs and outputs are being added constantly.

#### Reddit Configuration

The configuration for a bot is placed at the url:

    https://www.reddit.com/r/[subreddit]/wiki/dfb-config

Here is a simple example of a configuration:


```yaml
---

# Show moderators

# This rule will only be executed on users.
type: user 

# This is the moderator input rule.
moderator: 
    value: True # We want the output to be performed if the user *is* a moderator of this sub.

# The priority of this rule is 5. Higher priority overrides lower priority.
# A priority of -1 overrides everything.
priority: 5 
    
# This is the flair output.
# This will set the flair to "Moderator flair text" and the class to "Moderator"
flair:
  user_text: Moderator flair text
  user_class: Moderator
  
---

# This rule will only be executed on users as well.
type: user

# This is a comment score input. 
# It will run the output if the value is *less* than 15.
total_comment_score:
    value: 15
    condition: less

# A fairly low priority of 1. Easy to override 
priority: 1

# These users will be labled as "NOOB" with a class of noob
flair:
   user_text: NOOB
   user_class: noob
```

#### Server Configuration

Configuring the server requires creating a config.yml file. The contents of this file are demonstrated below:

```yaml
---

# Mod accounts are capable of moderator actions.
# Any action that needs mod perms will be done with these accounts.
type: mod

username: [reddit_username]

password: [reddit_password]

client-id: [api_client_id]

client-secret: [api_client_secret]


---

# Workers do not have moderator abilites. 
# These are only for random data collection purposes
type: worker

username: [reddit_username]

password: [reddit_password]

client-id: [api_client_id]

client-secret: [api_client_secret]

---

# You can add as many workers or mods as you want.
# As you add workers and mods, the bot will experience less cooldown times and respond faster
type: worker

username: [reddit_username]

password: [reddit_password]

client-id: [api_client_id]

client-secret: [api_client_secret]

```
