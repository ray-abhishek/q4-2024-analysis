import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

def load_data(file_path):
    # Read CSV with first row as header
    df = pd.read_csv(file_path, header=0)
    
    # Convert date columns safely
    date_columns = ['Created', 'Completed', 'Updated', 'Started']
    for col in date_columns:
        try:
            df[col] = pd.to_datetime(df[col], format='ISO8601', errors='coerce')
        except Exception as e:
            print(f"Error converting {col}: {e}")
            df[col] = pd.NaT
    
    # Calculate cycle time only for completed items
    df['Cycle Time'] = None
    mask = ~(df['Created'].isna() | df['Completed'].isna())
    df.loc[mask, 'Cycle Time'] = (df.loc[mask, 'Completed'] - df.loc[mask, 'Created']).dt.total_seconds() / (24 * 60 * 60)

    return df

def analyze_task_types(df):
    # Create task type column
    df['Task Type'] = df['Labels'].apply(lambda x: 
        'Bug' if any(label in str(x).lower() for label in ['bug', 'eoc-bug']) 
        else ('Feature' if 'feature' in str(x).lower() or 'enhancement' in str(x).lower()
        else ('Tech Initiative' if any(label in str(x).lower() for label in ['eoc-improvement', 'tech-internal'])
        else 'Other')))
    
    # Filter data for specific sprints
    df_filtered = df[df['Cycle Name'].isin(['OCT-S-1 / CY', 'OCT-S-2', 'NOV-S-1', 'NOV-S-2', 'DEC-S-1', 'DEC-S-2', 'DEC-S-3'])]
    
    # Task distribution over sprints
    task_dist = pd.crosstab(df_filtered['Cycle Name'], df_filtered['Task Type'])
    return px.bar(task_dist, 
                 title="Task Distribution by Type per Sprint",
                 barmode='stack')

def analyze_spillover(df):
    # Identify spillover tasks (tasks that appear in multiple sprints)
    spillover = df[df['Labels'].str.contains('spillover', case=False, na=False)]
    spillover_by_sprint = spillover.groupby('Cycle Name').size()
    return px.line(spillover_by_sprint, 
                  title="Spillover Tasks Trend")

def get_dev_trivia(df, dev_email):
    trivia = {
        "average_cycle_time": f"Average completion time: {df[df['Assignee']==dev_email]['Cycle Time'].mean():.1f} days",
        "favorite_priority": f"Favorite priority: {df[df['Assignee']==dev_email]['Priority'].mode().iloc[0]}",
        "busiest_sprint": f"Busiest in: {df[df['Assignee']==dev_email]['Cycle Name'].mode().iloc[0]}",
        "most_common_type": f"Specializes in: {df[df['Assignee']==dev_email]['Task Type'].mode().iloc[0]}"
    }
    return trivia

def create_dev_tabs(df):
    st.header("👩‍💻 Developer Deep Dive")
    
    # Get unique developers, handle missing or non-string assignees
    devs = df['Assignee'].dropna().astype(str).unique()
    
    # Remove specific assignees and non-email values
    devs = [dev for dev in devs if dev not in ['asignee@domain.com', 'rahul.kalashetti@urbanpiper.com', 'zaid.ansari@urbanpiper.com'] and '@' in dev]
    
    # Create tabs
    tabs = st.tabs([email.split('@')[0] for email in devs])
    
    for idx, dev in enumerate(devs):
        with tabs[idx]:
            dev_df = df[df['Assignee'] == dev]
            
            # Fun Trivia
            trivia = get_dev_trivia(df, dev)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🎯 Fun Facts")
                for fact in trivia.values():
                    st.write(fact)
            
            # Tasks Table
            st.subheader("📝 Tasks")
            if 'Created' in dev_df.columns:
                dev_df = dev_df.sort_values('Created', ascending=False)
            st.dataframe(
                dev_df[['ID', 'Title', 'Status', 'Priority', 'Cycle Name', 'Labels']],
                use_container_width=True,
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Priority": st.column_config.TextColumn("Priority", width="small"),
                    "Cycle Name": st.column_config.TextColumn("Sprint", width="medium"),
                    "Labels": st.column_config.TextColumn("Labels", width="medium"),
                }
            )

def create_dashboard():
    st.title("Menu Squad Q4 2024 Sprint Analysis 🚀")
    
    # Load data
    df = load_data('menu_q4_sprints.csv')
    
    # Sprint Overview
    st.header("Sprint Performance")
    fig_task_types = analyze_task_types(df)
    st.plotly_chart(fig_task_types)

    # Team Member Analysis
    st.header("Team Member Insights")
    assignee_counts = df['Assignee'].value_counts()
    fig_team = px.pie(values=assignee_counts.values, 
                      names=assignee_counts.index,
                      title="Task Distribution Across Team")
    st.plotly_chart(fig_team)

    # Priority Analysis
    col1, col2 = st.columns(2)
    with col1:
        priority_counts = df['Priority'].value_counts()
        fig_priority = px.pie(values=priority_counts.values,
                            names=priority_counts.index,
                            title="Priority Distribution")
        st.plotly_chart(fig_priority)

    # Fun Stats
    st.header("🎉 Fun Team Stats")
    col4, col5 = st.columns(2)

    with col4:
        most_eoc_bugs = df[df['Labels'].str.contains('eoc-bug', case=False, na=False)]['Assignee'].value_counts().idxmax()
        st.metric("Most EOC Bugs", most_eoc_bugs.split('@')[0])

    with col5:
        most_features = df[df['Labels'].str.contains('feature', case=False, na=False)]['Assignee'].value_counts().idxmax()
        st.metric("Most Feature Work", most_features.split('@')[0])

    # Add developer tabs section
    create_dev_tabs(df)

if __name__ == "__main__":
    create_dashboard()