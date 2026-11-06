from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

DATABASE_URL = settings.DATABASE_URL.strip()

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_database_schema(target_engine=None):
    """Ensure all tables and columns are created and compatible."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)

    # SQLite migration guard for existing orders table columns
    if str(eng.url).startswith("sqlite"):
        with eng.connect() as conn:
            try:
                res = conn.execute(text("PRAGMA table_info(orders)"))
                cols = {r[1] for r in res.fetchall()}
                new_cols = [
                    ("payment_status", "VARCHAR(50) DEFAULT 'PENDING'"),
                    ("subtotal_amount", "NUMERIC(12, 2) DEFAULT 0.00"),
                    ("discount_amount", "NUMERIC(12, 2) DEFAULT 0.00"),
                    ("tax_amount", "NUMERIC(12, 2) DEFAULT 0.00"),
                    ("shipping_amount", "NUMERIC(12, 2) DEFAULT 0.00"),
                    ("coupon_code", "VARCHAR(50)"),
                    ("shipping_method_code", "VARCHAR(50)"),
                    ("notes", "TEXT"),
                    ("updated_at", "DATETIME")
                ]
                for col_name, col_type in new_cols:
                    if col_name not in cols:
                        conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}"))

                # Migration guard for order_items columns
                res_items = conn.execute(text("PRAGMA table_info(order_items)"))
                item_cols = {r[1] for r in res_items.fetchall()}
                new_item_cols = [
                    ("description_snapshot", "TEXT"),
                    ("variant_attributes_snapshot", "JSON"),
                    ("fulfillment_status", "VARCHAR(50) DEFAULT 'PENDING'")
                ]
                for c_name, c_type in new_item_cols:
                    if c_name not in item_cols:
                        conn.execute(text(f"ALTER TABLE order_items ADD COLUMN {c_name} {c_type}"))

                conn.commit()
            except Exception:
                pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
