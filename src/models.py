import enum
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Date, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.associationproxy import association_proxy

db = SQLAlchemy()


class PostStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELETED = "deleted"
    BLOCKED = "blocked"
    ARCHIVED = "archived"

    @classmethod
    def choices(cls):
        return [status.value for status in cls]


class Follow(db.Model):
    __tablename__ = "follows"
    follower_id: Mapped[int] = mapped_column(
        db.ForeignKey('users.id'), primary_key=True)
    followed_id: Mapped[int] = mapped_column(
        db.ForeignKey('users.id'), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now)

    follower: Mapped["User"] = relationship(back_populates="following_associations", foreign_keys=[follower_id])
    followed: Mapped["User"] = relationship(back_populates="followers_associations", foreign_keys=[followed_id])

    def __init__(self, follower_id, followed_id):
        self.follower_id = follower_id
        self.followed_id = followed_id

    def __repr__(self):
        return f"Follow(follower_id={self.follower_id}, followed_id={self.followed_id})"
    
    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"

    def serialize(self):
        return {
            "follower_id": self.follower_id,
            "followed_id": self.followed_id,
            "created_at": self.created_at.isoformat(),
        }



class User(db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    birth_date: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    is_verified: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)

    ###########################
    # relationships
    ###########################

    # A) one-to-many relationships
    # one user can have many posts and one post can belong to one user
    posts: Mapped[list["Post"]] = relationship(
        back_populates="user", cascade="all, delete-orphan")
    # one user can have many comments and one comment can belong to one user
    comments: Mapped[list["Comment"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # B) many-to-many relationships
    # one user can like many posts and one post can be liked by many users
    # Association object
    likes: Mapped[list["Like"]] = relationship(
        back_populates="user", cascade="all, delete-orphan")

    # C) self-referential many-to-many relationships
    # one user can follow many users and one user can be followed by many users
    # Association object
    # The association object is the Follow class
    following_associations: Mapped[list["Follow"]] = relationship(
        back_populates="follower",
        foreign_keys=[Follow.follower_id],
        cascade="all, delete-orphan"
    )

    followers_associations: Mapped[list["Follow"]] = relationship(
        back_populates="followed",
        foreign_keys=[Follow.followed_id],
        cascade="all, delete-orphan"
    )

    # Accessors de conveniencia con association_proxy
    following: Mapped[list["User"]] = association_proxy(
        "following_associations", "followed",
        creator=lambda followed: Follow(follower_id=None, followed_id=followed.id)
    )

    followers: Mapped[list["User"]] = association_proxy(
        "followers_associations", "follower",
        creator=lambda follower: Follow(follower_id=follower.id, followed_id=None)
    )
    

    # Method that define how the user is represented as a string
    # this is used for debugging purposes
    # and for the admin interface
    # it is not used in the API
    def __repr__(self):
        return f"User(id={self.id}, username={self.username})"
    
    def __str__(self):
        return self.username

    # Method that serialize the user object to a dictionary
    # this is used for the API
    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            # do not serialize the password, its a security breach
            "email": self.email,
            "birth_date": self.birth_date,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "posts": [post.id for post in self.posts],
            "followers": [user.username for user in self.followers],
            "following": [user.username for user in self.following],
        }


class Post(db.Model):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(800), nullable=False)
    media_url: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[enum] = mapped_column(
        Enum(PostStatus), default=PostStatus.APPROVED)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now)
    user_id: Mapped[int] = mapped_column(
        db.ForeignKey('users.id'), nullable=False)

    user: Mapped["User"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    # Association object
    likes_associations: Mapped[list["Like"]] = relationship(
        back_populates="post", cascade="all, delete-orphan")
    # Convenience accessor
    liked_by: Mapped[list["User"]] = association_proxy(
        "likes_associations", "user",
        creator=lambda user: Like(user_id=user.id, post_id=None)
    )

    def __repr__(self):
        return f"Post(id={self.id})"
    
    def __str__(self):
        return self.description

    def serialize(self):
        return {
            "id": self.id,
            "description": self.description,
            "media_url": self.media_url,
            "status": self.status.name,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "user": self.user.username,
            "comments": [comment.text for comment in self.comments],
            "liked_by": [user.username for user in self.liked_by],
            "likes_count": len(self.liked_by),
            "comments_count": len(self.comments),
        }


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(800), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now)
    post_id: Mapped[int] = mapped_column(
        db.ForeignKey('posts.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(
        db.ForeignKey('users.id'), nullable=False)

    post: Mapped["Post"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(back_populates="comments")

    def __repr__(self):
        return f"Comment(id={self.id})"
    
    def __str__(self):
        return self.text

    def serialize(self):
        return {
            "id": self.id,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
            "post_id": self.post_id,
            "post": self.post.description,
            "user_id": self.user_id,
            "user": self.user.username,
        }




class Like(db.Model):
    __tablename__ = "likes"
    user_id: Mapped[int] = mapped_column(
        db.ForeignKey('users.id'), primary_key=True)
    post_id: Mapped[int] = mapped_column(
        db.ForeignKey('posts.id'), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now)

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="likes")
    post: Mapped["Post"] = relationship(
        "Post", foreign_keys=[post_id], back_populates="likes_associations")
    
    def __init__(self, user_id, post_id):
        self.user_id = user_id
        self.post_id = post_id

    def __repr__(self):
        return f"Like(user_id={self.user_id}, post_id={self.post_id})"
    
    def __str__(self):
        return f"{self.user.username} likes it"

    def serialize(self):
        return {
            "user_id": self.user_id,
            "user": self.user.username,
            "post_id": self.post_id,
            "post": self.post.description,
            "created_at": self.created_at.isoformat(),
        }