import os
from flask_admin import Admin
from models import db, User, Post, Comment
from flask_admin.contrib.sqla import ModelView

# #VERSIÓN SIMPLE
# def setup_admin(app):
#     app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
#     app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
#     admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

#     # Add your models here, for example this is how we add a the User model to the admin
#     admin.add_view(ModelView(User, db.session))
#     admin.add_view(ModelView(Post, db.session))
#     admin.add_view(ModelView(Comment, db.session))

#     # You can duplicate that line to add mew models
#     # admin.add_view(ModelView(YourModelName, db.session))
# #FIN VERSIÓN SIMPLE


#VERSIÓN AVANZADA
#Incluye la configuración de las columnas que deseas mostrar en el admin
#De esta manera se podrán ver las listas asociadas a las relaciones de los modelos


class UserAdmin(ModelView):
    # Especifica las columnas que deseas mostrar
    column_list = ['id', 'username', 'email',
                   'is_verified', 'created_at', "posts", "comments", "likes", "followed_by", "following"]


class PostAdmin(ModelView):
    column_list = ['id', 'description', 'media_url',
                   'status', 'created_at', "user_id", "user", "comments", "liked_by"]


class CommentAdmin(ModelView):
    column_list = ['id', 'text', 'created_at',
                   'user_id', "user", 'post_id', "post"]


def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

    # Add your models here, for example this is how we add a the User model to the admin
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(PostAdmin(Post, db.session))
    admin.add_view(CommentAdmin(Comment, db.session))

    # You can duplicate that line to add mew models
    # admin.add_view(ModelView(YourModelName, db.session))
# FIN VERSIÓN AVANZADA
