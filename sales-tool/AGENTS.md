<!-- From: D:\xuexi\AI\jilu\projects\sales-tool\AGENTS.md -->
# AGENTS.md — sales-tool Project Agent Guide

## Project Overview

A lightweight CLI tool for managing and analyzing sales records, written in Python.

- **Project root:** `D:\xuexi\AI\jilu\projects\sales-tool`
- **Technology stack:** Python 3 (standard library only — `argparse`, `csv`, `datetime`, `pathlib`)
- **Data file:** `sales_data.csv` (auto-created on first `add`)

## File Structure

```
sales-tool/
├── sales_tool.py      # Main CLI entry point
├── sales_data.csv     # Sales data (CSV: date,product,amount)
└── AGENTS.md          # This file
```

## Commands

```bash
# Add a sales record
python sales_tool.py add <date> <product> <amount>
# Example: python sales_tool.py add 2024-01-15 "Product A" 1200.50

# List all sales records
python sales_tool.py list

# Analyze sales data (monthly summary, MoM & YoY growth, highest/lowest)
python sales_tool.py analyze

# Analyze + generate charts (requires matplotlib)
python sales_tool.py analyze --chart
```

## Build and Test Commands

No external build system is required. To run:

```bash
python sales_tool.py <command>
```

### Optional: Chart Generation

The `--chart` option requires **matplotlib**:

```bash
pip install matplotlib
```

Charts are saved to the `output/` directory:
- `output/monthly_sales.png` — Monthly sales bar chart
- `output/growth_trend.png` — Month-over-month & year-over-year growth trend line chart

Chinese fonts are auto-detected on Windows (Microsoft YaHei / SimHei / Noto Sans SC).

## Code Style Guidelines

- Use standard library only (no third-party dependencies).
- CSV I/O uses `csv.DictReader` / `csv.writer` with UTF-8 encoding.
- Dates are formatted as `YYYY-MM-DD`; months are aggregated as `YYYY-MM`.
- Money values are stored and displayed with two decimal places.
- Error messages are printed to `sys.stderr` and exit with code `1`.
- The CLI uses `argparse` with subparsers (`add`, `list`, `analyze`).

## Testing Instructions

Manual test checklist:
1. `python sales_tool.py add 2024-01-15 "Test" 100`
2. `python sales_tool.py list`
3. `python sales_tool.py analyze`
4. Delete `sales_data.csv` and run `analyze` to verify missing-file handling.
5. Create a CSV with only headers and run `analyze` to verify empty-data handling.
6. Append malformed rows (bad date / bad amount) and run `analyze` to verify error skipping.

## Security Considerations

- The tool operates only on the local `sales_data.csv` file in the working directory.
- No network access, authentication, or sensitive data handling.
