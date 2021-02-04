import time
import math
import threading

from IBapi import IBapi
from order_service import *

import tkinter as tk

class TradeOrder:
    def __init__(self, q, d, ot, st, pf, r=None):
        self.quantity = q #20000
        self.delta = d #0.0005
        self.ratio = r #2
        self.taken_space = []
        self.orderType = ot
        self.stratType = st

        self.printFunction = pf

        self.stop = False

    def connect(self, currency='EURUSD'):
        self.app = IBapi()
        self.app.connect('127.0.0.1', 7497, 123)

        self.app.nextorderId = None

        api_thread = threading.Thread(target=self.run_loop, daemon=True, args=[self.app])
        api_thread.start()

        while True:
            if isinstance(self.app.nextorderId, int):
                print('connected')
                self.printFunction('connected')
                break
            else:
                print('waiting for connection')
                self.printFunction('waiting for connection')
                time.sleep(1)

        self.currentContract = FX_order(currency)
        self.app.reqMktData(1, self.currentContract, '', False, False, [])
        self.app.reqAccountSummary(9002, "All", "$LEDGER")

        while True:
            if self.app.current_bid_price is not None:
                break


    def set_one_order(self, app, quantity, delta, contract, orderType, stratType, ratio=None):
        price_to_buy = calculate_current_buy_price(app)
        self.printFunction(f'type: {orderType}, strategy: {stratType}, quantity: {quantity}')
        if orderType == 'profit_taker':
            set_order_profit_taker(stratType, quantity, 'MKT', str(price_to_buy), delta, contract, app)
        if orderType == 'stop_loss':
            set_bracket_order(stratType, quantity, 'MKT', str(price_to_buy), delta, contract, app, ratio)

        return price_to_buy

    def profit_taker_loop(self, app, taken_space, delta, price_bought, currentContract, quantity):

        if taken_space[-1] + delta <= calculate_current_buy_price(app):
            taken_space.pop()
            if len(taken_space) > 0:
                price_bought = taken_space[-1]


        if len(taken_space) == 0:
            price_bought = self.set_one_order(app, quantity, delta, currentContract, 'profit_taker', 'BUY')
            taken_space.append(price_bought)

        if calculate_current_buy_price(app) <= (price_bought - delta):
            price_bought = self.set_one_order(app, quantity, delta, currentContract, 'profit_taker', 'BUY')
            
            taken_space.append(price_bought)

    def profit_taker_loop_reverse(self, app, taken_space, delta, price_bought, currentContract, quantity):

        if taken_space[-1] - delta >= calculate_current_buy_price(app):
            taken_space.pop()
            if len(taken_space) > 0:
                price_bought = taken_space[-1]


        if len(taken_space) == 0:
            price_bought = self.set_one_order(app, quantity, delta, currentContract, 'profit_taker', 'SELL')
            taken_space.append(price_bought)

        if calculate_current_buy_price(app) <= (price_bought + delta):
            price_bought = self.set_one_order(app, quantity, delta, currentContract, 'profit_taker', 'SELL')
            taken_space.append(price_bought)

    def stop_loss_loop(self, app, taken_space, delta, price_bought, currentContract, quantity, ratio):
        
        if taken_space[-1] + delta <= calculate_current_buy_price(app) or taken_space[-1] - delta/ratio >= app.current_bid_price:
            taken_space.pop()
            if len(taken_space) > 0:
                price_bought = taken_space[-1]


        if len(taken_space) == 0:
            price_bought = self.set_one_order(app, quantity, delta, currentContract, 'stop_loss', 'BUY', ratio)
            taken_space.append(price_bought)


    def stop_loss_loop_reverse(self, app, taken_space, delta, price_bought, currentContract, quantity, ratio):
        
        if taken_space[-1] - delta >= calculate_current_buy_price(app) or taken_space[-1] + delta/ratio <= app.current_bid_price:
            taken_space.pop()
            if len(taken_space) > 0:
                price_bought = taken_space[-1]


        if len(taken_space) == 0:
            price_bought = self.set_one_order(app, quantity, delta, currentContract, 'stop_loss', 'SELL', ratio)
            taken_space.append(price_bought)



    def run_loop(self, app):
        self.app.run()

    
    def stop_loop(self):
        self.stop = True

    def ibkr_func(self):
        if self.app is None:
            print('IBKT not connected!')
            return

        price_bought = self.set_one_order(self.app, self.quantity, self.delta, self.currentContract, self.orderType, self.stratType, self.ratio)
        self.taken_space.append(price_bought)
        curr_time = time.time()

        while True:
            if self.stop:
                break

            if self.orderType == 'profit_taker' and self.stratType == 'SELL':
                self.profit_taker_loop_reverse(self.app, self.taken_space, self.delta, price_bought, self.currentContract, self.quantity)

            elif self.orderType == 'profit_taker' and self.stratType == 'BUY':
                self.profit_taker_loop(self.app, self.taken_space, self.delta, price_bought, self.currentContract, self.quantity)

            elif self.orderType == 'stop_loss' and self.stratType == 'SELL':
                self.stop_loss_loop_reverse(self.app, self.taken_space, self.delta, price_bought, self.currentContract, self.quantity, self.ratio)

            elif self.orderType == 'stop_loss' and self.stratType == 'BUY':
                self.stop_loss_loop(self.app, self.taken_space, self.delta, price_bought, self.currentContract, self.quantity, self.ratio)
            

        try:
            self.app.disconnect()
        except:
            print('disconnect')



class TradeUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Welcome to IBKR API station")
        self.window.geometry('450x600')

        self.strategy_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.ratio_var = tk.IntVar()

    def strategy_select(self):
        self.strategy = self.strategy_var.get()
    
    def type_select(self):
        self.type = self.type_var.get()

    def ratio_select(self):
        self.ratio = self.ratio_var.get()
        print(self.ratio)
    


    def basic_input(self):
        self.frameBI = tk.Frame(self.window)

        self.labelQ = tk.Label(self.frameBI, text="Quantity:")
        self.labelQ.pack()

        self.txtQ = tk.Entry(self.frameBI, width=20)
        self.txtQ.pack()

        self.labelD = tk.Label(self.frameBI, text="Delta:")
        self.labelD.pack()

        self.txtD = tk.Entry(self.frameBI, width=20)
        self.txtD.pack()
        
        self.frameBI.place(x=5, y=5)

    def strategy_input(self):
        self.frameSI = tk.Frame(self.window)

        self.labelSI = tk.Label(self.frameSI, text="Strategy:")
        self.labelSI.pack(side=tk.LEFT)

        self.rb = tk.Radiobutton(self.frameSI, text='BUY', variable=self.strategy_var, value='BUY', command=self.strategy_select)
        self.rb.pack(side=tk.LEFT)

        self.rs = tk.Radiobutton(self.frameSI, text='SELL', variable=self.strategy_var, value='SELL', command=self.strategy_select)
        self.rs.pack(side=tk.LEFT)
        
        self.strategy_var.set(None)

        self.frameSI.place(x=200, y=5)

    def type_input(self):
        self.frameTI = tk.Frame(self.window)

        self.labelTI = tk.Label(self.frameTI, text="Type:")
        self.labelTI.pack(side=tk.LEFT)

        self.rsl = tk.Radiobutton(self.frameTI, text='stop loss', variable=self.type_var, value='stop_loss', command=self.type_select)
        self.rsl.pack(side=tk.LEFT)

        self.rtp = tk.Radiobutton(self.frameTI, text='profit taker', variable=self.type_var, value='profit_taker', command=self.type_select)
        self.rtp.pack(side=tk.LEFT)
        
        self.type_var.set(None)

        self.frameTI.place(x=200, y=35)

    def ratio_input(self):
        self.frameRI = tk.Frame(self.window)

        self.labelRI = tk.Label(self.frameRI, text="Ratio:",width=10)
        self.labelRI.pack(side=tk.LEFT)

        self.r2 = tk.Radiobutton(self.frameRI, text='2', variable=self.ratio_var, value=2, command=self.ratio_select)
        self.r2.pack(side=tk.LEFT)

        self.r3 = tk.Radiobutton(self.frameRI, text='3', variable=self.ratio_var, value=3, command=self.ratio_select)
        self.r3.pack(side=tk.LEFT)
        
        self.ratio_var.set(None)

        self.frameRI.place(x=180, y=70)

    def buttons(self):
        self.frameButton = tk.Frame(self.window)

        self.buttonStart = tk.Button(self.frameButton, text='Start', command=self.startIbkr)
        self.buttonStart.pack(side= tk.LEFT, pady=10)

        self.buttonStop = tk.Button(self.frameButton, text='Stop', command=self.stopIbkr)
        self.buttonStop.pack(side= tk.RIGHT, padx=10, pady=10)

        self.frameButton.place(x=120, y=100)

    def startIbkr(self):
        self.insert_into_textbox('start\n')
        self.to = TradeOrder(int(self.txtQ.get()), float(self.txtD.get()), self.type, self.strategy, self.insert_into_textbox, self.ratio)
        
        self.threadConnect = threading.Thread(target=self.threadFunctionIbkr, daemon=True)
        self.threadConnect.start()
 

    def stopIbkr(self):
        self.insert_into_textbox('stop\n')
        self.to.stop_loop()

    def threadFunctionIbkr(self):
        self.to.connect()
        self.to.ibkr_func()


    def text_box(self):
        self.frameTB = tk.Frame(self.window)

        self.tb = tk.Text(self.frameTB, height=20, width=50)
        self.tb.config(state=tk.DISABLED)
        self.tb.pack()

        self.frameTB.place(x=20, y=200)

    def insert_into_textbox(self, text):
        self.tb.config(state=tk.NORMAL)
        self.tb.insert(tk.END, text + "\n")
        self.tb.config(state=tk.DISABLED)

    def show(self):
        

        self.basic_input()
        self.strategy_input()
        self.type_input()
        self.ratio_input()

        self.buttons()
        self.text_box()
        self.window.mainloop()


if __name__ == "__main__":
    # to = TradeOrder(20000, 0.0005, 'stop_loss', 'BUY', 2)
    # to.connect()
    # to.ibkr_func()
    ui = TradeUI()
    ui.show()