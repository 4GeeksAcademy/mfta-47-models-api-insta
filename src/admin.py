import os
from flask_admin import Admin
from models import db, User, Post, Comment, Follow, Like
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.orm import class_mapper, RelationshipProperty

# VERSIÓN SIMPLE
def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='4Geeks Admin')

    # Add your models here, for example this is how we add a the User model to the admin
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Post, db.session))
    admin.add_view(ModelView(Comment, db.session))
    admin.add_view(ModelView(Follow, db.session))
    admin.add_view(ModelView(Like, db.session))

    # You can duplicate that line to add mew models
    # admin.add_view(ModelView(YourModelName, db.session))
# FIN VERSIÓN SIMPLE


# # VERSIÓN AVANZADA
# # Incluye la configuración de las columnas que deseas mostrar en el admin
# # De esta manera se podrán ver las listas asociadas a las relaciones de los modelos
# class UserAdmin(ModelView):
#     # Especifica las columnas que deseas mostrar
#     column_list = ['id', 'username', 'email',
#                    'is_verified', 'created_at', "posts", "comments", "likes", "followed_by", "following"]


# class PostAdmin(ModelView):
#     column_list = ['id', 'description', 'media_url',
#                    'status', 'created_at', "user_id", "user", "comments", "liked_by"]


# class CommentAdmin(ModelView):
#     column_list = ['id', 'text', 'created_at',
#                    'user_id', "user", 'post_id', "post"]


# def setup_admin(app):
#     app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
#     app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
#     admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

#     # Add your models here, for example this is how we add a the User model to the admin
#     admin.add_view(UserAdmin(User, db.session))
#     admin.add_view(PostAdmin(Post, db.session))
#     admin.add_view(CommentAdmin(Comment, db.session))

#     # You can duplicate that line to add mew models
#     # admin.add_view(ModelView(YourModelName, db.session))
# # FIN VERSIÓN AVANZADA


# # VERSIÓN AVANZADA REDUCIDA
# class FullView(ModelView):
#     def __init__(self, model, session, **kwargs):
#         mapper = class_mapper(model)

#         # Columnas simples (FK incluidas al inicio)
#         column_keys = [c.key for c in mapper.columns]

#         # Relaciones (no dinámicas)
#         relation_keys = [
#             r.key for r in mapper.relationships
#             if r.lazy != 'dynamic'
#         ]

#         # Mostrar todas las columnas + relaciones en la vista general
#         self.column_list = column_keys + relation_keys

#         # Excluir el PK (ej. id) y los *_id si existe una relación equivalente
#         fk_to_exclude = {
#             f"{rel}_id" for rel in relation_keys
#         }
#         self.form_columns = [
#             c for c in column_keys + relation_keys
#             if c != 'id' and c not in fk_to_exclude
#         ]

#         super().__init__(model, session, **kwargs)


# def setup_admin(app):
#     app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
#     app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
#     admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

#     # Add your models here, for example this is how we add a the User model to the admin
#     admin.add_view(FullView(User, db.session))
#     admin.add_view(FullView(Post, db.session))
#     admin.add_view(FullView(Comment, db.session))
#     admin.add_view(FullView(Follow, db.session))
#     admin.add_view(FullView(Like, db.session))

#     # You can duplicate that line to add mew models
#     # admin.add_view(ModelView(YourModelName, db.session))
# # FIN VERSIÓN AVANZADA REDUCIDA