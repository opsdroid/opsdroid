from .base import Base


class Teams(Base):
    endpoint = "/teams"
    # No endpoints are used from this API yet - but this will likely change with additional features in the future
    # we just neet the endpoint path segment because querying channels by name is done for a team
