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
filepath = 'https://github.com/christiebarron/dvc10-hr/blob/main/data/raw/HRDataset_v14.csv'
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

## get dynamic fields
dept_select = hr_df.Department.unique()
position_select = hr_df.Position.unique() #consider not providing executive positions here.


# RUN APP ##################


app = Dash()

app.layout = [
    html.H1(children='Employee Satisfaction', style={'textAlign':'center'}),
    dcc.Checklist(dept_select, dept_select, id='checklist-dept-selection'),
    dcc.Graph(id='graph-content')
]

@callback(
    Output('graph-content', 'figure'),
    Input('checklist-dept-selection', 'value')
)
def update_graph(value):
    EngagementSurveyAvg = hr_df[hr_df.Department==value]
    return px.histogram(EngagementSurveyAvg, x='EngagementSurvey', y='Department', histfunc = 'avg')

if __name__ == '__main__':
    app.run(debug=True)

