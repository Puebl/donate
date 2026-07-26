"""empty message

Revision ID: fea02b158770
Revises: 
Create Date: 2026-03-27 17:28:08.433238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fea02b158770'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.create_table('deals',
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('deal_id', sa.Text(), nullable=False),
    sa.Column('amount', sa.Integer(), server_default='0', nullable=False),
    sa.Column('stake_reserved', sa.Integer(), server_default='0', nullable=False),
    sa.Column('open_status', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('is_locked', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('deal_type', sa.Text(), server_default='N1', nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.CheckConstraint('amount >= 0', name='ck_deals_amount_non_negative'),
    sa.CheckConstraint('amount >= stake_reserved', name='ck_deals_amount_gte_reserved'),
    sa.CheckConstraint('stake_reserved >= 0', name='ck_deals_reserved_non_negative'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('deal_id')
    )
    op.create_table('stakes',
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('min_sum', sa.Integer(), server_default='0', nullable=False),
    sa.Column('multiple_choice', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('active', 'paused', 'finished', name='stakestatusenum', native_enum=False), nullable=False),
    sa.Column('stake_type', sa.Enum('vote', 'quiz', 'fundraising', name='staketypeenum', native_enum=False), nullable=False),
    sa.Column('vote_mechanic', sa.Enum('fixed', 'weighted', name='votemechanicenum', native_enum=False), nullable=False),
    sa.Column('paused_time', sa.DateTime(), nullable=True),
    sa.Column('finished_time', sa.DateTime(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('file_id', sa.Uuid(), nullable=True),
    sa.Column('winner_outcome_id', sa.Uuid(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('currency', sa.String(length=3), server_default='RUB', nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('streamers_commissions',
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('withdraw_comission_sbp', sa.Integer(), nullable=True),
    sa.Column('withdraw_comission_card', sa.Integer(), nullable=True),
    sa.Column('viewer_commission_sbp', sa.Integer(), nullable=True),
    sa.Column('viewer_commission_card', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('streamer_id')
    )
    op.create_table('tinkoff_deposit_requests',
    sa.Column('order_id', sa.String(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('order_id')
    )
    op.create_table('tinkoff_withdraw_methods',
    sa.Column('bank_name', sa.String(length=100), nullable=False),
    sa.Column('card_id', sa.String(length=100), nullable=True),
    sa.Column('sbp_member_id', sa.String(length=100), nullable=True),
    sa.Column('type', sa.Enum('card', 'sbp', name='tinkoffwithdrawtypeenum', native_enum=False), nullable=False),
    sa.Column('provider', sa.Enum('tinkoff', 'oxypay', name='paymentproviderenum', native_enum=False), nullable=True),
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('phone', sa.String(length=30), nullable=True),
    sa.Column('card_pan', sa.String(length=20), nullable=True),
    sa.Column('request_id', sa.Uuid(), nullable=True),
    sa.Column('is_main', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('removed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('streamer_id')
    )
    op.create_table('stake_distributions',
    sa.Column('stake_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('distribution_type', sa.String(), nullable=False),
    sa.Column('source_streamer_id', sa.Integer(), nullable=False),
    sa.Column('payout_status', sa.String(), server_default='pending', nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.ForeignKeyConstraint(['stake_id'], ['stakes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('stake_outcome',
    sa.Column('stake_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('coefficient', sa.Float(), nullable=False),
    sa.Column('is_winner', sa.Boolean(), nullable=False),
    sa.Column('target_amount', sa.Integer(), nullable=True),
    sa.Column('current_amount', sa.Integer(), server_default='0', nullable=False),
    sa.Column('votes_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.ForeignKeyConstraint(['stake_id'], ['stakes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('stake_balances',
    sa.Column('stake_id', sa.Uuid(), nullable=False),
    sa.Column('outcome_id', sa.Uuid(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('total_amount', sa.Integer(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.ForeignKeyConstraint(['outcome_id'], ['stake_outcome.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['stake_id'], ['stakes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transactions',
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'completed', 'failed', name='transactionstatusenum', native_enum=False), nullable=False),
    sa.Column('commission', sa.Integer(), nullable=True),
    sa.Column('payment_provider', sa.Enum('tinkoff', 'oxypay', name='paymentproviderenum', native_enum=False), nullable=False),
    sa.Column('external_transaction_id', sa.String(), nullable=True),
    sa.Column('operation_type', sa.Enum('t_withdraw_fee_sbp', 't_withdraw_card_fee', 't_withdraw_sbp_fee', 't_deposit_sbp_fee', 't_deposit_card_fee', 't_deposit_sbp', 't_deposit_card', 't_withdraw_sbp', 't_withdraw_card', 't_withdraw_sbp_rollback', 't_withdraw_card_rollback', 't_withdraw_sbp_rollback_fee', 't_withdraw_card_rollback_fee', 'ox_deposit_card', 'ox_deposit_card_fee', 'ox_withdraw_card', 'ox_withdraw_card_fee', 'ox_withdraw_card_rollback', 'ox_withdraw_card_rollback_fee', 'stake_payout_credit', 'stake_payout_withdraw', 'stake_payout_withdraw_fee', 'stake_payout_rollback', 'init', 'withdraw', 'credit', name='operationtypeenum', native_enum=False), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('rolled_back', sa.Boolean(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('outcome_id', sa.Uuid(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.ForeignKeyConstraint(['outcome_id'], ['stake_outcome.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.streamer_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('balances',
    sa.Column('operation_type', sa.Enum('t_withdraw_fee_sbp', 't_withdraw_card_fee', 't_withdraw_sbp_fee', 't_deposit_sbp_fee', 't_deposit_card_fee', 't_deposit_sbp', 't_deposit_card', 't_withdraw_sbp', 't_withdraw_card', 't_withdraw_sbp_rollback', 't_withdraw_card_rollback', 't_withdraw_sbp_rollback_fee', 't_withdraw_card_rollback_fee', 'ox_deposit_card', 'ox_deposit_card_fee', 'ox_withdraw_card', 'ox_withdraw_card_fee', 'ox_withdraw_card_rollback', 'ox_withdraw_card_rollback_fee', 'stake_payout_credit', 'stake_payout_withdraw', 'stake_payout_withdraw_fee', 'stake_payout_rollback', 'init', 'withdraw', 'credit', name='operationtypeenum', native_enum=False), nullable=False),
    sa.Column('balance_diff', sa.Integer(), nullable=False),
    sa.Column('balance_total', sa.Integer(), nullable=False),
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(length=3), server_default='RUB', nullable=False),
    sa.Column('transaction_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('payments',
    sa.Column('order_id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('deal_id', sa.Text(), nullable=False),
    sa.Column('transaction_id', sa.Uuid(), nullable=True),
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['deal_id'], ['deals.deal_id'], ),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
    sa.PrimaryKeyConstraint('order_id')
    )
    op.create_table('tinkoff_withdraws',
    sa.Column('streamer_id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Uuid(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('payment_id', sa.String(length=100), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('balance_id', sa.Uuid(), nullable=True),
    sa.Column('tinkoff_withdraw_method_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['balance_id'], ['balances.id'], ),
    sa.ForeignKeyConstraint(['tinkoff_withdraw_method_id'], ['tinkoff_withdraw_methods.id'], ),
    sa.PrimaryKeyConstraint('order_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')
    op.drop_table('tinkoff_withdraws')
    op.drop_table('payments')
    op.drop_table('balances')
    op.drop_table('transactions')
    op.drop_table('stake_balances')
    op.drop_table('stake_outcome')
    op.drop_table('stake_distributions')
    op.drop_table('users')
    op.drop_table('tinkoff_withdraw_methods')
    op.drop_table('tinkoff_deposit_requests')
    op.drop_table('streamers_commissions')
    op.drop_table('stakes')
    op.drop_table('deals')
    # ### end Alembic commands ###
