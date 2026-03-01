import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="My Investment Journey",
    page_icon="📈",
    layout="wide"
)

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1ijmWpuQGk-Qys4wn46JE8aqzh8eKdzrTRjYCFM6tgWQ/export?format=csv"


# -----------------------------
# DATA LOADING
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)

    # Clean column names (safety)
    df.columns = df.columns.str.strip()

    # Parse date (MM-YYYY)
    df["Date"] = pd.to_datetime(df["Date"], format="%m-%Y")

    # Remove $ , % and convert to numeric
    money_cols = [
        "Monthly Contribution",
        "Total Invested($)",
        "Current Value($)",
        "Gain/Loss($)"
    ]
    for col in money_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Gain/Loss(%)"] = (
        df["Gain/Loss(%)"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .astype(float)
    )

    df = df.sort_values("Date")
    return df


df = load_data()

def compute_drawdown(series: pd.Series) -> pd.Series:
    peak = series.cummax()
    drawdown = (series / peak) - 1.0
    return drawdown * 100  # percent

# -----------------------------
# SNAPSHOT (LATEST ROW)
# -----------------------------
latest = df[df["Is Latest"] == "Yes"].iloc[0]

total_invested = latest["Total Invested($)"]
current_value = latest["Current Value($)"]
gain_value = latest["Gain/Loss($)"]
gain_pct = latest["Gain/Loss(%)"]

# -----------------------------
# HEADER
# -----------------------------
st.title("My Investment Journey")
st.caption("Tracking discipline, growth, and long-term wealth building")

# -----------------------------
# METRIC CARDS
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Invested", f"${total_invested:,.0f}")
col2.metric("Current Value", f"${current_value:,.0f}")
col3.metric("Total Gain", f"${gain_value:,.0f}")
col4.metric("Total Gain (%)", f"{gain_pct:.2f}%")

st.divider()

# -----------------------------
# PORTFOLIO GROWTH CHART
# -----------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Total Invested($)"],
    name="Total Invested",
    mode="lines",
    line=dict(color="#A0A0A0"),
    fill="tozeroy"
))

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Current Value($)"],
    name="Current Value",
    mode="lines",
    line=dict(color="#2E7DFF"),
    fill="tonexty"
))

fig.update_layout(
    title="Portfolio Growth Over Time",
    xaxis_title="Date",
    yaxis_title="Value ($)",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(orientation="h", y=1.15)
)

st.plotly_chart(fig, use_container_width="stretch")

# -----------------------------
# GAIN / LOSS % CHART
# -----------------------------
fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Gain/Loss(%)"],
    mode="lines",
    name="Gain / Loss (%)",
    line=dict(color="#00A676")
))

fig2.update_layout(
    title="Gain / Loss Percentage Over Time",
    xaxis_title="Date",
    yaxis_title="Gain / Loss (%)",
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig2, use_container_width="stretch")

# -----------------------------
# DRAWDOWN CHART
# -----------------------------
df["Drawdown(%)"] = compute_drawdown(df["Current Value($)"])
max_dd = df["Drawdown(%)"].min()
max_dd_date = df.loc[df["Drawdown(%)"].idxmin(), "Date"]

fig3 = go.Figure()

fig3.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Drawdown(%)"],
    mode="lines",
    name="Drawdown (%)",
    line=dict(color="#D64545")  # red
))

fig3.update_layout(
    title=f"Drawdown Over Time (Max Drawdown: {max_dd:.2f}% on {max_dd_date:%b %Y})",
    xaxis_title="Date",
    yaxis_title="Drawdown (%)",
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig3, use_container_width="stretch")
