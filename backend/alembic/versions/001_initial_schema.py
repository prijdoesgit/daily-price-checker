"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "medications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("canonical_name", sa.String(200), nullable=False),
        sa.Column("generic_name", sa.String(200)),
        sa.Column("manufacturer", sa.String(200)),
        sa.Column("category", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("drug_type", sa.String(50), nullable=False, server_default="brand"),
        sa.Column("aliases", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_medications_name", "medications", ["name"])
    op.create_index("ix_medications_canonical_name", "medications", ["canonical_name"])

    op.create_table(
        "medication_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("medication_id", sa.Integer(), sa.ForeignKey("medications.id"), nullable=False),
        sa.Column("strength", sa.String(50), nullable=False),
        sa.Column("strength_numeric", sa.Float()),
        sa.Column("unit", sa.String(20), nullable=False, server_default="mg"),
        sa.Column("form", sa.String(50), nullable=False, server_default="injection"),
        sa.Column("pack_size", sa.String(100)),
        sa.Column("mrp", sa.Float()),
        sa.Column("canonical_strength", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("medication_id", "strength", "form", name="uq_variant"),
    )
    op.create_index("ix_medication_variants_medication_id", "medication_variants", ["medication_id"])
    op.create_index("ix_variant_canonical", "medication_variants", ["canonical_strength"])

    op.create_table(
        "platforms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("scraper_class", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_scraped_at", sa.DateTime()),
        sa.Column("scrape_success_rate", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("contact_name", sa.String(200)),
        sa.Column("phone", sa.String(50)),
        sa.Column("email", sa.String(200)),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(100)),
        sa.Column("address", sa.Text()),
        sa.Column("vendor_type", sa.String(50), nullable=False, server_default="distributor"),
        sa.Column("medications_handled", sa.Text()),
        sa.Column("delivery_coverage", sa.Text()),
        sa.Column("referred_by", sa.String(500)),
        sa.Column("notes", sa.Text()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_newly_discovered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("discovery_source", sa.String(200)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("name", "city", "phone", name="uq_vendor"),
    )

    op.create_table(
        "scraping_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("platform_id", sa.Integer(), sa.ForeignKey("platforms.id")),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("triggered_by", sa.String(50), nullable=False, server_default="scheduler"),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_log", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "price_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("medication_variants.id"), nullable=False),
        sa.Column("platform_id", sa.Integer(), sa.ForeignKey("platforms.id")),
        sa.Column("price", sa.Float()),
        sa.Column("mrp", sa.Float()),
        sa.Column("discount_pct", sa.Float()),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_serviceable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("city", sa.String(100)),
        sa.Column("product_url", sa.Text()),
        sa.Column("product_name_raw", sa.String(500)),
        sa.Column("pack_info", sa.String(200)),
        sa.Column("scraped_at", sa.DateTime(), nullable=False),
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("scraping_job_id", sa.Integer(), sa.ForeignKey("scraping_jobs.id")),
    )
    op.create_index("ix_price_records_variant_id", "price_records", ["variant_id"])
    op.create_index("ix_price_records_platform_id", "price_records", ["platform_id"])
    op.create_index("ix_price_variant_platform_latest", "price_records", ["variant_id", "platform_id", "is_latest"])

    op.create_table(
        "vendor_discoveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_name", sa.String(300), nullable=False),
        sa.Column("raw_city", sa.String(100)),
        sa.Column("raw_phone", sa.String(100)),
        sa.Column("raw_url", sa.Text()),
        sa.Column("source_url", sa.Text()),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("medications_found", sa.Text()),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id")),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("vendor_discoveries")
    op.drop_table("price_records")
    op.drop_table("scraping_jobs")
    op.drop_table("vendors")
    op.drop_table("platforms")
    op.drop_table("medication_variants")
    op.drop_table("medications")
