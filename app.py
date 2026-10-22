"""Michigan County Air Quality Explorer (2025) — Streamlit app."""
from pathlib import Path
import calendar
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Michigan AQI Explorer | 2025", page_icon="🌤️", layout="wide")
BASE = Path(__file__).resolve().parent
DATA = BASE / "michigan_aqi_2025.csv"
CATEGORY_ORDER = ["Good", "Moderate", "Unhealthy for Sensitive Groups", "Unhealthy", "Very Unhealthy", "Hazardous"]
CATEGORY_RANGES = {"Good":"0–50", "Moderate":"51–100", "Unhealthy for Sensitive Groups":"101–150", "Unhealthy":"151–200", "Very Unhealthy":"201–300", "Hazardous":"301–500"}
CATEGORY_COLORS = {"Good":"#26834a", "Moderate":"#e5bb16", "Unhealthy for Sensitive Groups":"#e58a2c", "Unhealthy":"#d34a45", "Very Unhealthy":"#8156a6", "Hazardous":"#7b2738"}

@st.cache_data
def load_data():
    d = pd.read_csv(DATA, parse_dates=["Date"])
    d = d[d["State Name"].eq("Michigan")].copy()
    d["AQI"] = pd.to_numeric(d["AQI"], errors="coerce")
    d = d.dropna(subset=["AQI", "Date", "county Name"])
    d["Month"] = d["Date"].dt.month
    return d

@st.cache_data(show_spinner=False)
def load_boundaries():
    import geopandas as gpd
    url = "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip"
    counties = gpd.read_file(url)
    return counties[counties["STATEFP"].eq("26")][["NAME", "geometry"]].copy()

if not DATA.exists():
    st.error("Missing michigan_aqi_2025.csv. Put it in the same folder as app.py.")
    st.stop()

df = load_data()
all_counties = sorted(df["county Name"].unique())

# Fix map colors to the full, unfiltered 2025 county mean AQI range.
# This stays unchanged when county or month filters are adjusted.
full_year_county_means = df.groupby("county Name")["AQI"].mean()
MAP_COLOR_MIN = float(full_year_county_means.min())
MAP_COLOR_MAX = float(full_year_county_means.max())

st.title("Michigan County Air Quality Explorer (2025)")
st.caption("2025 · U.S. EPA AirData · Daily AQI by County")
st.header("Project Objective")
st.write(
    "To analyze air quality across Michigan counties in 2025 "
    "using the EPA Air Quality Index (AQI) dataset."
)
st.header("Intended Audience")
st.write(
    "Michigan residents, students, and anyone interested "
    "in understanding local air quality conditions."
)
st.header("Main Question")
st.markdown(
    "**How does air quality vary across Michigan counties throughout the year?**"
)

st.header("Dataset After Cleaning")
st.write(
    "The original national dataset contains air quality observations "
    "from counties across the United States. After filtering and cleaning "
    "the data for Michigan, the final dataset contains 8,373 county-day "
    "observations from 27 counties in 2025."
)

with st.sidebar:
    st.header("Explore the data")
    selected = st.multiselect("Counties", all_counties, default=all_counties, help="Choose one or more counties. All charts and summaries update together.")
    month_range = st.select_slider("Months", options=list(range(1,13)), value=(1,12), format_func=lambda x:calendar.month_abbr[x])
    st.caption("Selections apply to the charts and summary metrics. The map uses the same selected counties and months, with other counties shown as unavailable for this view.")
    if st.button("Reset filters"):
        st.session_state.clear()
        st.rerun()

if not selected:
    st.info("Select at least one county in the sidebar.")
    st.stop()

filtered = df[df["county Name"].isin(selected) & df["Month"].between(*month_range)].copy()
if filtered.empty:
    st.warning("No observations match these filters.")
    st.stop()

# Reporting-day denominator is based on the selected 2025 calendar interval.
start = pd.Timestamp(2025, month_range[0], 1)
end = pd.Timestamp(2025, month_range[1], calendar.monthrange(2025,month_range[1])[1])
possible_days = (end-start).days + 1

county = (filtered.groupby("county Name")
          .agg(Mean_AQI=("AQI", "mean"), Reported_Days=("Date", "nunique"))
          .reset_index().rename(columns={"county Name":"County"}))
county["Coverage (%)"] = county["Reported_Days"] / possible_days * 100
county = county.sort_values("Mean_AQI", ascending=False)

st.subheader("Overview")
a,b,c,d = st.columns(4)
a.metric("Mean reported AQI", f"{filtered['AQI'].mean():.1f}")
b.metric("County-day observations", f"{len(filtered):,}")
c.metric("Counties selected", f"{filtered['county Name'].nunique()} / 83")
d.metric("Median AQI", f"{filtered['AQI'].median():.0f}")
st.caption("Each record represents one reported county-day, not one unique statewide day. These are observation-weighted summaries for the current selection.")

st.subheader("1 · AQI distribution and categories")
left,right = st.columns(2)
with left:
    fig = px.histogram(filtered, x="AQI", nbins=30, labels={"AQI":"Daily AQI"}, title="Distribution of reported AQI")
    fig.update_traces(marker_color="#4f83a7")
    fig.update_layout(yaxis_title="Reported county-days", bargap=0.04)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Median AQI: {filtered['AQI'].median():.0f}; 90th percentile: {filtered['AQI'].quantile(.9):.0f}; maximum: {filtered['AQI'].max():.0f}. Higher AQI observations are less frequent in the full 2025 dataset.")
with right:
    cat = filtered["Category"].value_counts().reindex(CATEGORY_ORDER, fill_value=0).rename_axis("Category").reset_index(name="County-days")
    fig = go.Figure()
    for category in CATEGORY_ORDER:
        count = int(cat.loc[cat["Category"].eq(category), "County-days"].iloc[0])
        aqi_range = CATEGORY_RANGES[category]
        fig.add_trace(go.Bar(
            x=[category], y=[count],
            name=f"{category}: {aqi_range}",
            marker_color=CATEGORY_COLORS[category],
            hovertemplate=(f"Category: {category}<br>AQI range: {aqi_range}"
                           "<br>Reported county-days: %{y}<extra></extra>")
        ))
    fig.update_layout(
        title="EPA AQI category distribution",
        xaxis_title="Category", yaxis_title="County-days",
        xaxis_tickangle=-25,
        showlegend=True,
        legend=dict(title="EPA AQI ranges", x=0.99, y=0.99,
                    xanchor="right", yanchor="top",
                    bgcolor="rgba(255,255,255,0.90)",
                    bordercolor="lightgray", borderwidth=1,
                    font=dict(size=10)),
        height=530,
        margin=dict(l=20, r=10, t=55, b=110),
        bargap=0.35
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("AQI categories are supplied in the EPA dataset. Ranges follow EPA definitions; counts include zero-observation categories.")
    with st.expander("Category counts"):
        cat["AQI range"] = cat["Category"].map(CATEGORY_RANGES)
        st.dataframe(cat[["Category", "AQI range", "County-days"]], hide_index=True, use_container_width=True)

st.subheader("2 · Compare counties")
fig = px.bar(county.sort_values("Mean_AQI"), x="Mean_AQI", y="County", orientation="h", title="Mean daily AQI by reporting county", labels={"Mean_AQI":"Mean reported AQI"})
fig.update_traces(marker_color="#4f83a7")
fig.add_vline(x=50, line_dash="dash", line_color="#c13b3b", annotation_text="AQI 50")
fig.update_layout(height=max(450, len(county)*25+120))
st.plotly_chart(fig, use_container_width=True)
st.caption("AQI 50 is the upper boundary of the daily 'Good' category. A county's average AQI is not itself a daily AQI category. County averages are calculated only from reported days.")

highest = county.loc[county["Mean_AQI"].idxmax()]

st.caption(
    f"Finding: {highest['County']} County had the highest mean AQI "
    f"({highest['Mean_AQI']:.1f}) among the selected counties "
    "during the selected period."
)

fig = px.bar(county.sort_values("Coverage (%)"), x="Coverage (%)", y="County", orientation="h", title="Reporting coverage by county", labels={"Coverage (%)":"Reporting coverage (%)"})
fig.update_traces(marker_color="#719eb9")
fig.update_xaxes(range=[0,100])
fig.update_layout(height=max(450, len(county)*25+120))
st.plotly_chart(fig, use_container_width=True)
st.caption(f"Coverage is the number of unique reported days divided by {possible_days} possible calendar days in the selected period. Low coverage makes county comparisons less representative.")
with st.expander("County summary table"):
    st.dataframe(county.round(2).reset_index(drop=True), hide_index=True, use_container_width=True)

st.subheader("3 · Monthly air quality")
monthly = filtered.groupby("Month").agg(Mean_AQI=("AQI","mean"), Reported_Observations=("AQI","count")).reset_index()
monthly["Month name"] = monthly["Month"].map(lambda m:calendar.month_abbr[m])
fig = px.line(monthly, x="Month name", y="Mean_AQI", markers=True, title="Monthly mean reported AQI", labels={"Month name":"Month", "Mean_AQI":"Mean AQI"}, hover_data=["Reported_Observations"])
fig.update_traces(line_color="#e39a20", line_width=3)
st.plotly_chart(fig, use_container_width=True)
st.caption("Monthly means pool all reported county-day observations in the selection. Changes in county reporting coverage can influence month-to-month comparisons; this chart does not establish causes of seasonal differences.")
with st.expander("Monthly summary table"):
    st.dataframe(monthly[["Month name","Mean_AQI","Reported_Observations"]].round(2), hide_index=True, use_container_width=True)

st.subheader("4 · Defining air pollutants")
pollutants = filtered["Defining Parameter"].value_counts().rename_axis("Pollutant").reset_index(name="County-days")
pollutants["Percentage (%)"] = pollutants["County-days"] / len(filtered) * 100
fig = px.bar(pollutants, x="Pollutant", y="Percentage (%)", text="Percentage (%)", title="Share of reported county-days by defining pollutant")
fig.update_traces(marker_color="#d35e53", texttemplate="%{text:.2f}%", textposition="outside")
fig.update_yaxes(range=[0,max(10,pollutants["Percentage (%)"].max()*1.2)])
st.plotly_chart(fig, use_container_width=True)
st.caption("A defining pollutant is the pollutant that determined that day's reported AQI. These percentages are not pollutant concentration shares.")
with st.expander("Pollutant summary table"):
    st.dataframe(pollutants.round(2), hide_index=True, use_container_width=True)

st.subheader("5 · Michigan county map")
st.write("Hover over any county to see its name, mean AQI, reported days, and reporting coverage. Gray counties have no data for the current selection. The color scale stays fixed to the full 2025 dataset. You can also zoom and pan.")
try:
    boundaries = load_boundaries()
    mapped = boundaries.merge(county[["County", "Mean_AQI"]], left_on="NAME", right_on="County", how="left")
    # Interactive county polygons with hover details, including counties without data.
    import json
    mapped = mapped.merge(county[["County", "Reported_Days", "Coverage (%)"]], on="County", how="left")
    mapped["Hover county"] = mapped["NAME"]
    mapped["AQI label"] = mapped["Mean_AQI"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "No AQI Data")
    mapped["Days label"] = mapped["Reported_Days"].map(lambda x: str(int(x)) if pd.notna(x) else "No AQI Data")
    mapped["Coverage label"] = mapped["Coverage (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "No AQI Data")
    mapped = mapped.reset_index(drop=True)
    mapped["map_id"] = mapped.index.astype(str)
    geojson = json.loads(mapped.to_json())
    for feature in geojson["features"]:
        feature["id"] = feature["properties"]["map_id"]

    fig = go.Figure()
    missing = mapped[mapped["Mean_AQI"].isna()]
    observed = mapped[mapped["Mean_AQI"].notna()]
    def add_counties(frame, colorscale, show_scale):
        if frame.empty:
            return
        fig.add_trace(go.Choropleth(
            geojson=geojson,
            locations=frame["map_id"],
            z=frame["Mean_AQI"].fillna(0),
            featureidkey="id",
            colorscale=colorscale,
            zmin=0 if not show_scale else MAP_COLOR_MIN,
            zmax=1 if not show_scale else MAP_COLOR_MAX,
            showscale=show_scale,
            colorbar=dict(title="Mean AQI", len=0.7) if show_scale else None,
            marker_line_color="#777777", marker_line_width=0.6,
            customdata=frame[["Hover county", "AQI label", "Days label", "Coverage label"]].to_numpy(),
            hovertemplate=("<b>%{customdata[0]} County</b><br>Mean AQI: %{customdata[1]}"
                           "<br>Reported days: %{customdata[2]}<br>Coverage: %{customdata[3]}<extra></extra>"),
            name="Counties",
        ))
    add_counties(missing, [[0, "#d6d9dd"], [1, "#d6d9dd"]], False)
    add_counties(observed, "YlOrRd", True)
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator")
    fig.update_layout(title="Mean reported AQI by Michigan county (2025)",
                      height=900, margin=dict(l=0, r=0, t=45, b=0),
                      showlegend=False, dragmode="pan")
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
    st.caption(f"{mapped['Mean_AQI'].notna().sum()} of 83 counties have observations in this selection. Gray does not mean good air quality. County boundaries: U.S. Census Bureau, 2024 cartographic boundaries.")
except Exception as exc:
    st.warning("The county boundary file could not be loaded. The map requires internet access to the U.S. Census Bureau on first run.")
    st.caption(f"Map loading detail: {type(exc).__name__}: {exc}")
    st.dataframe(county[["County","Mean_AQI"]].round(2), hide_index=True)

st.subheader("Findings and limitations")
if len(selected)==len(all_counties) and month_range==(1,12):
    st.write("**Full dataset findings:** Wayne (56.12) and Kent (53.68) have the highest reported mean AQI among reporting counties. June (57.16) and July (54.73) have the highest monthly means. Ozone (56.10%) and PM2.5 (43.66%) are the most frequent defining pollutants.")
else:
    highest = county.iloc[0]
    st.write(f"**Current selection:** {highest['County']} has the highest mean AQI among selected counties ({highest['Mean_AQI']:.2f}), based on {int(highest['Reported_Days'])} reported days. These results change with the filters.")

st.info("""
**Limitations:**

1. AQI observations are available for only 27 of Michigan's 83 counties.

2. Reporting coverage varies among counties, which may affect comparisons of annual mean AQI.

3. The analysis uses data from 2025 only and does not establish long-term trends.

4. A complete dataset covering all Michigan counties and every day of the year would improve the accuracy and completeness of the analysis and allow more reliable comparisons across counties.
""")

st.markdown("""
**Caution:** Counties with fewer reported days may have less representative
annual mean AQI values. Therefore, county comparisons should be interpreted carefully.

**Next Step:** Extend the analysis to multiple years and include more counties
with complete daily observations to better understand long-term air quality
patterns across Michigan.
""")

st.caption("Source: U.S. EPA AirData, Daily AQI by County (2025) · https://aqs.epa.gov/aqsweb/airdata/download_files.html")
