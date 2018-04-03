from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app
from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login
from app.search import add_to_index, remove_from_index, query_index

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

# ###Replies
# post_replies = db.Table('post_replies',
#     db.Column('replier', db.Integer, db.ForeignKey('post.id')),
#     db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
#     )


class User(SearchableMixin, UserMixin, db.Model):
    __tablename__ = 'user'
    __searchable__ = ['username']
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    occupation = db.Column(db.String(120))
    first_name = db.Column(db.String(120))
    middle_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    flagged_user = db.Column(db.Integer)
    account_access = db.Column(db.Integer)

    posts = db.relationship('Post', backref='author', lazy='dynamic') #1:M
    projects = db.relationship('Project', backref='creator', lazy='dynamic') #1:M
    flagged_projects = db.relationship('ProjectFlagged', back_populates='flagger') #1:M association class object

    favorites = db.relationship('Project', secondary=project_favorites, backref='admirer', lazy='dynamic') #M:M
    contributes = db.relationship('Project', secondary=project_contributors, backref='contributor', lazy='dynamic') #M:M
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

class Post(SearchableMixin, db.Model):
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


class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    headline = db.Column(db.String(30))
    description = db.Column(db.String(500))
    completion_date = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Integer)
    tags = db.Column(db.String(120))
    beds = db.Column(db.Integer)
    baths = db.Column(db.Integer)
    sqft = db.Column(db.Integer)
    lotsqft = db.Column(db.Integer)
    build_type = db.Column(db.String(50))
    property_type = db.Column(db.String(50))
    num_units = db.Column(db.Integer)
    year_built = db.Column(db.Integer)
    year_renovated = db.Column(db.Integer)

    address_id = db.Column(db.Integer, db.ForeignKey('address.id')) ##M:1 Address backref: Site
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) ##M:1 User backref: creator & admirer
    links = db.relationship('Link', backref='link_project', lazy='dynamic') ##1:M
    posts = db.relationship('Post', backref='post_project', lazy='dynamic') ##1:M
    images = db.relationship('ProjectImage', backref='image_project', lazy='dynamic') ##1:M

    flaggers = db.relationship('ProjectFlagged', back_populates='project') ##M:M class association object
    similar = db.relationship(
        'Project', secondary=similar_projects,
        primaryjoin=(similar_projects.c.project_id == id),
        secondaryjoin=(similar_projects.c.similar_project_id == id),
        backref=db.backref('similar_project', lazy='dynamic'), lazy='dynamic') ##M:M

    def __repr__(self):
        return '<Project {}>'.format(self.name)

    def queue_comparable(self, project):
        if not self.is_similar(project):
            self.similar_projects.append(project)

    def dequeue_comparable(self, project):
        if self.is_similar(project):
            self.similar_projects.remove(project)

    def is_similar(self, project):
        return self.similar_projects.filter(
            followers.c.followed_id == project.id).count() > 0

    def add_post(self, post):
        self.followed.append(post)

    def remove_post(self, post):
        self.followed.remove(post)

class ProjectImage(db.Model):
    __tablename__ = 'projectimage'
    id = db.Column(db.Integer, primary_key=True)
    image_feature = db.Column(db.Integer) ##Boolean
    image_url = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id')) ##M:1 Project image_project

class Address(SearchableMixin, db.Model):
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

class Link(db.Model):
    __tablename__ = 'link'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id')) ##M:1 Project link_project

#######ASSOCIATION OBJECT############
class ProjectFlagged(db.Model):
    __tablename__ = 'projectflagged'
    flagger_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True) ##Reporter
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    flag_reason = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    flagger = db.relationship('User', back_populates='flagged_projects')
    project = db.relationship('Project', back_populates='flaggers')

class ProjectContributor(db.Model):
    __tablename__ = 'projectcontributor'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    verified = db.Column(db.Integer) ##Boolean
    project = db.relationship('Project', backref='contributor_associations')
    user = db.relationship('User', backref='project_associations')


##Listening for ElasticSearch
db.event.listen(db.session, 'before_commit', Post.before_commit)
db.event.listen(db.session, 'after_commit', Post.after_commit)
# db.event.listen(db.session, 'before_commit', User.before_commit)
# db.event.listen(db.session, 'after_commit', User.after_commit)
# db.event.listen(db.session, 'before_commit', Address.before_commit)
# db.event.listen(db.session, 'after_commit', Address.after_commit)
