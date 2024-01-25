from flask_login import UserMixin
from sqlalchemy import Column, Text
from werkzeug.security import check_password_hash, generate_password_hash

from database import Base


class Users(UserMixin):
    # __tablename__ = "users"

    # user_id = Column(Text(36), primary_key=True)
    # first_name = Column(Text(45), nullable=False)
    # last_name = Column(Text(45), nullable=False)
    # email = Column(Text(45), nullable=False, unique=True)
    # password = Column(Text(162), nullable=False)
    # role = Column(Text(20), nullable=False)

    def __init__(self, user_dict):
        self.user_dict = user_dict

    # Overriding get_id is required if you don't have the id property
    # Check the source code for UserMixin for details
    def get_id(self):
        object_id = self.user_dict.get("user_id")
        return str(object_id)

    # @property
    # def password(self):
    #     raise AttributeError("Password is not a readable attribute!")

    # @password.setter
    # def password(self, password):
    #     self.password = generate_password_hash(password)

    # def verify_password(self, password):
    #     return check_password_hash(self.password, password)

    # Create A Text
    def __repr__(self):
        return "<Name %r>" % self.first_name
