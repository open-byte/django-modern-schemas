from django_modern_schemas import Schema


class Team:
    def __init__(self, name: str) -> None:
        self.name = name


class Member:
    def __init__(self, name: str, team: Team | None = None) -> None:
        self.name = name
        self.team = team


class TeamSchema(Schema):
    name: str


class MemberSchema(Schema):
    name: str
    team: TeamSchema | None = None


def serialize_member(member: Member) -> dict[str, object]:
    """Serialize an attribute-based Python object with Schema."""
    return MemberSchema.model_validate(member).model_dump()
