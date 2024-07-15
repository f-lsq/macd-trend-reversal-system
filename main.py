
# MACD Trend Reversal Trading System (18 MAR 2023)

import pandas as pd
import queue
import statistics

def select_method():
    """
    Allows user to select either the SSMA or EMA method to calculate the MACD histogram.

    Returns:
        ma_choice (int): Choice of calculation method
    """
    print("\nWhich method would you like to use in your computation of the MACD histogram?")
    print("- Method 1: Standard Simple Moving Average (SSMA)")
    print("- Method 2: Exponential Moving Average (EMA)")
    while True:
        ma_choice = input("Enter your choice: ")
        if ma_choice.isdigit() and int(ma_choice) in [1, 2]:
            return int(ma_choice)
        else:
            print("- ERROR: Please only enter digits 1 or 2.")

def select_excel_file():
    """
    Allows user to select the financial excel data file to be used.

    Returns:
        new_df (pandas.dataframe): Dataframe from excel file selected, with "null" values removed
    """
    print("\nPlease enter the path to the financial excel file of your choice.")
    while True:
        file_path = input ("(e.g C:/Users/Name/Downloads/File_Name.csv): ")
        if file_path.endswith(('.csv','.xlsx')):
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path, skipinitialspace = True)
                else:
                    df = pd.read_excel(file_path, engine='openpyxl')
                
                new_df = df.dropna().copy()

                if file_path.endswith('.xlsx'):
                    new_df.columns = new_df.iloc[0]  
                    new_df = new_df[1:]
                new_df["Date"] = pd.to_datetime(new_df["Date"], errors='coerce')
                new_df_sorted = new_df.sort_values("Date").reset_index(drop=True)

                return new_df_sorted
            
            except:
                print("The file path may be incorrect. Please enter the file path again.")
        else:
            print("The file should be in .csv or .xlsx format. Please enter the file path again.")
        
def calculate_sma(price_macd_list, sma_period):
    """
    Calculates Simple Moving Average (SMA) for the given list of prices.

    Parameters:
        price_macd_list (list): List of closing prices and MACD lines
        sma_period (int): Period for which SMA is to be calculated

    Returns:
        A list of SMA values (list)
    """
    sma_queue = queue.Queue(sma_period)
    sma_list = []
    for each in price_macd_list:
        sma_queue.put(each)
        if sma_queue.full():
            sma_value = statistics.mean(list(sma_queue.queue))
            sma_list.append(sma_value)
            sma_queue.get()
    
    return sma_list

def calculate_ema(price_macd_list, ema_period):
    """
    Calculates Exponential Moving Average (EMA) for the given list of prices.

    Parameters:
        price_macd_list (list): List of closing prices and MACD lines
        ema_period (int): Period for which EMA is to be calculated

    Returns:
        A list of EMA values (list)
    """
    ema_k = 2/(ema_period+1)
    
    ema_queue = queue.Queue(ema_period)
    ema_list = []
    for price_macd in price_macd_list:
        ema_queue.put(price_macd)
        if ema_queue.full():
            ema_value = statistics.mean(list(ema_queue.queue))
            ema_list.append(ema_value)
            break
    
    ema_count = 0
    for each in price_macd_list[ema_period:]:
        ema_value = each * ema_k + (ema_list[ema_count] * (1 - ema_k))
        ema_list.append(ema_value)
        ema_count += 1
    
    return ema_list

def create_ma_list(price_macd_list, ma_period, method):
    """
    Create a list storing the values for short, long and nine moving-averages.

    Parameters:
        price_macd_list (list): List of closing prices and MACD lines
        ma_period (int): Respective periods for MA calculation
        method (int): Method for MA calculation

    Returns:
        ma_list (list): List of moving averages
    """
    if method == 1:
        ma_list = calculate_sma(price_macd_list, ma_period)
    elif method == 2:
        ma_list = calculate_ema(price_macd_list, ma_period)
    return ma_list

def calculate_macd_histo(dataframe, shortma_period, longma_period, ninema_period, method):
    """
    Calculates MACD histogram for a given dataframe using either the SMA or EMA method.

    Parameters:
        dataframe (pandas.dataFrame): Dataframe from excel file selected
        shortma_period (int): Short-term period for MA calculation
        longma_period (int): Long-term period for MA calculation
        ninema_period (int): Nine-term period for MA calculation
        method (int): Method for MA calculation

    Returns:
        closing_date_list (list): List of closing prices
        closing_price_list (list): List of closing dates
        macd_histo_list (list): List of MACD histogram calculated
    """
    # Retrieve closing stock prices and date from excel file and store them in lists
    closing_price_list = dataframe["Close"].tolist()
    closing_date_list = dataframe["Date"].tolist()
    
    shortma_list = create_ma_list(closing_price_list, shortma_period, method)
    shortma_list = shortma_list[longma_period-shortma_period:] 

    longma_list = create_ma_list(closing_price_list, longma_period, method)

    # MACD line calculation and list generation
    macd_line_list = [shortma_value - longma_value for shortma_value, longma_value in zip(shortma_list, longma_list)]

    ninema_list = create_ma_list(macd_line_list, ninema_period, method)
    
    # Slicing the macd_line_list, such that its length = that of ninema_list (For calculation of MACD histogram)
    macd_line_list = macd_line_list[ninema_period-1:] 

    # MACD line calculation and list generation
    macd_histo_list = [macd_line_value - ninema_value for macd_line_value, ninema_value in zip(macd_line_list, ninema_list)]

    # Slice the lists so that their length match with that of MACD histogram 
    closing_date_list = closing_date_list[longma_period-1+ninema_period-1:]
    closing_price_list = closing_price_list[longma_period-1+ninema_period-1:]
    
    return {"closing_date_list": closing_date_list,
            "closing_price_list": closing_price_list,
            "macd_histo_list": macd_histo_list           
            }

def identifybuysellsignal_macd(macd_histo_dict, capital, commission):
    """
    Identifies buy or sell signal on each trading day, and return the final capital and number of trades done.
    This is under the MACD method.

    Parameters:
        macd_histo_dict (dict): Dictionary containing the closing date list (list), closing price list (list) and macd histogram list (list)
        capital (int): Initial capital amount, before any trade is done
        commission (float): Commission rate per trade done

    Returns:
        no_of_trade (int): Number of trades done for the entire period
        capital (int): Final capital amount, after all trade is completed
    """
    
    # To determine whether the trader is holding on to the stock (position)
    # - position = 0, means that the trader is not holding on to any asset 
    # - position = 1, means that the trader is holding on to an asset
    position, no_of_trade = 0, 0
    print("\nHere are the trading days where there are buy or sell signals:")

    for each in range(len(macd_histo_dict["macd_histo_list"])):

        # Buy Signal for first MACD histogram calculated and subsequent ones
        if (each == 0 and macd_histo_dict["macd_histo_list"][each] > 0) or (macd_histo_dict["macd_histo_list"][each] > 0 and macd_histo_dict["macd_histo_list"][each-1] <= 0 and position == 0):
            position = 1
            print("- [{}] Buy at ${:.2f}.".format(macd_histo_dict["closing_date_list"][each], macd_histo_dict["closing_price_list"][each]))

            no_of_shares = capital * (1 - commission) / macd_histo_dict["closing_price_list"][each]
            capital = 0

        # Sell Signal for subsequent MACD histogram and last histogram calculated
        elif (each == len(macd_histo_dict["macd_histo_list"])-1 and position == 1) or (macd_histo_dict["macd_histo_list"][each] < 0 and macd_histo_dict["macd_histo_list"][each-1] >= 0 and position == 1):
            position = 0
            print("- [{}] Sell at ${:.2f}.".format(macd_histo_dict["closing_date_list"][each], macd_histo_dict["closing_price_list"][each]))

            capital += no_of_shares * macd_histo_dict["closing_price_list"][each] * (1 - commission)
            no_of_shares = 0 
            no_of_trade += 1

    return no_of_trade, capital

def identifybuysellsignal_buyholdsell(dataframe, capital, commission):
    """
    Identifies buy or sell signal at the start and end of the trading period, and return the final capital.
    This is under the BUY-HOLD-SELL method.

    Parameters:
        dataframe (pandas.dataFrame): Dataframe from excel file selected
        capital (int): Initial capital amount, before any trade is done
        commission (float): commission rate per trade done

    Returns:
        capital (int): Final capital amount, after all trade is completed
    """
    closing_price_list = dataframe["Close"].tolist()
    no_of_shares = capital * (1 - commission) /closing_price_list[0]
    capital = 0
    capital += no_of_shares * closing_price_list[len(closing_price_list)-1] * (1 - commission)
    return capital

def currency_message(currency_amount):
    """
    Formats and return a string value corresponding to the currency amount.

    Parameters:
        currency_amount (float): Monetary value, can be positive or negative

    Returns:
        (str): String value corresponding to the respective currency amount, formatted accordingly
    """
    if currency_amount < 0:
        return f"-${-currency_amount:,.2f}"
    else:
        return f"${currency_amount:,.2f}"

def MACD_system(shortma_period, longma_period, ninema_period, initial_capital, commission_rate):
    """
    Main MACD trend reversal program.

    Parameters:
        shortma_period (int): Short-term period for MA calculation
        longma_period (int): Long-term period for MA calculation
        ninema_period (int): Nine-term period for MA calculation
        initial_capital (int): Initial capital before any trade is done
        commission_rate (float): Commision rate paid in each trade (Incurred twice per buy-sell trade)
    """
    print("Welcome to the MACD trend reversal system!")
    while True:

        ma_choice = select_method()
        excelfile_df = select_excel_file()
        macd_histo_dict = calculate_macd_histo(excelfile_df, shortma_period, longma_period, ninema_period, ma_choice)
        no_of_trade, final_capital_macd = identifybuysellsignal_macd(macd_histo_dict, initial_capital, commission_rate)
        final_capital_buyholdsell = identifybuysellsignal_buyholdsell(excelfile_df, initial_capital, commission_rate)

        avg_return_per_trade = (final_capital_macd - initial_capital) / no_of_trade
        relative_income = final_capital_macd - final_capital_buyholdsell

        print("\nFinal capital amount: {}".format(currency_message(final_capital_macd)))
        print("Total number of trades made using MACD: {}".format(no_of_trade))
        print("Average return per trade using MACD: {}".format(currency_message(avg_return_per_trade)))
        print("Relative gain or loss against a long-term Buy-Hold-Sell strategy: {}".format(currency_message(relative_income)))
    
        print("\nWould you like to use another method or excel file?")
        continue_analysis = input("(Enter @ to stop the program, any button to continue) ")
        if continue_analysis == "@":
            break
        
    print("\nThank you for using the MACD trend reversal system. Goodbye!\n")


# ==================== Main Body ==================== #

shortma_period = 12
longma_period = 26
ninema_period = 9
initial_capital = 100000
commission_rate = 0.125/100 # 7/8 percent per trade

MACD_system(shortma_period, longma_period, ninema_period, initial_capital, commission_rate)