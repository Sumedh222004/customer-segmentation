import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

st.set_page_config(page_title="Customer Segmentation Dashboard", layout="wide")
st.title("Customer Segmentation & Revenue Intelligence")
st.markdown("**Built by Sumedh Wankhede | IIT Gandhinagar**")
st.markdown("---")

# Load data
conn = sqlite3.connect("customers.db")
rfm = pd.read_sql("SELECT * FROM rfm_segments", conn)
transactions = pd.read_sql("SELECT * FROM transactions", conn)
conn.close()

transactions["trans_date"] = pd.to_datetime(transactions["trans_date"])

colors = {
    "Champions": "#2ecc71", "Loyal": "#3498db",
    "Promising": "#9b59b6", "At Risk": "#e67e22",
    "High Value Churned": "#e74c3c", "Lost": "#95a5a6"
}

# Sidebar
st.sidebar.header("Filters")
segments = st.sidebar.multiselect(
    "Select Segments",
    options=rfm["segment"].unique().tolist(),
    default=rfm["segment"].unique().tolist()
)
filtered = rfm[rfm["segment"].isin(segments)]

# KPIs
st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Customers", f"{len(filtered):,}")
col2.metric("Total Revenue", f"Rs.{filtered['monetary'].sum():,.0f}")
col3.metric("Avg Customer Value", f"Rs.{filtered['monetary'].mean():,.0f}")
col4.metric("Avg Recency (days)", f"{filtered['recency'].mean():.0f}")

st.markdown("---")

# Segment summary table
st.subheader("Segment Summary")
summary = filtered.groupby("segment").agg(
    Customers=("customer_id", "count"),
    Avg_Recency=("recency", "mean"),
    Avg_Frequency=("frequency", "mean"),
    Avg_Monetary=("monetary", "mean"),
    Total_Revenue=("monetary", "sum")
).round(0).sort_values("Total_Revenue", ascending=False)
summary["Revenue_%"] = (summary["Total_Revenue"] / summary["Total_Revenue"].sum() * 100).round(1)
st.dataframe(summary)

st.markdown("---")

# Charts
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Revenue by Segment")
    fig, ax = plt.subplots(figsize=(7, 4))
    seg_colors = [colors.get(s, "#607D8B") for s in summary.index]
    bars = ax.bar(summary.index, summary["Total_Revenue"], color=seg_colors)
    for bar, pct in zip(bars, summary["Revenue_%"]):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 10000,
                f"{pct}%", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylabel("Revenue (Rs.)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    st.pyplot(fig)

with col_b:
    st.subheader("Customer Distribution")
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    seg_colors2 = [colors.get(s, "#607D8B") for s in summary.index]
    ax2.pie(summary["Customers"], labels=summary.index,
            colors=seg_colors2, autopct="%1.1f%%", startangle=90)
    plt.tight_layout()
    st.pyplot(fig2)

st.markdown("---")

# Monthly trend
st.subheader("Monthly Revenue Trend")
transactions["month"] = transactions["trans_date"].dt.to_period("M").astype(str)
monthly = transactions.groupby("month")["tran_amount"].sum().reset_index()
fig3, ax3 = plt.subplots(figsize=(14, 4))
ax3.plot(monthly["month"], monthly["tran_amount"],
         color="#2ecc71", linewidth=2, marker="o", markersize=3)
ax3.set_ylabel("Revenue (Rs.)")
ax3.set_xlabel("Month")
plt.xticks(rotation=45, ha="right", fontsize=7)
plt.tight_layout()
st.pyplot(fig3)

st.markdown("---")

# Winback list
st.subheader("High Value Churned — Winback Priority List")
st.markdown("These customers had high spend but haven't purchased recently. Highest ROI for re-engagement.")
churned = rfm[rfm["segment"] == "High Value Churned"].copy()
churned["Winback Priority"] = churned["recency"].apply(
    lambda x: "Priority 1" if x <= 200 else "Priority 2" if x <= 400 else "Low"
)
st.dataframe(
    churned[["customer_id", "recency", "frequency", "monetary", "Winback Priority"]]
    .sort_values("monetary", ascending=False)
    .reset_index(drop=True)
)