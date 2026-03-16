# Sales Analysis Project

A Python-based sales analytics demo that generates synthetic sales data, loads it into SQLite, runs SQL-based KPI queries, and creates visual dashboards.

## Files

- `sales_analysis.py` - Main script that generates data, performs analysis, and produces visual output.
- `requirements.txt` - Required Python libraries.
- `README.md` - Project overview and run instructions.

## Prerequisites

- Python 3.9+
- Git (optional, for version control)

## Setup

1. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

## Run

```bash
python sales_analysis.py
```

The script will generate synthetic sales data, run SQL analytics, and save the outputs to `outputs/`.

### Output images

After running, the script saves these charts as PNG files:

- `outputs/fig1_executive_dashboard.png`
- `outputs/fig2_segment_channel.png`
- `outputs/fig3_profitability.png`
- `outputs/fig4_pie_charts.png`

You can open them directly in your file explorer or any image viewer.

## GitHub Push

```bash
git init
git add .
git commit -m "Initial commit: sales analytics script"
git remote add origin https://github.com/<your-user>/<your-repo>.git
git branch -M main
git push -u origin main
```

Replace `<your-user>` and `<your-repo>` with your GitHub details.
