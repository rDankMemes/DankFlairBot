
class InfoNotFetchedError(Exception):
    def __init__(self, m):
        self.message = m
    def __str__(self):
        return self.message