import pandas as pd
import matplotlib.pyplot as plt
import math, json
from IPython.display import display, HTML
import plotly.graph_objects as go
from datetime import datetime

f = open('data.json', "w+")
f.write('[\n')

class Backtest:
    def __init__(self, balance, quantity, delta, df):
        self.balance = balance
        self.portfolio_value = balance
        self.portfolio_history = [balance]
        self.quantity = quantity
        self.delta = delta
        self.data = df
        self.current_taken_prices = []
        self.balance_history = [balance] 
        self.number_of_transaction = 0

        self.table_array = {
            'tip testa': [],
            'Delta': [], 
            'pocetni balans': [], 
            'Broj kupljenih po transakciji': [],
            'Ukupan broj otvorenih': [],
            'Ukupan broj zatvorenih': [],
            'Broj nezatvorenih pozicija': [],
            'Konacna vrednot portfolija': [],
            'Dobit u procentima': [],
            'Ukupan broj dobijenih': [],
            'Ukupan broj izgubljenih': [],
            'Odnos': [],
            }

    def calculate_portfolio_buy(self, close_price):
        self.portfolio_value = self.balance + len(self.current_taken_prices) * self.quantity * close_price
        self.portfolio_history.append(self.portfolio_value)

    def calculate_portfolio_sell(self, close_price):
        self.portfolio_value = self.balance - len(self.current_taken_prices) * self.quantity * close_price
        self.portfolio_history.append(self.portfolio_value)


    def calculate_current_buy_price(self, price):
        price_to_buy = float(price) * 1000000 / 10
        last_digit = price_to_buy % 10
        if last_digit >= 5:
            price_to_buy = math.ceil(price_to_buy / 10) * 10 
        else:
            price_to_buy = math.floor(price_to_buy / 10) * 10 + 5
        price_to_buy = price_to_buy / 100000

        return price_to_buy

    def buy(self, price):
        if price in self.current_taken_prices:
            return -1

        self.balance -= self.quantity * price
        self.balance_history.append(self.balance)
        self.number_of_transaction += 1
        self.current_taken_prices.append(price)
        # print(f'Transaction: Buy, amount: {self.quantity}, price: {price}')

    def sell(self, price):
        self.balance += self.quantity * price
        self.balance_history.append(self.balance)
        self.number_of_transaction += 1
        self.current_taken_prices.remove((price - self.delta))
        # print(f'Transaction: Sell, amount: {self.quantity}, price: {price}')

    def buy_reverse(self, price):
        self.balance -= self.quantity * price
        self.balance_history.append(self.balance)
        self.number_of_transaction += 1
        self.current_taken_prices.remove(round(price + self.delta, 5))
        # print(f'Transaction: Buy, amount: {self.quantity}, price: {price}')

    def sell_reverse(self, price):
        if price in self.current_taken_prices:
            return -1

        self.balance += self.quantity * price
        self.balance_history.append(self.balance)
        self.number_of_transaction += 1
        self.current_taken_prices.append(round(price, 5))
        # print(f'Transaction: Sell, amount: {self.quantity}, price: {price}')

    def buy_stop_loss_reverse(self, price, ratio):
        self.balance -= self.quantity * price
        self.balance_history.append(self.balance)
        self.number_of_transaction += 1
        self.current_taken_prices.remove(round(price - self.delta/ratio, 5))
        # print(f'Transaction: Buy, amount: {self.quantity}, price: {price}')


    def test(self):
        last = 0
        for index, row in self.data.iterrows():
           
            if len(self.current_taken_prices) == 0:
                price = self.calculate_current_buy_price(row['Open'])
                self.buy(price)
                self.calculate_portfolio_buy(row['Close'])
            
            reversed_list_prices = self.current_taken_prices[::-1]
            for level in reversed_list_prices:
                if float(row['High']) >= level + self.delta:
                    self.sell(level + self.delta)
                    self.calculate_portfolio_buy(row['Close'])
                else:
                    break
            correct = 1
            # if len(self.current_taken_prices) > 15:
            #     correct = math.ceil(float(len(self.current_taken_prices))/15)

            if len(self.current_taken_prices) > 0 and float(row['Low']) <= self.current_taken_prices[-1] - correct * self.delta:
                self.buy(self.current_taken_prices[-1] - correct*self.delta)
                self.calculate_portfolio_buy(row['Close'])
                if float(row['Low']) <= self.current_taken_prices[-1] - 2*correct*self.delta:
                    self.buy(self.current_taken_prices[-1] - 2*correct*self.delta)
                    self.calculate_portfolio_buy(row['Close'])

            last = float(row['High'])

        print(self.data.head())
        print(f'Portfolio: {self.portfolio_value}, Number of transactions: {self.number_of_transaction}, length of bought prices: {len(self.current_taken_prices)}')
        print(f'Balance {self.balance + len(self.current_taken_prices) * self.quantity * last}')
        print(self.current_taken_prices[0])
        close_num = (self.number_of_transaction - len(self.current_taken_prices)) / 2
        portfolio_val = self.balance + len(self.current_taken_prices) * self.quantity * last
        self.portfolio_history.append(portfolio_val)
        
        self.table_array['tip testa'].append( 'profit taker kontra trenda')
        self.table_array['Delta'].append( self.delta)
        self.table_array['pocetni balans'].append( 1000000)
        self.table_array['Broj kupljenih po transakciji'].append( self.quantity)
        self.table_array['Ukupan broj otvorenih'].append( close_num + len(self.current_taken_prices))
        self.table_array['Ukupan broj zatvorenih'].append( close_num)
        self.table_array['Broj nezatvorenih pozicija'].append( len(self.current_taken_prices))
        self.table_array['Konacna vrednot portfolija'].append( portfolio_val)
        self.table_array['Dobit u procentima'].append( (portfolio_val - 1000000)/10000)
        self.table_array['Ukupan broj dobijenih'].append(-1)
        self.table_array['Ukupan broj izgubljenih'].append(-1)
        self.table_array['Odnos'].append(-1)
        f.write(json.dumps(self.table_array))
        f.write(',\n')
        
        plt.plot(self.portfolio_history)
        plt.show()

    def test_reverse(self):
        last = 0
        for index, row in self.data.iterrows():
            # if index == 10:
            #     break
            if len(self.current_taken_prices) == 0:
                price = self.calculate_current_buy_price(row['Open'])
                self.sell_reverse(price)
                self.calculate_portfolio_sell(row['Close'])
            
            reversed_list_prices = self.current_taken_prices[::-1]
            for level in reversed_list_prices:
                if float(row['Low']) <= level - self.delta:
                    self.buy_reverse(level - self.delta)
                    self.calculate_portfolio_sell(row['Close'])
                else:
                    break
            correct = 1
            # if len(self.current_taken_prices) > 15:
            #     correct = math.ceil(float(len(self.current_taken_prices))/15)

            if len(self.current_taken_prices) > 0 and float(row['High']) >= self.current_taken_prices[-1] + correct * self.delta:
                self.sell_reverse(self.current_taken_prices[-1] + correct*self.delta)
                self.calculate_portfolio_sell(row['Close'])
                if float(row['High']) >= self.current_taken_prices[-1] + 2*correct*self.delta:
                    self.sell_reverse(self.current_taken_prices[-1] + 2*correct*self.delta)
                    self.calculate_portfolio_sell(row['Close'])

            last = float(row['Low'])

        print(self.data.head())
        print(f'Balance: {self.portfolio_value}, Number of transactions: {self.number_of_transaction}, length of bought prices: {len(self.current_taken_prices)}')
        close_num = (self.number_of_transaction - len(self.current_taken_prices)) / 2
        portfolio_val = self.balance - len(self.current_taken_prices) * self.quantity * last
        self.portfolio_history.append(portfolio_val)

        self.table_array['tip testa'].append('profit taker uz trend')
        self.table_array['Delta'].append(self.delta)
        self.table_array['pocetni balans'].append(1000000)
        self.table_array['Broj kupljenih po transakciji'].append( self.quantity)
        self.table_array['Ukupan broj otvorenih'].append( close_num + len(self.current_taken_prices))
        self.table_array['Ukupan broj zatvorenih'].append( close_num)
        self.table_array['Broj nezatvorenih pozicija'].append( len(self.current_taken_prices))
        self.table_array['Konacna vrednot portfolija'].append( portfolio_val)
        self.table_array['Dobit u procentima'].append( (portfolio_val - 1000000)/10000)
        self.table_array['Ukupan broj dobijenih'].append(-1)
        self.table_array['Ukupan broj izgubljenih'].append(-1)
        self.table_array['Odnos'].append(-1)
        f.write(json.dumps(self.table_array))
        f.write(',\n')
        
        plt.plot(self.portfolio_history)
        plt.show()
        
    def test_stop_loss_reverse(self, ratio):
        last = 0
        number_of_wins = 0
        number_of_losses = 0
        for index, row in self.data.iterrows():
            if len(self.current_taken_prices) == 0:
                price = self.calculate_current_buy_price(row['Open'])
                self.sell_reverse(price)
                self.calculate_portfolio_sell(row['Close'])
            
            reversed_list_prices = self.current_taken_prices[::-1]
            for level in reversed_list_prices:
                if float(row['Low']) <= level - self.delta:
                    self.buy_reverse(level - self.delta)
                    self.calculate_portfolio_sell(row['Close'])
                    number_of_wins += 1

                elif float(row['High']) >= level + (self.delta/ratio):
                    self.buy_stop_loss_reverse(level + (self.delta/ratio), ratio)
                    self.calculate_portfolio_sell(row['Close'])
                    number_of_losses += 1
                else:
                    break
            correct = 1
            # if len(self.current_taken_prices) > 15:
            #     correct = math.ceil(float(len(self.current_taken_prices))/15)

            if len(self.current_taken_prices) > 0 and float(row['High']) >= self.current_taken_prices[-1] + correct * self.delta:
                self.sell_reverse(self.current_taken_prices[-1] + correct*self.delta)
                self.calculate_portfolio_sell(row['Close'])
                if float(row['High']) >= self.current_taken_prices[-1] + 2*correct*self.delta:
                    self.sell_reverse(self.current_taken_prices[-1] + 2*correct*self.delta)
                    self.calculate_portfolio_sell(row['Close'])

            last = float(row['Low'])

        print(self.data.head())
        print(f'Balance: {self.portfolio_value}, Number of transactions: {self.number_of_transaction}, length of bought prices: {len(self.current_taken_prices)}')
        print(f'Wins: {number_of_wins}, Losses: {number_of_losses}')
        close_num = (self.number_of_transaction - len(self.current_taken_prices)) / 2
        portfolio_val = self.balance - len(self.current_taken_prices) * self.quantity * last
        self.portfolio_history.append(portfolio_val)
        
        self.table_array['tip testa'].append('stop loss')
        self.table_array['Delta'].append(self.delta)
        self.table_array['pocetni balans'].append(1000000)
        self.table_array['Broj kupljenih po transakciji'].append( self.quantity)
        self.table_array['Ukupan broj otvorenih'].append( close_num + len(self.current_taken_prices))
        self.table_array['Ukupan broj zatvorenih'].append( close_num)
        self.table_array['Broj nezatvorenih pozicija'].append( len(self.current_taken_prices))
        self.table_array['Konacna vrednot portfolija'].append( portfolio_val)
        self.table_array['Dobit u procentima'].append( (portfolio_val - 1000000)/10000)
        self.table_array['Ukupan broj dobijenih'].append(number_of_wins)
        self.table_array['Ukupan broj izgubljenih'].append(number_of_losses)
        self.table_array['Odnos'].append(ratio)
        f.write(json.dumps(self.table_array))
        f.write('\n]')
        
        plt.plot(self.portfolio_history)
        plt.show()
            
        # plt.plot(self.portfolio_history)
        # plt.show()

def main():
    

    data2018 = pd.read_csv('DAT_MT_EURUSD_M1_2018.csv')
    data2019 = pd.read_csv('DAT_MT_EURUSD_M1_2019.csv')
    frames = [data2018, data2019]
    data = pd.concat(frames, ignore_index=True)



    # bt1 = Backtest(1000000, 20000, 0.0005, data2019)
    # bt1.test()
    # ta1 = bt1.table_array

    # bt2 = Backtest(1000000, 20000, 0.0005, data2019)
    # bt2.test_reverse()
    # ta2 = bt2.table_array

    bt3 = Backtest(1000000, 200000, 0.0005, data2018)
    bt3.test_stop_loss_reverse(3)
    t3 = bt3.table_array

    # bt4 = Backtest(1000000, 20000, 0.0005, data2019)
    # bt4.test_stop_loss_reverse(2)
    # ta4 = bt4.table_array
    
    # ta = {
    #         'tip testa': [1, 2, 4],
    #         'Delta': [1, 2, 4], 
    #         'pocetni balans': [1, 2, 4], 
    #         'Broj kupljenih po transakciji': [1, 2, 4],
    #         'Ukupan broj otvorenih': [1, 2, 4],
    #         'Ukupan broj zatvorenih': [1, 2, 4],
    #         'Broj nezatvorenih pozicija': [1, 2, 4],
    #         'Konacna vrednot portfolija': [1, 2, 4],
    #         'Dobit u procentima': [1, 2, 4],
    #         'Ukupan broj dobijenih': [1, 2, 4],
    #         'Ukupan broj izgubljenih': [1, 2, 4],
    #         'Odnos': [1, 2, 4],
    #         }
    # for k in ta1.keys():
    #     ta[k] = ta1[k] + ta2[k] + ta3[k] + ta4[k]

    # df = pd.DataFrame(ta)
    # vals = [df[key] for key in list(ta.keys())]
    # print(vals)
    # fig = go.Figure(data=[go.Table(
    #     header=dict(values=list(df.columns),
    #                 fill_color='paleturquoise',
    #                 align='left'),
    #     cells=dict(values=vals,
    #             fill_color='lavender',
    #             align='left'))
    # ])

    # fig.show()

    # display(df_table)
    # display(HTML(df_table.to_html()))
    # df_table.style 

if __name__ == "__main__":
    main()