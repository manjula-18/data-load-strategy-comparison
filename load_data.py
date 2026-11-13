
import sqlite3
from data_generator import generate_customers, generate_orders


def load_source_data(num_customers=10, num_orders=20):

    conn = sqlite3.connect("comparison.db")
    cursor = conn.cursor()

    try:
        customers = generate_customers(num_customers)
        orders = generate_orders(num_orders, num_customers)

        # Update customer records
        cursor.executemany(
            """
            INSERT OR REPLACE INTO customers
            (customer_id, customer_name)
            VALUES (?, ?)
            """,
            [
                (c["customer_id"], c["customer_name"])
                for c in customers
            ]
        )

        # Start with a clean source orders table
        cursor.execute("DELETE FROM source_orders")

        # Insert fresh orders
        cursor.executemany(
            """
            INSERT INTO source_orders
            (order_id, customer_id, order_date, amount,
             status, updated_at, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    o["order_id"],
                    o["customer_id"],
                    o["order_date"],
                    o["amount"],
                    o["status"],
                    o["updated_at"],
                    o["source_file"]
                )
                for o in orders
            ]
        )

        conn.commit()

        print(f"Loaded {len(customers)} customers")
        print(f"Loaded {len(orders)} orders")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    load_source_data()
