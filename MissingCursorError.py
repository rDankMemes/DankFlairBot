

class MissingCursorError(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return "A cursor must be present in order to update the database."