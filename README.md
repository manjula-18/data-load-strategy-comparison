
# Data Loading Strategy Comparison

## 1. Project Overview

This project compares three data loading strategies using Python and SQLite. It demonstrates data validation, duplicate handling, incremental processing, partition replacement, and performance tracking through an interactive dashboard.

## 2. Loading Strategies

### Full Refresh
Deletes existing target records and loads all valid source records again.

### Incremental Merge
Uses a watermark and a 24-hour lookback window to identify new and updated records. Unchanged records are skipped.

### Partition Replacement
Replaces only the affected monthly partitions in the target table.

## 3. Features

- Source data generation
- Data validation and duplicate removal
- Rejected record tracking
- Incremental loading with watermarks
- Late-arriving record handling
- SQLite transaction management
- Pipeline execution history
- Performance comparison
- Interactive Streamlit dashboard

## 4. Technologies

- Python
- SQLite
- SQL
- Pandas
- Streamlit

## 5. Project Structure

- `app.py` - Streamlit dashboard
- `database.py` - Database creation and connection
- `data_generator.py` - Generates sample customers and orders
- `load_data.py` - Loads generated source data
- `loading_strategies.py` - Implements the three loading strategies
- `performance_report.py` - Displays execution performance
- `README.md` - Project documentation

## 6. Installation and Setup

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd data_load_comparison
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

### Step 3: Activate the environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```bash
pip install pandas streamlit
```

### Step 5: Initialize the database

```bash
python -c "from database import initialize_db; initialize_db()"
```

### Step 6: Generate and load source data

```bash
python load_data.py
```

### Step 7: Run the loading strategies

```bash
python loading_strategies.py
```

### Step 8: Generate the performance report

```bash
python performance_report.py
```

### Step 9: Launch the dashboard

```bash
python -m streamlit run app.py
```

## 7. Database Tables

- `customers`
- `source_orders`
- `target_full_refresh`
- `target_incremental_merge`
- `target_partition_replace`
- `rejected_records`
- `pipeline_runs`
- `pipeline_watermarks`

## 8. Performance Evaluation

The project tracks input records, output records, rejected records, execution time, and pipeline status.

Execution times depend on the number of records processed. Comparisons should consider differences in workload.

## 9. Future Improvements

- Automated testing
- Equal-workload performance benchmarking
- Additional data quality checks
- Support for larger datasets
