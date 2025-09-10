"""Add contract_name field to contract_abis (simplified)

Revision ID: add_contract_name_simple
Revises: 82df76890258
Create Date: 2025-09-10 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_contract_name_simple'
down_revision = '82df76890258'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add contract_name field to contract_abis table"""
    op.add_column('contract_abis', sa.Column('contract_name', sa.String(length=255), nullable=True, comment='合约名称（用户定义的可读名称）'))


def downgrade() -> None:
    """Remove contract_name field from contract_abis table"""
    op.drop_column('contract_abis', 'contract_name')