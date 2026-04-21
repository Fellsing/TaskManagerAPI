class PostAppException(Exception):
    pass

class TaskNotFoundException(PostAppException):
    pass

class NotEnoughPermission(PostAppException):
    pass