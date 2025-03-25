import yaml
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description="Generate SQL from YAML file")
parser.add_argument("--config", type=str, required=True, help="Path to the YAML file")

# Parse arguments
args = parser.parse_args()

# Read YAML file
with open(args.config, "r") as file:
    data = yaml.safe_load(file)

# Start SQL query
sql_query = "SELECT date_column,\n  CASE"

# Loop through YAML data to generate CASE WHEN statements
for entry in data['interest_by_date']:
    sql_query += f"\n    WHEN date_column BETWEEN '{entry['start_date']}' AND '{entry['end_date']}' THEN {entry['interest']}"

# Add default case and end CASE statement
sql_query += "\n    ELSE 0\n  END AS interest_value\nFROM table_name;"

# Print the SQL query
print(sql_query)
