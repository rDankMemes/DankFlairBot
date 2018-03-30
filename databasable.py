import MissingCursorError


class databasable(object):

    def __init__(self, cursor = None):
        self.__cursor = cursor
        pass

    @property
    def cursor(self):
        return self.__cursor

    def fetchall(self):
        # TODO: hard fetch all. Fetch everything about this object. Even if that requires fetching other object types.
        raise NotImplementedError
        pass

    def fetch(self):
        # TODO: update data this object is immediately concerned about from reddit. Calculate values with local database.
        raise NotImplementedError
        pass


    def update(self, cursor):
        # TODO: update the database representation, or insert.
        active_cursor = None

        if(cursor is None and self.cursor is None):
            raise MissingCursorError
        elif(cursor is None):
            active_cursor = self.cursor
        else:
            active_cursor = cursor

        return active_cursor
