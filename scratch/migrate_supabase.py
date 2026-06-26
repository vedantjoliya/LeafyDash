import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, make_transient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import Base
from backend.models import (
    User, UserAnswers, ActiveModule, Location, Product, Employee, 
    OperationalExpense, Sale, SaleItem, MarketingCampaign, 
    CampaignCustomerTracking, ContactMessage, AdminMessage, Review
)

sqlite_url = "sqlite:///./database.db"
postgres_url = "postgresql://postgres:Joliya283283joker@db.sgushsxnhnipqewomuby.supabase.co:5432/postgres"

print("Connecting to local SQLite database...")
sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

print("Connecting to Supabase PostgreSQL database...")
postgres_engine = create_engine(postgres_url)

SQLiteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

sqlite_session = SQLiteSession()
postgres_session = PostgresSession()

# Order of tables to migrate (topological order to satisfy foreign key constraints)
models_to_migrate = [
    User,
    UserAnswers,
    ActiveModule,
    Location,
    Product,
    Employee,
    OperationalExpense,
    Sale,
    SaleItem,
    MarketingCampaign,
    CampaignCustomerTracking,
    ContactMessage,
    AdminMessage,
    Review
]

inserted_ids = {model: set() for model in models_to_migrate}

try:
    # 1. Drop existing tables to start clean
    print("\n1. Dropping existing tables on Supabase...")
    for model in reversed(models_to_migrate):
        print(f"  Dropping table '{model.__tablename__}' if exists...")
        model.__table__.drop(bind=postgres_engine, checkfirst=True)
        
    print("\n2. Creating fresh tables on Supabase...")
    Base.metadata.create_all(bind=postgres_engine)
    print("  Schema created successfully.")

    # 2. Copy records
    print("\n3. Migrating records from SQLite to Supabase...")
    for model in models_to_migrate:
        name = model.__name__
        table_name = model.__tablename__
        print(f"  Migrating '{table_name}' ({name})...")
        
        sqlite_objs = sqlite_session.query(model).all()
        initial_count = len(sqlite_objs)
        
        # Apply foreign key reference filtering using only successfully inserted parent IDs
        if model == UserAnswers or model == ActiveModule or model == Employee or model == OperationalExpense or model == ContactMessage or model == AdminMessage:
            sqlite_objs = [o for o in sqlite_objs if o.user_id in inserted_ids[User]]
        elif model == Location:
            sqlite_objs = [o for o in sqlite_objs if o.user_id in inserted_ids[User]]
        elif model == Product:
            sqlite_objs = [o for o in sqlite_objs if o.user_id in inserted_ids[User] and (o.location_id is None or o.location_id in inserted_ids[Location])]
        elif model == Sale:
            sqlite_objs = [o for o in sqlite_objs if o.user_id in inserted_ids[User] and (o.location_id is None or o.location_id in inserted_ids[Location])]
        elif model == SaleItem:
            sqlite_objs = [o for o in sqlite_objs if o.sale_id in inserted_ids[Sale] and (o.product_id is None or o.product_id in inserted_ids[Product])]
        elif model == MarketingCampaign:
            sqlite_objs = [o for o in sqlite_objs if o.user_id in inserted_ids[User]]
        elif model == CampaignCustomerTracking:
            sqlite_objs = [o for o in sqlite_objs if o.campaign_id in inserted_ids[MarketingCampaign] and (o.sale_id is None or o.sale_id in inserted_ids[Sale])]
        elif model == Review:
            sqlite_objs = [o for o in sqlite_objs if o.user_id in inserted_ids[User] and (o.location_id is None or o.location_id in inserted_ids[Location])]

        print(f"    SQLite original count: {initial_count}, valid count to migrate: {len(sqlite_objs)}")
        
        for obj in sqlite_objs:
            # Track ID as inserted
            inserted_ids[model].add(obj.id)
            
            # Expunge object from SQLite session so it can be added to PostgreSQL
            sqlite_session.expunge(obj)
            make_transient(obj)
            postgres_session.add(obj)
            
        postgres_session.commit()
        print(f"    Successfully migrated {len(sqlite_objs)} records.")
        
    # 3. Reset primary key serial sequences
    print("\n4. Resetting PostgreSQL serial sequences...")
    for model in models_to_migrate:
        table_name = model.__tablename__
        # Query max ID
        res = postgres_session.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}"))
        max_id = res.scalar()
        
        if max_id > 0:
            # Reset the sequence to next_id
            seq_query = text(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), {max_id}, true)")
            print(f"  Sequence for '{table_name}': Current max ID = {max_id}, setting sequence to {max_id}")
            postgres_session.execute(seq_query)
        else:
            print(f"  Sequence for '{table_name}': Empty table, sequence remains at default (1).")
        
    postgres_session.commit()
    print("  All sequences reset successfully.")
    print("\nDATABASE MIGRATION COMPLETED SUCCESSFULLY!")

except Exception as e:
    postgres_session.rollback()
    print(f"\nERROR OCCURRED DURING MIGRATION: {e}")
    raise
finally:
    sqlite_session.close()
    postgres_session.close()
