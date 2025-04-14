"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Post, Comment
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
# Agregado por mi, para que no cambie el orden de las llaves en el json
app.json.sort_keys = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/users', methods=['GET'])
def get_users():
    """
    Get all users
    """
    users = User.query.all()
    return jsonify([user.serialize() for user in users]), 200


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a user by id
    """
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"message": "User not found"}), 404
    return jsonify(user.serialize()), 200


@app.route('/users', methods=['POST'])
def create_user():
    """
    Create a user
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    if 'username' not in body:
        return jsonify({"message": "No username provided"}), 400
    # Verificar que el username no exista
    if User.query.filter_by(username=body['username']).first() is not None:
        return jsonify({"message": "Username already exists"}), 400
    if 'password' not in body:
        return jsonify({"message": "No password provided"}), 400
    if 'email' not in body:
        return jsonify({"message": "No email provided"}), 400
    # Verificar que el email no exista
    if User.query.filter_by(email=body['email']).first() is not None:   
        return jsonify({"message": "Email already exists"}), 400

    user = User(
        username=body['username'],
        password=body['password'],
        email=body['email'],
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.serialize()), 201


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update a user
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"message": "User not found"}), 404

    if 'username' in body:
        if user.username != body['username']:
            # Verificar que el nuevo username no exista
            if User.query.filter_by(username=body['username']).first() is not None:
                return jsonify({"message": "Username already exists"}), 400
            user.username = body['username']
    if 'password' in body:
        if user.password != body['password']:
            user.password = body['password']
    if 'email' in body:
        if user.email != body['email']:
            # Verificar que el nuevo email no exista
            if User.query.filter_by(email=body['email']).first() is not None:
                return jsonify({"message": "Email already exists"}), 400
            user.email = body['email']
    if 'birth_date' in body:
        user.birth_date = body['birth_date']
    if 'is_verified' in body:
        user.is_verified = body['is_verified']

    db.session.commit()
    return jsonify(user.serialize()), 200


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user
    """
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"message": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200


@app.route('/users/<int:followed_id>/follow', methods=['POST'])
def follow_user(followed_id):
    """
    Follow a user
    Example body:
    {
        "follower_id": 1
    }
    
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    if 'follower_id' not in body:
        return jsonify({"message": "No follower_id provided"}), 400

    followed = User.query.get(followed_id)
    if followed is None:
        return jsonify({"message": "Followed not found"}), 404

    follower = User.query.get(body['follower_id'])
    if follower is None:
        return jsonify({"message": "Follower not found"}), 404
    
    # Verificar que el usuario no se siga a si mismo
    if followed.id == follower.id:
        return jsonify({"message": "User cannot follow itself"}), 400
    # Verificar que el usuario no siga al usuario ya
    if follower in followed.followers:
        return jsonify({"message": "User already follows this user"}), 400

    followed.followers.append(follower)
    db.session.commit()
    return jsonify(followed.serialize()), 200


@app.route('/users/<int:followed_id>/unfollow', methods=['POST'])
def unfollow_user(followed_id):
    """
    Unfollow a user
    Example body:
    {
        "follower_id": 1
    }
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    if 'follower_id' not in body:
        return jsonify({"message": "No follower_id provided"}), 400

    followed = User.query.get(followed_id)
    if followed is None:
        return jsonify({"message": "User not found"}), 404

    follower = User.query.get(body['follower_id'])
    if follower is None:
        return jsonify({"message": "Follower not found"}), 404
    
    # Verificar que el follower ya siga al usuario
    if follower not in followed.followers:
        return jsonify({"message": "User does not follow this user"}), 400

    followed.followers.remove(follower)
    db.session.commit()
    return jsonify({"message": "Unfollowed user"}), 200


@app.route('/users/<int:user_id>/like', methods=['POST'])
def like_post(user_id):
    """
    Like a post
    Example body:
    {
        "post_id": 1
    }
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    if 'post_id' not in body:
        return jsonify({"message": "No post_id provided"}), 400

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"message": "User not found"}), 404

    post = Post.query.get(body['post_id'])
    if post is None:
        return jsonify({"message": "Post not found"}), 404
    
    # Verificar que el usuario no haya dado like al post ya
    if user in post.liked_by:
        return jsonify({"message": "User already liked this post"}), 400

    post.liked_by.append(user)
    db.session.commit()
    return jsonify(post.serialize()), 200


@app.route('/users/<int:user_id>/unlike', methods=['POST'])
def unlike_post(user_id):
    """
    Unlike a post
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    if 'post_id' not in body:
        return jsonify({"message": "No post_id provided"}), 400

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"message": "User not found"}), 404

    post = Post.query.get(body['post_id'])
    if post is None:
        return jsonify({"message": "Post not found"}), 404

    user.likes.remove(post)
    db.session.commit()
    return jsonify(user.serialize()), 200


@app.route('/posts', methods=['GET'])
def get_posts():
    """
    Get all posts
    """
    posts = Post.query.all()
    return jsonify([post.serialize() for post in posts]), 200


@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """
    Get a post by id
    """
    post = Post.query.get(post_id)
    if post is None:
        return jsonify({"message": "Post not found"}), 404
    return jsonify(post.serialize()), 200


@app.route('/posts', methods=['POST'])
def create_post():
    """
    Create a post
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    if 'description' not in body:
        return jsonify({"message": "No description provided"}), 400
    if 'media_url' not in body:
        return jsonify({"message": "No media_url provided"}), 400
    if 'user_id' not in body:
        return jsonify({"message": "No user_id provided"}), 400

    post = Post(
        description=body['description'],
        media_url=body['media_url'],
        user_id=body['user_id']
    )
    db.session.add(post)
    db.session.commit()
    return jsonify(post.serialize()), 201


@app.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """
    Update a post
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    post = Post.query.get(post_id)
    if post is None:
        return jsonify({"message": "Post not found"}), 404

    if 'description' in body:
        post.description = body['description']
    if 'media_url' in body:
        post.media_url = body['media_url']
    if 'status' in body:
        post.status = body['status']
    if 'user_id' in body:
        post.user_id = body['user_id']

    db.session.commit()
    return jsonify(post.serialize()), 200


@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """
    Delete a post
    """
    post = Post.query.get(post_id)
    if post is None:
        return jsonify({"message": "Post not found"}), 404
    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted"}), 200


@app.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """
    Get all comments for a post
    """
    post = Post.query.get(post_id)
    if post is None:
        return jsonify({"message": "Post not found"}), 404
    return jsonify([comment.serialize() for comment in post.comments]), 200


@app.route('/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    """
    Create a comment for a post
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    if 'text' not in body:
        return jsonify({"message": "No text provided"}), 400
    if 'user_id' not in body:
        return jsonify({"message": "No user_id provided"}), 400

    post = Post.query.get(post_id)
    if post is None:
        return jsonify({"message": "Post not found"}), 404

    comment = Comment(
        text=body['text'],
        user_id=body['user_id'],
        post_id=post_id
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.serialize()), 201


@app.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['PUT'])
def update_comment(post_id, comment_id):
    """
    Update a comment for a post
    """
    body = request.get_json()
    if not body:
        return jsonify({"message": "No body provided"}), 400
    comment = Comment.query.get(comment_id)
    if comment is None:
        return jsonify({"message": "Comment not found"}), 404

    if 'text' in body:
        comment.text = body['text']
    if 'user_id' in body:
        comment.user_id = body['user_id']
    if 'post_id' in body:
        comment.post_id = body['post_id']

    db.session.commit()
    return jsonify(comment.serialize()), 200


@app.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(post_id, comment_id):
    """
    Delete a comment for a post
    """
    comment = Comment.query.get(comment_id)
    if comment is None:
        return jsonify({"message": "Comment not found"}), 404
    db.session.delete(comment)
    db.session.commit()
    return jsonify({"message": "Comment deleted"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
