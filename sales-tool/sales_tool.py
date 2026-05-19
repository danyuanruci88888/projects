#!/usr/bin/env python3
"""
Sales Tool - A simple CLI for managing and analyzing sales records.
"""

import argparse
import csv
import os
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("output")

CSV_FILE = Path("sales_data.csv")
CSV_HEADERS = ["date", "product", "amount"]


def ensure_csv_exists():
    """Create the CSV file with headers if it doesn't exist."""
    if not CSV_FILE.exists():
        with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def parse_date(date_str):
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return None


def cmd_add(args):
    """Add a new sales record."""
    ensure_csv_exists()

    date_obj = parse_date(args.date)
    if date_obj is None:
        print(f"Error: Invalid date format '{args.date}'. Expected YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)

    try:
        amount = float(args.amount)
    except ValueError:
        print(f"Error: Invalid amount '{args.amount}'. Expected a number.", file=sys.stderr)
        sys.exit(1)

    with CSV_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([args.date, args.product, f"{amount:.2f}"])

    print(f"Added: {args.date} | {args.product} | {amount:.2f}")


def cmd_list(args):
    """List all sales records."""
    if not CSV_FILE.exists():
        print("No sales data found. Use 'add' to create records.")
        return

    with CSV_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)

    if not records:
        print("No sales records found.")
        return

    print(f"{'Date':<12} {'Product':<20} {'Amount':>10}")
    print("-" * 46)
    for row in records:
        print(f"{row['date']:<12} {row['product']:<20} {float(row['amount']):>10.2f}")


def cmd_analyze(args):
    """Analyze sales data and print a formatted Markdown report."""
    if not CSV_FILE.exists():
        print("## Sales Analysis Report\n")
        print("_No sales data found. CSV file does not exist._")
        return

    with CSV_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("## Sales Analysis Report\n")
        print("_No sales records found. The data file is empty._")
        return

    # Aggregate by month
    monthly = {}
    invalid_dates = []
    invalid_amounts = []

    for idx, row in enumerate(rows, start=2):  # start=2 because row 1 is header
        raw_date = row.get("date", "").strip()
        raw_amount = row.get("amount", "").strip()
        date_obj = parse_date(raw_date)

        if date_obj is None:
            invalid_dates.append((idx, raw_date))
            continue

        try:
            amount = float(raw_amount)
        except ValueError:
            invalid_amounts.append((idx, raw_amount))
            continue

        month_key = date_obj.strftime("%Y-%m")
        monthly[month_key] = monthly.get(month_key, 0.0) + amount

    print("## Sales Analysis Report\n")

    if invalid_dates or invalid_amounts:
        if invalid_dates:
            print("**Warning:** The following rows have invalid date formats (skipped):")
            for row_num, val in invalid_dates:
                print(f"- Row {row_num}: '{val}'")
            print()
        if invalid_amounts:
            print("**Warning:** The following rows have invalid amount values (skipped):")
            for row_num, val in invalid_amounts:
                print(f"- Row {row_num}: '{val}'")
            print()

    if not monthly:
        print("_No valid data to analyze after filtering errors._")
        return

    # Sort by month
    sorted_months = OrderedDict(sorted(monthly.items()))
    month_keys = list(sorted_months.keys())
    month_values = list(sorted_months.values())

    # Compute MoM growth and YoY growth
    report_rows = []
    growth_rates = [None]  # First month has no previous month
    yoy_rates = []  # Parallel list matching month_keys
    for i, (month, total) in enumerate(zip(month_keys, month_values)):
        if i == 0:
            growth_str = "N/A"
        else:
            prev = month_values[i - 1]
            if prev == 0:
                growth_str = "N/A (prev 0)"
            else:
                growth = ((total - prev) / prev) * 100
                growth_str = f"{growth:+.2f}%"
                growth_rates.append(growth)

        year, mon = map(int, month.split("-"))
        last_year_month = f"{year-1:04d}-{mon:02d}"
        if last_year_month in monthly:
            yoy = ((total - monthly[last_year_month]) / monthly[last_year_month]) * 100
            yoy_str = f"{yoy:+.2f}%"
            yoy_rates.append(yoy)
        else:
            yoy_str = "N/A"
            yoy_rates.append(None)

        report_rows.append((month, total, growth_str, yoy_str))

    # Statistical insights
    total_sales = sum(month_values)
    avg_sales = total_sales / len(month_values)
    max_month = max(sorted_months, key=sorted_months.get)
    min_month = min(sorted_months, key=sorted_months.get)
    max_amount = sorted_months[max_month]
    min_amount = sorted_months[min_month]

    # Growth / decline streaks
    max_up_streak = 0
    max_down_streak = 0
    current_up = 0
    current_down = 0
    current_trend = "flat"
    current_streak = 0

    for g in growth_rates[1:]:
        if g is None:
            continue
        if g > 0:
            current_up += 1
            current_down = 0
            max_up_streak = max(max_up_streak, current_up)
            if current_trend == "up":
                current_streak += 1
            else:
                current_trend = "up"
                current_streak = 1
        elif g < 0:
            current_down += 1
            current_up = 0
            max_down_streak = max(max_down_streak, current_down)
            if current_trend == "down":
                current_streak += 1
            else:
                current_trend = "down"
                current_streak = 1
        else:
            current_up = 0
            current_down = 0
            current_trend = "flat"
            current_streak = 0

    # Best / worst growth month
    valid_growth = [(month_keys[i + 1], growth_rates[i + 1]) for i in range(len(growth_rates) - 1)]
    best_growth = max(valid_growth, key=lambda x: x[1]) if valid_growth else (None, 0)
    worst_growth = min(valid_growth, key=lambda x: x[1]) if valid_growth else (None, 0)

    # Best / worst YoY growth
    valid_yoy = [(month_keys[i], yoy_rates[i]) for i in range(len(yoy_rates)) if yoy_rates[i] is not None]
    best_yoy = max(valid_yoy, key=lambda x: x[1]) if valid_yoy else (None, 0)
    worst_yoy = min(valid_yoy, key=lambda x: x[1]) if valid_yoy else (None, 0)

    # Calculate column widths for alignment
    month_width = max(len("Month"), max(len(m) for m in month_keys))
    amount_width = max(len("Sales Amount"), max(len(f"{v:,.2f}") for v in month_values))
    growth_width = max(len("MoM Growth"), max(len(g) for _, _, g, _ in report_rows))
    yoy_width = max(len("YoY Growth"), max(len(y) for _, _, _, y in report_rows))

    month_sep = ':' + '-' * (month_width - 2) + ':' if month_width >= 2 else '-'
    amount_sep = '-' * (amount_width - 1) + ':' if amount_width >= 1 else '-'
    growth_sep = '-' * (growth_width - 1) + ':' if growth_width >= 1 else '-'
    yoy_sep = '-' * (yoy_width - 1) + ':' if yoy_width >= 1 else '-'
    sep = f"| {month_sep} | {amount_sep} | {growth_sep} | {yoy_sep} |"
    header = f"| {'Month':^{month_width}} | {'Sales Amount':>{amount_width}} | {'MoM Growth':>{growth_width}} | {'YoY Growth':>{yoy_width}} |"

    # Output Markdown report
    print(header)
    print(sep)
    for month, total, growth, yoy in report_rows:
        print(f"| {month:^{month_width}} | {total:>{amount_width},.2f} | {growth:>{growth_width}} | {yoy:>{yoy_width}} |")

    print()
    print("### Key Insights\n")
    print(f"- **Total Sales:**     {total_sales:,.2f}")
    print(f"- **Average Monthly:** {avg_sales:,.2f}")
    print(f"- **Highest Month:**   {max_month} ({max_amount:,.2f})")
    print(f"- **Lowest Month:**    {min_month} ({min_amount:,.2f})")
    print()
    if valid_growth:
        print(f"- **Best MoM Growth:**  {best_growth[0]} ({best_growth[1]:+.2f}%)")
        print(f"- **Worst MoM Growth:** {worst_growth[0]} ({worst_growth[1]:+.2f}%)")
    if valid_yoy:
        print(f"- **Best YoY Growth:**  {best_yoy[0]} ({best_yoy[1]:+.2f}%)")
        print(f"- **Worst YoY Growth:** {worst_yoy[0]} ({worst_yoy[1]:+.2f}%)")
    print()
    if max_up_streak > 0:
        print(f"- **Longest Growth Streak:**   {max_up_streak} month(s)")
    if max_down_streak > 0:
        print(f"- **Longest Decline Streak:**  {max_down_streak} month(s)")
    if current_streak > 1 and current_trend in ("up", "down"):
        trend_word = "growing" if current_trend == "up" else "declining"
        print(f"- **Current Trend:**           {current_streak} consecutive month(s) of {trend_word}")

    if args.chart:
        generate_charts(month_keys, month_values, growth_rates, valid_growth, valid_yoy)


def _setup_chinese_font():
    """Configure matplotlib to use a Chinese font on Windows."""
    import matplotlib
    import matplotlib.pyplot as plt

    font_candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans SC",
        "STHeiti",
        "WenQuanYi Micro Hei",
    ]
    available = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
    chosen = None
    for font in font_candidates:
        if font in available:
            chosen = font
            break

    if chosen:
        plt.rcParams["font.sans-serif"] = [chosen, "sans-serif"]
    else:
        plt.rcParams["font.sans-serif"] = ["sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


def generate_charts(month_keys, month_values, growth_rates, valid_growth, valid_yoy):
    """Generate bar chart and line chart, saved to output/."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n**Warning:** matplotlib is not installed. Charts skipped.")
        print("To install: pip install matplotlib")
        return

    _setup_chinese_font()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Monthly sales bar chart
    fig, ax = plt.subplots(figsize=(max(6, len(month_keys) * 0.8), 5))
    bars = ax.bar(month_keys, month_values, color="#4A90D9", edgecolor="white")
    ax.set_xlabel("月份", fontsize=12)
    ax.set_ylabel("销售额", fontsize=12)
    ax.set_title("月度销售额汇总", fontsize=14, fontweight="bold")
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle="--", alpha=0.6)

    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:,.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    chart1_path = OUTPUT_DIR / "monthly_sales.png"
    plt.savefig(chart1_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nChart saved: {chart1_path}")

    # 2. Growth trend line chart (MoM + YoY)
    if len(valid_growth) < 1 and not valid_yoy:
        print("Not enough data to generate growth trend chart.")
        return

    growth_months = [m for m, _ in valid_growth]
    growth_values = [v for _, v in valid_growth]

    fig, ax = plt.subplots(figsize=(max(6, len(month_keys) * 0.8), 5))

    # MoM line
    if valid_growth:
        ax.plot(
            growth_months, growth_values,
            marker="o", color="#E94B3C", linewidth=2, markersize=6,
            label="环比 (MoM)",
        )

    # YoY line
    if valid_yoy:
        yoy_months = [m for m, _ in valid_yoy]
        yoy_values_list = [v for _, v in valid_yoy]
        ax.plot(
            yoy_months, yoy_values_list,
            marker="s", color="#2E7D32", linewidth=2, markersize=6,
            label="同比 (YoY)",
        )

    ax.set_xlabel("月份", fontsize=12)
    ax.set_ylabel("增长率 (%)", fontsize=12)
    ax.set_title("月度增长趋势 (MoM & YoY)", fontsize=14, fontweight="bold")
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle="--", alpha=0.6)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.legend(loc="best")

    # Adjust Y axis to fit all values
    all_values = []
    if growth_values:
        all_values.extend(growth_values)
    if valid_yoy:
        all_values.extend([v for _, v in valid_yoy])

    if all_values:
        y_range = max(all_values) - min(all_values)
        y_pad = y_range * 0.15 if y_range != 0 else 2
        ax.set_ylim(min(all_values) - y_pad, max(all_values) + y_pad)

    # Annotate highest and lowest points for MoM
    if growth_values:
        max_idx = growth_values.index(max(growth_values))
        min_idx = growth_values.index(min(growth_values))

        for idx, label, color in ((max_idx, "最高", "#2E7D32"), (min_idx, "最低", "#C62828")):
            offset = 25 if idx == max_idx else -30
            ax.annotate(
                f"{label}: {growth_values[idx]:+.2f}%",
                xy=(growth_months[idx], growth_values[idx]),
                xytext=(0, offset),
                textcoords="offset points",
                ha="center",
                va="bottom" if idx == max_idx else "top",
                fontsize=9,
                color=color,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=color, alpha=0.9),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
            )

    chart2_path = OUTPUT_DIR / "growth_trend.png"
    plt.savefig(chart2_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Chart saved: {chart2_path}")


def main():
    parser = argparse.ArgumentParser(
        prog="sales_tool",
        description="A simple CLI tool for managing and analyzing sales records.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # add
    add_parser = subparsers.add_parser("add", help="Add a sales record")
    add_parser.add_argument("date", help="Sale date (YYYY-MM-DD)")
    add_parser.add_argument("product", help="Product name")
    add_parser.add_argument("amount", help="Sale amount")
    add_parser.set_defaults(func=cmd_add)

    # list
    list_parser = subparsers.add_parser("list", help="List all sales records")
    list_parser.set_defaults(func=cmd_list)

    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze sales data")
    analyze_parser.add_argument("--chart", action="store_true", help="Generate chart images in output/")
    analyze_parser.set_defaults(func=cmd_analyze)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
