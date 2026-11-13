
import sqlite3


def generate_report():

    conn = sqlite3.connect("comparison.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT strategy, status, input_count,
               output_count, duration_ms
        FROM pipeline_runs
        ORDER BY rowid DESC
        LIMIT 3
    """)

    results = cursor.fetchall()

    conn.close()

    if not results:
        print("No pipeline records found.")
        return

    print("\n========== PERFORMANCE REPORT ==========\n")

    for row in results:
        strategy, status, input_count, output_count, duration = row

        print("Strategy:", strategy)
        print("Status:", status)
        print("Input records:", input_count)
        print("Output records:", output_count)
        print("Execution time:", round(duration, 3), "ms")
        print("----------------------------------------")

    successful = [
        row for row in results if row[1] == "SUCCESS"
    ]

    if successful:
        fastest = min(successful, key=lambda row: row[4])

        print("\nFASTEST STRATEGY:", fastest[0])
        print("TIME:", round(fastest[4], 3), "ms")

    print("\n========================================")


if __name__ == "__main__":
    generate_report()
