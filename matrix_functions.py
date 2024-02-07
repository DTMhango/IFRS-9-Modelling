import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as pyo


def base_matrices(df: pd.DataFrame) -> pd.DataFrame:
    """Create the base transition matrices. Assumes dataframe is output from 'data_prep()[0]' or 'merged_recoveries'. See data_validation.py
    
    Returns:
    - transition matrix dataframe containing PDs TMs for each loan segment.
    
    """

    df = df[df['next_stage'] != 'exit']

    matrices = pd.crosstab(index=[df['loan_type'], df['current_stage']],
                           columns=[df['next_stage']],
                           values=df['out_balance'],
                           rownames=['Loan Segment', 'Current Stage'],
                           colnames=['Next Stage'],
                           aggfunc="sum",
                           margins=False,
                           dropna=False,
                           normalize='index')
    return matrices


def absorbing_state(matrices_df: pd.DataFrame, matrix_size: int=3) -> pd.DataFrame:
    """Creates the absorbing stage for stage 3 in 3x3 transition matrix dataframe.

    Parameters:
    - df: MultiIndex dataframe containing transition matrices for all identified loan segments -> Output of base_matrices function.
    - matrix_size: Integer value representing size of the transition matrix.

    Returns:
    - modified base transition matrix converting stage 3 to an absorbing state.
    
    """
    
    if matrix_size not in {3, 4}:
        raise ValueError("Invalid matrix size. Should be 3 or 4 only.")
    

    if matrix_size == 3:
        for loan_segment in matrices_df.index.get_level_values('Loan Segment').unique():
            matrices_df.loc[loan_segment].iloc[2] = (0, 0, 1)

    elif matrix_size == 4:
        for loan_segment in matrices_df.index.get_level_values('Loan Segment').unique():
            matrices_df.loc[loan_segment].iloc[3] = (0, 0, 0, 1)

    return matrices_df 


def extract_pds(matrices_df: pd.DataFrame, matrix_size: int=3) -> tuple:
    """Extract the probabilities of default from the provided transition matrix dataframe. 

    Parameters:    
    - df: MultiIndex dataframe containing cumulative pds for each loan segment -> Output from 'absorbing_state()'
    - matrix_size: Integer value representing size of the transition matrix.
    
    Returns:
    - tuple of cumulative and marginal PDs dataframes.

    """

    if matrix_size not in {3, 4}:
        raise ValueError("Invalid matrix size. Should be 3 or 4 only")
    
    stage_dicts = {stage: {"cumulative_dict": {}, "marginal_dict": {}} for stage in range(matrix_size - 1)}

    for loan_segment in matrices_df.index.get_level_values('Loan Segment').unique():
        for stage in range(matrix_size - 1):
            cumulative_pds = [np.linalg.matrix_power(matrices_df.loc[loan_segment], i)[stage, matrix_size -1] for i in range(1, 301)]

            marginal_pds = [cumulative_pds[i] if i == 0 else cumulative_pds[i] - cumulative_pds[i-1] for i in range(len(cumulative_pds))]

            stage_dicts[stage]['cumulative_dict'][loan_segment] = cumulative_pds
            stage_dicts[stage]['marginal_dict'][loan_segment] = marginal_pds

    df_cumulative = {f"non-default-{stage}-cumulative": pd.DataFrame(stage_dicts[stage]['cumulative_dict']) for stage in stage_dicts.keys()}
    df_marginal = {f"non-default-{stage}-marginal": pd.DataFrame(stage_dicts[stage]['marginal_dict']) for stage in stage_dicts.keys()}

    return tuple(df_cumulative.values()) + tuple(df_marginal.values())


def cure_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Function creates the transition matrix for cures and recoveries. If recoveries are not present in the dataset, returns df with cures only.

    Parameters:
    - df: cleaned dataframe containing cures and recoveries (or cures only if no recoveries observed) -> df is expected as output from ```merge_recoveries()``` or ```data_prep()```

    Returns:
    - dataframe containing cure rates and recovery rates (or cures only if no recoveries observed in the data)
    
    """
    if 'recoveries' in df.columns:
        cr_rr = np.identity(3)
        cr_rr[2, 0] = df.groupby('recoveries')['out_balance'].sum().loc['cured']
        cr_rr[2, 1] = df.groupby('recoveries')['out_balance'].sum().loc['recovered']
        cr_rr[2, 2] = df.groupby('recoveries')['out_balance'].sum().loc['stage_3']
        cr_rr = cr_rr/cr_rr.sum(axis=1, keepdims=1)
        
        rates = {'cure_rates': None, 'recovery_rates': None}

        cumulative_cure_rate = [np.linalg.matrix_power(cr_rr, i)[2, 0] for i in range(1, 301)]
        cumulative_recovery_rate = [np.linalg.matrix_power(cr_rr, i)[2, 1] for i in range(1, 301)]
        
        rates['cure_rates'] = [cumulative_cure_rate[i] if i == 0 else cumulative_cure_rate[i] - cumulative_cure_rate[i-1] for i in range(len(cumulative_cure_rate))]
        rates['recovery_rates'] = [cumulative_recovery_rate[i] if i == 0 else cumulative_recovery_rate[i] - cumulative_recovery_rate[i-1] for i in range(len(cumulative_recovery_rate))]

    else:
        cr = np.identity(3)
        cr[2, 0] = df.groupby('cures')['out_balance'].sum().loc['cured']
        cr_rr[2, 2] = df.groupby('recoveries')['out_balance'].sum().loc['stage_3']
        cr_rr = cr_rr/cr_rr.sum(axis=1, keepdims=1)
        
        rates = {'cure_rates': None}
        
        cumulative_cure_rate = [np.linalg.matrix_power(cr_rr, i)[2, 0] for i in range(1, 301)]

        rates['cure_rates'] = [cumulative_cure_rate[i] if i == 0 else cumulative_cure_rate[i] - cumulative_cure_rate[i-1] for i in range(len(cumulative_cure_rate))]

    return pd.DataFrame(rates)


def plot_rates(df: pd.DataFrame, name_of_file: str, main_title: str='Title', x_title: str='Time Period - Quarters', y_title: str='Probability of Default', x_range: int=100 ):
    """
    Function to plot the dataframe passed to it. Designed for plotting cumulative and marginal PDs as well as cure and recovery rates per loan segment.

    """
    df = df.head(x_range)
    data = [go.Scatter(x=df.index,
                    y=df[col],
                    mode='lines',
                    name=col) for col in df.columns]

    layout = go.Layout(title=main_title,
                    xaxis=dict(title=x_title),
                    yaxis=dict(title="Probability of Default"),
                    hovermode="closest")

    fig = go.Figure(data=data, layout=layout)
    
    return pyo.iplot(fig, filename=name_of_file)  # change between iplot and plot for embedded notebook plotting vs online plotting
