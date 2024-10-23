# load dependencies

import pandas as pd
import numpy as np
#import plotly.express as px
import plotly.graph_objects as go
import plotly.io as io
#io.renderers.default = 'browser' #to ensure prints as expect
import dash
from dash import Dash, html, dcc, callback
from dash.dependencies import Input, Output
import plotly.express as px



# read file
filepath = 'https://raw.githubusercontent.com/christiebarron/dvc10-hr/refs/heads/main/data/raw/HRDataset_v14.csv'
hr_df = pd.read_csv(filepath) #encoding='utf-16')

# initial data wrangle  ##########################

# convert EmpID, ManagerID, deptid to string.
    # married, martial status, gender, emp status, fromdiv jobfair, recruitmentsource to unordered factor.
to_string = ['EmpID', 'MarriedID', 'DeptID', 'MarriedID', 'MaritalStatusID', 'GenderID', 'FromDiversityJobFairID', 'PositionID', 'ManagerID']
for var in to_string:
    hr_df[var] = hr_df[var].astype(str)

# performance score, satisfaction as ordered factor.
to_cat_ord = ['PerfScoreID', 'EmpSatisfaction']
for var in to_cat_ord:
    hr_df[var] = pd.Categorical(hr_df[var].astype(str), categories = ['1','2','3','4','5'], ordered = True)

# lastperformReview_date, DateofHire, DateofTermination as date object. 
to_date = ['LastPerformanceReview_Date', 'DateofHire', 'DateofTermination']
for var in to_date:
    hr_df[var] = pd.to_datetime(hr_df[var], format = '%m/%d/%Y')

#birthday as datetime object
hr_df['DOB'] = pd.to_datetime(hr_df['DOB'], format = '%m/%d/%y')

# Calculate a proxy for age
date_of_data_collection = pd.to_datetime('2019-02-07')
hr_df['Age'] = (hr_df['LastPerformanceReview_Date'] - hr_df['DOB']) /pd.Timedelta(days=365.25)
#hr_df['Age'] = (date_of_data_collection - hr_df['DOB']) /pd.Timedelta(days=365.25)

 #remove executive data for confidentiality
hr_df = hr_df[hr_df['Department'] != 'Executive Office'] # CIO

## Calculate BANs ===================
# Calculate BANs

def aggregate_var(df, column_name, var_type = 'continuous'):
    """
    Function that calculates the aggregation of a continuous or categorical variable for the BANs
    """

    res_list = []

    if var_type == 'continuous':
        res_list = df[column_name].mean(),df[column_name].median()
    elif var_type == 'categorical':
        length_no_miss = df[column_name].notna().sum()
        res_list = np.round((df[column_name].isin(['4', '5']).sum() / length_no_miss) * 100, 2), np.round((df[column_name].isin(['1','2','3']).sum() / length_no_miss) * 100, 2)
    elif var_type == 'count':
        res_list = df[column_name].notna().sum()

    return(res_list)

#count
EmpIDRes = len(hr_df.EmpID.unique())
#cont
EngagementSurveyRes = aggregate_var(df = hr_df, column_name = 'EngagementSurvey', var_type = 'continuous')
SalaryRes = aggregate_var(df = hr_df, column_name = 'Salary', var_type = 'continuous')
#cat
EmpSatisfactionRes = aggregate_var(df = hr_df, column_name = 'EmpSatisfaction', var_type = 'categorical')
PerfScoreIDRes = aggregate_var(df = hr_df, column_name = 'PerfScoreID', var_type = 'categorical')

## get dynamic fields  (unique values for dept and position) =========
dept_select = hr_df.Department.unique()
position_select = hr_df.Position.unique() #consider not providing executive positions here.


# CONVIENINCE FUNCTIONS #########################
#stacked bar
def satisfaction_stacked_fig(hr_df, 
                             filter_var = ['Department', 'EmpSatisfaction'],
                             group_var = ['Department']):

    # dynamic variables
    #filter_var = ['Department', 'EmpSatisfaction']
    #group_var = ['Department']

    #data wrangling
    satis_df_long = hr_df[filter_var].melt(id_vars = group_var, var_name = 'Question', value_name = 'Response')
    satis_df_clean = satis_df_long.groupby(by = ['Department', 'Question', 'Response']).size().reset_index(name = 'Count')
    total_counts = satis_df_clean.groupby(['Department', 'Question'])['Count'].transform('sum')
    satis_df_clean['Percentage'] = ((satis_df_clean['Count']/total_counts)*100).round(1)#.astype(str) + '%'
    satis_df_clean['Label'] = satis_df_clean['Percentage'].astype(str) + '%'
    #color
    satis_color = [px.colors.sequential.RdBu[i] for i in [2, 4, 5, 7, 9]]
    satis_color[2] = 'rgb(211, 211, 211)'

    #create figure
    satis_fig = px.bar(satis_df_clean, y='Department', x='Percentage', color='Response', title='Employee Satisfaction', 
                    color_discrete_sequence = satis_color,
                    text = 'Label', #add percent labels to the graph
                        template='plotly_white') #make the background white, not default light blue

    satis_fig.update_traces(texttemplate='%{text}', textposition='inside', insidetextanchor='middle')
    # Update the layout to make it a stacked bar chart
    satis_fig.update_layout(barmode='stack', xaxis_title='Percent of Responses', yaxis_title='Department', legend_title='Responses'
                    #remove background color
                    #plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    satis_fig.update_xaxes(showgrid=False)
    satis_fig.update_yaxes(showgrid=False)

    # Show the figure
    #satis_fig.show()

    return(satis_fig)

#egagement bar
def engagement_bar_fig(hr_df):

    engage_df = hr_df.groupby('Department')[['EngagementSurvey']].mean().reset_index().round(1)

    engage_fig = px.histogram(engage_df, x = 'EngagementSurvey', y = 'Department', title = 'Engagement by Department',
                            template='plotly_white',
                            #text = 'EngagementSurvey'
                            )
    engage_fig.update_layout(xaxis_title = 'Engagement')
    engage_fig.update_traces(marker_color = px.colors.sequential.RdBu[7])
    engage_fig.update_traces(text=engage_df['EngagementSurvey'], textposition='outside') #, marker=dict(color='blue', line=dict(color='darkblue', width=1.5)))
    #egage_fig.update_traces(marker = dict(color = satis_color[3]), line = dict(color = 'darkblue', width = 1.0))
    #egage_fig.show()
    return(engage_fig)

# gender pie
def gender_pie_fig(hr_df):

    gender_df = hr_df.groupby(by = 'GenderID').size().reset_index(name = 'Count')
    gender_total_counts = gender_df['Count'].sum()
    gender_df['Percentage'] = ((gender_df['Count']/gender_total_counts)*100).round(1)#.astype(str) + '%'
    gender_pie_fig = px.pie(gender_df, values = 'Count', names = 'GenderID', hole = .6, title = "Gender Composition",  
        color_discrete_sequence=[px.colors.qualitative.Pastel[5], px.colors.qualitative.Pastel[3]]
        )
    return(gender_pie_fig)


# RUN APP ##################


app = Dash()

app.layout = html.Div([
    html.H1(children='Employee Satisfaction', style={'textAlign':'center'}),
    dcc.Checklist(options = dept_select, #{'label' : dept, 'value': 'dept} for category in dept_select
                  value = dept_select, 
                  id='checklist-dept-selection'),
    dcc.Graph(id = 'satisfaction-bar-id'),
    dcc.Graph(id='gender-pie-id'),
    dcc.Graph(id = 'engagement-bar-id')
])

# update satisfaction chart based on checklist selection
@callback(
    Output('satisfaction-bar-id', 'figure'),
    Input('checklist-dept-selection', 'value')
)
def update_satisfaction_stacked_fig(selected_categories):
    filtered_df = hr_df[hr_df['Department'].isin(selected_categories)]
    fig3 = satisfaction_stacked_fig(filtered_df)
    return fig3



# update engagement chart based on checklist selection
@callback(
    Output('engagement-bar-id', 'figure'),
    Input('checklist-dept-selection', 'value')
)
def update_engagement_bar_fig(selected_categories):
    filtered_df = hr_df[hr_df['Department'].isin(selected_categories)]
    fig2 = engagement_bar_fig(filtered_df)
    return fig2

# Update pie chart based on checklist selection
@app.callback(
    Output('gender-pie-id', 'figure'),
    Input('checklist-dept-selection', 'value')
)
def update_gender_pie_fig(selected_categories):
    filtered_df = hr_df[hr_df['Department'].isin(selected_categories)]
    fig1 = gender_pie_fig(filtered_df)
    #fig = px.pie(filtered_df, values='Values', names='Category', title='Pie Chart')
    return fig1


if __name__ == '__main__':
    app.run(debug=True)
