

import random
from datetime import datetime, timedelta


def generate_customers(num_customers):
    customers = []

    for i in range(1, num_customers + 1):
        customers.append({
            "customer_id": i,
            "customer_name": f"Customer_{i}"
        })

    return customers


def generate_orders(num_orders, num_customers):
    orders = []

    for i in range(1, num_orders + 1):
        orders.append({
            "order_id": i,
            "customer_id": random.randint(1, num_customers),
            "order_date": (
                datetime.now() - timedelta(days=random.randint(1, 365))
            ).strftime("%Y-%m-%d"),
            "amount": round(random.uniform(100, 10000), 2),
            "status": random.choice(
                ["Pending", "Completed", "Cancelled"]
            ),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_file": "generated_data"
        })

    return orders


if __name__ == "__main__":
    customers = generate_customers(1000)
    orders = generate_orders(10000, 1000)

    print("Customers generated:", len(customers))
    print("Orders generated:", len(orders))
