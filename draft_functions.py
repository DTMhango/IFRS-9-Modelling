import numpy as np
import pandas as pd


def df_lookup(df: pd.DataFrame, value_column: str, search_columm: str, return_column: str, value_not_found=None, new_column_name='lookup_result') -> pd.DataFrame:
    """Search for value column in search column and return the return column. Ensure no duplicates in search_column."""
    result = pd.merge(df, df[[search_columm, return_column]], how='left', left_on=value_column, right_on=search_columm, suffixes=('', '_return'))
    for col in result.columns:
        if 'return' not in col or search_columm in col:
            result = result.drop(col, axis=1)
    result.columns = [new_column_name]
    final_result = pd.concat([df, result], axis=1)
    return final_result.fillna(value_not_found)


def staging_4x4(dpd: int) -> int:
    """Assigns IFRS 9 Staging to loan facility based on Days Past Due value. Staging 4x4 is meant to be used for 4x4 transition matrices."""
    if dpd <= 30:
        stage = 'stage_1'
    elif dpd <= 60:
        stage = 'stage_2a'
    elif dpd <= 90:
        stage = 'stage_2b'
    else:
        stage = 'stage_3'
    return stage


def extract_pds(matrices_df: pd.DataFrame, matrix_size: int=3) -> tuple:
    """Extract the probabilities of default from the provided transition matrix dataframe. 
    
    df: MultiIndex dataframe containing cumulative pds for each loan segment -> Output from 'absorbing_state()'

    matrix_size: takes integer values 3 or 4 only representative of 3x3 or 4x4 transition matrices per user requirements -> Default = 3
    
    """

    if matrix_size == 3:
        stage_1_cumulative_dict = {}
        stage_1_marginal_dict = {}
        stage_2_cumulative_dict = {}
        stage_2_marginal_dict = {}

        for loan_segment in matrices_df.index.get_level_values('Loan Segment'):
            cumulative_pds_stage_1 = [np.linalg.matrix_power(matrices_df.loc[loan_segment], i)[0, 2] for i in range(1, 301)]
            cumulative_pds_stage_2 = [np.linalg.matrix_power(matrices_df.loc[loan_segment], i)[1, 2] for i in range(1, 301)]

            marginal_pds_stage_1 = [cumulative_pds_stage_1[i] if i == 0 else 
                                    cumulative_pds_stage_1[i] - cumulative_pds_stage_1[i-1] for i in range(0, len(cumulative_pds_stage_1))]
            marginal_pds_stage_2 = [cumulative_pds_stage_2[i] if i == 0 else
                                    cumulative_pds_stage_2[i] - cumulative_pds_stage_2[i-1] for i in range(0, len(cumulative_pds_stage_2))]
            
            stage_1_cumulative_dict[loan_segment] = cumulative_pds_stage_1
            stage_2_cumulative_dict[loan_segment] = cumulative_pds_stage_2
            stage_1_marginal_dict[loan_segment] = marginal_pds_stage_1
            stage_2_marginal_dict[loan_segment] = marginal_pds_stage_2

        df_stage_1_cuml = pd.DataFrame(stage_1_cumulative_dict)
        df_stage_2_cuml = pd.DataFrame(stage_2_cumulative_dict)

        df_stage_1_marg = pd.DataFrame(stage_1_marginal_dict)
        df_stage_2_marg = pd.DataFrame(stage_2_marginal_dict)

        return df_stage_1_cuml, df_stage_2_cuml, df_stage_1_marg, df_stage_2_marg

    elif matrix_size == 4:
        stage_1_cumulative_dict = {}
        stage_1_marginal_dict = {}
        stage_2a_cumulative_dict = {}
        stage_2b_cumulative_dict = {}
        stage_2a_marginal_dict = {}
        stage_2b_marginal_dict = {}

        for loan_segment in matrices_df.index.get_level_values('Loan Segment'):
            cumulative_pds_stage_1 = [np.linalg.matrix_power(matrices_df.loc[loan_segment], i)[0, 3] for i in range(1, 301)]
            cumulative_pds_stage_2a = [np.linalg.matrix_power(matrices_df.loc[loan_segment], i)[1, 3] for i in range(1, 301)]
            cumulative_pds_stage_2b = [np.linalg.matrix_power(matrices_df.loc[loan_segment], i)[2, 3] for i in range(1, 301)]

            marginal_pds_stage_1 = [cumulative_pds_stage_1[i] if i == 0 else 
                                    cumulative_pds_stage_1[i] - cumulative_pds_stage_1[i-1] for i in range(0, len(cumulative_pds_stage_1))]
            
            marginal_pds_stage_2a = [cumulative_pds_stage_2a[i] if i == 0 else
                                     cumulative_pds_stage_2a[i] - cumulative_pds_stage_2a[i-1] for i in range(0, len(cumulative_pds_stage_2a))]
            
            marginal_pds_stage_2b = [cumulative_pds_stage_2b[i] if i == 0 else
                                     cumulative_pds_stage_2b[i] - cumulative_pds_stage_2b[i-1] for i in range(0, len(cumulative_pds_stage_2b))]
            
            stage_1_cumulative_dict[loan_segment] = cumulative_pds_stage_1
            stage_2a_cumulative_dict[loan_segment] = cumulative_pds_stage_2a
            stage_2b_cumulative_dict[loan_segment] = cumulative_pds_stage_2b            
            stage_1_marginal_dict[loan_segment] = marginal_pds_stage_1
            stage_2a_marginal_dict[loan_segment] = marginal_pds_stage_2a
            stage_2b_marginal_dict[loan_segment] = marginal_pds_stage_2b

        df_stage_1_cuml = pd.DataFrame(stage_1_cumulative_dict)
        df_stage_2a_cuml = pd.DataFrame(stage_2a_cumulative_dict)
        df_stage_2b_cuml = pd.DataFrame(stage_2b_cumulative_dict)

        df_stage_1_marg = pd.DataFrame(stage_1_marginal_dict)
        df_stage_2a_marg = pd.DataFrame(stage_2a_marginal_dict)
        df_stage_2b_marg = pd.DataFrame(stage_2b_marginal_dict)

        return df_stage_1_cuml, df_stage_2a_cuml, df_stage_2b_cuml, df_stage_1_marg, df_stage_2a_marg, df_stage_2b_marg
    

def remaining_balance(A, i, p, num_payments, payment_interval):
    balance = A * (1 + i)**num_payments - (p * ((1 + i)**num_payments - 1) / i) 
    return balance

def loan_amortization_schedule(A, i, p, total_payments, payment_interval):
    schedule = []
    for payment_num in range(1, total_payments + 1):
        balance = remaining_balance(A, i, p, payment_num, payment_interval)
        schedule.append((payment_num, balance))
    return schedule
