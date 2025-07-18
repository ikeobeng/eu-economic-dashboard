# Import libraries
import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter

# Page configuration 
st.set_page_config(page_title="EU Economic Dashboard", layout="wide", initial_sidebar_state="expanded")

# CSS for the multiselect component
st.markdown("""
    <style>
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #dff0d8 !important;  
        color: #3c763d !important;                       
        border: 1px solid #c2e0c6   
    }
    </style>
""", unsafe_allow_html=True)

# Load data (https://docs.streamlit.io/)
@st.cache_data
def load_data():
    return pd.read_excel("dataCA2_clean.xlsx", sheet_name="Sheet1")

df = load_data()

# Define layout (https://blog.streamlit.io/crafting-a-dashboard-app-in-python-using-streamlit/)
col = st.columns((1.5, 4.5, 2), gap="medium")  

# Column 1: Sidebar for general filters and user controls 
with col[0]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.title("EU Economic Dashboard")
    
    selected_country = st.selectbox("Country", df["country_name"].unique())

    available_years = df[df["country_name"] == selected_country]["year"]
    year_range = st.slider(
        "Years",
        min_value=int(available_years.min()),
        max_value=int(available_years.max()),
        value=(int(available_years.min()), int(available_years.max())),
        step=1
    )

    df_filtered = df[
        (df["country_name"] == selected_country) &
        (df["year"].between(year_range[0], year_range[1]))
    ]

# Plotly theme 
plotly_theme = "plotly_white"

# Column 2: Charts and map (https://www.kaggle.com/learn/data-visualization; https://plotly.com/python/plotly-express/)
with col[1]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader(f"📈 {selected_country}: {year_range[0]} - {year_range[1]}")

    # Line chart for comparing economic indicators over time
    with st.expander("Economic Indicators Over Time", expanded=True):
        st.subheader("Compare Metrics Over Time")        

        # Nicer display names
        metric_labels = {
            'foreign_direct_investment (US$)': 'FDI (US$)',
            'nonperforming_loans (%)': 'Nonperforming Loans (%)',
            'exports (%)': 'Exports (%)',
            'gdp_per_capita (US$)': 'GDP Per Capita (US$)',
            'high_tech_exports (%)': 'High Tech Exports (%)',
            'inflation_annual (%)': 'Inflation Annual (%)',
            'net_capital (US$)': 'Net Capital (US$)',
            'population_total': 'Population Total',
            'tax_revenue (%)': 'Tax Revenue (%)',
            'unemployment_rate (%)': 'Unemployment Rate (%)'
        }

        metric_options = list(metric_labels.keys())

        selected_metrics = st.multiselect(
            "Select metrics to analyse",
            options=metric_options,
            format_func=lambda x: metric_labels[x],
            default=['unemployment_rate (%)', 'gdp_per_capita (US$)']
        )

        if not selected_metrics:
            st.warning("Please select at least one metric to visualise.")
        else:
            # Responsive behavior is stack if more than 2 metrics
            if len(selected_metrics) > 2:
                for metric in selected_metrics:
                    with st.container():
                        fig_line = px.line(
                            df_filtered,
                            x="year",
                            y=metric,
                            markers=True,
                            labels={metric: metric_labels[metric]},
                            title=metric_labels[metric],
                            template=plotly_theme
                        )
                        fig_line.update_layout(height=300, margin=dict(t=30, b=10), title=dict(x=0.5))
                        st.plotly_chart(fig_line, use_container_width=True)
            else:
                chart_cols = st.columns(2)
                for i, metric in enumerate(selected_metrics):
                    with chart_cols[i % 2]:
                        fig_line = px.line(
                            df_filtered,
                            x="year",
                            y=metric,
                            markers=True,
                            labels={metric: metric_labels[metric]},
                            title=metric_labels[metric],
                            template=plotly_theme
                        )
                        fig_line.update_layout(height=300, margin=dict(t=30, b=10), title=dict(x=0.5))
                        st.plotly_chart(fig_line, use_container_width=True)

    # Bar chart for comparing two aggregated metrics across time  (Ford, 2025. Exploratory data analysis and statistics [IS41570_lab_8]. University College Dublin.)
    with st.expander("Dynamic Indicators Comparison Tool"):
        st.subheader("Compare Metrics With Aggregation Methods")

        left_col, right_col = st.columns(2)

        metric_options = list(metric_labels.keys())

        # Left metric
        with left_col:
            metric1 = st.selectbox("Select first metric", options=metric_options, format_func=lambda x: metric_labels[x], key="bar_metric1")
            agg_method1 = st.radio("Aggregation method", ["Mean", "Median", "Max", "Min"], horizontal=True, key="bar_agg1")

        # Right metric
        with right_col:
            metric2 = st.selectbox("Select second metric", options=metric_options, format_func=lambda x: metric_labels[x], key="bar_metric2")
            agg_method2 = st.radio("Aggregation method", ["Mean", "Median", "Max", "Min"], horizontal=True, key="bar_agg2")

        # Metric aggregation function
        def aggregate(df, metric, method):
            if method == "Mean":
                return df.groupby("year")[metric].mean().reset_index()
            elif method == "Median":
                return df.groupby("year")[metric].median().reset_index()
            elif method == "Max":
                return df.groupby("year")[metric].max().reset_index()
            else: # Min
                return df.groupby("year")[metric].min().reset_index()

        df_metric1 = aggregate(df_filtered, metric1, agg_method1)
        df_metric2 = aggregate(df_filtered, metric2, agg_method2)
        
        # Merge dataframes for comparison
        comparison_df = pd.merge(df_metric1, df_metric2, on="year", suffixes=(f" ({agg_method1})", f" ({agg_method2})"))
        comparison_long = comparison_df.melt(id_vars="year", var_name="Metric", value_name="Value")

        # Create bar chart for comparison
        fig_compare = px.bar(
            comparison_long,
            x="year",
            y="Value",
            color="Metric",
            barmode="group",
            template=plotly_theme,
            title=f"{metric_labels[metric1]} vs {metric_labels[metric2]} Over Time"
        )
        
        # Update layout for better readability
        fig_compare.update_layout(
            title=dict(
            text=f"{metric_labels.get(metric1, metric1)} vs {metric_labels.get(metric2, metric2)} Over Time",
            x=0.5,
            xanchor="center"
        ),
        height=350,
        margin=dict(t=40, b=20)
    )

        st.plotly_chart(fig_compare, use_container_width=True)

    # Bubble scatter plot to explore relationships between two metrics
    with st.expander("Explore Relationships Between Any Two Indicators"):
        st.subheader("Relationship Metric Comparison")

        metric_options = list(metric_labels.keys())

        # Select X and Y metrics for scatter plot relationship
        col1, col2 = st.columns(2)
        with col1:
            x_metric = st.selectbox("Select X-axis", options=metric_options, format_func=lambda x: metric_labels[x], key="scatter_x_metric")
        with col2:
            y_metric = st.selectbox("Select Y-axis", options=metric_options, format_func=lambda x: metric_labels[x], key="scatter_y_metric")

        if x_metric == y_metric:
            st.warning("Please select two different metrics for X and Y axes.")
        else:
            color_option = st.radio("Color by:", options=["None", "year", "country_name"], horizontal=True, key="scatter_color")
            
            # Filter data for selected metrics
            try:
                required_cols = [x_metric, y_metric, "year", "country_name", "population_total"]
                if not all(col in df_filtered.columns for col in required_cols):
                    missing = [col for col in required_cols if col not in df_filtered.columns]
                    st.error(f"Missing columns in data: {missing}")
                else:
                    df_scatter = df_filtered[required_cols].copy()

                    def make_column_names_unique_locally(df):
                        counter = Counter()
                        new_cols = []
                        for col in df.columns:
                            counter[col] += 1
                            new_cols.append(f"{col}_{counter[col]}" if counter[col] > 1 else col)
                        df.columns = new_cols
                        return df
                    
                    # Ensure unique column names for scatter plot
                    df_scatter = make_column_names_unique_locally(df_scatter)
                    x_col = next(col for col in df_scatter.columns if col.startswith(x_metric))
                    y_col = next(col for col in df_scatter.columns if col.startswith(y_metric))
                    size_col = next(col for col in df_scatter.columns if col.startswith("population_total"))
                    color_col = color_option if color_option != "None" else None

                    # Create bubble scatter plot
                    fig = px.scatter(
                        df_scatter,
                        x=x_col,
                        y=y_col,
                        color=color_col,
                        size=size_col,
                        hover_name="country_name",
                        template="plotly",
                        labels={
                            x_col: metric_labels[x_metric],
                            y_col: metric_labels[y_metric],
                            size_col: "Population"
                        },
                        title=f"{metric_labels[x_metric]} vs {metric_labels[y_metric]}"
                    )

                    fig.update_layout(
                        title=dict(
                            text=f"{metric_labels.get(x_metric, x_metric)} vs {metric_labels.get(y_metric, y_metric)}",
                            x=0.5,
                            xanchor="center"
                        ),
                        height=400,
                        margin=dict(t=40, l=20, r=20, b=20)
                    )


                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"An error occurred while creating the scatter plot: {e}")


   # Choropleth Map 
    with st.expander("🌍 Visualise Economic Indicators Across Europe", expanded=False):
        st.subheader("Choropleth Map - Regional Average Metrics")

        # Select metric category and metric for map
        selected_category = st.selectbox("Select metric category", options=["Economic", "Social"], key="map_category")

        if selected_category == "Economic":
            available_metrics = ['gdp_per_capita (US$)', 'exports (%)', 'foreign_direct_investment (US$)', 'tax_revenue (%)', 'net_capital (US$)']
        else: # Social
            available_metrics = ['unemployment_rate (%)', 'population_total', 'inflation_annual (%)', 'nonperforming_loans (%)']

        # Select specific metric for map
        selected_metric = st.selectbox("Select metric to display", options=available_metrics, format_func=lambda x: metric_labels[x], key="map_metric")

        # Group data for map visualisation
        map_df = df[df["year"].between(year_range[0], year_range[1])]
        map_df = map_df.groupby("country_name", as_index=False)[selected_metric].mean()

        # Create choropleth map
        fig_map = px.choropleth(
            map_df,
            locations="country_name",
            locationmode="country names",
            color=selected_metric,
            color_continuous_scale="OrRd",
            labels={selected_metric: metric_labels[selected_metric]},
            scope="europe",
            template=plotly_theme
        )
        
        fig_map.update_layout(
            title=dict(
                text=f"{metric_labels.get(selected_metric, selected_metric)} (Avg)",
                x=0.5, xanchor="center"
            ),
            height=400,
            margin=dict(t=30, b=20)
        )
        
        st.plotly_chart(fig_map, use_container_width=True)


# Column 3: Metrics and data table
with col[2]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("Metrics")

    # Difference between selected years
    try:
        prev_period = df_filtered[df_filtered["year"] == year_range[0]]
        latest_period = df_filtered[df_filtered["year"] == year_range[1]]

        delta_unemp = latest_period["unemployment_rate (%)"].values[0] - prev_period["unemployment_rate (%)"].values[0]
        delta_infl = latest_period["inflation_annual (%)"].values[0] - prev_period["inflation_annual (%)"].values[0]
        delta_gdp = latest_period["gdp_per_capita (US$)"].values[0] - prev_period["gdp_per_capita (US$)"].values[0]
        delta_pop = latest_period["population_total"].values[0] - prev_period["population_total"].values[0]
    except Exception:
        delta_unemp = delta_infl = delta_gdp = delta_pop = 0

    def styled_delta(delta, is_percentage=True):
        if delta > 0:
            arrow = "▲"
            color = "#28a745"  # green
        elif delta < 0:
            arrow = "▼"
            color = "#dc3545"  # red
        else:
            arrow = "▶"
            color = "#6c757d"  # gray

        val = f"{abs(delta):.2f}%" if is_percentage else f"{abs(delta):,.0f}"
        return f"<div style='color:{color}; font-size: 0.9em; margin-top: 4px;'>{arrow} {val}</div>"

    # Display metric function
    def display_metric(label, value, delta_html):
        st.markdown(f"""
            <div style="padding-bottom:10px;">
                <div style="font-size:14px; color: #6c757d;">{label}</div>
                <div style="font-size:22px; font-weight:500; line-height:1.2;">{value}</div>
                {delta_html}
            </div>
        """, unsafe_allow_html=True)

    # Layout
    m1, m2 = st.columns(2)
    with m1:
        display_metric(
            "Avg Unemployment",
            f"{df_filtered['unemployment_rate (%)'].mean():.2f}%",
            styled_delta(delta_unemp)
        )

    with m2:
        display_metric(
            "Avg Inflation",
            f"{df_filtered['inflation_annual (%)'].mean():.2f}%",
            styled_delta(delta_infl)
        )

    m3, m4 = st.columns(2)
    with m3:
        display_metric(
            "Avg GDP/Capita",
            f"${df_filtered['gdp_per_capita (US$)'].mean():,.0f}",
            styled_delta(delta_gdp, is_percentage=False)
        )

    with m4:
        display_metric(
            "Avg Population",
            f"{df_filtered['population_total'].mean():,.0f}",
            styled_delta(delta_pop, is_percentage=False)
        )

    # Latest year highlights
    latest_data = df_filtered[df_filtered["year"] == df_filtered["year"].max()]
    if not latest_data.empty:
        st.markdown("#### Latest Year Snapshot")
        st.success(f"""
        For **{selected_country}** in **{latest_data['year'].values[0]}**:
        - Unemployment: **{latest_data['unemployment_rate (%)'].values[0]:.2f}%**
        - Inflation: **{latest_data['inflation_annual (%)'].values[0]:.2f}%**
        - GDP per Capita: **${latest_data['gdp_per_capita (US$)'].values[0]:,.0f}**
        """)

    # Filtered data table
    with st.expander("View Filtered Data Table"):
        st.dataframe(df_filtered.sort_values(by="year"), use_container_width=True, height=200)

        # CSV Download
        csv = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button("Download Data as CSV", csv, f"{selected_country}_filtered_data.csv", "text/csv", key="download-csv")

    # Data source information
    with st.expander("Quick Data Info.", expanded=True):
        st.write('''
            - Data: World Bank Group - World Development Indicators  
            - Description: This dataset contains key economic indicators for EU countries.  
            - Source: [World Bank](https://data.worldbank.org/indicator/SL.UEM.TOTL.ZS?locations=EU)
        ''')

# Block container and padding for the entire app
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)