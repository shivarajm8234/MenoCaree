from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    @staticmethod
    def get(user_id):
        # This is a placeholder. In a real app, you'd query your database
        # For now, we'll just return a dummy user for testing
        return User(1, "test_user", "test@example.com")
