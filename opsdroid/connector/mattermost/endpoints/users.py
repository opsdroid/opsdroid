from .base import Base


class Users(Base):
    endpoint = "/users"

    def get_user(self, user_id):
        return self.get(f"{self.endpoint}/{user_id}")
