# portfolio/stock.py
"""
Provides a powerful interface to access, manage, visualize and store data about a stock

This module contains the following classes:
    -`Stock(ticker, displayCurrency=None, baseSaveDirectory=None, isJSE=False, *args, **kwargs)` - Powerful interface that allows you to access, manage, visualize and store data about a stock.

The Stock class contains the following instance methods:
    -`stock_purchase_history`
"""

import pandas as pd
import datetime as dt 
import os
import json
import pathlib

from yfinance import Ticker
from typing import Union
from currency_converter import CurrencyConverter
from matplotlib import pyplot as plt
from matplotlib import dates as mpl_dates


class Stock(Ticker):
    """
    Powerful interface to access, manage, visualize and store data about a stock.
    It inherits from the Ticker class of the yfinance package.

    Args:
        Ticker: The stock symbol of the company that you want to interact with. It can be in all CAPS or in small CAPS
        displayCurrency: The currency in which all the money related data will be displayed in
        baseSaveDirectory: The base/main directory that will store all the saved details of the stock
        isJSE: Whether the stock is from the JSE market
    """
    # object that has enables you to convert a value between two currencies
    currencyConverter = CurrencyConverter()
    
    # Keys for the dictionary returned by the cleanInfo method
    cleanInfoKeys = ['sector', 'zip', 'fullTimeEmployees', 'longBusinessSummary', 'city', 'phone', 'country', 'website', 'address1', 'address2', "fax", "industry", "recommendationKey", "financialCurrency", "exchange", "shortName", "longName", "exchangeTimezoneName", "symbol", "logo_url"]
    
    # details stored about every purchase made to the stock
    stockPurchaseHistoryColumns = ["DateofPurchase", "PurchasePrice", "StocksPurchased", "StockPrice", "Currency"]
    roguePurchaseHistoryColumns = stockPurchaseHistoryColumns[1:]
    
    
    def __init__(self, ticker: str, displayCurrency: str =None, baseSaveDirectory: Union[str, os.PathLike]=None, isJSE: bool=False, *args, **kwargs):
        super().__init__(ticker, *args, **kwargs)
        
        # Populating attributes that are based on arguments with default values
        #self.displayCurrency = displayCurrency if displayCurrency else self.info["financialCurrency"]
        self.baseSaveDirectory = os.path.normpath(baseSaveDirectory) if baseSaveDirectory else None
        self.isJSE = isJSE

        # Directory for the Cashflow, BalanceSheet and income Statements of the stock 
        self.cashflowSaveDirectory = os.path.normpath(os.path.join(self.baseSaveDirectory,"cashflow")) if baseSaveDirectory else None
        self.incomestatementSaveDirectory = os.path.normpath(os.path.join(self.baseSaveDirectory, "incomestatement")) if baseSaveDirectory else None
        self.balancesheetSaveDirectory = os.path.normpath(os.path.join(self.baseSaveDirectory, "balancesheet")) if baseSaveDirectory else None

        # Path to the file containing the deprecated return value of the info method from the base class Ticker
        self._StockInfoFilePath = os.path.normpath(os.path.join(self.baseSaveDirectory, "StockInfo.json")) if baseSaveDirectory else None

        # Path to the file containing the purchase history made to the stock
        self._StockPurchaseHistoryFilePath = os.path.normpath(os.path.join(self.baseSaveDirectory, "stockPurchaseHistory.json")) if baseSaveDirectory else None
        
        # Path to the file containing the purchases that were made to the stock but do not have a purchase date recorded
        self._RogueStockHoldingsFilePath = os.path.join(self.baseSaveDirectory, "rogueHoldings.json") if baseSaveDirectory else None

    
    def loadDirectories(self):
        """This function creates the necessary directories for storing data about the stock

        Raises:
            ValueError: If the base directory is not provided during initialization
        """
        
        if self.baseSaveDirectory:
            
            # Getting the keys to directory based attributes
            directoryAttributeKeys = [x for x in self.__dict__.keys() if x.endswith("Directory")]

            # Creating the directories 
            for key in directoryAttributeKeys:
                
                # Accessing the path created from initialization
                directory = self.__dict__[key]
                
                # Checking if directory already exist
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    
        else:
            raise ValueError(f"No base directory for storing the data was provided. self.baseSaveDirectory = {self.baseSaveDirectory}")        
        
    
    @property
    def stock_purchase_history(self) -> pd.DataFrame:
        """This function will return a pandas data frame object of the details about the purchases made to the stock, if the stock does not have a purchase history then it will raise an exception

        Returns:
            pd.DataFrame: the details about the purchases made to the stock
        """
        
        # creating an empty pandas data frame with headings only
        df = pd.DataFrame(columns=self._stockPurchaseHistoryColumns)  
        
        # check if json data table exists
        if os.path.exists(self._StockPurchaseHistoryFilePath):
            # Load the json data table into a pandas data frame
            try:
                df = pd.read_json(self._StockPurchaseHistoryFilePath)
                
            except ValueError: # if the json data table is not empty   
                return df           
            
            # Converting the dates into datetime objects
            df["DateofPurchase"] = [dt.datetime.strptime(date, "%Y-%m-%d") for date in df["DateofPurchase"] if date]
            
            # making the dates into the data frame indexes
            df.set_index("DateofPurchase", inplace=True)
            
            return df
        
        else:
            return df
    
    @property
    def rogueHoldings(self) -> pd.DataFrame:
        """Existing tocks holdings that dont have a purchase date

        Returns:
            pd.DataFrame: data frame object containing the rogue holdings
        """
        
        # creating an empty pandas data frame with headings only
        df = pd.DataFrame(columns=[colum for colum in self._stockPurchaseHistoryColumns if not colum == "DateofPurchase"]) 
        
        # check if json data table exists
        if os.path.exists(self._RogueStockHoldingsFilePath):
            # Load the json data table into a pandas data frame
            try:
                df = pd.read_json(self._RogueStockHoldingsFilePath)
                
            except ValueError: # if the json data table is not empty    
                return df
            
            return df
        
        else:  
            return df
        
    @property
    def purchaseValue(self) -> float:
        """ This function will return the total sum of money invested into the stock

        Returns:
            float: total sum of money invested into the stock
        """
        # loading the purchase history
        df = self.stock_purchase_history
        
        # loading the rogue purchase history
        rogue_df = self.rogueHoldings
        
        # adding the purchases of made to the stock
        purchaseValue = 0
        for value, currency in rogue_df[["PurchasePrice", "Currency"]].values: # Rogue purchases
            if(currency != self.displayCurrency):
                purchaseValue += self.currencyConverter.convert(amount=value, currency=currency, new_currency=self.displayCurrency)
            else:
                purchaseValue += value
        
        for value, currency in df[["PurchasePrice", "Currency"]].values: # recorded purchases
            if(currency != self.displayCurrency):
                purchaseValue += self.currencyConverter.convert(amount=value, currency=currency, new_currency=self.displayCurrency)
            else:
                purchaseValue += value
        
        return purchaseValue
    
    @property
    def _numberofpurchases(self) -> int:
        """        
        Returns:
            int: The number of purchases made to the stock
        """
        numberofpurchases = 0
        return self.stock_purchase_history
        # getting the number of recorded purchases
        numberofpurchases += self.stock_purchase_history.shape[0]
        
        # getting the number of rogue purchases
        numberofpurchases += self.rogueHoldings.shape[0]
        
        return numberofpurchases
        
    @property
    def shares(self) -> float:
        """This function will return the number of shares owned in the company and if purchase history data table does not exist an exception will raised

        Returns:
            float:  the number of shares owned in the company
        """ 
        # loading the purchase history
        df = self.stock_purchase_history
        
        # loading the rogue purchase history
        rogue_df = self.rogueHoldings
        
        # adding the stocks owned in the stock
        stocks = 0
        for value in rogue_df["StocksPurchased"].values: # Rogue purchases
            stocks += value
        
        for value in df["StocksPurchased"].values: # recorded purchases
            stocks += value
        
        return stocks
        
    @property
    def saveCashFlow(self):
        """
            Saves the cash flow statement of the stock in a csv or json file
        """

    @property
    def saveBalanceSheet(self):
        """
            Saves the Balance sheet of the stock in a csv or json file
        """

    @property
    def saveIncomeStatement(self):
        """
            Saves the income statement of a stock in a csv or json file
        """

    @property
    def returnOnInvestment(self) -> float:
        """
            returns the profit/loss of the investment relative to your purchase
        """

    @property
    def financial_analysis(self) -> dict:
        """
            returns the financial analysis of the stock based on the latest yearly financial statement
        """

    @property
    def quarterly_financial_analysis(self) -> dict:
        """
            returns the financial analysis of the stock based on the latest quarterly financial statement
        """

    def cleanInfo(self, updated: bool=False) -> dict:
        """
            (args) updated: determines whether to return stored data or get new data from api
            gets useful info about the stock
        """

        if updated or not(os.path.exists(self._StockInfoFilePath)):
            # Saving updated data
            self.saveCleanInfo()
            
            # getting the updated data            
            return self.cleanInfo(updated=False)

        else:
            # Returning the stored data, if updated is false
            with open(self._StockInfoFilePath, 'r') as file:
                data = json.load(file)

            return data        

    def __JSE_YAHOO_CORRECTION(self, stockHistory):
        """
            Corrects the price data of JSE stocks from yahoo finance
        """
        # Correcting Open price data
        stockHistory['Open'] = [x*10**-2 for x in stockHistory['Open']]

        # Correcting High price data
        stockHistory['High'] = [x*10**-2 for x in stockHistory['High']]

        # Correcting Low price data
        stockHistory['Low'] = [x*10**-2 for x in stockHistory['Low']]

        # Correcting Close price data
        stockHistory['Close'] = [x*10**-2 for x in stockHistory['Close']]

        return stockHistory

    def history(self, *args, **kwargs) -> pd.DataFrame:
        # TODO: create a caching system
        if(self.isJSE):
            return self.__JSE_YAHOO_CORRECTION(super().history(*args, **kwargs))
        else:
            return super().history(*args, **kwargs)

    def saveCleanInfo(self, destination: str=None) -> bool:
        """
            (args) destination: defines the directory that the stock info will be stored in, defaults to the baseStockDataSaves
            saves the useful data about the stock in a json file in the base directory of the stock
        """

        # Confirming the destination of the directory
        destination = destination if not destination else self.baseStockDataDirectory

        # Creating the data storage variable
        info = self.info
        cleanInfo = { key:info[key] for key in self.cleanInfoKeys if info.get(key)}

        # Storing the data into json file
        with open(self._StockInfoFilePath, 'w') as file:
            json.dump(cleanInfo, file, indent=4)

        return os.path.exists(self._StockInfoFilePath)

    def graphStock(self, save: bool = False, show: bool = True, directory = None, *args, **kwargs):
        """
        arg: save -> bool: determines whether the graph will be saved to storage, defaults to false
        arg: show -> bool: determines whether the graph will be displayed or not, defaults to true
        arg: directory: the directory that the graph is going to be saved in, defaults to the stock's base directory

        This function graphs the price of the stocks for specific periods and intervals
        """
        # Getting the data that will be graphed
        data = self.history(*args, **kwargs)
        
        # Extracting the x value from the data
        x = data.index
        
        # extracting the y value from the data
        y = data["Close"]
        
        # ploting the data
        plt.plot_date(x, y, linestyle='solid')
        plt.gcf().autofmt_xdate()
        plt.show()
           
    def isCurrentPriceAvgDiscount(self, discount) -> bool:
        """
        arg: discount: a float that will be used to determine the criteria

        check whether the current price of the stock is a discount relative to the average purchase price you made towards the stock
        """
        # getting the number of payments made
    
    def addRoguePurchase(self, purchasePrice: float, stocksPurch: float, purchaseCurrency: str=None, save: bool=True) -> pd.DataFrame:
        """Updates the RoguePurchase history json data table

        Args:
            purchasePrice (float): The purchase price of the stock that was bought. Defaults to None.
            stocksPurch (float): number of stocks purchased. Defaults to None.
            purchaseCurrency (str, optional): the currency in which the transaction for buying the stock used. Defaults to None.
            save (bool, optional): whether to update the json data table. Defaults to True.

        Returns:
            pd.DataFrame: updated json data table of the rogue data or the new data table if save is false
        """
        # Defaulting the purchaseCurrency if no currency provided
        purchaseCurrency = purchaseCurrency if purchaseCurrency else self.displayCurrency
        
        # Currency correct purchase price
        converted_purchasePrice = self.currencyConverter.convert(purchasePrice, purchaseCurrency, self.cleanInfo()["financialCurrency"])
         
        # calculating the stock price of the stocks owned
        stockPrice = converted_purchasePrice / stocksPurch
        
        # Converting the stockPrice into the display currency 
        stockPrice = self.currencyConverter.convert(stockPrice, self.cleanInfo()["financialCurrency"] ,self.displayCurrency)
        
        # Converting the purchase price to the display currency
        purchasePrice = self.currencyConverter.convert(purchasePrice, purchaseCurrency, self.displayCurrency)
        
        # Creating the data frame that will be saved
        new_df = self.__createDataFrameForRoguePurchases(purchasePrice=purchasePrice, stocksPurch=stocksPurch, purchaseCurrency=self.displayCurrency, stockPrice=stockPrice)
        
        # Checking if the user wishes to save the data
        if save:
            # Saving the new data into memory
            self.__updateRoguePurchases(new_df)
            
            return self.rogueHoldings
        
        else:
            return self.rogueHoldings.append(new_df, ignore_index=True)
            
    def buyStock(self, dateOfpurch: dt.datetime, purchasePrice: float=None, stocksPurch: float=None, purchaseCurrency: str=None, save: bool=True):
        """
            if purchasePrice is'nt provided the function will use the stockspurch value and the date of puchase to estimate
            how much you own and if the stockspurch is not provided the funtion will use the purchaseprice and date of puchase to estimate
            how many stocks you own.
            
            Updates the purchase history of the stock, by storing the date of purchase of the stock and its price on that date, as well as the number of stocks bought and the price paid for that quantity.

            Parameters:
            -- purchasePrice: the money spent on a specific date to buy stock(s)
            -- dateOfpurch: the date at which the stock was bought, datetime object
            -- stocksPurch: the number of stocks purchased on the date
            -- purchaseCurrency: the currency used to purchase the stock, defaults to displayCurrency
        """

        # Defaulting the purchaseCurrency if no currency provided
        purchaseCurrency = purchaseCurrency if purchaseCurrency else self.displayCurrency

        # Getting the stocks financialCurrency
        financialCurrency = self.cleanInfo()["financialCurrency"]

        # Raise an ValueError if both stocksPurch and purchasePrice is not given
        if not (purchasePrice or stocksPurch):
            raise ValueError("Both stocksPurch and purchasePrice do not have a value. Please provide data for either one")

        # Acquire the stock price of the stock on the given date
        stockPrice = self.history(start=(dateOfpurch - dt.timedelta(days=2)), end=(dateOfpurch + dt.timedelta(days=2)), interval="1d")["Close"][dateOfpurch]

        # Calculating the purchase price of the stock if it is not given
        if not purchasePrice:
            purchasePrice = stocksPurch * stockPrice

            # Ensuring that the purchasePrice currency matches the display currency
            if financialCurrency != self.displayCurrency:
                purchasePrice = self.currencyConverter.convert(purchasePrice, financialCurrency, self.displayCurrency)

        # Calculating the stocks purchases if it is not given
        if not stocksPurch:
            # Ensuring that the purchase currency matches the stock financial currency
            converted_purchasePrice = purchasePrice
            if purchaseCurrency != financialCurrency:
                converted_purchasePrice = self.currencyConverter.convert(purchasePrice, purchaseCurrency, financialCurrency)

            stocksPurch = converted_purchasePrice / stockPrice

            # Ensuring that the purchasePrice currency matches the display currency
            if financialCurrency != self.displayCurrency:
                purchasePrice = self.currencyConverter.convert(purchasePrice, financialCurrency, self.displayCurrency)

        # Creating the dataframe that will be saved
        new_df = self.__createDataFrameforPurchaseHistory(DateofPurchase=dateOfpurch, PurchasePrice=purchasePrice, StocksPurchased=stocksPurch, StockPrice=stockPrice, Currency=self.displayCurrency)
            
        # Checking if the user wishes to save the data
        if save:            
            # Saving the new purchases
            self._updatePurchaseHistory(new_df)
            
            return self.stock_purchase_history
        
        else:
            return self.stock_purchase_history.append(new_df, ignore_index=True)
    
    def __createDataFrameforPurchaseHistory(self, DateofPurchase: dt.datetime, PurchasePrice: float, StocksPurchased: float, StockPrice: float, Currency:str) -> pd.DataFrame:
        """responsible for creating a data frame of the new purchase info

        Args:
            dateOfpurch (dt.datetime): the date that the stock was purchased
            purchasePrice (float): the price paid to purchase the stock(s)
            stocksPurch (float): the number of stocks purchased
            stockPrice (float): the price for a single stock on the date of purchase
            
        Returns:
            pd.DataFrame: pandas dataframe containing the new purchase data
        """
        
        # Creating a new dataframe
        df = pd.DataFrame({"DateofPurchase":[DateofPurchase.strftime("%Y-%m-%d")], "PurchasePrice":[PurchasePrice], "StocksPurchased":[StocksPurchased],"StockPrice":[StockPrice], "Currency":[Currency]})
        
        return df
    
    def __createDataFrameForRoguePurchases(self, purchasePrice: float, stocksPurch: float, purchaseCurrency: str, stockPrice: float) -> pd.DataFrame:
        """Creates a data frame that contains a single row of rogue purchase data

        Args:
            purchasePrice (float): The purchase price of the stock that was bought
            stocksPurch (float): number of stocks purchased
            purchaseCurrency (str): the currency in which the transaction for buying the stock used
            stockPrice (float): the price for the group of stock bought

        Returns:
            pd.DataFrame: of the single row of rogue purchase data
        """
        # Creating a new data frame
        df = pd.DataFrame({"PurchasePrice":[purchasePrice], "StocksPurchased":[stocksPurch],"StockPrice":[stockPrice], "Currency":[purchaseCurrency]})
        
        return df
    
    def _updatePurchaseHistory(self, new_df: pd.DataFrame) -> bool:
        """This code is responsible for saving the new purchase data into a data table containing the data history of the purchases made in the past

        Args:
            new_df (pd.DataFrame): the date frame containing the new purchase data

        Returns:
            bool: the updating of the file was successful or not
        """
        # load in the json file
        df = self.stock_purchase_history
            
        # getting the new data row
        new_df_row = new_df.iloc[0]
            
        # adding the new data and saving the updated data table
        df.append(new_df_row, ignore_index=True).to_json(self._StockPurchaseHistoryFilePath, indent=4)
            
        return os.path.exists(self._StockPurchaseHistoryFilePath)

    def __updateRoguePurchases(self, new_df: pd.DataFrame) -> bool:
        """responsible for updating the existing rogue data with new row

        Args:
            new_df (pd.DataFrame): the date frame containing the new rogue  data

        Returns:
            bool: whether the update is successful or not
        """
        # load in the json file
        df = self.rogueHoldings
            
        # getting the new data row
        new_df_row = new_df.iloc[0]
            
        # adding the new data and saving the updated data table
        df.append(new_df_row, ignore_index=True).to_json(self._RogueStockHoldingsFilePath, indent=4)
            
        return os.path.exists(self._RogueStockHoldingsFilePath)
    
if __name__ == '__main__':
    # stock = Stock("msft", baseSaveDirectory="C:/Users/lelet/Desktop(offline)/Personal Finacial Records/InvestmentPortfolio/InvestementTracker/AgentFinance", displayCurrency="ZAR")
    
    # if not os.path.exists(stock.baseStockDataDirectory):
    #     stock.loadDirectories()
    stock = Stock("msft")
    
    print(stock.displayCurrency)
        