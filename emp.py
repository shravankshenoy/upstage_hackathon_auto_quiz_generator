import pandas as pd
import numpy as np

# Generate 7-digit employee IDs
employee_ids = np.random.randint(1000000, 10000000, size=10)

# Generate random task1_rate and task2_rate between 5 and 100
task1_rates = np.random.randint(5, 101, size=10)
task2_rates = np.random.randint(5, 101, size=10)

# Create DataFrame
df = pd.DataFrame({
    'employee_id': employee_ids,
    'task1_rate': task1_rates,
    'task2_rate': task2_rates
})

# Compute percentiles for task1_rate
percentiles_task1 = np.percentile(df['task1_rate'], [0, 25, 50, 75, 100])

# Compute percentiles for task2_rate
percentiles_task2 = np.percentile(df['task2_rate'], [0, 25, 50, 75, 100])

# Function to categorize task1_rate
def categorize_task1_rate(rate):
    if rate <= percentiles_task1[1]:
        return 1
    elif rate <= percentiles_task1[2]:
        return 2
    elif rate <= percentiles_task1[3]:
        return 3
    else:
        return 4

# Function to categorize task2_rate
def categorize_task2_rate(rate):
    if rate <= percentiles_task2[1]:
        return 1
    elif rate <= percentiles_task2[2]:
        return 2
    elif rate <= percentiles_task2[3]:
        return 3
    else:
        return 4

# Create new columns for task1_rate and task2_rate categories
df['task1_rate_category'] = df['task1_rate'].apply(categorize_task1_rate)
df['task2_rate_category'] = df['task2_rate'].apply(categorize_task2_rate)

# Calculate the overall category as the average of task1_rate_category and task2_rate_category
df['overall_category'] = df[['task1_rate_category', 'task2_rate_category']].mean(axis=1)

print(df)
