#!/usr/bin/env python3
""" Tyler Osso 
    CS 270 - PA7 - Stock Price Scraper/Logger
    02 December 2025
    First Python project. Lots of help from google, stack overflow, realpython, classmates, etc
    to run:  ./stock.py [symbols for stocks seperated by spaces ie ./stock.py GSPC DJI FTSE """
import requests # get html from yahoo
import pprint # easy printing for debugging
import sys #allows for command line args
import os # allow working with .finance directory creating/checking
import datetime # to timestamp price checks
import glob # make it easy to find files in .finance with SYMBOL_*
from bs4 import BeautifulSoup # given for html parsing

URL = "https://finance.yahoo.com/markets/world-indices/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.3"
    )
}

#given function to fetch html from yahoo
def fetch_soup(): 
    """Download the page and return a BeautifulSoup object to read and parse"""
    response = requests.get(URL, headers=HEADERS)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    return soup

#check if finance directory exists and if not create it
def check_finance_dir():
    if not os.path.exists(".finance"):
        os.makedirs(".finance")
        
#search for "table" which ends up being <table class=...>
def search_container(soup): 
   #create the table object to later parse
    table = soup.find("table")
    if table is None:
        print("No table found")
        return None
    return table

#create a map of stock names/prices to search
def break_down_table(table):
    stock_index_map = {}
    # tr is the outer tree table row element
    rows = table.find_all("tr")
    
    for row in rows:

        # find the price in a <fin-streamer> with data-value that contains price
        price_cell = row.find("fin-streamer", attrs={"data-value": True})
        #in python, continue skips to the next iteration of the loop its in

        if price_cell is None:
            continue  # not a data row with a price


        price_text = price_cell["data-value"]
        
        price = float(price_text)
        

        # get the symbol from data-symbol
        
        raw_symbol = price_cell.get("data-symbol")
        #in python, continue skips to the next iteration of the loop its in
        if not raw_symbol:
            continue

        symbol = raw_symbol.lstrip("^").upper()

        # get the full name from a <div> that has a title attribute ie s&p 500 since its not in finstreamer

        name_div = row.find("div", attrs={"title": True})

        if name_div is not None:
            name = name_div.get("title", symbol)
            name = name.strip()

        # Store result in map giving us access to smbol name and price
        stock_index_map[symbol] = {
            "name": name,
            "price": price
        }

    return stock_index_map


#check for symbol arguments
def get_args():
    #ensure length allows for at least one symbol
    if len(sys.argv) < 2:
        print("Requires at least one stock symbol as an argument.")
        sys.exit(1)
    else:
        #take all args after the python3 stock.py call
        args = sys.argv[1:]
        #return ALL the other args in uppercase
        return [arg.upper() for arg in args]

#will check old price for math and update after printing
def update_return_oldPrice(symbol, info):
    #set price and name form info map
    price = info["price"]
    name = info["name"]
    print(f"\n{name}")
    print(f"Current price is ${price}")
    found = glob.glob(f".finance/{symbol}_*")
    #if theres no old file to compare to, create one and exit
    if not found:
        #manual path set by using symbol and current datetime
        update_price_path = (f".finance/{symbol}_{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}")
        with open(update_price_path, "w") as file:
            file.write(f"{price}")
        return
    #glob returns a list of found files so to access we need to use indexing
    old_file = found[0]
    #read old price from file and clean it and read it as a float
    with open(old_file, "r") as file:
        old_price_line = file.read()
        old_price_line = old_price_line.strip()
        old_price = float(old_price_line)
    price_change = price - old_price
    
    #use the filename to get the timestamp, remove underscores and symbol and strip whitespaces and print
    string_name = os.path.basename(old_file)
    timestamp = string_name.replace("_", " ")
    timestamp = timestamp.replace(symbol, "").strip()
    
    #comapare old to new price and print accordingly as float to 2 decimals
    if old_price > price:
        price_change *= -1
        print(f"Price decreased by -${price_change:.2f} since last check on {timestamp}")
    elif old_price < price:
        print(f"Price increased by ${price_change:.2f} since last check on {timestamp}")
    else:
        print("Price has not changed since last check.")
    
    #remove the old file and create a new one with writing updated price and time
    os.remove(old_file)
    update_price_path = (f".finance/{symbol}_{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}")
    with open(update_price_path, "w") as file:
        file.write(f"{price}")
        
if __name__ == "__main__":
    check_finance_dir() #create/check if .finance dir exists
    soup = fetch_soup()             # get the parsed HTML
    table = search_container(soup)  # search within it
    #if table exsists, break it into usable map else exit
    if table:
        index_map = break_down_table(table)
    else:
        sys.exit(1)
    #set args to only stock symbols
    args = get_args()
    # for each symbol in args check if its in the map then run the printing 
    #and updating function else print not found message
    for symbol in args:
        if symbol in index_map:
            info = index_map[symbol]
            update_return_oldPrice(symbol, info)
            
        else:
            print(f"{symbol} not found in table.")

