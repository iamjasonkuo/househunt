from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login, admin
from app.search import add_to_index, remove_from_index, query_index
from flask_admin.contrib.sqla import ModelView, filters
from wtforms import validators


# from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.event import listens_for
# from sqlalchemy.pool import Pool

Base = declarative_base()

class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': [obj for obj in session.new if isinstance(obj, cls)],
            'update': [obj for obj in session.dirty if isinstance(obj, cls)],
            'delete': [obj for obj in session.deleted if isinstance(obj, cls)]
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['update']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['delete']:
            remove_from_index(cls.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

###Followers
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
    )

###Similar Projects
similar_projects = db.Table('similar_projects',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
    db.Column('similar_project_id', db.Integer, db.ForeignKey('project.id')),
    )

###Project Favorites
project_favorites = db.Table('project_favorites',
    db.Column('favorite_id', db.Integer,
    db.ForeignKey('user.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'))
    )

###Contributors
project_contributors = db.Table('project_contributors',
    db.Column('contributor_id', db.Integer,
    db.ForeignKey('user.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'))
    )

###Project Tags
project_tags = db.Table('project_tags',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
    )

###ProjectImage Tags
projectimage_tags = db.Table('projectimage_tags',
    db.Column('projectimage_id', db.Integer, db.ForeignKey('projectimage.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
    )

class CommonColumns(Base):
    __abstract__ = True
    _created = db.Column(db.DateTime, default=datetime.utcnow)
    _updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    _etag = db.Column(db.String(40))

class User(SearchableMixin, UserMixin, db.Model, CommonColumns):
    __tablename__ = 'user'
    __searchable__ = ['username']
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    headline = db.Column(db.String(120))
    first_name = db.Column(db.String(120))
    middle_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    flagged_user = db.Column(db.Integer)
    account_access = db.Column(db.Integer) #Boolean
    posts = db.relationship('Post', backref='author', lazy='dynamic') #1:M
    projects = db.relationship('Project', backref='creator', lazy='dynamic') #1:M
    favorites = db.relationship('Project', secondary=project_favorites, backref='admirer', lazy='dynamic') #M:M
    contributes = db.relationship('Project', secondary=project_contributors, backref='contributor', lazy='dynamic') #TODO: May need to refactor to include what type of contributor. Convert into association object? M:M
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic') #M:M


    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in}, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithm='HS256')['reset_password']
        except:
            return
        return User.query.get(id)

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def favorite(self, project):
        if not self.is_favorited(project):
            self.favorites.append(project)

    def unfavorite(self, project):
        if self.is_favorited(project):
            self.favorites.remove(project)

    def is_favorited(self, project):
        return self.favorites.filter(
            project_favorites.c.project_id == project.id).count() > 0

    def contribute(self, project):
        if not self.has_contributed(project):
            self.contributes.append(project)

    def uncontribute(self, project):
        if self.has_contributed(project):
            self.contributes.remove(project)

    def has_contributed(self, project):
        return self.contributes.filter(
            project_contributors.c.project_id == project.id).count() > 0


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(SearchableMixin, db.Model, CommonColumns):
    __searchable__ = ['body']
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    language = db.Column(db.String(5))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) ##M:1 User backref: author
    project_id = db.Column(db.Integer, db.ForeignKey('project.id')) ##M:1 Project backref: post_project
    parent_post_id = db.Column(db.Integer)

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def is_review(self):
        return self.project_id != None


class Project(db.Model, CommonColumns):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    headline = db.Column(db.String(30))
    description = db.Column(db.String(500))
    context_description = db.Column(db.String)
    objective_description = db.Column(db.String)
    performance_description = db.Column(db.String)
    completion_date = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Integer)
    beds = db.Column(db.Integer)
    baths = db.Column(db.Integer)
    sqft = db.Column(db.Integer)
    lotsqft = db.Column(db.Integer)
    num_units = db.Column(db.Integer)
    year_renovated = db.Column(db.Integer)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id')) ##M:1 Address backref: Site
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) ##M:1 User backref: creator & admirer
    links = db.relationship('Link', backref='link_project', lazy='dynamic') ##1:M
    posts = db.relationship('Post', backref='post_project', lazy='dynamic') ##1:M
    images = db.relationship('ProjectImage', backref='image_project', lazy='dynamic') ##1:M
    tags = db.relationship('Tag', secondary=project_tags, backref='tag_project', lazy='dynamic') #1:M
    similar = db.relationship(
        'Project', secondary=similar_projects,
        primaryjoin=(similar_projects.c.project_id == id),
        secondaryjoin=(similar_projects.c.similar_project_id == id),
        backref=db.backref('similar_project', lazy='dynamic'), lazy='dynamic') ##M:M

    def add_tag(self, tag):
        self.tags.append(tag)

    def remove_tag(self, tag):
        self.tags.remove(tag)

    def get_project_tags(self, project):
        return self.tags.filter(project_tags.c.project_id == project.id)

    def add_image(self, image):
        self.images.append(image)

    def remove_image(self, image):
        self.images.remove(image)

    def add_link(self, link):
        self.links.append(link)

    def remove_link(self, link):
        self.links.remove(link)

    def add_post(self, post):
        self.posts.append(post)

    def remove_post(self, post):
        self.posts.remove(post)

class ProjectImage(db.Model, CommonColumns):
    __tablename__ = 'projectimage'
    id = db.Column(db.Integer, primary_key=True)
    image_feature = db.Column(db.Integer) ##Boolean
    image_url = db.Column(db.String)
    description = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id')) ##M:1 Project image_project
    tags = db.relationship('Tag', secondary=projectimage_tags, backref='tagged_image', lazy='dynamic')

    def __repr__(self):
        return '<ProjectImage {}>'.format(self.image_url)

    def add_tag(self, tag):
        self.tags.append(tag)

    def remove_tag(self, tag):
        self.tags.remove(tag)

    def get_project_tags(self, project):
        return self.tags.filter(project_tags.c.project_id == project.id)

class Address(SearchableMixin, db.Model, CommonColumns):
    __searchable__ = ['full_address']
    __tablename__ = 'address'
    id = db.Column(db.Integer, primary_key=True)
    address1 = db.Column(db.String(30))
    address2 = db.Column(db.String(30))
    city = db.Column(db.String(30))
    state = db.Column(db.String(30))
    zipcode = db.Column(db.String(15))
    country = db.Column(db.String(20))
    full_address = db.Column(db.String(250))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    projects = db.relationship('Project', backref='site', lazy='dynamic') ##1:M

    def __repr__(self):
        return '<Address {}>'.format(self.full_address)

    def add_project(self, project):
        self.projects.append(project)

    def remove_project(self, project):
        self.projects.remove(project)

class Link(db.Model, CommonColumns):
    __tablename__ = 'link'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id')) ##M:1 Project link_project

    def __repr__(self):
        return '<Link {}>'.format(self.url)

class Tag(db.Model, CommonColumns):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer)
    name = db.Column(db.String(30))

    def __repr__(self):
        return '<Tag {}>'.format(self.name)

    @staticmethod
    def get_all_tags():
        try:
            tag_list = [(value.id, value.name) for value in db.session.query(Tag).distinct()]
        except:
            return
        return tag_list




##Listening for ElasticSearch
db.event.listen(db.session, 'before_commit', Post.before_commit)
db.event.listen(db.session, 'after_commit', Post.after_commit)
# db.event.listen(db.session, 'before_commit', User.before_commit)
# db.event.listen(db.session, 'after_commit', User.after_commit)
# db.event.listen(db.session, 'before_commit', Address.before_commit)
# db.event.listen(db.session, 'after_commit', Address.after_commit)


##TODO: Enhance Admin view: http://examples.flask-admin.org/
admin.add_view(ModelView(User, db.session, endpoint='test1'))
admin.add_view(ModelView(Post, db.session, endpoint='test2'))
admin.add_view(ModelView(Project, db.session, endpoint='test3'))
admin.add_view(ModelView(ProjectImage, db.session, endpoint='test4'))
admin.add_view(ModelView(Address, db.session, endpoint='test5'))
admin.add_view(ModelView(Link, db.session, endpoint='test6'))
admin.add_view(ModelView(Tag, db.session, endpoint='test7'))
