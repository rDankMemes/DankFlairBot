import sqlite3
import threading
import sys
from comment import comment
from post import post
from user import user
from DisplayManager import DisplayManager


class DatabaseManager():

    _dbconnection = None

    _connection_dict = dict()

    _dbname = None

    @staticmethod
    def init_connection(dbname):

        DatabaseManager._dbname = dbname

    @staticmethod
    def get_connection():

        if threading.current_thread().ident in DatabaseManager._connection_dict:

            return DatabaseManager._connection_dict[threading.current_thread().ident]

        else:

            connection = sqlite3.connect(DatabaseManager._dbname)

            DatabaseManager._connection_dict[threading.current_thread().ident] = connection

            return connection

    @staticmethod
    def create_tables():

        cur_connection = DatabaseManager.get_connection()

        cursor = cur_connection.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users'
                       '('
                       'username TEXT NOT NULL,'
                       'subreddit TEXT NOT NULL,'
                       'user_id TEXT,'
                       'last_update INT NOT NULL,'
                       'CONSTRAINT user_username_subreddit_pk PRIMARY KEY (username, subreddit)'
                       ');')

        cursor.execute('CREATE TABLE IF NOT EXISTS posts'
                       '('
                       'post_id TEXT PRIMARY KEY NOT NULL,'
                       'username TEXT NOT NULL,'
                       'subreddit TEXT NOT NULL,'
                       'post_karma INT NOT NULL,'
                       'post_date INT NOT NULL,'
                       'CONSTRAINT table_name_users_username_fk FOREIGN KEY (username) REFERENCES users (username),'
                       'CONSTRAINT table_name_users_subreddit_fk FOREIGN KEY (subreddit) REFERENCES users (subreddit)'
                       ');'
                       )

        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS posts_post_id_uindex ON posts (post_id)'
                       )

        cursor.execute('CREATE TABLE IF NOT EXISTS comments ('
                       'comment_id     TEXT PRIMARY KEY,'
                       'post_id        TEXT,'
                       'username       TEXT,'
                       'parent_comment TEXT,'
                       'comment_karma  INTEGER,'
                       'comment_date   INTEGER,'
                       'subreddit      TEXT,'
                       'FOREIGN KEY (post_id) REFERENCES posts (post_id),'
                       'FOREIGN KEY (username) REFERENCES users (username),'
                       'FOREIGN KEY (parent_comment) REFERENCES comments (parent_comment)'
                       ')')

        cursor.executescript('''
                        CREATE TABLE IF NOT EXISTS maximum_ranks
                        (
                            post_id TEXT PRIMARY KEY,
                            max_hot_sub_rank INT,
                            max_hot_all_rank INT,
                            CONSTRAINT maximum_ranks_posts_post_id_fk FOREIGN KEY (post_id) REFERENCES posts (post_id)
                        );
                        CREATE UNIQUE INDEX IF NOT EXISTS maximum_ranks_post_id_uindex ON maximum_ranks (post_id);
                        ''')

        cursor.executescript('''
                        CREATE TABLE IF NOT EXISTS modded_subreddits
                        (
                            username TEXT,
                            subreddit TEXT,
                            CONSTRAINT modded_subreddits_username_subreddit_pk PRIMARY KEY (username, subreddit)
                        )
                        ''')

        cursor.executescript('''
                        CREATE TABLE IF NOT EXISTS flairs
                        (
                            subreddit TEXT,
                            username TEXT,
                            flair_text TEXT,
                            flair_class TEXT,
                            CONSTRAINT flairs_username_subreddit_pk PRIMARY KEY (username, subreddit)
                        )
                        ''')

        cursor.executescript('''
                        CREATE TABLE IF NOT EXISTS bans
                        (
                            username TEXT,
                            subreddit TEXT,
                            time INT,
                            note TEXT,
                            CONSTRAINT bans_username_subreddit_pk PRIMARY KEY (username, subreddit),
                            CONSTRAINT bans_users_username_subreddit_fk FOREIGN KEY (username, subreddit) REFERENCES users (username, subreddit)
                        );
        ''')

        cur_connection.commit()

        pass

    @staticmethod
    def userExists(username, subreddit):

        cur_connection = DatabaseManager.get_connection()

        cursor = cur_connection.cursor()

        query = "SELECT * FROM users WHERE username='{username}' and subreddit='{subreddit}'".format(username=username,
                                                                                           subreddit=subreddit)

        result = DatabaseManager._execute_robust(cursor, query)

        return len(result) > 0

    @staticmethod
    def updateCommentList(commentList):

        cur_connection = DatabaseManager.get_connection()

        for cur_comment in commentList:
            cur_comment.update(cur_connection.cursor())

        cur_connection.commit()

    @staticmethod
    def updatePostList(postList):

        cur_connection = DatabaseManager.get_connection()

        for cur_post in postList:
            cur_post.update(cur_connection.cursor())

        cur_connection.commit()

        pass


    @staticmethod
    def updateUser(user):

        cur_connection = DatabaseManager.get_connection()

        user.update(cur_connection.cursor())

        cur_connection.commit()

    @staticmethod
    def updateUserList(userList):

        cur_connection = DatabaseManager.get_connection()

        for cur_user in userList:
            cur_user.update(cur_connection.cursor())

        cur_connection.commit()

    @staticmethod
    def update_flairs(flair_list):

        inserts = "BEGIN TRANSACTION;"

        for flair_struct in flair_list:

            this_class = flair_struct.flair_class

            if this_class is None:
                this_class = "NULL"
            else:
                this_class = "'" + this_class + "'"


            inserts += "INSERT OR REPLACE INTO flairs(subreddit, username, flair_text, flair_class) " \
                        "VALUES ('{subreddit}'," \
                        "'{username}'," \
                        "'{flair_text}'," \
                        "{flair_class}" \
                        ");\n".format(subreddit=flair_struct.subreddit,
                                   username = flair_struct.username,
                                   flair_text = flair_struct.flair_text,
                                   flair_class = this_class)


        inserts += "COMMIT;"

        cur_connection = DatabaseManager.get_connection()

        DatabaseManager._execute_script_robust(cur_connection, inserts)

    @staticmethod
    def update_bans(ban_list, subreddit):

        query = "BEGIN TRANSACTION;"

        query += "DELETE FROM bans WHERE subreddit='{subreddit}';"\
            .format(subreddit=subreddit)

        for ban_struct in ban_list:

            query += '''INSERT OR REPLACE INTO bans(subreddit, username, time, note) VALUES (
                        '{subreddit}',
                        '{username}',
                        {time},
                        '{note}'
                        );\n'''.format(subreddit=ban_struct.subreddit,
                                   username = ban_struct.username,
                                   time = str(int(ban_struct.time)),
                                   note = ban_struct.note.translate(str.maketrans({"'":  r"''"})))


        query += "COMMIT;"

        cur_connection = DatabaseManager.get_connection()

        DatabaseManager._execute_script_robust(cur_connection, query)


    @staticmethod
    def get_all_comments(dateLimit = None, subreddit = None):

        comment_list = []

        cur_connection = DatabaseManager.get_connection()

        cursor = cur_connection.cursor()

        main_query = """
        SELECT
                comments.comment_id,
                comments.post_id,
                comments.username,
                comments.parent_comment,
                comments.comment_karma,
                comments.comment_date,
                comments.subreddit
          FROM comments
        """

        final_query = ""

        if subreddit is None and dateLimit is None:
            final_query = main_query
        elif subreddit is not None and dateLimit is None:
            final_query = main_query + """WHERE subreddit='{subreddit}'""".format(subreddit=subreddit)
        elif subreddit is None and dateLimit is not None:
            final_query = main_query + """WHERE comment_date > {dateLimit}""".format(dateLimit=str(dateLimit))
        else:
            final_query = main_query + """WHERE subreddit='{subreddit}'
                                      and comment_date > {dateLimit}""".format(subreddit=subreddit, dateLimit=str(dateLimit))

        result = DatabaseManager._execute_robust(cursor, final_query)

#        result = DatabaseManager._execute_robust(cursor, 'SELECT * FROM comments')

        for row in result:

            new_comment = comment(row[0], row[1], row[2], row[3], row[4], row[5], row[6])

            comment_list.append(new_comment)

        return comment_list

    @staticmethod
    def get_all_posts(dateLimit=None, subreddit=None):

        post_list = []

        cur_connection = DatabaseManager.get_connection()

        cursor = cur_connection.cursor()

        main_query = """
        SELECT
                posts.post_id,
                posts.username,
                posts.subreddit,
                posts.post_karma,
                posts.post_date,
                maximum_ranks.max_hot_sub_rank,
                maximum_ranks.max_hot_all_rank
          FROM posts
          LEFT JOIN maximum_ranks
          ON posts.post_id = maximum_ranks.post_id
        """

        final_query = ""

        if subreddit is None and dateLimit is None:
            final_query = main_query
        elif subreddit is not None and dateLimit is None:
            final_query = main_query + """WHERE subreddit='{subreddit}'""".format(subreddit=subreddit)
        elif subreddit is None and dateLimit is not None:
            final_query = main_query + """WHERE post_date > {dateLimit}""".format(dateLimit=str(dateLimit))
        else:
            final_query = main_query + """WHERE subreddit='{subreddit}'
                                      and post_date > {dateLimit}""".format(subreddit=subreddit, dateLimit=str(dateLimit))

        result = DatabaseManager._execute_robust(cursor, final_query)

        for row in result:
            new_post = post(post_id=row[0],username=row[1],subreddit=row[2],
                            post_karma=row[3],post_date=row[4], max_sub_rank=row[5], max_all_rank=row[6])

            post_list.append(new_post)

        return post_list

    @staticmethod
    def get_all_user_posts(username):

        post_list = []

        cur_connection = DatabaseManager.get_connection()

        cursor = cur_connection.cursor()

        result = DatabaseManager._execute_robust(cursor, '''
                    SELECT
                      posts.post_id, posts.username,
                      posts.subreddit, posts.post_karma,
                      posts.post_date,
                      maximum_ranks.max_hot_sub_rank,
                      maximum_ranks.max_hot_all_rank FROM posts
                    LEFT JOIN maximum_ranks
                    ON posts.post_id = maximum_ranks.post_id
                    WHERE username='{username}';
                '''.format(username=username))

        for post_result in result:

            new_post = post(post_id=post_result[0],username=post_result[1],subreddit=post_result[2],post_karma=post_result[3],
                 post_date=post_result[4], max_sub_rank=post_result[5], max_all_rank=post_result[6])

            post_list.append(new_post)

        return post_list

    @staticmethod
    def get_all_user_comments(username):

        comment_list = []

        cur_connection = DatabaseManager.get_connection()

        cursor = cur_connection.cursor()

        result = DatabaseManager._execute_robust(cursor, '''
                    SELECT comment_id,
                    post_id, username,
                    parent_comment, comment_karma,
                    comment_date, subreddit
                    FROM comments WHERE username='{username}'
                '''.format(username=username))

        for comment_result in result:

            new_comment = comment(comment_id=comment_result[0], post_id=comment_result[1],
                               username=comment_result[2], parent_comment=comment_result[3],
                               comment_karma=comment_result[4], comment_date=comment_result[5],
                               subreddit=comment_result[6])

            comment_list.append(new_comment)

        return comment_list

    @staticmethod
    def get_all_users(limit=None, sort='old', subreddit=None):
        user_list = []

        cur_connection = DatabaseManager.get_connection()

        cursor = cur_connection.cursor()

        query = """SELECT * FROM users """

        if subreddit is not None:
            query += """ Where subreddit='{subreddit}' """.format(subreddit=subreddit)


        query += """ ORDER BY last_update ASC, username ASC """

        if limit is not None:

            query += """ LIMIT {limit} """.format(limit=limit)

        result = DatabaseManager._execute_robust(cursor,
                                        query)

        for row in result:
            new_user = user(row[0], row[1], row[2])

            user_list.append(new_user)

        return user_list

    @staticmethod
    def get_count_all_users(subreddit):
        user_list = []

        cur_connection = DatabaseManager.get_connection()

        cursor = cur_connection.cursor()

        query = """SELECT COUNT(*) FROM users WHERE users.subreddit = "{subreddit}";""".format(subreddit=subreddit)

        result = DatabaseManager._execute_robust(cursor,
                                        query)

        return result[0][0]


    @staticmethod
    def get_user(username):

        # TODO: Grab everything from the database. Not just stuff in the user table.

        user_list = []

        new_user = None

        cur_connection = DatabaseManager.get_connection()

        cursor = cur_connection.cursor()

        result = DatabaseManager._execute_robust(cursor,
                                                 'SELECT * FROM users WHERE username=\'{username}\''.format(username=username))

        if len(result) >= 1:
            new_user = user(result[0][0], result[0][1], user_id=result[0][2])

        return new_user


    @staticmethod
    def ensure_user_exists(username, subreddit):

        if not DatabaseManager.userExists(username, subreddit):
            #print(username + " not in database for " + subreddit + "!")

            # new_user = RedditManager.fetchUserMeta(cur_post.username, cur_post.subreddit)

            new_user = user(username=username, subreddit=subreddit)

            DatabaseManager.updateUser(new_user)

    @staticmethod
    def get_post_all_rank(post_id):

        query_str = '''
            SELECT max_hot_all_rank FROM maximum_ranks WHERE post_id='{post_id}'
        '''.format(post_id=post_id)

        conn = DatabaseManager.get_connection()

        all_results = DatabaseManager._execute_robust(conn.cursor(), query_str)



        if len(all_results) <= 0:
            return None
        else:
            return all_results[0][0]

    @staticmethod
    def get_post_sub_rank(post_id):

        query_str = '''
            SELECT max_hot_sub_rank FROM maximum_ranks WHERE post_id='{post_id}'
        '''.format(post_id=post_id)

        conn = DatabaseManager.get_connection()

        all_results = DatabaseManager._execute_robust(conn.cursor(), query_str)

        if len(all_results) <= 0:
            return None
        else:
            return all_results[0][0]
        pass

    @staticmethod
    def update_post_rank(post_id, all_rank=None, sub_rank=None):

        query_str = '''
            INSERT OR REPLACE INTO maximum_ranks(post_id, max_hot_sub_rank, max_hot_all_rank)
             VALUES('{postid}',
                    {max_hot_sub_rank},
                    {max_hot_all_rank}
                    )
        '''

        cur_all_rank = DatabaseManager.get_post_all_rank(post_id)

        cur_sub_rank = DatabaseManager.get_post_sub_rank(post_id)

        all_rank_update_str = "NULL"

        sub_rank_update_str = "NULL"

        if cur_all_rank is not None:

            if all_rank is None or \
                    (all_rank is not None and cur_all_rank < all_rank):
                all_rank_update_str = str(cur_all_rank)
            elif all_rank is not None:
                all_rank_update_str = str(all_rank)

        elif all_rank is not None:
            all_rank_update_str = str(all_rank)

        if cur_sub_rank is not None:

            if sub_rank is None or \
                    (sub_rank is not None and cur_sub_rank < sub_rank):
                sub_rank_update_str = str(cur_sub_rank)
            elif sub_rank is not None:
                sub_rank_update_str = str(sub_rank)

        elif sub_rank is not None:
            sub_rank_update_str = str(sub_rank)


        conn = DatabaseManager.get_connection()

        DatabaseManager._execute_robust(conn.cursor(), query_str.format(postid=post_id,
                                          max_hot_sub_rank=sub_rank_update_str,
                                          max_hot_all_rank=all_rank_update_str))

        conn.commit()

    @staticmethod
    def insert_moderator(username, subreddit):

        conn = DatabaseManager.get_connection()


        DatabaseManager._execute_robust(conn.cursor(), """INSERT or REPLACE INTO modded_subreddits(username, subreddit)
                        VALUES('{username}',
                                '{subreddit}')
                    """.format(username=username, subreddit=subreddit))

        conn.commit()

    @staticmethod
    def remove_moderator(username, subreddit):

        conn = DatabaseManager.get_connection()

        DatabaseManager._execute_robust(conn.cursor(), """ DELETE FROM modded_subreddits
                         WHERE username='{username}' and subreddit='{subreddit}' COLLATE NOCASE
                    """.format(username=username, subreddit=subreddit))

        conn.commit()

    @staticmethod
    def remove_user(username, subreddit):

        conn = DatabaseManager.get_connection()

        query = """DELETE FROM users WHERE username='{username}' and subreddit='{subreddit}' COLLATE NOCASE"""\
            .format(username=username, subreddit=subreddit)

        DatabaseManager._execute_robust(conn.cursor(), query)

        conn.commit()

    @staticmethod
    def update_moderators(mod_list, subreddit):

        conn = DatabaseManager.get_connection()


        results = DatabaseManager._execute_robust(conn.cursor(), """ SELECT username FROM modded_subreddits
                         WHERE subreddit='{subreddit}' COLLATE NOCASE
                    """.format(subreddit=subreddit))

        mod_strings = []

        for mod in mod_list:
            mod_strings.append(mod.username)

        for mod in mod_strings:

            if not (mod,) in results:
                DatabaseManager.insert_moderator(mod, subreddit)

        for mod_tuple in results:
            if not mod_tuple[0] in mod_strings:
                DatabaseManager.remove_moderator(mod_tuple[0], subreddit)

        conn.commit()


    @staticmethod
    def get_user_comment_score(username, subreddit):

        conn = DatabaseManager.get_connection()

        results = DatabaseManager._execute_robust(conn.cursor(),
                                """SELECT comments.username, comments.subreddit, SUM(comments.comment_karma)
                                FROM comments Where comments.subreddit='{subreddit}' COLLATE NOCASE and comments.username='{username}'
                                GROUP BY comments.username""".format(subreddit=subreddit, username=username))

        if len(results) > 0:
            return results[0][2]

        return 0

    @staticmethod
    def get_user_post_score(username, subreddit):

        conn = DatabaseManager.get_connection()

        results = DatabaseManager._execute_robust(conn.cursor(),
                                """SELECT posts.username, posts.subreddit, SUM(posts.post_karma)
                                FROM posts Where posts.subreddit='{subreddit}' COLLATE NOCASE and posts.username='{username}'
                                GROUP BY posts.username""".format(subreddit=subreddit, username=username))

        if len(results) > 0:
            return results[0][2]

        return 0

    @staticmethod
    def is_moderator(username, subreddit):

        conn = DatabaseManager.get_connection()

        results = DatabaseManager._execute_robust(conn.cursor(),
                    """ SELECT username FROM modded_subreddits
                         WHERE subreddit='{subreddit}' COLLATE NOCASE and username='{username}'
                    """.format(subreddit=subreddit, username=username))

        return len(results) >= 1

    @staticmethod
    def is_flair(subreddit, username, flair_text, flair_class):
        conn = DatabaseManager.get_connection()

        this_class = flair_class

        if this_class is None:
            this_class = "NULL"
        else:
            this_class = "'" + this_class + "'"

        query = """ SELECT * FROM flairs WHERE username='{username}' and subreddit='{subreddit}'
                    and flairs.flair_text='{flair_text}' and flairs.flair_class={flair_class}"""\
            .format(subreddit=subreddit, username=username, flair_text=flair_text, flair_class=this_class)

        results = DatabaseManager._execute_robust(conn.cursor(), query)

        return len(results) >= 1

    @staticmethod
    def is_banned(username, subreddit):

        conn = DatabaseManager.get_connection()

        query = """
                SELECT * FROM bans WHERE username='{username}' and subreddit='{subreddit}'
                """.format(username=username, subreddit=subreddit)

        results = DatabaseManager._execute_robust(conn.cursor(), query)

        return len(results) >= 1

    @staticmethod
    def _execute_robust(cursor, query):

        while True:

            try:

                result = cursor.execute(query).fetchall()

                return result

            except Exception as e:

                DisplayManager.displayStatusString("Database error. Trying again..." + str(e))

    @staticmethod
    def _execute_script_robust(connection, query):

        connection.isolation_level = None

        q_split = query.split(";")

        while True:

            try:

                cursor = connection.cursor()

                for q in q_split:
                    #print(q)
                    cursor.execute(q)



                return

            except Exception as e:
                try:
                    cursor.execute("rollback")
                except:
                    pass
                    #print("rollback unnecessary")
                DisplayManager.displayStatusString("Database error. Trying again..." + str(e))