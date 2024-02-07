import pandas as pd
import numpy_financial as npf
import math


def periodic_rate(rate: float, periodicity: int) -> float:
    """Computes the periodic compound rate based on the input annual effective rate
    
    Parameters:
    - rate: annual effective interest rate
    - periodicity: the granularity to which to convert the annual rate to expressed as number of months per year i.e., 
    12 = monthly;
    4 = quarterly;
    2 = semi-annual;
    1 = annual  

    Returns:
    - nth_rate: the effective nth period rate
    
    """

    nth_rate = (1 + rate)**(1/periodicity) - 1
    return nth_rate


def loan_tenure(start_date: str, end_date: str) -> int:
    """Determine the loan tenure in months given the loan start and end dates
    
    Parameters:
    - start_date: Date string representing the loan start date
    - end_date: Date string representing the loan end date

    Returns:
    - tenure: the loan tenure in months as an integer

    """
    start = pd.to_datetime(start_date, dayfirst=False)
    end = pd.to_datetime(end_date, dayfirst=False)
    months = math.ceil((end - start).days / 365.25 * 12)
    return months


def loan_amortization_schedule(loan_amount: float, loan_duration: int, annual_rate: float, payment_frequency: int = 12) -> pd.DataFrame:
    """Create a loan amortization schedule for a given loan
    
    Parameters:
    - loan_amount: The outstanding loan balance
    - loan_tenure: The reamining expected time until fully repaid in years
    - annual_rate: The annual effective interest rate in decimal form e.g., 0.1 for 10%
    - payment_frequency: Interger representation of the frequency with which the loan is repaid i.e., total number of payments per year -> Default is monthly

    Returns:
    - amortization_schedule: DataFrame object containing the term structures for the Repayment Amount, Interest, Pricipal and Outstanding Balance
    
    """

    if payment_frequency not in set(range(0, 13)):
        raise ValueError("Payment Frequency must be integer value between 1 and 12")
    
    amortization_schedule = [loan_amount]
    principal_schedule = [0]
    interest_schedule = [0]
    payment_schedule = [0]
    payment = abs(round(npf.pmt(rate=periodic_rate(annual_rate, payment_frequency), nper=payment_frequency*loan_duration, pv=loan_amount), 2))
    counter = 1
    amount = loan_amount
    
    while round(amount, 0) > 0:

        if payment > amount:
            payment = round(amount * (1+periodic_rate(annual_rate, 12)), 2) + 0.001

        payment_schedule.append(payment) if not counter % int(12/payment_frequency) else payment_schedule.append(0)

        interest = round(amount * (periodic_rate(annual_rate, 12)), 2)
        interest_schedule.append(interest)

        principal = round(payment - interest, 2) if not counter % int(12/payment_frequency) else 0
        principal_schedule.append(principal)

        amount = round(amount * (1+periodic_rate(annual_rate, 12)) - payment, 2) if not counter % int(12/payment_frequency) else round(amount * (1+periodic_rate(annual_rate, 12)), 2)
        amortization_schedule.append(amount)

        counter +=1

    schedule_fin = pd.DataFrame({'Payment': payment_schedule,
                                'Interest': interest_schedule,
                                'Principal': principal_schedule,
                                'Outstanding Balance': amortization_schedule})
    
    return schedule_fin
