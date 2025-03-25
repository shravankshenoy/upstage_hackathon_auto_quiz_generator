import yaml

yaml_data = """
interest_by_date:
  - start_date: '2022-01-01'
    end_date: '2022-01-31'
    interest: 0.1
  - start_date: '2022-02-01'
    end_date: '2022-02-28'
    interest: 0.2
"""

# Load YAML data
data = yaml.safe_load(yaml_data)

# Start SQL query
sql_query = "SELECT date_column,\n  CASE"

# Loop through YAML data to generate CASE WHEN statements
for entry in data['interest_by_date']:
    sql_query += f"\n    WHEN date_column BETWEEN '{entry['start_date']}' AND '{entry['end_date']}' THEN {entry['interest']}"

# Add default case and end CASE statement
sql_query += "\n    ELSE 0\n  END AS interest_value\nFROM table_name;"

# Print the SQL query
print(sql_query)
