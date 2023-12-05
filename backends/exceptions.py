class BackendException(Exception):
    pass


class ObjectNotFound(BackendException):
    pass


class EntityTooLarge(BackendException):
    pass


class UnsupportedMediaType(BackendException):
    pass


class UnsupportedLinkOrigin(BackendException):
    pass
