from app import create_app, db
from app.models import User, Post, Project, ProjectImage, Address, Link, Tag, UserRole, followers, similar_projects, project_favorites, project_contributors, user_access, project_tags, projectimage_tags

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Project': Project, 'ProjectImage': ProjectImage, 'Address': Address, 'Link': Link ,'Tag': Tag, 'UserRole': UserRole,
    'followers': followers, 'similar_projects': similar_projects, 'project_favorites': project_favorites, 'project_contributors': project_contributors, 'user_access': user_access, 'project_tags': project_tags, 'projectimage_tags': projectimage_tags }
