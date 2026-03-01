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
# EXTRA METRICS (CAGR + MAX DRAWDOWN)
# -----------------------------
start_date = df["Date"].iloc[0]
end_date = latest["Date"]
years = (end_date - start_date).days / 365.25

# CAGR based on invested -> current value (simple and stable)
cagr = (current_value / total_invested) ** (1 / years) - 1 if years > 0 else 0

# Max drawdown already computed earlier? If not, compute here safely:
if "Drawdown(%)" in df.columns:
    max_dd = df["Drawdown(%)"].min()
else:
    peak = df["Current Value($)"].cummax()
    df["Drawdown(%)"] = (df["Current Value($)"] / peak - 1) * 100
    max_dd = df["Drawdown(%)"].min()

# -----------------------------
# HEADER
# -----------------------------
st.title("My Investment Journey")
st.markdown(
    "<div style='margin-top:-10px; color:#666;'>Tracking discipline, growth, and long-term wealth building</div>",
    unsafe_allow_html=True
)
st.write("")

# -----------------------------
# METRIC CARDS
# -----------------------------
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Total Invested", f"${total_invested:,.0f}")
col2.metric("Current Value", f"${current_value:,.0f}")
col3.metric("Total Gain", f"${gain_value:,.0f}")
col4.metric("Total Gain (%)", f"{gain_pct:.2f}%")
col5.metric("CAGR (annualised)", f"{cagr*100:.2f}%")
col6.metric("Max Drawdown", f"{max_dd:.2f}%")

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

# -----------------------------
# PROHECTION CHART
# -----------------------------
st.divider()
st.subheader("🔮 Future Projection")

left, right = st.columns([1, 2])

with left:
    st.caption("Adjust assumptions (simple monthly compounding model).")
    monthly_contrib = st.slider("Monthly contribution ($)", 0, 2000, 300, 50)
    years_forward = st.slider("Project forward (years)", 1, 30, 10, 1)

    # Default to CAGR, but let you override
    default_rate = float(cagr) if "cagr" in globals() else 0.07
    exp_return = st.slider(
        "Expected annual return (%)",
        0.0, 20.0, round(default_rate * 100, 2), 0.25
    ) / 100.0

    st.caption("Tip: Keep this conservative (e.g., 5–8%).")

with right:
    # Simple projection using monthly compounding
    start_val = float(current_value)
    r_m = (1 + exp_return) ** (1/12) - 1  # monthly rate
    months = years_forward * 12

    proj_dates = pd.date_range(
        start=latest["Date"] + pd.offsets.MonthBegin(1),
        periods=months,
        freq="MS"
    )

    values = []
    v = start_val
    for _ in range(months):
        v = v * (1 + r_m) + monthly_contrib
        values.append(v)

    proj_df = pd.DataFrame({
        "Date": proj_dates,
        "Projected Value($)": values
    })

    proj_df["Projected Value($)"] = proj_df["Projected Value($)"].round(2)

    # Merge historical + projected for a single chart
    hist_df = df[["Date", "Current Value($)"]].rename(columns={"Current Value($)": "Value($)"})
    fut_df = proj_df.rename(columns={"Projected Value($)": "Value($)"})
    combined = pd.concat([hist_df, fut_df], ignore_index=True)

def project_path(start_val, monthly_contrib, annual_return, months):
    r_m = (1 + annual_return) ** (1/12) - 1
    v = float(start_val)
    out = []
    for _ in range(months):
        v = v * (1 + r_m) + monthly_contrib
        out.append(v)
    return out

# Define scenarios around your selected expected return
bear = max(0.0, exp_return - 0.03)   # -3%
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

# Band (Bear to Bull)
figp.add_trace(go.Scatter(
    x=proj_df["Date"],
    y=proj_df["Bull($)"],
    mode="lines",
    name="Bull",
    line=dict(color="#2E7DFF"),
    hovertemplate="$%{y:,.2f}<extra>Bull</extra>"
))
figp.add_trace(go.Scatter(
    x=proj_df["Date"],
    y=proj_df["Bear($)"],
    mode="lines",
    name="Bear",
    line=dict(color="#2E7DFF"),
    fill="tonexty",
    hovertemplate="$%{y:,.2f}<extra>Bear</extra>"
))

# Base line
figp.add_trace(go.Scatter(
    x=proj_df["Date"],
    y=proj_df["Base($)"],
    mode="lines",
    name="Base",
    line=dict(color="#111111"),
    hovertemplate="$%{y:,.2f}<extra>Base</extra>"
))

# Historical line
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

st.caption("Note: This projection is a simple model (constant contribution + constant return). It does not account for fees, inflation, or changing market regimes.")

# Small table for key milestones
milestones_years = [1, 3, 5, 10, 15, 20, 25, 30]
milestones_years = [y for y in milestones_years if y <= years_forward]

if milestones_years:
    rows = []
    for y in milestones_years:
        idx = y * 12 - 1
        rows.append({
            "Year": y,
            "Projected Value($)": proj_df["Projected Value($)"].iloc[idx]
        })
    mile_df = pd.DataFrame(rows)
    mile_df["Projected Value($)"] = mile_df["Projected Value($)"].map(lambda x: f"${x:,.0f}")

    st.markdown("### Milestones")
    st.dataframe(mile_df, hide_index=True, width="stretch")
