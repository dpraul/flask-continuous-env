class BaseSiteError(Exception):
    pass


class HTTPMethodNotImplementedError(BaseSiteError):
    pass


class ConfigNotFoundError(BaseSiteError):
    pass


class ControllerNotFoundError(BaseSiteError):
    pass


class NoEnvFoundError(BaseSiteError):
    pass
