from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

from datetime import datetime


class IBapi(EWrapper, EClient):
    
    def __init__(self):
        EClient.__init__(self, self) 
        self.current_bid_price = None
        self.current_ask_price = None
        self.order_number = 0
        filename = 'cash_balance_sl_' + str(datetime.now()) + '.csv'
        self.file = open(filename, 'w')
        self.file.write('id,account,value,currecny,tag,time\n')
        self.file.flush()

    def accountSummary(self, reqId:int, account:str, tag:str, value:str, currency:str):
        if (tag == 'CashBalance' or tag == 'TotalCashBalance' or tag == 'NetLiquidationByCurrency') and  account == 'DU2795887':
            print(f'Id: {reqId}, account: {account}, value: {value}, currency: {currency}, tag: {tag}, order number: {self.order_number}')
            
            self.file.write(f'{reqId},{account},{value},{currency},{tag},{str(datetime.now())}\n')
            self.file.flush()

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        super().updateAccountValue(key, val, currency, accountName)
        print("UpdateAccountValue. Key:", key, "Value:", val, "Currency:", currency, "AccountName:", accountName)
    
    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float, marketValue: float, averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        super().updatePortfolio(contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName)
        print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:",
            contract.exchange, "Position:", position, "MarketPrice:", marketPrice,
            "MarketValue:", marketValue, "AverageCost:", averageCost,
                "UnrealizedPNL:", unrealizedPNL, "RealizedPNL:", realizedPNL,
                "AccountName:", accountName)
    
    def updateAccountTime(self, timeStamp: str):
        super().updateAccountTime(timeStamp)
        print("UpdateAccountTime. Time:", timeStamp)

    def accountDownloadEnd(self, accountName: str):
        super().accountDownloadEnd(accountName)
        print("AccountDownloadEnd. Account:", accountName)

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 2 and reqId == 1:
            self.current_ask_price = price
            # print('The current ask price is: ', price)
        if tickType == 1 and reqId == 1:
            self.current_bid_price = price
            # print('The current bid price is: ', price)
    
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        # print('The next valid order id is: ', self.nextorderId)
        
    # def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
    #     print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining, 'lastFillPrice', lastFillPrice)
	
    def openOrder(self, orderId, contract, order, orderState):
        self.order_number += 1
        print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action, order.orderType, order.totalQuantity, orderState.status)
        
    # def execDetails(self, reqId, contract, execution):
    #     print(f'Order Executed: , {reqId}, {contract.symbol}, {contract.secType}, {contract.currency}, {execution.orderId}, {execution.shares}, {execution.lastLiquidity}')
