import enum
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Date, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class PostStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELETED = "deleted"
    BLOCKED = "blocked"
    ARCHIVED = "archived"


# Auxiliary table for the many-to-many relationship between Users that follow each other
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey(
        'user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey(
        'user.id'), primary_key=True),
    db.Column('created_at', db.DateTime(timezone=True),
              default=datetime.datetime.now)
)


# Auxiliary table for the many-to-many relationship between Users and Posts that are liked
likes = db.Table(
    'likes',
    db.Column('user_id', db.Integer, db.ForeignKey(
        'user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey(
        'post.id'), primary_key=True),
    db.Column('created_at', db.DateTime(timezone=True),
              default=datetime.datetime.now)
)


class User(db.Model):
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
        back_populates="user")
    # one user can have many comments and one comment can belong to one user
    comments: Mapped[list["Comment"]] = relationship(back_populates="user")

    # B) many-to-many relationships
    # one user can like many posts and one post can be liked by many users
    # this is modeled by a auxiliary table called likes
    likes: Mapped[list["Post"]] = relationship(
        secondary=likes,
        back_populates="liked_by",
    )

    # C) self-referential many-to-many relationships
    # one user can follow many users and one user can be followed by many users
    followed_by: Mapped[list["User"]] = relationship(
        secondary=followers,
        primaryjoin=followers.c.follower_id == id,
        secondaryjoin=followers.c.followed_id == id,
        # foreign_keys=[followers.c.follower_id],
        back_populates="following",
    )
    following: Mapped[list["User"]] = relationship(
        secondary=followers,
        primaryjoin=followers.c.followed_id == id,
        secondaryjoin=followers.c.follower_id == id,
        # foreign_keys=[followers.c.followed_id],
        back_populates="followed_by",
    )

    # Method that define how the user is represented as a string
    # this is used for debugging purposes
    # and for the admin interface
    # it is not used in the API
    def __repr__(self):
        return f"User(id={self.id}, username={self.username})"

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
            "followers": [user.username for user in self.followed_by],
            "following": [user.username for user in self.following],
        }


class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(800), nullable=False)
    media_url: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[enum] = mapped_column(
        Enum(PostStatus), default=PostStatus.APPROVED)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now)
    user_id: Mapped[int] = mapped_column(
        db.ForeignKey('user.id'), nullable=False)

    user: Mapped["User"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post")
    liked_by: Mapped[list["User"]] = relationship(
        secondary=likes,
        back_populates="likes",
    )

    def __repr__(self):
        return f"Post(id={self.id})"

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
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(800), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now)
    post_id: Mapped[int] = mapped_column(
        db.ForeignKey('post.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(
        db.ForeignKey('user.id'), nullable=False)

    post: Mapped["Post"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(back_populates="comments")

    def __repr__(self):
        return f"Comment(id={self.id})"

    def serialize(self):
        return {
            "id": self.id,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
            "post_id": self.post_id,
            "user_id": self.user_id,
            "user": self.user.username,
        }
