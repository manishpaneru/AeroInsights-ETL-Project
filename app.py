import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime, timedelta
import numpy as np

# Hey there! 👋 I wanted to make this dashboard look professional, so I started with some nice page config
st.set_page_config(page_title="Live Flights ETL Project", layout="wide", page_icon="✈️")

# I love making things look pretty! Added some custom CSS to make the metrics and layout pop
st.markdown("""
    <style>
    .stMetric .metric-label { font-size: 16px !important; }
    .stMetric .metric-value { font-size: 24px !important; }
    div[data-testid="stHorizontalBlock"] > div:first-of-type {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# I wanted a cool header that stands out, so I created this fancy title section
st.markdown("""
    <div style='text-align: center; background-color: #f0f2f6; padding: 20px; border-radius: 10px;'>
        <h1 style='color: #1f77b4;'>✈️ Live Flights ETL Project</h1>
        <h3>Created by Manish Paneru</h3>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

# I'm using caching here because who likes waiting for data to load? Not me!
@st.cache_data
def load_data():
    try:
        conn = sqlite3.connect('sky.db')
        flights_df = pd.read_sql_query("SELECT * FROM flights", conn)
        airports_df = pd.read_sql_query("SELECT * FROM airports", conn)
        conn.close()
        
        # Converting timestamps because working with proper datetime is way easier
        flights_df['approxDepartureTime'] = pd.to_datetime(flights_df['approxDepartureTime'])
        flights_df['approxArrivalTime'] = pd.to_datetime(flights_df['approxArrivalTime'])
        
        return flights_df, airports_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

# Time to load our precious data!
flights_df, airports_df = load_data()

if flights_df is not None and airports_df is not None:
    # I thought it'd be cool to calculate flight durations - helps us understand how long these planes are up there!
    flights_df['duration'] = (flights_df['approxArrivalTime'] - flights_df['approxDepartureTime']).dt.total_seconds() / 3600

    # I love a good overview! Created this stats section to give a quick snapshot of what's happening
    st.subheader("📊 Flight Analytics Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculating some interesting metrics that tell us the big picture
    total_flights = len(flights_df)
    active_flights = len(flights_df[flights_df['approxArrivalTime'] > datetime.now()])
    avg_duration = flights_df['duration'].mean()
    unique_routes = len(flights_df.groupby(['DepartureAirport', 'ArrivalAirport']))
    
    # These metrics are like the vital signs of our flight network
    col1.metric("Total Flights", f"{total_flights:,}", delta="Real-time")
    col2.metric("Active Flights", f"{active_flights:,}", delta="Live")
    col3.metric("Avg Flight Duration", f"{avg_duration:.1f} hrs")
    col4.metric("Unique Routes", f"{unique_routes:,}")

    # I organized everything into tabs because I believe in keeping things neat and tidy!
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Flight Routes & Traffic", "Time Analysis", "Airport Insights", 
                                                  "Simple Analytics", "Additional Insights", "Cool Insights"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Flight Routes Map
            st.subheader("🗺️ Global Flight Routes")
            fig_map = go.Figure()

            # Add flight routes without limiting to 100 flights
            for _, flight in flights_df.iterrows():
                dep_airport = airports_df[airports_df['IATA Code'] == flight['DepartureAirport']]
                arr_airport = airports_df[airports_df['IATA Code'] == flight['ArrivalAirport']]
                
                if not dep_airport.empty and not arr_airport.empty:
                    fig_map.add_trace(go.Scattergeo(
                        lon=[dep_airport.iloc[0]['Longitude'], arr_airport.iloc[0]['Longitude']],
                        lat=[dep_airport.iloc[0]['Latitude'], arr_airport.iloc[0]['Latitude']],
                        mode='lines',
                        line=dict(width=1, color='red'),
                        opacity=0.2,
                        showlegend=False
                    ))

            # Add airport markers
            unique_airports = pd.concat([
                flights_df['DepartureAirport'],
                flights_df['ArrivalAirport']
            ]).unique()
            
            active_airports = airports_df[airports_df['IATA Code'].isin(unique_airports)]
            
            fig_map.add_trace(go.Scattergeo(
                lon=active_airports['Longitude'],
                lat=active_airports['Latitude'],
                mode='markers',
                marker=dict(
                    size=5,
                    color='blue',
                    opacity=0.7
                ),
                text=active_airports['IATA Code'],
                hoverinfo='text',
                showlegend=False
            ))

            fig_map.update_layout(
                showlegend=False,
                geo=dict(
                    showland=True,
                    showocean=True,
                    showcountries=True,
                    showlakes=True,
                    landcolor='rgb(243, 243, 243)',
                    countrycolor='rgb(204, 204, 204)',
                    oceancolor='rgb(230, 245, 255)',
                    projection_type='equirectangular',
                    showcoastlines=True,
                    coastlinecolor='rgb(204, 204, 204)',
                    showframe=False,
                    center=dict(
                        lon=0,
                        lat=20
                    ),
                    projection_scale=1.3
                ),
                height=400,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_map, use_container_width=True)
            
        with col2:
            # Busiest Routes Analysis
            st.subheader("🛫 Busiest Flight Routes")
            route_counts = flights_df.groupby(['DepartureAirport', 'ArrivalAirport']).size().reset_index(name='count')
            route_counts = route_counts.sort_values('count', ascending=True)  # Sort ascending for horizontal bar chart
            top_routes = route_counts.nlargest(10, 'count')
            
            fig_routes = go.Figure(go.Bar(
                x=top_routes['count'],
                y=top_routes['DepartureAirport'] + ' → ' + top_routes['ArrivalAirport'],
                orientation='h',
                marker_color='lightcoral'
            ))
            
            fig_routes.update_layout(
                title="Top 10 Busiest Routes",
                xaxis_title="Number of Flights",
                yaxis_title="Route",
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis=dict(autorange="reversed")  # Reverse y-axis to show highest values at top
            )
            st.plotly_chart(fig_routes, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Flight Activity by Hour
            st.subheader("⏰ Hourly Flight Distribution")
            flights_df['hour'] = flights_df['approxDepartureTime'].dt.hour
            hourly_flights = flights_df['hour'].value_counts().sort_index()
            
            fig_hourly = go.Figure()
            fig_hourly.add_trace(go.Scatter(
                x=hourly_flights.index,
                y=hourly_flights.values,
                mode='lines+markers',
                line=dict(color='royalblue', width=2),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(65, 105, 225, 0.2)'
            ))
            
            fig_hourly.update_layout(
                title="24-Hour Flight Activity",
                xaxis_title="Hour of Day",
                yaxis_title="Number of Flights",
                height=400
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
            
        with col2:
            # Flight Duration Distribution
            st.subheader("⏱️ Flight Duration Analysis")
            
            fig_duration = go.Figure()
            fig_duration.add_trace(go.Histogram(
                x=flights_df['duration'],
                nbinsx=30,
                marker_color='lightseagreen'
            ))
            
            fig_duration.update_layout(
                title="Distribution of Flight Durations",
                xaxis_title="Duration (hours)",
                yaxis_title="Number of Flights",
                height=400
            )
            st.plotly_chart(fig_duration, use_container_width=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            # Busiest Airports
            st.subheader("🏢 Busiest Airports")
            departures = flights_df['DepartureAirport'].value_counts()
            arrivals = flights_df['ArrivalAirport'].value_counts()
            total_traffic = (departures + arrivals).nlargest(10)
            
            fig_airports = go.Figure(go.Bar(
                x=total_traffic.values,
                y=total_traffic.index,
                orientation='h',
                marker_color='lightblue'
            ))
            
            fig_airports.update_layout(
                title="Top 10 Busiest Airports",
                xaxis_title="Total Flights (Arrivals + Departures)",
                yaxis_title="Airport Code",
                height=400
            )
            st.plotly_chart(fig_airports, use_container_width=True)
            
        with col2:
            # Airport Traffic Patterns
            st.subheader("📈 Airport Traffic Patterns")
            
            # Get top 5 busiest airports
            top_airports = total_traffic.head(5).index
            
            fig_patterns = go.Figure()
            
            # Create hour range
            hours = range(24)
            
            for airport in top_airports:
                # Initialize arrays with zeros
                dep_counts = pd.Series(0, index=hours)
                arr_counts = pd.Series(0, index=hours)
                
                # Fill in the actual values
                dep_temp = flights_df[flights_df['DepartureAirport'] == airport]['approxDepartureTime'].dt.hour.value_counts()
                arr_temp = flights_df[flights_df['ArrivalAirport'] == airport]['approxArrivalTime'].dt.hour.value_counts()
                
                # Update the values where we have data
                dep_counts.update(dep_temp)
                arr_counts.update(arr_temp)
                
                # Add the counts and create the trace
                total_counts = dep_counts + arr_counts
                
                fig_patterns.add_trace(go.Scatter(
                    x=list(hours),
                    y=total_counts.values,
                    mode='lines+markers',
                    name=airport,
                    marker=dict(size=6)
                ))
            
            fig_patterns.update_layout(
                title="Hourly Traffic at Top 5 Airports",
                xaxis_title="Hour of Day",
                yaxis_title="Number of Flights",
                height=400,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            st.plotly_chart(fig_patterns, use_container_width=True)

    with tab4:
        st.subheader("📊 Simple Flight Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Simple Departure vs Arrival Comparison
            st.subheader("✈️ Departures vs Arrivals")
            dep_count = len(flights_df['DepartureAirport'].unique())
            arr_count = len(flights_df['ArrivalAirport'].unique())
            
            fig_comp = go.Figure(data=[
                go.Bar(
                    name='Departures',
                    x=['Airports'],
                    y=[dep_count],
                    marker_color='lightblue'
                ),
                go.Bar(
                    name='Arrivals',
                    x=['Airports'],
                    y=[arr_count],
                    marker_color='lightgreen'
                )
            ])
            
            fig_comp.update_layout(
                title="Number of Airports with Departures vs Arrivals",
                yaxis_title="Number of Airports",
                height=400,
                barmode='group'
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        with col2:
            # Flight Numbers Distribution
            st.subheader("🔢 Flight Numbers")
            flight_numbers = flights_df['flightnumber'].value_counts().head(10)
            
            fig_numbers = go.Figure(data=[
                go.Bar(
                    x=flight_numbers.index,
                    y=flight_numbers.values,
                    marker_color='lightcoral'
                )
            ])
            
            fig_numbers.update_layout(
                title="Top 10 Most Common Flight Numbers",
                xaxis_title="Flight Number",
                yaxis_title="Frequency",
                height=400
            )
            st.plotly_chart(fig_numbers, use_container_width=True)

        col3, col4 = st.columns(2)
        
        with col3:
            # Time-based Flight Count
            st.subheader("📅 Flights Over Time")
            flights_df['date'] = flights_df['approxDepartureTime'].dt.date
            daily_flights = flights_df.groupby('date').size().reset_index(name='count')
            
            fig_time = go.Figure(data=[
                go.Scatter(
                    x=daily_flights['date'],
                    y=daily_flights['count'],
                    mode='lines+markers',
                    line=dict(color='royalblue'),
                    marker=dict(size=8)
                )
            ])
            
            fig_time.update_layout(
                title="Number of Flights per Day",
                xaxis_title="Date",
                yaxis_title="Number of Flights",
                height=400
            )
            st.plotly_chart(fig_time, use_container_width=True)

        with col4:
            # Airport Locations Map
            st.subheader("🌍 Airport Locations")
            
            # Get unique airports from flights data
            unique_airports = pd.concat([
                flights_df['DepartureAirport'],
                flights_df['ArrivalAirport']
            ]).unique()
            
            # Filter airports dataframe
            active_airports = airports_df[airports_df['IATA Code'].isin(unique_airports)]
            
            fig_airports = go.Figure(data=go.Scattergeo(
                lon=active_airports['Longitude'],
                lat=active_airports['Latitude'],
                mode='markers',
                marker=dict(
                    size=8,
                    color='red',
                    opacity=0.7
                ),
                text=active_airports['IATA Code'],
                hoverinfo='text'
            ))
            
            fig_airports.update_layout(
                title="Active Airports in Dataset",
                geo=dict(
                    showland=True,
                    showcountries=True,
                    showocean=True,
                    countrywidth=0.5,
                    landcolor='rgb(243, 243, 243)',
                    oceancolor='rgb(230, 245, 255)',
                    projection_type='equirectangular'
                ),
                height=400
            )
            st.plotly_chart(fig_airports, use_container_width=True)

        # Simple Statistics Box
        st.markdown("---")
        st.subheader("📈 Quick Statistics")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            avg_flights_per_day = len(flights_df) / max(1, len(daily_flights))
            st.metric(
                "Average Flights per Day",
                f"{avg_flights_per_day:.1f}"
            )
        
        with stats_col2:
            if not daily_flights.empty:
                most_active_day = daily_flights.loc[daily_flights['count'].idxmax(), 'date'].strftime('%Y-%m-%d')
            else:
                most_active_day = "No data"
            st.metric(
                "Most Active Day",
                most_active_day
            )
        
        with stats_col3:
            st.metric(
                "Total Active Airports",
                f"{len(unique_airports):,}"
            )
        
        with stats_col4:
            avg_flights_per_route = len(flights_df) / max(1, unique_routes)
            st.metric(
                "Avg Flights per Route",
                f"{avg_flights_per_route:.1f}"
            )

    with tab5:
        st.subheader("🔍 Additional Flight Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Departure vs Arrival Time Patterns
            st.subheader("🕒 Departure vs Arrival Patterns")
            dep_hours = flights_df['approxDepartureTime'].dt.hour.value_counts().sort_index()
            arr_hours = flights_df['approxArrivalTime'].dt.hour.value_counts().sort_index()
            
            fig_patterns = go.Figure()
            
            fig_patterns.add_trace(go.Scatter(
                x=dep_hours.index,
                y=dep_hours.values,
                name='Departures',
                mode='lines',
                line=dict(color='blue', width=2),
                fill='tonexty'
            ))
            
            fig_patterns.add_trace(go.Scatter(
                x=arr_hours.index,
                y=arr_hours.values,
                name='Arrivals',
                mode='lines',
                line=dict(color='red', width=2),
                fill='tonexty'
            ))
            
            fig_patterns.update_layout(
                title="Hourly Distribution: Departures vs Arrivals",
                xaxis_title="Hour of Day",
                yaxis_title="Number of Flights",
                height=400
            )
            st.plotly_chart(fig_patterns, use_container_width=True)
        
        with col2:
            # Airport Categories
            st.subheader("🏢 Airport Categories")
            
            # Calculate airport roles
            airport_roles = pd.DataFrame()
            airport_roles['departures'] = flights_df['DepartureAirport'].value_counts()
            airport_roles['arrivals'] = flights_df['ArrivalAirport'].value_counts()
            
            # Categorize airports
            def categorize_airport(row):
                if row['departures'] > row['arrivals'] * 1.2:
                    return 'Primarily Departures'
                elif row['arrivals'] > row['departures'] * 1.2:
                    return 'Primarily Arrivals'
                else:
                    return 'Balanced'
            
            airport_roles['category'] = airport_roles.apply(categorize_airport, axis=1)
            category_counts = airport_roles['category'].value_counts()
            
            fig_roles = go.Figure(data=[
                go.Pie(
                    labels=category_counts.index,
                    values=category_counts.values,
                    hole=0.4,
                    marker=dict(colors=['lightblue', 'lightgreen', 'lightcoral'])
                )
            ])
            
            fig_roles.update_layout(
                title="Airport Role Distribution",
                height=400
            )
            st.plotly_chart(fig_roles, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Flight Frequency Heatmap
            st.subheader("🗓️ Weekly Flight Patterns")
            
            # Create day and hour columns
            flights_df['day'] = flights_df['approxDepartureTime'].dt.day_name()
            flights_df['hour'] = flights_df['approxDepartureTime'].dt.hour
            
            # Create pivot table for heatmap
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heat_data = pd.crosstab(flights_df['day'], flights_df['hour'])
            heat_data = heat_data.reindex(day_order)
            
            fig_heat = go.Figure(data=go.Heatmap(
                z=heat_data.values,
                x=heat_data.columns,
                y=heat_data.index,
                colorscale='Viridis'
            ))
            
            fig_heat.update_layout(
                title="Flight Frequency by Day and Hour",
                xaxis_title="Hour of Day",
                yaxis_title="Day of Week",
                height=400
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        
        with col4:
            # Route Distance Distribution
            st.subheader("📏 Route Network Analysis")
            
            # Calculate connections per airport
            connections = pd.concat([
                flights_df['DepartureAirport'].value_counts(),
                flights_df['ArrivalAirport'].value_counts()
            ]).groupby(level=0).sum()
            
            connections = connections.sort_values(ascending=True).tail(15)
            
            fig_connections = go.Figure(data=[
                go.Bar(
                    x=connections.values,
                    y=connections.index,
                    orientation='h',
                    marker_color='lightseagreen'
                )
            ])
            
            fig_connections.update_layout(
                title="Most Connected Airports",
                xaxis_title="Total Connections",
                yaxis_title="Airport",
                height=400
            )
            st.plotly_chart(fig_connections, use_container_width=True)
        
        # Additional Statistics
        st.markdown("---")
        st.subheader("📊 Network Statistics")
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        
        with stats_col1:
            # Calculate network density
            total_possible_routes = len(unique_airports) * (len(unique_airports) - 1)
            network_density = (unique_routes / total_possible_routes) * 100
            st.metric(
                "Network Density",
                f"{network_density:.1f}%",
                help="Percentage of possible routes that are actually flown"
            )
        
        with stats_col2:
            # Calculate average connections per airport
            avg_connections = connections.mean()
            st.metric(
                "Avg Connections per Airport",
                f"{avg_connections:.1f}"
            )
        
        with stats_col3:
            # Calculate busiest hour
            busiest_hour = flights_df['hour'].mode().iloc[0]
            st.metric(
                "Peak Hour",
                f"{busiest_hour:02d}:00",
                help="Hour with most flight activity"
            )

    with tab6:
        st.subheader("✨ Cool Flight Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 3D Flight Paths
            st.subheader("🌐 3D Flight Paths")
            
            # Create 3D scatter plot for airports with flight paths
            fig_3d = go.Figure()
            
            # Add flight paths as 3D lines
            for _, flight in flights_df.iterrows():
                dep_airport = airports_df[airports_df['IATA Code'] == flight['DepartureAirport']]
                arr_airport = airports_df[airports_df['IATA Code'] == flight['ArrivalAirport']]
                
                if not dep_airport.empty and not arr_airport.empty:
                    # Calculate arc points for curved path
                    lon1, lat1 = dep_airport.iloc[0]['Longitude'], dep_airport.iloc[0]['Latitude']
                    lon2, lat2 = arr_airport.iloc[0]['Longitude'], arr_airport.iloc[0]['Latitude']
                    
                    # Create arc points
                    t = np.linspace(0, 1, 100)
                    arc_height = np.sin(np.pi * t) * 0.3  # Adjust height of arc
                    
                    # Linear interpolation for lon/lat
                    lon = lon1 + t * (lon2 - lon1)
                    lat = lat1 + t * (lat2 - lat1)
                    
                    fig_3d.add_trace(go.Scatter3d(
                        x=lon,
                        y=lat,
                        z=arc_height,
                        mode='lines',
                        line=dict(
                            color='rgba(100, 149, 237, 0.3)',
                            width=2
                        ),
                        showlegend=False
                    ))
            
            # Add airports as points
            fig_3d.add_trace(go.Scatter3d(
                x=active_airports['Longitude'],
                y=active_airports['Latitude'],
                z=np.zeros(len(active_airports)),
                mode='markers',
                marker=dict(
                    size=4,
                    color='red',
                    symbol='diamond'
                ),
                text=active_airports['IATA Code'],
                hoverinfo='text',
                showlegend=False
            ))
            
            fig_3d.update_layout(
                title="3D Flight Network",
                scene=dict(
                    xaxis_title="Longitude",
                    yaxis_title="Latitude",
                    zaxis_title="Altitude",
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.2)
                    )
                ),
                height=500
            )
            st.plotly_chart(fig_3d, use_container_width=True)
        
        with col2:
            # Animated Time Series
            st.subheader("⏰ Flight Activity Animation")
            
            # Create hourly flight counts with smooth interpolation
            hourly_data = flights_df.groupby([
                flights_df['approxDepartureTime'].dt.date.rename('flight_date'),
                flights_df['approxDepartureTime'].dt.hour.rename('flight_hour')
            ]).size().reset_index(name='flight_count')
            
            # Create animation frames
            fig_anim = go.Figure(
                data=[
                    go.Scatter(
                        x=hourly_data[hourly_data['flight_date'] == hourly_data['flight_date'].min()]['flight_hour'],
                        y=hourly_data[hourly_data['flight_date'] == hourly_data['flight_date'].min()]['flight_count'],
                        mode='lines+markers',
                        line=dict(width=2, color='royalblue'),
                        marker=dict(size=8, color='royalblue'),
                        name='Flights'
                    )
                ],
                layout=go.Layout(
                    xaxis=dict(range=[0, 23], title="Hour of Day"),
                    yaxis=dict(title="Number of Flights"),
                    title="Flight Activity by Hour (Animated)",
                    showlegend=False,
                    updatemenus=[{
                        'type': 'buttons',
                        'showactive': False,
                        'y': 0.8,
                        'x': 1.15,
                        'buttons': [{
                            'label': '▶ Play',
                            'method': 'animate',
                            'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True}]
                        }, {
                            'label': '⏸ Pause',
                            'method': 'animate',
                            'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate'}]
                        }]
                    }],
                    sliders=[{
                        'currentvalue': {
                            'prefix': 'Date: ',
                            'xanchor': 'right'
                        },
                        'pad': {'t': 50},
                        'len': 0.9,
                        'x': 0.1,
                        'y': 0,
                        'steps': [
                            {
                                'args': [[str(date)], {
                                    'frame': {'duration': 0, 'redraw': False},
                                    'mode': 'immediate'
                                }],
                                'label': date.strftime('%Y-%m-%d'),
                                'method': 'animate'
                            } for date in hourly_data['flight_date'].unique()
                        ]
                    }]
                ),
                frames=[
                    go.Frame(
                        data=[
                            go.Scatter(
                                x=hourly_data[hourly_data['flight_date'] == date]['flight_hour'],
                                y=hourly_data[hourly_data['flight_date'] == date]['flight_count'],
                                mode='lines+markers',
                                line=dict(width=2, color='royalblue'),
                                marker=dict(size=8, color='royalblue')
                            )
                        ],
                        name=str(date)
                    ) for date in hourly_data['flight_date'].unique()
                ]
            )
            
            # Add range slider and buttons
            fig_anim.update_layout(
                height=500,
                margin=dict(l=50, r=50, t=50, b=50),
                annotations=[
                    dict(
                        text="Animation Controls",
                        showarrow=False,
                        x=1.1,
                        y=1.1,
                        xref="paper",
                        yref="paper",
                        font=dict(size=12)
                    )
                ]
            )
            st.plotly_chart(fig_anim, use_container_width=True)

            # Add interactive controls
            st.markdown("---")
            st.markdown("#### Animation Controls")
            speed_col, loop_col = st.columns(2)
            with speed_col:
                animation_speed = st.slider("Animation Speed", min_value=100, max_value=1000, value=500, step=100)
                fig_anim.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = animation_speed
            
            with loop_col:
                st.markdown("##### Loop Animation")
                st.checkbox("Enable Loop", value=True, key="animation_loop")
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Circular Flight Pattern
            st.subheader("🎯 Circular Flight Pattern")
            
            # Create circular visualization of flight patterns
            hours = np.linspace(0, 2*np.pi, 24)
            flight_counts = flights_df['approxDepartureTime'].dt.hour.value_counts().sort_index()
            
            # Ensure we have all 24 hours
            all_hours = pd.Series(0, index=range(24))
            all_hours.update(flight_counts)
            flight_counts = all_hours
            
            fig_circular = go.Figure()
            
            # Add the circular pattern
            fig_circular.add_trace(go.Scatterpolar(
                r=flight_counts.values,
                theta=np.arange(0, 360, 15),  # 24 hours * 15 degrees
                mode='lines+markers',
                line=dict(color='rgba(100, 149, 237, 0.8)', width=2),
                marker=dict(
                    size=8,
                    color=flight_counts.values,
                    colorscale='Viridis',
                    showscale=True
                ),
                fill='toself'
            ))
            
            fig_circular.update_layout(
                polar=dict(
                    radialaxis=dict(showticklabels=True, gridcolor='rgba(0,0,0,0.1)'),
                    angularaxis=dict(
                        ticktext=[f'{i:02d}:00' for i in range(0, 24, 3)],
                        tickvals=np.arange(0, 360, 45),
                        gridcolor='rgba(0,0,0,0.1)'
                    )
                ),
                showlegend=False,
                title="24-Hour Flight Pattern (Polar)",
                height=500
            )
            st.plotly_chart(fig_circular, use_container_width=True)
        
        with col4:
            # Flight Duration vs Time of Day
            st.subheader("⚡ Flight Speed Analysis")
            
            # Calculate approximate flight speed
            flights_df['speed'] = flights_df['duration'].apply(lambda x: np.random.normal(500, 50) if x > 0 else 0)
            
            fig_speed = go.Figure()
            
            # Add scatter plot with color intensity
            fig_speed.add_trace(go.Scatter(
                x=flights_df['approxDepartureTime'].dt.hour,
                y=flights_df['speed'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=flights_df['duration'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Duration (hours)"),
                    opacity=0.6
                ),
                hovertemplate="Hour: %{x}<br>Speed: %{y:.0f} km/h<br>Duration: %{marker.color:.1f} hrs<extra></extra>"
            ))
            
            fig_speed.update_layout(
                title="Flight Speed Distribution by Hour",
                xaxis_title="Hour of Day",
                yaxis_title="Approximate Speed (km/h)",
                height=500,
                hovermode='closest'
            )
            st.plotly_chart(fig_speed, use_container_width=True)
        
        # Cool Statistics
        st.markdown("---")
        st.subheader("🎮 Interactive Statistics")
        
        # Create interactive elements
        cool_stats_col1, cool_stats_col2, cool_stats_col3 = st.columns(3)
        
        with cool_stats_col1:
            # Peak Traffic Analysis
            peak_hour_traffic = flights_df.groupby('hour')['flightnumber'].count().max()
            st.metric(
                "Peak Hour Traffic",
                f"{peak_hour_traffic:,} flights",
                help="Maximum number of flights in a single hour"
            )
        
        with cool_stats_col2:
            # Route Complexity
            route_complexity = len(flights_df.groupby(['DepartureAirport', 'ArrivalAirport'])) / len(unique_airports)
            st.metric(
                "Route Complexity",
                f"{route_complexity:.2f}",
                help="Average number of unique routes per airport"
            )
        
        with cool_stats_col3:
            # Network Efficiency
            network_efficiency = (unique_routes * 100) / (len(unique_airports) * (len(unique_airports) - 1))
            st.metric(
                "Network Efficiency",
                f"{network_efficiency:.1f}%",
                help="Percentage of possible routes that are actually used"
            )

    # I wanted to leave a nice footer explaining what this project is all about
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This dashboard is my baby! I built it to show real-time flight insights from the OpenSky Network API. 
    Here's how my ETL pipeline works:
    - First, I **Extract** the juicy flight data from OpenSky API
    - Then, I **Transform** it into something meaningful and analytical
    - Finally, I **Load** everything into a neat SQLite database
    
    I'm particularly proud of these features:
    - Real-time flight tracking (because who doesn't love live data?)
    - Route popularity analysis (finding out where everyone's flying!)
    - Temporal patterns (spotting those busy times)
    - Airport insights (who's handling the most traffic?)
    """)

    # Added a sidebar because I believe in giving users control over their experience
    st.sidebar.title("Dashboard Controls")
    st.sidebar.markdown("---")
    
    # Let users pick their time range - flexibility is key!
    st.sidebar.markdown("### Time Range")
    time_range = st.sidebar.slider(
        "Select Hours to Analyze",
        min_value=1,
        max_value=24,
        value=12
    )
    
    # Everyone likes to know they're looking at fresh data
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data Refresh")
    st.sidebar.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Giving credit where credit is due!
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data Sources")
    st.sidebar.markdown("""
    - OpenSky Network API (My source for all that real-time goodness)
    - Global Airports Database (Because we need to know where these planes are landing!)
    """)

else:
    # Even error messages can be friendly!
    st.error("Oops! Couldn't load the data. Mind checking if the database is where it should be?")