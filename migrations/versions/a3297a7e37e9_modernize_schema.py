"""modernize schema

Revision ID: a3297a7e37e9
Revises: 710958432794
Create Date: 2026-07-21 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3297a7e37e9'
down_revision = '710958432794'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Modify users table
    # Make password_hash nullable (required for OAuth)
    op.alter_column('users', 'password_hash',
               existing_type=sa.String(length=256),
               nullable=True)
    # Add google_id and profile_pic
    op.add_column('users', sa.Column('google_id', sa.String(length=256), nullable=True))
    op.create_unique_constraint('uq_users_google_id', 'users', ['google_id'])
    op.add_column('users', sa.Column('profile_pic', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # 2. Rename resumes table to resume_metadata
    op.rename_table('resumes', 'resume_metadata')

    # 3. Modify interview_sessions table
    # Add new columns (ai_provider and updated_at)
    op.add_column('interview_sessions', sa.Column('ai_provider', sa.String(length=50), nullable=True))
    op.add_column('interview_sessions', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Re-link the resume foreign key to point to resume_metadata instead of resumes
    # Using batch alter to ensure it works across SQLite (during development/testing) and Postgres
    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        # Drop old constraint (naming can be dynamic, try by column reference if possible)
        # For Postgres, standard naming of foreign keys is 'table_column_fkey'
        try:
            batch_op.drop_constraint('interview_sessions_resume_id_fkey', type_='foreignkey')
        except Exception:
            pass
        batch_op.create_foreign_key(
            'interview_sessions_resume_id_fkey',
            'resume_metadata',
            ['resume_id'],
            ['id']
        )

    # 4. Create new scores table for 6-dimensional scoring
    op.create_table('scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('content_relevance', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('answer_structure', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('voice_clarity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('voice_modulation', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('filler_control', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('answer_depth', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], name='scores_session_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Add created_at to questions and answers tables
    op.add_column('questions', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('answers', sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade():
    # 1. Drop created_at columns
    op.drop_column('answers', 'created_at')
    op.drop_column('questions', 'created_at')

    # 2. Drop scores table
    op.drop_table('scores')

    # 3. Modify interview_sessions
    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('interview_sessions_resume_id_fkey', type_='foreignkey')
        except Exception:
            pass
        batch_op.create_foreign_key(
            'interview_sessions_resume_id_fkey',
            'resumes',
            ['resume_id'],
            ['id']
        )
    op.drop_column('interview_sessions', 'updated_at')
    op.drop_column('interview_sessions', 'ai_provider')

    # 4. Rename resume_metadata back to resumes
    op.rename_table('resume_metadata', 'resumes')

    # 5. Modify users
    op.drop_constraint('uq_users_google_id', 'users', type_='unique')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'profile_pic')
    op.drop_column('users', 'google_id')
    op.alter_column('users', 'password_hash',
               existing_type=sa.String(length=256),
               nullable=False)
