# IFRS-9-Modelling

The purpose of this project is to develop a fully automated IFRS 9 impairment model that computes expected credit losses (ECLs) for banks and microfinancing entities. 

The three core ECL parameters are the Probability of Default (PD), the Loss Given Default (LGD), and the Exposure at Default (EAD). Additionally, the effect(s) of Macroeconomic information (Forward-Looking Information) is modeled.

The Probability of Default is modeled using a transition matrix approach. The base transition matrix is determined from monthly or quarterly historical loan book positions. The 12-month and lifetime PDs are then obtained from the n-step transition matrices. Forward-looking information is then used to determine a macroeconomic adjustment factor that is applied to the PDs.

The Loss Given Default is modeled and can be calibrated with considerations for the following:
- collateral types,
- discounted collateral values,
- market and entity haircut assumptions,
- time to realization
- cash recoveries and
- cure rates

Finally, the EAD is modeled using an amortization approach accounting for loan repayment frequency and the nature of the facility - on-balance sheet facilities vs off-balance sheet facilities.
