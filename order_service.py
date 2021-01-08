from ibapi.contract import Contract
from ibapi.order import *
import math
from datetime import datetime

filename = 'trading_logg_sl_' + str(datetime.now()) + '.csv'
loggfile = open(filename, 'w')
loggfile.write(f'typeAction,quantity,lmtPrice,delta,ratio,time\n')
loggfile.flush()

def calculate_current_buy_price(app):
    price_to_buy = float(app.current_bid_price) * 1000000 / 10
    last_digit = price_to_buy % 10
    if last_digit >= 5:
        price_to_buy =  math.floor(price_to_buy / 10) * 10 + 5 
    else:
        price_to_buy = math.floor(price_to_buy / 10) * 10
    price_to_buy = price_to_buy / 100000

    return price_to_buy

def calculate_current_round_price(number):
    price_to_buy = number * 1000000 / 10
    last_digit = price_to_buy % 10
    if last_digit >= 5:
        price_to_buy = math.ceil(price_to_buy / 10) * 10 
    else:
        price_to_buy = math.floor(price_to_buy / 10) * 10 + 5
    price_to_buy = price_to_buy / 100000

    return price_to_buy

def FX_order(symbol):
    contract = Contract()
    contract.symbol = symbol[:3]
    contract.secType = 'CASH'
    contract.exchange = 'IDEALPRO'
    contract.currency = symbol[3:]
    return contract

def set_order(typeAction, quantity, orderType, lmtPrice, finInstr, app):
    print(f'Setting order action:{typeAction}, quantity:{quantity}, price:{lmtPrice}')
    loggfile.write(f'{typeAction},{quantity},{lmtPrice},False,False,{str(datetime.now())}\n')
    loggfile.flush()
    order = Order()
    order.action = typeAction
    order.totalQuantity = quantity
    order.orderType = orderType
    order.lmtPrice = lmtPrice
    order.orderId = app.nextorderId
    app.nextorderId += 1
    order.transmit = True
    
    app.placeOrder(order.orderId, finInstr, order)

def set_order_profit_taker(typeAction, quantity, orderType, lmtPrice, deltaProfit, finInstr, app):
    print(f'Setting order action:{typeAction}, quantity:{quantity}, price:{lmtPrice}')
    loggfile.write(f'{typeAction},{quantity},{lmtPrice},{deltaProfit},False,{str(datetime.now())}\n')
    loggfile.flush()
    order = Order()
    order.action = typeAction
    order.totalQuantity = quantity
    order.orderType = orderType
    order.lmtPrice = lmtPrice
    order.orderId = app.nextorderId
    app.nextorderId += 1
    order.transmit = False

    takeProfit = Order()
    takeProfit.orderId = app.nextorderId
    app.nextorderId += 1
    takeProfit.action = "SELL" if typeAction == "BUY" else "BUY"
    takeProfit.orderType = "LMT"
    takeProfit.totalQuantity = quantity
    takeProfit.lmtPrice = str(float(lmtPrice) + deltaProfit) if typeAction == "BUY" else str(float(lmtPrice) - deltaProfit) 
    takeProfit.parentId = order.orderId
    takeProfit.transmit = True
    
    app.placeOrder(order.orderId, finInstr, order)
    app.placeOrder(takeProfit.orderId, finInstr, takeProfit)

def set_order_stop_loss(typeAction, quantity, orderType, lmtPrice, deltaProfit, finInstr, app):
    print(f'Setting order action:{typeAction}, quantity:{quantity}, price:{lmtPrice}')
    order = Order()
    order.action = typeAction
    order.totalQuantity = quantity
    order.orderType = orderType
    order.lmtPrice = lmtPrice
    order.orderId = app.nextorderId
    app.nextorderId += 1
    order.transmit = False

    stopLoss = Order()
    stopLoss.orderId = order.orderId + 1
    stopLoss.action = "SELL" if typeAction == "BUY" else "BUY"
    stopLoss.orderType = "STP"
    stopLoss.totalQuantity = quantity
    stopLoss.auxPrice = str(float(lmtPrice) + deltaProfit) if typeAction == "BUY" else str(float(lmtPrice) - deltaProfit) 
    stopLoss.parentId = order.orderId
    stopLoss.transmit = True
    
    app.placeOrder(order.orderId, finInstr, order)
    app.placeOrder(stopLoss.orderId, finInstr, stopLoss)



def set_bracket_order(typeAction, quantity, orderType, lmtPrice, deltaProfit, finInstr, app, ratio):
    print(f'Setting bracket order action:{typeAction}, quantity:{quantity}, price:{lmtPrice}')
    loggfile.write(f'{typeAction},{quantity},{lmtPrice},{deltaProfit},{ratio},{str(datetime.now())}\n')
    loggfile.flush()
    order = Order()
    order.action = typeAction
    order.totalQuantity = quantity
    order.orderType = orderType
    order.lmtPrice = lmtPrice
    order.orderId = app.nextorderId
    app.nextorderId += 3
    order.transmit = False

    takeProfit = Order()
    takeProfit.orderId = order.orderId + 1
    takeProfit.action = "SELL" if typeAction == "BUY" else "BUY"
    takeProfit.orderType = "LMT"
    takeProfit.totalQuantity = quantity
    takeProfit.lmtPrice = str(float(lmtPrice) + deltaProfit) if typeAction == "BUY" else str(float(lmtPrice) - deltaProfit) 
    takeProfit.parentId = order.orderId
    takeProfit.transmit = False

    stopLoss = Order()
    stopLoss.orderId = order.orderId + 2
    stopLoss.action = "SELL" if typeAction == "BUY" else "BUY"
    stopLoss.orderType = "STP"
    stopLoss.totalQuantity = quantity
    stopLoss.auxPrice = str(calculate_current_round_price(float(lmtPrice) - deltaProfit/ratio)) if typeAction == "BUY" else str(calculate_current_round_price(float(lmtPrice) + deltaProfit/ratio)) 
    stopLoss.parentId = order.orderId
    stopLoss.transmit = True
    
    app.placeOrder(order.orderId, finInstr, order)
    app.placeOrder(takeProfit.orderId, finInstr, takeProfit)
    app.placeOrder(stopLoss.orderId, finInstr, stopLoss)