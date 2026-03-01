import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="My Investment Journey",
    page_icon="📈",
    layout="wide"
)

# Google Sheets CSV export link (no API, no billing)
SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1ijmWpuQGk-Qys4wn46JE8aqzh8eKdzrTRjYCFM6tgWQ/export?format=csv"
)

# ============================================================
# DATA LOADING + CLEANING
# ============================================================
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(SHEET_CSV_URL)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Parse date (MM-YYYY)
    df["Date"] = pd.to_datetime(df["Date"], format="%m-%Y")

    # Money columns: strip $, commas -> numeric
    money_cols = [
        "Monthly Contribution",
        "Total Invested($)",
        "Current Value($)",
        "Gain/Loss($)",
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

    # Percent column: strip % -> float
    df["Gain/Loss(%)"] = (
        df["Gain/Loss(%)"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .astype(float)
    )

    df = df.sort_values("Date")
    return df


def compute_drawdown(value_series: pd.Series) -> pd.Series:
    """
    Drawdown (%) relative to running peak.
    0% at highs, negative during drawdowns.
    """
    peak = value_series.cummax()
    drawdown = (value_series / peak) - 1.0
    return drawdown * 100


def project_path(start_val: float, monthly_contrib: float, annual_return: float, months: int) -> list[float]:
    """
    Simple projection with constant monthly contribution + constant annual return.
    Compounded monthly.
    """
    r_m = (1 + annual_return) ** (1 / 12) - 1
    v = float(start_val)
    out = []
    for _ in range(months):
        v = v * (1 + r_m) + monthly_contrib
        out.append(v)
    return out


# ============================================================
# LOAD DATA
# ============================================================
df = load_data()

# ============================================================
# LATEST SNAPSHOT ROW
# ============================================================
latest = df[df["Is Latest"] == "Yes"].iloc[0]

total_invested = float(latest["Total Invested($)"])
current_value = float(latest["Current Value($)"])
gain_value = float(latest["Gain/Loss($)"])
gain_pct = float(latest["Gain/Loss(%)"])

# ============================================================
# EXTRA METRICS: CAGR + DRAWDOWN
# ============================================================
start_date = df["Date"].iloc[0]
end_date = latest["Date"]
years = (end_date - start_date).days / 365.25

# Simple CAGR: invested -> current value (time-normalized)
cagr = (current_value / total_invested) ** (1 / years) - 1 if years > 0 else 0.0

# Drawdown (historical)
df["Drawdown(%)"] = compute_drawdown(df["Current Value($)"])
max_dd = float(df["Drawdown(%)"].min())
max_dd_date = df.loc[df["Drawdown(%)"].idxmin(), "Date"]

# ============================================================
# HEADER
# ============================================================
st.title("My Investment Journey")
st.markdown(
    "<div style='margin-top:-10px; color:#666;'>Tracking discipline, growth, and long-term wealth building</div>",
    unsafe_allow_html=True
)
st.write("")

# ============================================================
# METRIC CARDS
# ============================================================
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Invested", f"${total_invested:,.0f}")
col2.metric("Current Value", f"${current_value:,.0f}")
col3.metric("Total Gain", f"${gain_value:,.0f}")
col4.metric("Total Gain (%)", f"{gain_pct:.2f}%")
col5.metric("CAGR (annualised)", f"{cagr * 100:.2f}%")
col6.metric("Max Drawdown", f"{max_dd:.2f}%")

st.divider()

# ============================================================
# CHART 1: PORTFOLIO GROWTH
# ============================================================
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Total Invested($)"],
    name="Total Invested",
    mode="lines",
    line=dict(color="#A0A0A0"),
    fill="tozeroy",
    hovertemplate="$%{y:,.2f}<extra>Total Invested</extra>"
))

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Current Value($)"],
    name="Current Value",
    mode="lines",
    line=dict(color="#2E7DFF"),
    fill="tonexty",
    hovertemplate="$%{y:,.2f}<extra>Current Value</extra>"
))

fig.update_layout(
    title="Portfolio Growth Over Time",
    xaxis_title="Date",
    yaxis_title="Value ($)",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(orientation="h", y=1.15),
    yaxis_tickformat=",.2f"
)

st.plotly_chart(fig, width="stretch")

# ============================================================
# CHART 2: GAIN / LOSS %
# ============================================================
fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Gain/Loss(%)"],
    mode="lines",
    name="Gain / Loss (%)",
    line=dict(color="#00A676"),
    hovertemplate="%{y:.2f}%<extra>Gain/Loss</extra>"
))

fig2.update_layout(
    title="Gain / Loss Percentage Over Time",
    xaxis_title="Date",
    yaxis_title="Gain / Loss (%)",
    hovermode="x unified",
    template="plotly_white",
    yaxis_tickformat=".2f"
)

st.plotly_chart(fig2, width="stretch")

# ============================================================
# CHART 3: DRAWDOWN
# ============================================================
fig3 = go.Figure()

fig3.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Drawdown(%)"],
    mode="lines",
    name="Drawdown (%)",
    line=dict(color="#D64545"),
    hovertemplate="%{y:.2f}%<extra>Drawdown</extra>"
))

fig3.update_layout(
    title=f"Drawdown Over Time (Max Drawdown: {max_dd:.2f}% on {max_dd_date:%b %Y})",
    xaxis_title="Date",
    yaxis_title="Drawdown (%)",
    hovermode="x unified",
    template="plotly_white",
    yaxis_tickformat=".2f"
)

st.plotly_chart(fig3, width="stretch")

# ============================================================
# FUTURE PROJECTION (Bear / Base / Bull)
# ============================================================
st.divider()
st.subheader("🔮 Future Projection")

left, right = st.columns([1, 2])

with left:
    st.caption("Adjust assumptions (simple monthly compounding model).")
    monthly_contrib = st.slider("Monthly contribution ($)", 0, 2000, 300, 50)
    years_forward = st.slider("Project forward (years)", 1, 30, 10, 1)

    # Default expected return = your CAGR, but user can override
    default_rate = float(cagr) if pd.notna(cagr) else 0.07
    exp_return = st.slider(
        "Expected annual return (%)",
        0.0, 20.0, round(default_rate * 100, 2), 0.25
    ) / 100.0

    st.caption("Tip: Keep this conservative (e.g., 5–8%).")

with right:
    months = years_forward * 12

    proj_dates = pd.date_range(
        start=latest["Date"] + pd.offsets.MonthBegin(1),
        periods=months,
        freq="MS"
    )

    # Scenarios around expected return
    bear = max(0.0, exp_return - 0.03)    # -3%
    base = exp_return
    bull = min(0.20, exp_return + 0.03)  # +3% (cap at 20%)

    bear_vals = project_path(current_value, monthly_contrib, bear, months)
    base_vals = project_path(current_value, monthly_contrib, base, months)
    bull_vals = project_path(current_value, monthly_contrib, bull, months)

    proj_df = pd.DataFrame({
        "Date": proj_dates,
        "Bear($)": pd.Series(bear_vals).round(2),
        "Base($)": pd.Series(base_vals).round(2),
        "Bull($)": pd.Series(bull_vals).round(2),
    })

    figp = go.Figure()

    # Bull line (top of band)
    figp.add_trace(go.Scatter(
        x=proj_df["Date"],
        y=proj_df["Bull($)"],
        mode="lines",
        name="Bull",
        line=dict(color="#2E7DFF"),
        hovertemplate="$%{y:,.2f}<extra>Bull</extra>"
    ))

    # Bear line (bottom of band) + fill up to bull
    figp.add_trace(go.Scatter(
        x=proj_df["Date"],
        y=proj_df["Bear($)"],
        mode="lines",
        name="Bear",
        line=dict(color="#2E7DFF"),
        fill="tonexty",
        hovertemplate="$%{y:,.2f}<extra>Bear</extra>"
    ))

    # Base line (center)
    figp.add_trace(go.Scatter(
        x=proj_df["Date"],
        y=proj_df["Base($)"],
        mode="lines",
        name="Base",
        line=dict(color="#111111"),
        hovertemplate="$%{y:,.2f}<extra>Base</extra>"
    ))

    # Historical actuals
    figp.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Current Value($)"],
        mode="lines",
        name="Actual",
        line=dict(color="#A0A0A0"),
        hovertemplate="$%{y:,.2f}<extra>Actual</extra>"
    ))

    # Latest marker
    figp.add_trace(go.Scatter(
        x=[latest["Date"]],
        y=[current_value],
        mode="markers",
        name="Latest",
        marker=dict(size=10, color="#111111"),
        hovertemplate="$%{y:,.2f}<extra>Latest</extra>"
    ))

    figp.update_layout(
        title="Projected Portfolio Value (Bear / Base / Bull)",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", y=1.12),
        yaxis_tickformat=",.2f"
    )

    st.plotly_chart(figp, width="stretch")

st.caption(
    "Note: Projection is a simple model (constant contribution + constant return). "
    "It does not account for fees, taxes, inflation, or changing market conditions."
)

# ============================================================
# MILESTONES TABLE (Base scenario)
# ============================================================
milestones_years = [1, 3, 5, 10, 15, 20, 25, 30]
milestones_years = [y for y in milestones_years if y <= years_forward]

if milestones_years:
    rows = []
    for y in milestones_years:
        idx = y * 12 - 1
        rows.append({
            "Year": y,
            "Projected Value (Base)": float(proj_df["Base($)"].iloc[idx])
        })

    mile_df = pd.DataFrame(rows)
    mile_df["Projected Value (Base)"] = mile_df["Projected Value (Base)"].map(lambda x: f"${x:,.2f}")

    st.markdown("### Milestones (Base case)")
    st.dataframe(mile_df, hide_index=True, width="stretch")
