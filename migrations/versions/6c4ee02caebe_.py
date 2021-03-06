"""empty message

Revision ID: 6c4ee02caebe
Revises: 
Create Date: 2018-04-15 21:48:56.282528

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c4ee02caebe'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('address',
    sa.Column('_created', sa.DateTime(), nullable=True),
    sa.Column('_updated', sa.DateTime(), nullable=True),
    sa.Column('_etag', sa.String(length=40), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('address1', sa.String(length=30), nullable=True),
    sa.Column('address2', sa.String(length=30), nullable=True),
    sa.Column('city', sa.String(length=30), nullable=True),
    sa.Column('state', sa.String(length=30), nullable=True),
    sa.Column('zipcode', sa.String(length=15), nullable=True),
    sa.Column('country', sa.String(length=20), nullable=True),
    sa.Column('full_address', sa.String(length=250), nullable=True),
    sa.Column('lat', sa.Float(), nullable=True),
    sa.Column('lng', sa.Float(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tag',
    sa.Column('_created', sa.DateTime(), nullable=True),
    sa.Column('_updated', sa.DateTime(), nullable=True),
    sa.Column('_etag', sa.String(length=40), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('_created', sa.DateTime(), nullable=True),
    sa.Column('_updated', sa.DateTime(), nullable=True),
    sa.Column('_etag', sa.String(length=40), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('about_me', sa.String(length=140), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('headline', sa.String(length=120), nullable=True),
    sa.Column('first_name', sa.String(length=120), nullable=True),
    sa.Column('middle_name', sa.String(length=120), nullable=True),
    sa.Column('last_name', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    op.create_table('project',
    sa.Column('_created', sa.DateTime(), nullable=True),
    sa.Column('_updated', sa.DateTime(), nullable=True),
    sa.Column('_etag', sa.String(length=40), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.Column('headline', sa.String(length=30), nullable=True),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('context_description', sa.String(), nullable=True),
    sa.Column('objective_description', sa.String(), nullable=True),
    sa.Column('performance_description', sa.String(), nullable=True),
    sa.Column('completion_date', sa.DateTime(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.Column('beds', sa.Integer(), nullable=True),
    sa.Column('baths', sa.Integer(), nullable=True),
    sa.Column('sqft', sa.Integer(), nullable=True),
    sa.Column('lotsqft', sa.Integer(), nullable=True),
    sa.Column('num_units', sa.Integer(), nullable=True),
    sa.Column('year_renovated', sa.Integer(), nullable=True),
    sa.Column('publish', sa.Integer(), nullable=True),
    sa.Column('address_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['address_id'], ['address.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('userrole',
    sa.Column('_created', sa.DateTime(), nullable=True),
    sa.Column('_updated', sa.DateTime(), nullable=True),
    sa.Column('_etag', sa.String(length=40), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('link',
    sa.Column('_created', sa.DateTime(), nullable=True),
    sa.Column('_updated', sa.DateTime(), nullable=True),
    sa.Column('_etag', sa.String(length=40), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=120), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('post',
    sa.Column('_created', sa.DateTime(), nullable=True),
    sa.Column('_updated', sa.DateTime(), nullable=True),
    sa.Column('_etag', sa.String(length=40), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.String(length=140), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('language', sa.String(length=5), nullable=True),
    sa.Column('path', sa.Text(), nullable=True),
    sa.Column('overall_score', sa.Integer(), nullable=True),
    sa.Column('architectural_score', sa.Integer(), nullable=True),
    sa.Column('sustainability_score', sa.Integer(), nullable=True),
    sa.Column('craftmanship_score', sa.Integer(), nullable=True),
    sa.Column('landscape_score', sa.Integer(), nullable=True),
    sa.Column('interior_score', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['post.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_post_path'), 'post', ['path'], unique=False)
    op.create_index(op.f('ix_post_timestamp'), 'post', ['timestamp'], unique=False)
    op.create_table('project_contributors',
    sa.Column('contributor_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['contributor_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], )
    )
    op.create_table('project_favorites',
    sa.Column('favorite_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['favorite_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], )
    )
    op.create_table('project_tags',
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], )
    )
    op.create_table('projectimage',
    sa.Column('_created', sa.DateTime(), nullable=True),
    sa.Column('_updated', sa.DateTime(), nullable=True),
    sa.Column('_etag', sa.String(length=40), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('image_feature', sa.Integer(), nullable=True),
    sa.Column('image_url', sa.String(), nullable=True),
    sa.Column('description', sa.String(length=120), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('similar_projects',
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('similar_project_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['similar_project_id'], ['project.id'], )
    )
    op.create_table('user_access',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('access_level_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['access_level_id'], ['userrole.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('projectimage_tags',
    sa.Column('projectimage_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['projectimage_id'], ['projectimage.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('projectimage_tags')
    op.drop_table('user_access')
    op.drop_table('similar_projects')
    op.drop_table('projectimage')
    op.drop_table('project_tags')
    op.drop_table('project_favorites')
    op.drop_table('project_contributors')
    op.drop_index(op.f('ix_post_timestamp'), table_name='post')
    op.drop_index(op.f('ix_post_path'), table_name='post')
    op.drop_table('post')
    op.drop_table('link')
    op.drop_table('userrole')
    op.drop_table('project')
    op.drop_table('followers')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_table('tag')
    op.drop_table('address')
    # ### end Alembic commands ###
