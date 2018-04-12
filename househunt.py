from app import create_app, db
from app.models import User, Post, Project, ProjectImage, Address, Link, Tag

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Project': Project, 'ProjectImage': ProjectImage, 'Address': Address, 'Link': Link ,'Tag': Tag }
