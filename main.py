import time
import math
import threading

from IBapi import IBapi
from order_service import *

# def calculate_current_buy_price(app):
#     price_to_buy = float(app.current_bid_price) * 1000000 / 10
#     last_digit = price_to_buy % 10
#     if last_digit >= 5:
#         price_to_buy = math.ceil(price_to_buy / 10) * 10 
#     else:
#         price_to_buy = math.floor(price_to_buy / 10) * 10 + 5
#     price_to_buy = price_to_buy / 100000

#     return price_to_buy

def set_one_order(app, quantity, delta, contract, orderType, ratio=None):
    price_to_buy = calculate_current_buy_price(app)
    print(price_to_buy)
    if orderType == 'profit_taker':
        set_order_profit_taker('BUY', quantity, 'LMT', str(price_to_buy), delta, contract, app)
    if orderType == 'stop_loss':
        set_bracket_order('BUY', quantity, 'LMT', str(price_to_buy), delta, contract, app, ratio)

    return price_to_buy

def profit_taker_loop(app, taken_space, delta, price_bought, quantity):

    if taken_space[-1] + delta <= calculate_current_buy_price(app):
        taken_space.pop()
        if len(taken_space) > 0:
            price_bought = taken_space[-1]


    if len(taken_space) == 0:
        price_bought = set_one_order(app, quantity, delta, currentContract, 'profit_taker')
        taken_space.append(price_bought)

    if calculate_current_buy_price(app) <= (price_bought - delta):
        price_bought = set_one_order(app, quantity, delta, currentContract, 'profit_taker')
        
        taken_space.append(price_bought)

def stop_loss_loop(app, taken_space, delta, price_bought,currentContract, quantity, ratio):
    # print(taken_space)
    if taken_space[-1] + delta <= calculate_current_buy_price(app) or taken_space[-1] - delta/ratio >= app.current_bid_price:
        print('POP')
        taken_space.pop()
        if len(taken_space) > 0:
            price_bought = taken_space[-1]


    if len(taken_space) == 0:
        print('EMPTY')
        price_bought = set_one_order(app, quantity, delta, currentContract, 'stop_loss', ratio)
        taken_space.append(price_bought)

    # if calculate_current_buy_price(app) <= (price_bought - delta):
    #     price_bought = set_one_order(app, quantity, delta, currentContract, 'stop_loss', ratio)
    #     print('ANOTHER ONE')
    #     taken_space.append(price_bought)


def run_loop(app):
	app.run()

def main():

    app = IBapi()
    app.connect('127.0.0.1', 7497, 123)

    app.nextorderId = None

    api_thread = threading.Thread(target=run_loop, daemon=True, args=[app])
    api_thread.start()

    while True:
        if isinstance(app.nextorderId, int):
            print('connected')
            break
        else:
            print('waiting for connection')
            time.sleep(1)

    currentContract = FX_order('EURUSD')
    app.reqMktData(1, currentContract, '', False, False, [])
    app.reqAccountSummary(9002, "All", "$LEDGER")

    while True:
        if app.current_bid_price is not None:
            break

    quantity = 20000
    delta = 0.0005
    ratio = 2
    taken_space = []
    price_bought = set_one_order(app, quantity, delta, currentContract, 'stop_loss', ratio)
    taken_space.append(price_bought)
    curr_time = time.time()

    while True:
        stop_loss_loop(app, taken_space, delta, price_bought, currentContract,quantity, ratio)
        


    app.disconnect()

if __name__ == "__main__":
    main()