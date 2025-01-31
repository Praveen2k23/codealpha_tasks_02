import datetime
import json
import os
import yfinance as yf
from typing import Dict, Optional, Tuple


class StockAPI:
    @staticmethod
    def get_stock_data(symbol: str) -> Tuple[Optional[float], Optional[dict]]:
        """
        Fetch real-time stock data using Yahoo Finance API.
        Returns: Tuple of (current_price, stock_details).
        """
        try:
            stock = yf.Ticker(symbol)

            # Get real-time stock price
            current_price = stock.history(period="1d")["Close"].iloc[-1]  

            # Get company information
            company_data = {
                "Name": stock.info.get("longName", "N/A"),
                "Sector": stock.info.get("sector", "N/A"),
                "MarketCapitalization": stock.info.get("marketCap", "N/A"),
                "PERatio": stock.info.get("trailingPE", "N/A"),
                "DividendYield": stock.info.get("dividendYield", "N/A"),
                "52WeekHigh": stock.info.get("fiftyTwoWeekHigh", "N/A"),
                "52WeekLow": stock.info.get("fiftyTwoWeekLow", "N/A"),
            }

            return current_price, company_data

        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {e}")
            return None, None


class Stock:
    def __init__(self, symbol: str, shares: int, purchase_price: float, purchase_date: str):
        self.symbol = symbol.upper()
        self.shares = shares
        self.purchase_price = purchase_price
        self.purchase_date = purchase_date
        self.current_price = 0.0
        self.company_info = {}
        self.update_stock_data()

    def update_stock_data(self) -> None:
        """Update stock with real-time data."""
        price, company_info = StockAPI.get_stock_data(self.symbol)
        if price:
            self.current_price = price
        if company_info:
            self.company_info = company_info

    def to_dict(self) -> dict:
        """Convert stock object to a dictionary for saving."""
        return {
            "symbol": self.symbol,
            "shares": self.shares,
            "purchase_price": self.purchase_price,
            "purchase_date": self.purchase_date,
            "current_price": self.current_price,
            "company_info": self.company_info
        }

    @staticmethod
    def from_dict(data: dict, symbol: str) -> "Stock":
        """Recreate a Stock object from a dictionary."""
        stock = Stock(
            symbol=symbol,
            shares=data["shares"],
            purchase_price=data["purchase_price"],
            purchase_date=data["purchase_date"]
        )
        stock.current_price = data.get("current_price", 0.0)
        stock.company_info = data.get("company_info", {})
        return stock


class Portfolio:
    def __init__(self):
        self.stocks: Dict[str, Stock] = {}
        self.filename = "portfolio.json"
        self.load_portfolio()

    def add_stock(self, symbol: str, shares: int, purchase_price: float) -> None:
        """Add a new stock to the portfolio."""
        price, _ = StockAPI.get_stock_data(symbol)
        if price is None:
            print(f"Error: Could not verify stock {symbol}. Please check the symbol and try again.")
            return

        purchase_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if symbol.upper() in self.stocks:
            print(f"Stock {symbol} already exists in portfolio. Use update_stock to modify.")
            return

        self.stocks[symbol.upper()] = Stock(symbol, shares, purchase_price, purchase_date)
        self.save_portfolio()
        print(f"Added {shares} shares of {symbol} at ${purchase_price:.2f} per share")

    def remove_stock(self, symbol: str) -> None:
        """Remove a stock from the portfolio."""
        if symbol.upper() in self.stocks:
            del self.stocks[symbol.upper()]
            self.save_portfolio()
            print(f"Removed {symbol} from portfolio")
        else:
            print(f"Stock {symbol} not found in portfolio")

    def display_portfolio(self) -> None:
        """Display the entire portfolio including stock details."""
        if not self.stocks:
            print("Portfolio is empty")
            return

        print("\nCurrent Portfolio:")
        print("=" * 100)
        print("Symbol | Shares | Purchase Price | Current Price | Profit/Loss | Change%")
        print("=" * 100)

        for symbol, stock in self.stocks.items():
            stock.update_stock_data()

            cost = stock.shares * stock.purchase_price
            value = stock.shares * stock.current_price
            profit_loss = value - cost
            change_percent = (stock.current_price / stock.purchase_price - 1) * 100

            print(f"{symbol}\t{stock.shares}\t${stock.purchase_price:.2f}\t\t"
                  f"${stock.current_price:.2f}\t\t${profit_loss:.2f}\t\t{change_percent:.2f}%")

            # Display Stock Details
            company_info = stock.company_info
            if company_info:
                print("\nCompany Information:")
                print(f"  📌 Name: {company_info.get('Name', 'N/A')}")
                print(f"  🏢 Sector: {company_info.get('Sector', 'N/A')}")
                print(f"  💰 Market Cap: {company_info.get('MarketCapitalization', 'N/A')}")
                print(f"  📊 P/E Ratio: {company_info.get('PERatio', 'N/A')}")
                print(f"  💵 Dividend Yield: {company_info.get('DividendYield', 'N/A')}")
                print(f"  📈 52-Week High: ${company_info.get('52WeekHigh', 'N/A')}")
                print(f"  📉 52-Week Low: ${company_info.get('52WeekLow', 'N/A')}")
                print("-" * 100)

    def save_portfolio(self) -> None:
        """Save portfolio data to a JSON file."""
        data = {symbol: stock.to_dict() for symbol, stock in self.stocks.items()}
        try:
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving portfolio: {e}")

    def load_portfolio(self) -> None:
        """Load portfolio data from a JSON file."""
        try:
            if not os.path.exists(self.filename):
                self.stocks = {}
                return

            with open(self.filename, 'r') as f:
                data = json.load(f)
                self.stocks = {symbol.upper(): Stock.from_dict(stock_data, symbol) for symbol, stock_data in data.items()}
        except Exception as e:
            print(f"Error loading portfolio: {e}")
            self.stocks = {}


def main():
    portfolio = Portfolio()

    while True:
        print("\nStock Portfolio Tracker")
        print("1. Add Stock")
        print("2. Remove Stock")
        print("3. View Portfolio")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ")

        if choice == '1':
            symbol = input("Enter stock symbol: ")
            shares = int(input("Enter number of shares: "))
            price = float(input("Enter purchase price per share: "))
            portfolio.add_stock(symbol, shares, price)
        elif choice == '2':
            symbol = input("Enter stock symbol to remove: ")
            portfolio.remove_stock(symbol)
        elif choice == '3':
            portfolio.display_portfolio()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
