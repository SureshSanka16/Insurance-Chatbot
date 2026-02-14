"""add fraud_status to claims

Revision ID: add_fraud_status
Revises: 5ffc303dd1ba
Create Date: 2026-02-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_fraud_status'
down_revision = '5ffc303dd1ba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add fraud_status column to claims table."""
    # Add fraud_status enum type
    fraudstatus_enum = sa.Enum('PENDING', 'ANALYZING', 'COMPLETED', 'FAILED', name='fraudstatus')
    fraudstatus_enum.create(op.get_bind(), checkfirst=True)
    
    # Add fraud_status column with default PENDING
    op.add_column('claims', sa.Column('fraud_status', fraudstatus_enum, nullable=True))
    
    # Update existing claims to PENDING status
    op.execute("UPDATE claims SET fraud_status = 'PENDING' WHERE fraud_status IS NULL")


def downgrade() -> None:
    """Remove fraud_status column from claims table."""
    op.drop_column('claims', 'fraud_status')
    
    # Drop enum type
    fraudstatus_enum = sa.Enum('PENDING', 'ANALYZING', 'COMPLETED', 'FAILED', name='fraudstatus')
    fraudstatus_enum.drop(op.get_bind(), checkfirst=True)
