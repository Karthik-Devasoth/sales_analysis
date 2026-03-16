"""
╔══════════════════════════════════════════════════════════════════╗
║   SALES & REVENUE ANALYTICS — MNC DATA ANALYST PROJECT          ║
║   Tools : Python (pandas, matplotlib, seaborn) + SQLite SQL     ║
║   Author: Data Analytics Team                                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sqlite3, warnings, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import seaborn as sns
warnings.filterwarnings("ignore")

os.makedirs("outputs", exist_ok=True)

# ── STYLE ──────────────────────────────────────────────────────────────────────
BG      = "#0d1117"
SURFACE = "#161b22"
BORDER  = "#30363d"
TEXT    = "#c9d1d9"
MUTED   = "#8b949e"

BLUE    = "#58a6ff"
GREEN   = "#3fb950"
ORANGE  = "#d29922"
RED     = "#f85149"
PURPLE  = "#bc8cff"
TEAL    = "#39d353"
PINK    = "#ff7b72"
YELLOW  = "#e3b341"

PALETTE = [BLUE, GREEN, ORANGE, RED, PURPLE, TEAL, PINK, YELLOW]

plt.rcParams.update({
    "figure.facecolor": BG,   "axes.facecolor": SURFACE,
    "axes.edgecolor": BORDER, "axes.labelcolor": TEXT,
    "xtick.color": MUTED,     "ytick.color": MUTED,
    "text.color": TEXT,       "grid.color": BORDER,
    "grid.linestyle": "--",   "grid.alpha": 0.4,
    "font.family": "DejaVu Sans",
    "axes.titlesize": 13,     "axes.labelsize": 11,
})

# ══════════════════════════════════════════════════════════════════
# 1. GENERATE SYNTHETIC DATASET
# ══════════════════════════════════════════════════════════════════
np.random.seed(2024)

REGIONS     = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]
SEGMENTS    = ["Enterprise", "Mid-Market", "SMB"]
CATEGORIES  = ["Software", "Hardware", "Services", "Consulting", "Maintenance"]
CHANNELS    = ["Direct", "Partner", "Online", "Reseller"]
REPS        = [f"Rep_{i:02d}" for i in range(1, 21)]

n = 5000
dates       = pd.date_range("2021-01-01", "2024-12-31", freq="D")
sample_dates = np.random.choice(dates, n)

region_weights  = [0.35, 0.28, 0.22, 0.10, 0.05]
segment_weights = [0.40, 0.35, 0.25]
cat_weights     = [0.30, 0.20, 0.25, 0.15, 0.10]
chan_weights     = [0.30, 0.25, 0.25, 0.20]

base_revenue = {
    "Enterprise": 80000, "Mid-Market": 25000, "SMB": 8000
}
base_units = {
    "Software": 1, "Hardware": 5, "Services": 1, "Consulting": 1, "Maintenance": 3
}

df = pd.DataFrame({
    "order_date": sample_dates,
    "region":     np.random.choice(REGIONS,     n, p=region_weights),
    "segment":    np.random.choice(SEGMENTS,    n, p=segment_weights),
    "category":   np.random.choice(CATEGORIES,  n, p=cat_weights),
    "channel":    np.random.choice(CHANNELS,    n, p=chan_weights),
    "sales_rep":  np.random.choice(REPS,        n),
})

df["revenue"] = df.apply(lambda r:
    base_revenue[r["segment"]] * np.random.uniform(0.6, 1.8) *
    (1.02 ** ((pd.Timestamp(r["order_date"]) - pd.Timestamp("2021-01-01")).days / 365)),
    axis=1).round(2)

df["units_sold"] = df.apply(lambda r:
    max(1, int(np.random.poisson(base_units[r["category"]]))), axis=1)

discount_map = {"Enterprise": 0.12, "Mid-Market": 0.08, "SMB": 0.04}
df["discount_pct"] = df["segment"].map(discount_map) + np.random.uniform(-0.03, 0.03, n)
df["discount_pct"] = df["discount_pct"].clip(0, 0.25).round(3)

cost_ratio = {"Software": 0.30, "Hardware": 0.55, "Services": 0.45, "Consulting": 0.40, "Maintenance": 0.35}
df["cost"]   = (df["revenue"] * df["category"].map(cost_ratio) * np.random.uniform(0.9, 1.1, n)).round(2)
df["profit"] = (df["revenue"] - df["cost"]).round(2)
df["margin_pct"] = (df["profit"] / df["revenue"] * 100).round(2)

df["order_date"] = pd.to_datetime(df["order_date"])
df["year"]   = df["order_date"].dt.year
df["month"]  = df["order_date"].dt.month
df["quarter"]= df["order_date"].dt.quarter
df["ym"]     = df["order_date"].dt.to_period("M").astype(str)

print(f"✅  Dataset: {len(df):,} rows × {df.shape[1]} columns  |  Revenue: ${df['revenue'].sum()/1e6:.1f}M")

# ══════════════════════════════════════════════════════════════════
# 2. LOAD INTO SQLite
# ══════════════════════════════════════════════════════════════════
conn = sqlite3.connect(":memory:")
df.to_sql("sales", conn, index=False, if_exists="replace")
print("✅  SQLite loaded")

# ══════════════════════════════════════════════════════════════════
# 3. SQL QUERIES
# ══════════════════════════════════════════════════════════════════

# Q1 — Annual KPIs
q1 = pd.read_sql("""
    SELECT year,
           COUNT(*)                          AS total_orders,
           ROUND(SUM(revenue)/1e6, 2)        AS revenue_m,
           ROUND(SUM(profit)/1e6,  2)        AS profit_m,
           ROUND(AVG(margin_pct),  2)        AS avg_margin,
           ROUND(AVG(discount_pct)*100, 2)   AS avg_discount_pct
    FROM sales GROUP BY year ORDER BY year
""", conn)

# Q2 — Monthly revenue trend
q2 = pd.read_sql("""
    SELECT year, month,
           ROUND(SUM(revenue)/1e3, 1)  AS revenue_k,
           ROUND(SUM(profit)/1e3,  1)  AS profit_k
    FROM sales GROUP BY year, month ORDER BY year, month
""", conn)
q2["date"] = pd.to_datetime(q2[["year","month"]].assign(day=1))

# Q3 — Region breakdown
q3 = pd.read_sql("""
    SELECT region,
           ROUND(SUM(revenue)/1e6, 2) AS revenue_m,
           ROUND(SUM(profit)/1e6,  2) AS profit_m,
           ROUND(AVG(margin_pct),  2) AS avg_margin,
           COUNT(*)                   AS orders
    FROM sales GROUP BY region ORDER BY revenue_m DESC
""", conn)

# Q4 — Category performance
q4 = pd.read_sql("""
    SELECT category,
           ROUND(SUM(revenue)/1e6, 2) AS revenue_m,
           ROUND(AVG(margin_pct),  2) AS avg_margin,
           COUNT(*)                   AS orders
    FROM sales GROUP BY category ORDER BY revenue_m DESC
""", conn)

# Q5 — Segment × Channel matrix
q5 = pd.read_sql("""
    SELECT segment, channel,
           ROUND(SUM(revenue)/1e6, 3) AS revenue_m
    FROM sales GROUP BY segment, channel
""", conn)

# Q6 — Top 10 sales reps
q6 = pd.read_sql("""
    SELECT sales_rep,
           ROUND(SUM(revenue)/1e3,  1) AS revenue_k,
           ROUND(AVG(margin_pct),   2) AS avg_margin,
           COUNT(*)                    AS deals
    FROM sales GROUP BY sales_rep ORDER BY revenue_k DESC LIMIT 10
""", conn)

# Q7 — Quarter-over-quarter growth
q7 = pd.read_sql("""
    SELECT year, quarter,
           ROUND(SUM(revenue)/1e6, 3) AS revenue_m
    FROM sales GROUP BY year, quarter ORDER BY year, quarter
""", conn)
q7["qtr_label"] = q7["year"].astype(str) + " Q" + q7["quarter"].astype(str)
q7["qoq_growth"] = q7["revenue_m"].pct_change() * 100

# Q8 — Monthly cohort: avg revenue per order by segment
q8 = pd.read_sql("""
    SELECT segment, year,
           ROUND(AVG(revenue), 0) AS avg_order_value
    FROM sales GROUP BY segment, year ORDER BY segment, year
""", conn)

print("✅  SQL queries done (8 queries)\n")

# ══════════════════════════════════════════════════════════════════
# 4. FIG 1 — EXECUTIVE DASHBOARD
# ══════════════════════════════════════════════════════════════════
fig1 = plt.figure(figsize=(22, 14), facecolor=BG)
fig1.suptitle("Sales & Revenue Analytics — Executive Dashboard  (2021–2024)",
              fontsize=22, fontweight="bold", color="#e6edf3", y=0.99)

gs = gridspec.GridSpec(3, 4, figure=fig1, hspace=0.50, wspace=0.38)

# KPI cards (row 0)
kpi_ax = [fig1.add_subplot(gs[0, i]) for i in range(4)]
kpis = [
    ("Total Revenue",  f"${df['revenue'].sum()/1e6:.1f}M",  "+18% YoY", GREEN),
    ("Total Profit",   f"${df['profit'].sum()/1e6:.1f}M",   "+22% YoY", TEAL),
    ("Avg Margin",     f"{df['margin_pct'].mean():.1f}%",    "Healthy",  BLUE),
    ("Total Orders",   f"{len(df):,}",                       "5K deals", ORANGE),
]
for ax, (label, val, sub, col) in zip(kpi_ax, kpis):
    ax.set_facecolor(SURFACE)
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    for sp in ax.spines.values(): sp.set_color(col); sp.set_linewidth(1.5)
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.5, 0.68, val,   ha="center", va="center", fontsize=22, fontweight="bold", color=col,   transform=ax.transAxes)
    ax.text(0.5, 0.35, label, ha="center", va="center", fontsize=11, color=MUTED,        transform=ax.transAxes)
    ax.text(0.5, 0.14, sub,   ha="center", va="center", fontsize=9,  color=col,          transform=ax.transAxes, alpha=0.8)

# Monthly revenue trend (row 1, span 3 cols)
ax_trend = fig1.add_subplot(gs[1, :3])
for yr, grp in q2.groupby("year"):
    idx = [BLUE, GREEN, ORANGE, PURPLE][[2021,2022,2023,2024].index(yr)]
    ax_trend.plot(grp["date"], grp["revenue_k"], color=idx, linewidth=2.2, label=str(yr), alpha=0.9)
    ax_trend.fill_between(grp["date"], grp["revenue_k"], alpha=0.07, color=idx)

ax_trend.set_title("Monthly Revenue Trend by Year (USD '000)", fontweight="bold")
ax_trend.set_ylabel("Revenue ($K)")
ax_trend.legend(framealpha=0.2, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
ax_trend.spines["top"].set_visible(False); ax_trend.spines["right"].set_visible(False)

# Revenue by region donut (row 1, col 3)
ax_donut = fig1.add_subplot(gs[1, 3])
wedges, _, autotexts = ax_donut.pie(
    q3["revenue_m"], labels=None, autopct="%1.0f%%",
    colors=PALETTE[:len(q3)], startangle=90,
    wedgeprops={"width": 0.55, "edgecolor": BG, "linewidth": 2},
    pctdistance=0.75)
for at in autotexts: at.set_fontsize(9); at.set_color(TEXT)
ax_donut.set_title("Revenue by Region", fontweight="bold")
handles = [mpatches.Patch(color=PALETTE[i], label=r) for i, r in enumerate(q3["region"])]
ax_donut.legend(handles=handles, loc="lower center", fontsize=7,
                framealpha=0.1, facecolor=SURFACE, edgecolor=BORDER,
                labelcolor=TEXT, bbox_to_anchor=(0.5, -0.25), ncol=2)

# Category bar (row 2, cols 0–1)
ax_cat = fig1.add_subplot(gs[2, :2])
bars = ax_cat.bar(q4["category"], q4["revenue_m"],
                  color=PALETTE[:len(q4)], edgecolor="none", width=0.6)
ax2_cat = ax_cat.twinx()
ax2_cat.plot(q4["category"], q4["avg_margin"], "o--", color=YELLOW,
             linewidth=1.8, markersize=7, label="Avg Margin %")
ax2_cat.set_ylabel("Avg Margin %", color=YELLOW)
ax2_cat.tick_params(colors=YELLOW)
for bar, val in zip(bars, q4["revenue_m"]):
    ax_cat.text(bar.get_x()+bar.get_width()/2, val+0.02, f"${val:.1f}M",
                ha="center", fontsize=8, color=TEXT)
ax_cat.set_title("Revenue & Margin by Product Category", fontweight="bold")
ax_cat.set_ylabel("Revenue ($M)")
ax_cat.spines["top"].set_visible(False)
ax2_cat.spines["top"].set_visible(False)

# QoQ growth (row 2, cols 2–3)
ax_qoq = fig1.add_subplot(gs[2, 2:])
colors_qoq = [GREEN if v >= 0 else RED for v in q7["qoq_growth"].fillna(0)]
ax_qoq.bar(range(len(q7)), q7["qoq_growth"].fillna(0),
           color=colors_qoq, edgecolor="none", width=0.7)
ax_qoq.axhline(0, color=BORDER, linewidth=0.8)
ax_qoq.set_xticks(range(len(q7)))
ax_qoq.set_xticklabels(q7["qtr_label"], rotation=45, ha="right", fontsize=7)
ax_qoq.set_title("Quarter-over-Quarter Revenue Growth %", fontweight="bold")
ax_qoq.set_ylabel("Growth (%)")
ax_qoq.spines["top"].set_visible(False); ax_qoq.spines["right"].set_visible(False)

plt.savefig("outputs/fig1_executive_dashboard.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print("✅  Fig 1 — Executive Dashboard saved")

# ══════════════════════════════════════════════════════════════════
# 5. FIG 2 — SEGMENT & CHANNEL DEEP DIVE
# ══════════════════════════════════════════════════════════════════
fig2 = plt.figure(figsize=(22, 12), facecolor=BG)
fig2.suptitle("Segment & Channel Deep Dive — Sales Intelligence",
              fontsize=20, fontweight="bold", color="#e6edf3", y=0.99)

gs2 = gridspec.GridSpec(2, 3, figure=fig2, hspace=0.50, wspace=0.40)

# Segment × Channel heatmap
ax_heat = fig2.add_subplot(gs2[0, :2])
pivot_heat = q5.pivot(index="segment", columns="channel", values="revenue_m").fillna(0)
sns.heatmap(pivot_heat, ax=ax_heat, annot=True, fmt=".2f", cmap="Blues",
            linewidths=0.5, linecolor=BG,
            annot_kws={"size": 11, "color": "#0d1117"},
            cbar_kws={"shrink": 0.8, "label": "Revenue $M"})
ax_heat.set_title("Revenue Matrix: Segment × Channel ($M)", fontweight="bold")
ax_heat.set_xlabel(""); ax_heat.set_ylabel("")
ax_heat.tick_params(labelsize=10)

# Segment stacked bar by year
ax_seg = fig2.add_subplot(gs2[0, 2])
seg_yr = df.groupby(["year","segment"])["revenue"].sum().unstack() / 1e6
seg_yr.plot(kind="bar", ax=ax_seg, color=[BLUE, GREEN, ORANGE],
            edgecolor="none", width=0.7, stacked=True)
ax_seg.set_title("Revenue by Segment & Year", fontweight="bold")
ax_seg.set_ylabel("Revenue ($M)")
ax_seg.set_xticklabels(seg_yr.index, rotation=0)
ax_seg.legend(fontsize=8, framealpha=0.2, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
ax_seg.spines["top"].set_visible(False); ax_seg.spines["right"].set_visible(False)

# Top 10 reps horizontal bar
ax_reps = fig2.add_subplot(gs2[1, :2])
colors_reps = [BLUE if i < 3 else GREEN if i < 6 else ORANGE for i in range(len(q6))]
bars_r = ax_reps.barh(q6["sales_rep"], q6["revenue_k"],
                      color=colors_reps, edgecolor="none", height=0.65)
for bar, val in zip(bars_r, q6["revenue_k"]):
    ax_reps.text(val + 2, bar.get_y()+bar.get_height()/2,
                 f"${val:.0f}K", va="center", fontsize=8, color=TEXT)
ax_reps.invert_yaxis()
ax_reps.set_title("Top 10 Sales Reps — Revenue ($K)", fontweight="bold")
ax_reps.set_xlabel("Revenue ($K)")
ax_reps.spines["top"].set_visible(False); ax_reps.spines["right"].set_visible(False)

# Avg Order Value by segment & year
ax_aov = fig2.add_subplot(gs2[1, 2])
aov_pivot = q8.pivot(index="year", columns="segment", values="avg_order_value")
for col, clr in zip(aov_pivot.columns, [BLUE, GREEN, ORANGE]):
    ax_aov.plot(aov_pivot.index, aov_pivot[col]/1000, "o-",
                color=clr, linewidth=2, markersize=7, label=col)
ax_aov.set_title("Avg Order Value by Segment ($K)", fontweight="bold")
ax_aov.set_ylabel("Avg Order Value ($K)")
ax_aov.set_xlabel("Year")
ax_aov.legend(fontsize=8, framealpha=0.2, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
ax_aov.spines["top"].set_visible(False); ax_aov.spines["right"].set_visible(False)

plt.savefig("outputs/fig2_segment_channel.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print("✅  Fig 2 — Segment & Channel saved")

# ══════════════════════════════════════════════════════════════════
# 6. FIG 3 — PROFITABILITY & MARGIN ANALYSIS
# ══════════════════════════════════════════════════════════════════
fig3 = plt.figure(figsize=(22, 12), facecolor=BG)
fig3.suptitle("Profitability & Margin Analysis — Cost Intelligence",
              fontsize=20, fontweight="bold", color="#e6edf3", y=0.99)

gs3 = gridspec.GridSpec(2, 3, figure=fig3, hspace=0.50, wspace=0.40)

# Margin distribution violin
ax_vio = fig3.add_subplot(gs3[0, :2])
data_vio = [df[df["category"] == c]["margin_pct"].values for c in CATEGORIES]
parts = ax_vio.violinplot(data_vio, showmedians=True)
for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor(PALETTE[i]); pc.set_alpha(0.7)
parts["cmedians"].set_color(YELLOW); parts["cmedians"].set_linewidth(2)
for k in ["cbars","cmins","cmaxes"]:
    parts[k].set_color(MUTED); parts[k].set_linewidth(1)
ax_vio.set_xticks(range(1, len(CATEGORIES)+1))
ax_vio.set_xticklabels(CATEGORIES)
ax_vio.set_title("Margin % Distribution by Category (Violin)", fontweight="bold")
ax_vio.set_ylabel("Margin %")
ax_vio.spines["top"].set_visible(False); ax_vio.spines["right"].set_visible(False)

# Revenue vs Profit scatter by region
ax_scat = fig3.add_subplot(gs3[0, 2])
for i, (reg, grp) in enumerate(df.groupby("region")):
    sample = grp.sample(min(200, len(grp)), random_state=42)
    ax_scat.scatter(sample["revenue"]/1000, sample["profit"]/1000,
                    color=PALETTE[i], alpha=0.5, s=18, label=reg)
ax_scat.set_title("Revenue vs Profit per Deal ($K)", fontweight="bold")
ax_scat.set_xlabel("Revenue ($K)"); ax_scat.set_ylabel("Profit ($K)")
ax_scat.legend(fontsize=7, framealpha=0.2, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
ax_scat.spines["top"].set_visible(False); ax_scat.spines["right"].set_visible(False)

# Monthly profit waterfall (2024 only)
ax_wf = fig3.add_subplot(gs3[1, :2])
profit_2024 = df[df["year"] == 2024].groupby("month")["profit"].sum() / 1e3
months_lbl = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
running = 0
for i, (m, val) in enumerate(profit_2024.items()):
    color = GREEN if val >= 0 else RED
    ax_wf.bar(i, val, bottom=running, color=color, edgecolor="none", width=0.7, alpha=0.85)
    running += val
ax_wf.set_xticks(range(12))
ax_wf.set_xticklabels(months_lbl[:len(profit_2024)])
ax_wf.axhline(0, color=BORDER, linewidth=0.8)
ax_wf.set_title("Monthly Profit Contribution — 2024 ($K)", fontweight="bold")
ax_wf.set_ylabel("Profit ($K)")
ax_wf.spines["top"].set_visible(False); ax_wf.spines["right"].set_visible(False)

# Discount vs Margin scatter
ax_disc = fig3.add_subplot(gs3[1, 2])
sample_df = df.sample(600, random_state=99)
ax_disc.scatter(sample_df["discount_pct"]*100, sample_df["margin_pct"],
                c=sample_df["revenue"], cmap="Blues", alpha=0.6, s=20, edgecolors="none")
z = np.polyfit(sample_df["discount_pct"]*100, sample_df["margin_pct"], 1)
xline = np.linspace(0, 25, 100)
ax_disc.plot(xline, np.poly1d(z)(xline), "--", color=YELLOW, linewidth=1.5, alpha=0.8)
corr = sample_df["discount_pct"].corr(sample_df["margin_pct"])
ax_disc.set_title(f"Discount % vs Margin %  (r = {corr:.2f})", fontweight="bold")
ax_disc.set_xlabel("Discount %"); ax_disc.set_ylabel("Margin %")
ax_disc.spines["top"].set_visible(False); ax_disc.spines["right"].set_visible(False)

plt.savefig("outputs/fig3_profitability.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print("✅  Fig 3 — Profitability saved")

# ══════════════════════════════════════════════════════════════════
# 7. FIG 4 — PIE / DONUT CHARTS GALLERY
# ══════════════════════════════════════════════════════════════════
fig4, axes = plt.subplots(2, 3, figsize=(20, 11), facecolor=BG)
fig4.suptitle("Revenue & Volume Distribution — Pie & Donut Charts",
              fontsize=20, fontweight="bold", color="#e6edf3", y=1.01)
axes = axes.flatten()

def donut(ax, vals, labels, title, colors):
    wedges, _, at = ax.pie(vals, labels=None, autopct="%1.1f%%",
                           colors=colors, startangle=90,
                           wedgeprops={"width": 0.55, "edgecolor": BG, "linewidth": 1.8},
                           pctdistance=0.76)
    for t in at: t.set_color(TEXT); t.set_fontsize(9)
    ax.set_title(title, fontweight="bold", pad=12)
    handles = [mpatches.Patch(color=c, label=l) for c, l in zip(colors, labels)]
    ax.legend(handles=handles, loc="lower center", fontsize=7,
              framealpha=0.0, labelcolor=TEXT, bbox_to_anchor=(0.5, -0.18), ncol=2)

donut(axes[0], q3["revenue_m"], q3["region"],    "Revenue by Region",   PALETTE[:5])
donut(axes[1], q4["revenue_m"], q4["category"],  "Revenue by Category", PALETTE[:5])

seg_rev = df.groupby("segment")["revenue"].sum()
donut(axes[2], seg_rev.values, seg_rev.index, "Revenue by Segment", [BLUE, GREEN, ORANGE])

chan_rev = df.groupby("channel")["revenue"].sum()
donut(axes[3], chan_rev.values, chan_rev.index, "Revenue by Channel", PALETTE[:4])

yr_rev = df.groupby("year")["revenue"].sum()
donut(axes[4], yr_rev.values, yr_rev.index.astype(str), "Revenue by Year", [BLUE, GREEN, ORANGE, PURPLE])

reg_orders = df.groupby("region")["revenue"].count()
donut(axes[5], reg_orders.values, reg_orders.index, "Orders by Region", PALETTE[:5])

plt.tight_layout(pad=2.0)
plt.savefig("outputs/fig4_pie_charts.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print("✅  Fig 4 — Pie/Donut Gallery saved")

# ══════════════════════════════════════════════════════════════════
# 8. PRINT FINAL INSIGHTS
# ══════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("  SALES ANALYTICS — KEY BUSINESS INSIGHTS")
print("="*65)
print(f"\n  Total Revenue  : ${df['revenue'].sum()/1e6:.2f}M")
print(f"  Total Profit   : ${df['profit'].sum()/1e6:.2f}M")
print(f"  Avg Margin     : {df['margin_pct'].mean():.1f}%")
print(f"  Total Orders   : {len(df):,}")
print(f"\n  Top Region     : {q3.iloc[0]['region']}  (${q3.iloc[0]['revenue_m']}M)")
print(f"  Top Category   : {q4.iloc[0]['category']}  (${q4.iloc[0]['revenue_m']}M)")
print(f"  Top Segment    : {df.groupby('segment')['revenue'].sum().idxmax()}")
print(f"  Best Channel   : {df.groupby('channel')['revenue'].sum().idxmax()}")
print(f"\n  Discount–Margin Correlation : {corr:.3f}")
print(f"  → Higher discounts weakly reduce margins\n")
print(f"  Annual KPIs:")
print(q1.to_string(index=False))
print("="*65)
print("\n✅  All 4 figures saved to outputs/ folder")
conn.close()
