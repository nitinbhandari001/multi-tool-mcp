#!/usr/bin/env python3
"""Setup database tables and seed with demo data."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    from dotenv import load_dotenv
    load_dotenv()

    import asyncpg
    from faker import Faker

    db_url = os.getenv("DATABASE_URL", "postgresql://dev:devpassword@localhost:5432/portfolio")
    fake = Faker()
    Faker.seed(42)

    print(f"Connecting to {db_url}...")
    conn = await asyncpg.connect(db_url)

    try:
        # Drop and recreate tables
        print("Creating tables...")
        await conn.execute("""
            DROP TABLE IF EXISTS demo_analytics CASCADE;
            DROP TABLE IF EXISTS demo_logs CASCADE;
            DROP TABLE IF EXISTS demo_orders CASCADE;
            DROP TABLE IF EXISTS demo_products CASCADE;
            DROP TABLE IF EXISTS demo_users CASCADE;
        """)

        await conn.execute("""
            CREATE TABLE demo_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(200) UNIQUE NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE demo_products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                category VARCHAR(100),
                stock INTEGER DEFAULT 0
            );

            CREATE TABLE demo_orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES demo_users(id),
                product_id INTEGER REFERENCES demo_products(id),
                quantity INTEGER DEFAULT 1,
                total DECIMAL(10,2),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE demo_logs (
                id SERIAL PRIMARY KEY,
                level VARCHAR(20) DEFAULT 'INFO',
                message TEXT,
                source VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE demo_analytics (
                id SERIAL PRIMARY KEY,
                event VARCHAR(100) NOT NULL,
                user_id INTEGER,
                properties JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Seed demo_users (10 rows)
        print("Seeding users...")
        for _ in range(10):
            await conn.execute(
                "INSERT INTO demo_users (name, email, role) VALUES ($1, $2, $3)",
                fake.name(), fake.unique.email(), fake.random_element(["user", "admin", "analyst"])
            )

        # Seed demo_products (10 rows)
        print("Seeding products...")
        categories = ["Electronics", "Software", "Services", "Hardware"]
        for _ in range(10):
            await conn.execute(
                "INSERT INTO demo_products (name, price, category, stock) VALUES ($1, $2, $3, $4)",
                fake.catch_phrase(), round(fake.pyfloat(min_value=9.99, max_value=999.99), 2),
                fake.random_element(categories), fake.random_int(0, 100)
            )

        # Seed demo_orders (15 rows)
        print("Seeding orders...")
        statuses = ["pending", "completed", "cancelled", "processing"]
        for _ in range(15):
            user_id = fake.random_int(1, 10)
            product_id = fake.random_int(1, 10)
            quantity = fake.random_int(1, 5)
            total = round(quantity * fake.pyfloat(min_value=9.99, max_value=499.99), 2)
            await conn.execute(
                "INSERT INTO demo_orders (user_id, product_id, quantity, total, status) VALUES ($1, $2, $3, $4, $5)",
                user_id, product_id, quantity, total, fake.random_element(statuses)
            )

        # Seed demo_logs (10 rows)
        print("Seeding logs...")
        levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        sources = ["api", "auth", "database", "scheduler"]
        for _ in range(10):
            await conn.execute(
                "INSERT INTO demo_logs (level, message, source) VALUES ($1, $2, $3)",
                fake.random_element(levels), fake.sentence(), fake.random_element(sources)
            )

        # Seed demo_analytics (10 rows)
        print("Seeding analytics...")
        events = ["page_view", "login", "purchase", "logout", "search"]
        import json
        for _ in range(10):
            await conn.execute(
                "INSERT INTO demo_analytics (event, user_id, properties) VALUES ($1, $2, $3)",
                fake.random_element(events), fake.random_int(1, 10),
                json.dumps({"source": fake.random_element(["web", "mobile", "api"])})
            )

        print("✓ Database setup complete!")
        print("  Tables: demo_users, demo_products, demo_orders, demo_logs, demo_analytics")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
