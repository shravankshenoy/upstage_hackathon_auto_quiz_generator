import yaml
import argparse

def generate_sql(yaml_file):
    """Generate an SQL query with a CASE WHEN statement for multiple categories from a YAML config file."""
    with open(yaml_file, "r") as file:
        data = yaml.safe_load(file)

    sql_queries = []

    # Iterate over each category in interest_by_date
    for category, entries in data['interest_by_date'].items():
        sql_query = f"SELECT date_column,\n  CASE"
        
        # Generate CASE WHEN statements for each entry
        for entry in entries:
            sql_query += f"\n    WHEN date_column BETWEEN '{entry['start_date']}' AND '{entry['end_date']}' THEN {entry['interest']}"
        
        # Add default case and end CASE statement
        sql_query += f"\n    ELSE 0\n  END AS interest_value\nFROM {category}_table;"  # Assuming a table per category

        sql_queries.append(sql_query)

    return "\n\n".join(sql_queries)  # Combine SQL queries for different categories

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate SQL from YAML file")
    parser.add_argument("--config", type=str, required=True, help="Path to the YAML file")

    # Parse arguments
    args = parser.parse_args()

    # Generate and print SQL
    sql_query = generate_sql(args.config)
    print(sql_query)
