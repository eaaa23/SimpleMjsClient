class MjsError(Exception):
    TEXT_KEY: str = ""
    @classmethod
    def check(cls, res):
        if res.error.code:
            raise cls(res.error.code)

class ClientError(MjsError):
    pass

class PhaseInvalid(ClientError):
    pass

class ControllerError(MjsError):
    pass

class ClientConnectionError(ClientError):
    TEXT_KEY = "connection"

class LoginError(ClientError):
    TEXT_KEY = "login"

class StartUnifiedMatchError(ClientError):
    pass

class CreateRoomError(ClientError):
    pass

class AddBotError(ClientError):
    pass

class JoinRoomError(ClientError):
    pass

class StartRoomError(ClientError):
    pass

class GameError(ClientError):
    pass
