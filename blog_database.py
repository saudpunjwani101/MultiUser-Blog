import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Unicode, create_engine	
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	username = Column(String(100), nullable=False, primary_key=True)
	password = Column(Unicode(100), nullable=False)
	profile_photo_url = Column(String(150), nullable=False, default='/static/uploaded/user.png')
	posts = relationship("Post", backref="posts", lazy="dynamic")
	photos = relationship("UserPhoto", back_populates="user")

class Post(Base):
	__tablename__ = 'post'

	id = Column(Integer, nullable=False, primary_key=True)
	content = Column(Text(500), nullable=False)
	likes = Column(Integer, default=0)
	user_name = Column(String(100), ForeignKey('user.username'))
	user = relationship(User)
	comments = Column(Integer, default=0)

class Tweet(Base):
	__tablename__ = 'tweet'

	id = Column(Integer, nullable=False, primary_key=True)
	post_id = Column(Integer, ForeignKey('post.id'))
	post = relationship(Post)
	content = Column(Text(500), nullable=False) 
	username = Column(String(100), ForeignKey('user.username'))
	user = relationship(User)

class Like(Base):
	__tablename__ = 'like'

	id = Column(Integer, nullable=True, primary_key=True)
	post_id = Column(Integer, ForeignKey('post.id'))
	post = relationship(Post)
	username = Column(String(100), ForeignKey('user.username'))
	user = relationship(User)

class UserPhoto(Base):
	__tablename__ = 'userphoto'

	id = Column(Integer, primary_key=True)
	filename = Column(String(100))
	url = Column(String(150))
	user_name = Column(String(100), ForeignKey('user.username'))
	user = relationship(User)

engine = create_engine('sqlite:///multiblog.db')
Base.metadata.create_all(engine)