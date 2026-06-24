"""initial_schema

Revision ID: 9d01d6aa5f02
Revises: 
Create Date: 2026-06-23 15:25:51.619095

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '9d01d6aa5f02'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing tables already in DB — skip drop/create.
    # Only add the new manager_id foreign key that our model needs.
    op.create_foreign_key(
        'fk_employees_manager',
        'employees', 'employees',
        ['manager_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_employees_manager', 'employees', type_='foreignkey')