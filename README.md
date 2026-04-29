
# README.md

## Setup & Execution

### 1. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 2. Run Data Pipeline
```bash
python src/data/tidy_postsecondary_tables.py
```
Generates tidy dataset: `outputs/tables/nces_postsecondary_tidy.csv`

### 3. Execute Analysis Notebook
```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/notebook_file_name.ipynb
```
Produces figures in `outputs/figures/`

## Project Structure

- **`src/data/`**: Data ingestion and parsing
- **`src/analysis/`**: Analysis helpers
- **`notebooks/`**: Jupyter notebooks for exploration and analysis
- **`data/sources/`**: Raw Excel workbooks (immutable)
- **`outputs/`**: Generated tidy data, review artifacts, and figures
- **`reports/`**: Methodology and notes
