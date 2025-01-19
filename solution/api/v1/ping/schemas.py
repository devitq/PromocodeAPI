from ninja import Schema


class PingOut(Schema):
    message_from_basement: str


__all__ = ["PingOut"]
