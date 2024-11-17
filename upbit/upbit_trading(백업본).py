from common_Import import *
from utils.Generate_plot_and_indicators import *  # plot_candles 함수를 올바르게 임포트

'''
<OpenAPI key관리>
트레이딩 시스템을 실행하기 전, 본인의 업비트 계정에 로그인을 해야합니다

계정 로그인을 위해 회원가입 및 UPBIT 보안인증을 마치고, OpenAPI 사용을 신청해 본인의 Secret key와 Access key를 발급받으세요

이 때, Access key는 발급 이후에도 조회를 통해서 확인이 가능하지만 Secret key는 최초 1회에 한 해서 발급이되고 추가적인 확인이 불가능합니다

반드시 Secret key는 발급 이후 메모장과 같은 별도의 공간에 저장해두세요

txt파일에 본인의 Access key, Secret key 순서로 2개의 행으로 나눠 작성한 후 저장하세요(txt파일의 이름은 본인 마음대로 지정하셔도 됩니다)

<주의 사항>
전체 코드의 모든 부분은 필요에 따라서 수정이 가능하니, 자유롭게 활용하셔도 됩니다.

단, 일부 코드의 경우 수정과정에서 오류가 발생할 수 있으니 유의하여 사용하세요.

아래 코드에서 시각화 부분을 함께 활용할 경우엔 차트를 생성하는 과정에서 시간이 소요되어 1초마다 데이터를 갱신하는 것엔 무리가 있습니다.

차트와 함께 거래가 수행되는 과정을 바라보면 좋겠지만, 시간이 딜레이되어 실시간 거래에 리스크 요소가 생기게됩니다.

또한, 다양한 시간대와 범위를 모두 활용하면 좋겠지만, 그 만큼 더 많은 시간이 딜레이되어 거래가 수행되는 과정에 제약이 생길 수 있습니다.

적절한 균형을 맞출 필요가 있으니 잘 고민해보고 사용하길 바랍니다.

'''


class Upbit_trading_system(QAxWidget):
    def __init__(self):
        super().__init__()
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f'{current_time} : 업비트 OpenAPI를 사용해 계좌정보에 접근합니다.\n')
        
        self.upbit = None
        
        #### 사용자 정의 변수 지정 ####
        # 해당 ticker를 수정해 투자 종목을 자유롭게 변경할 수 있습니다 #
        self.target_ticker = "KRW-SOL"
            
        #### 거래에서 사용하기 위한 캔들 개수 ####
        self.num_long_period = 6 * 24 * 5
        self.num_medium_period = 6 * 24 * 3
        self.num_short_period = 6 * 24 * 1      
                
        #### 거래에 활용하기 위한 변수 정의 ####       
        self.balance = 0 # 현재 계좌 정보
        self.seed_money = 0 # 계좌 보유 현금
              

        self.op_mode = False # 시스템 실행 전 계좌정보를 불러오기 위해 잠시 시스템을 중지하는 변수
        self.hold = False # 매수 이후 홀딩 변수
        self.seed_ratio = 0 # 진입한 시드의 비율을 확인
        self.buy_ticker_data = None # 보유 종목 정보
        self.buy_ticker_order_books = None # 보유 종목의 호가창 정보
        
        
        self.avg_buy_price = 0 # target 종목 매수평균가
        self.buy_ticker_price = 0 # target 종목 현재가격
        self.profit_rate = 0 # target 종목 현재 수익률
        
        #### 손절 및 익절 기준 변수 설정 ####
        self.stop_loss_threshold_panic = -5.0 # 하락장의 패닉상황 손절 기준
        self.stop_loss_threshold = -3.0  # 하락장 + 횡보장의 과매도 상황 손절 기준
        self.take_profit_threshold_sideway = 1.5  # 횡보장에서의 익절 기준
        self.take_profit_threshold_uptrend = 2.5  # 상승장에서의 익절 기준
        
        #### 업비트 OpenAPI 접속관련 함수 모음 ####        
        try:
            self.upbit_login()
            self.get_account_info()
            self.start_trading()
            
        except Exception as e:
            print(f"시스템 초기화 중 오류 발생: {e}")
    
    # ----------------------------------------------------------------------------------
    # 업비트 계좌 로그인 
    def upbit_login(self):
        try:
            with open('./upbit_login.txt') as f:
                lines = f.readlines()
            access_key = lines[0].strip()
            secret_key = lines[1].strip()
            self.upbit = pyupbit.Upbit(access_key, secret_key)
        except FileNotFoundError:
            print("upbit_login.txt 파일을 찾을 수 없습니다. 파일 경로를 확인하세요.")
        except IndexError:
            print("upbit_login.txt 파일의 형식이 잘못되었습니다. Access key와 Secret key를 올바르게 작성했는지 확인하세요.")
        except Exception as e:
            print(f"로그인 중 오류 발생: {e}")

     
    # 업비트 잔고 정보 조회
    def get_account_info(self):
        '''
        이 부분은 트레이딩 시스템을 새롭게 시작했을 때 또는 트레이딩 시스템이 어떠한 이유로 인해 중단됐을 경우에 
        원활한 거래 수행을 이어가기 위해서 현재 본인의 거래상태를 확인하는 부분입니다.    
        만약, 현재 시장의 추세 및 보유하고 있는 종목의 시드 진입 비율에 따라 거래를 위한 변수를 재정의하는 과정입니다.   
        '''
        
        try:
            print("\n----계좌 내 잔고 정보 조회 부분----\n")
            self.balance = self.upbit.get_balances()
            krw_data = [item for item in self.balance if item['currency'] == 'KRW' and float(item['balance']) >= 10000]
            self.seed_money = int(float(krw_data[0]['balance'])) if krw_data else None
            # self.buy_ticker_data = [item for item in self.balance if item['currency'] != 'KRW' and float(item['avg_buy_price']) >= 1 and float(item['balance']) >= 1]
            self.buy_ticker_data = self.upbit.get_balance(self.target_ticker)
            print("12123", self.buy_ticker_data)
            
            
            if self.buy_ticker_data:
                self.avg_buy_price = float(self.buy_ticker_data[0]['avg_buy_price'])
                self.buy_ticker_order_books = pyupbit.get_orderbook(f"{self.target_ticker}")
                self.buy_ticker_price = self.buy_ticker_order_books['orderbook_units'][0]['ask_price']
                self.profit_rate = ((self.buy_ticker_price - self.avg_buy_price) / self.avg_buy_price) * 100
            else:
                self.profit_rate = None

            if self.seed_money and not self.buy_ticker_data:
                print('현재 상태: 원화만 보유 중입니다.')
                print('현재 보유 시드:', self.seed_money)
                self.op_mode = True
                
            elif self.seed_money and self.buy_ticker_data:
                print('현재 상태: 분할 거래 상태입니다.')
                print('현재 보유 시드:', self.seed_money)
                print(f"현재 보유 종목: {self.target_ticker} | 현재 수익률 : {self.profit_rate:.2f}%")
                self.op_mode = True
                self.hold = True
                self.seed_ratio = 0.5
                
            elif not self.seed_money and self.buy_ticker_data:
                print('현재 상태: 모든 시드가 진입된 상태입니다.')
                print(f"현재 보유 종목: {self.target_ticker} | 현재 수익률 : {self.profit_rate:.2f}")
                self.op_mode = True
                self.hold = True
                self.seed_ratio = 1.0
            else:
                print('계좌에 아무런 잔고가 없습니다.')
                
            print(f"\n패닉 상황 발생 시 손절 조건은 {self.stop_loss_threshold_panic}% 입니다\n")
            print(f"하락장 혹은 횡보장에서의 손절 조건은 {self.stop_loss_threshold}% 입니다\n")
            print(f"하락장 혹은 횡보장에서의 익절 조건은 {self.take_profit_threshold_sideway}% 입니다\n")
            print(f"상승장에서의 익절 조건은 {self.take_profit_threshold_uptrend}% 입니다\n")
            
        except Exception as e:
            print(f"계좌 정보 조회 중 오류 발생: {e}")   
        
                             
    # ----------------------------------------------------------------------------------
    # 해당 시점부터 거래를 수행하는 부분입니다.
    def start_trading(self):
        try:      
            plt.ion()  # Interactive mode on

            while True:
                '''
                모든 과정이 진행되기 전, 가격 정보를 각 시간 단위로 갱신하는 부분입니다           
                본인의 취향에 따라서 사용하고 싶지 않은 시간 단위의 경우, dataframes와 timeframes리스트에서 삭제하고 진행을 하면 됩니다            
                단, 삭제를 한다면 작동될 때 제약이 생길 수 있는 부분이 발생할 수 있으니, 잘 확인해서 수행해주시길 바랍니다
                '''
                target_ticker_df_long = pyupbit.get_ohlcv(self.target_ticker, "minute10", count=self.num_long_period)
                target_ticker_df_medium = target_ticker_df_long.tail(self.num_medium_period).copy()
                target_ticker_df_short = target_ticker_df_long.tail(self.num_short_period).copy()
                            
                        
                dataframes = [target_ticker_df_long,
                            target_ticker_df_medium,
                            target_ticker_df_short                     
                            ]
                
                timeframes = [f"Long Period ({self.num_long_period / (6 * 24)} Day)",
                            f"Midium Period ({self.num_medium_period / (6 * 24)} Day)", 
                            f"Short Period ({self.num_short_period / (6 * 24)} Day)"                           
                            ]
                
                trend_results = []
                        
                for i in range(len(dataframes)):
                    trend = generate_trend(dataframes[i])                
                    trend_results.append(f"{timeframes[i]}: {trend}")        
                
                # 현재 시간을 가져와서 trend_results에 추가
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                trend_results.insert(0, f"Current Time: {current_time}")

                # 트렌드 결과를 종합해 최종 추세를 확인      
                short_trend = trend_results[2].split(": ")[1]  # Short Period
                medium_trend = trend_results[1].split(": ")[1]  # Medium Period
                long_trend = trend_results[0].split(": ")[1]  # Long Period
                final_trend = get_final_trend(short_trend, medium_trend, long_trend)
                
                #print(" | ".join(trend_results), f"| Final Trend: {final_trend}")
                # -----------------------------------------------------------------------------------------------------------------------------------------------
                '''
                해당 부분은 거래 수행을 위해 8개의 시간 단위마다 하나의 plt에 시각화하여 가격 변동을 확인하는 부분입니다            
                시각화 창을 실수로 닫더라도, 다시 켜질 수 있도록 코드를 설계했으니 필요에 따라 수정해도 괜찮습니다
                단, 이 부분은 시스템 소개의 앞 부분에서 설명했듯이 시각화 창을 띄울 경우 차트를 생성하는 시간이 소요되기 때문에 거래과정이 원활하지 못할 수 있습니다.
                전 추세에 대한 판단이 정말 맞는지 확인한 이후엔 사용하지 않는 방향으로 설정했습니다.            
                '''
                        
                ''' if not plt.get_fignums():
                    fig, axes = plt.subplots(1, len(dataframes), figsize=(20, 8))
                    fig.tight_layout(pad=1.0)
                
                for i, ax in enumerate(axes.flatten()):
                    ax.clear()
                    plot_candles(dataframes[i], trend_line=True, mean_std_line = True, volume_bars=False, title=f"{timeframes[i]} Chart", ax=ax)
                    
                plt.pause(1)  # Pause for 1 second to allow for the update
                fig.canvas.draw()  # Draw the canvas to update the figure
                
                if not plt.get_fignums():
                    plt.close(fig) '''
                
                # -----------------------------------------------------------------------------------------------------------------------------------------------
                '''            
                해당 부분이 앞으로의 트레이딩 시스템을 실행하기 위해서 전략을 설계하는 공간입니다            
                전략은 별도의 공간에서 새롭게 정의하여 자유롭게 활용이 가능합니다         
                '''         

                # 기술적 지표 추가
                target_ticker_df_long = generate_technical_analysis_indicators(target_ticker_df_long)
                
                # MOM의 추세 파악 (추세 전환 확인을 위함) -> 근데 굳이 사용 안 함
                # target_ticker_df_long = add_mom_trend_column(target_ticker_df_long, self.num_long_period)
                
                # 기술적 지표 추가(단기, 중기, 장기 EMA)
                target_ticker_df_long['EMA_10'] = target_ticker_df_long['close'].ewm(span=10, adjust=False).mean()
                target_ticker_df_long['EMA_20'] = target_ticker_df_long['close'].ewm(span=20, adjust=False).mean()
                target_ticker_df_long['EMA_50'] = target_ticker_df_long['close'].ewm(span=50, adjust=False).mean()              
                
                # 거래 수행을 위한 가격 정보 load
                close = target_ticker_df_long.tail(1)['close'].values[0]
                bband_lower = target_ticker_df_long.tail(1)['BBAND_lOWER'].values[0]
                bband_upper = target_ticker_df_long.tail(1)['BBAND_UPPER'].values[0]
                rsi = target_ticker_df_long.tail(1)['RSI'].values[0]
                mom = target_ticker_df_long.tail(1)['MOM'].values[0]
                ema_10 = target_ticker_df_long.tail(1)['EMA_10'].values[0]
                ema_20 = target_ticker_df_long.tail(1)['EMA_20'].values[0]
                ema_50 = target_ticker_df_long.tail(1)['EMA_50'].values[0]
                
                # -----------------------------------------------------------------------------------------------------------------------------------------------
                # 매수시도
                if self.op_mode ==True and self.hold == False :
                    if final_trend == "down":
                        print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 추세가 하락이므로 매수를 수행하지 않습니다")
                    
                    elif final_trend == "sideway":
                        if close <= bband_lower and rsi <= 40:
                            print(f"{current_time} : 현재 횡보장에서 종가({close})가 볼린저밴드의 하단({bband_lower:.2f})을 터치하고, RSI({rsi:.2f})가 40 미만이므로 1차 매수를 진행합니다")
                            buy_price = self.seed_money / 2
                            self.upbit.buy_market_order(self.target_ticker, buy_price)
                            self.seed_ratio = 0.5
                            self.hold = True
                            
                            print("+------------------+")
                            print("!!!   매수성공   !!!")
                            print("+------------------+")
                        
                        else:
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 횡보장이지만 종가({close})가 볼린저밴드의 하단({bband_lower:.2f}) 터치 및 RSI({rsi:.2f}) 매수조건을 충족하지않아 매수를 보류합니다")
                        
                    elif final_trend == "up":
                        if rsi <= 50 and ema_10 < ema_20:
                            print(f"{current_time} : 현재 상승장에서 이평선(단기 : {ema_10:.2f} < 중기 : {ema_20:.2f})과 RSI({rsi:.2f})의 매수조건이 충족되어 단기 눌림목에 1차 매수를 진행합니다")
                            buy_price = self.seed_money / 2
                            self.upbit.buy_market_order(self.target_ticker, buy_price)
                            self.seed_ratio = 0.5
                            self.hold = True
                            
                            print("+------------------+")
                            print("!!!   매수성공   !!!")
                            print("+------------------+")
                            
                        else :
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 상승장이지만 이평선(단기 : {ema_10:.2f} > 중기 : {ema_20:.2f})과 RSI({rsi:.2f})의 매수조건을 충족하지않아 매수를 보류합니다")
                
                # -----------------------------------------------------------------------------------------------------------------------------------------------
                # 매도 혹은 추가 매수 시도
                if self.op_mode ==True and self.hold == True:
                    
                    # 원화 정보 확인
                    krw_data = [
                    item for item in self.balance 
                    if item['currency'] == 'KRW' and float(item['balance']) >= 10000
                    ][0]
                    self.seed_money = int(float(krw_data['balance'])) if krw_data else None
                            
                    # 투자중인 종목 정보 확인
                    self.buy_ticker_data = [
                        item for item in self.balance
                        if item['currency'] != 'KRW' and float(item['avg_buy_price']) >= 1 and float(item['balance']) >= 1
                    ]
                                        
                    # 투자중인 종목의 현재 수익률 확인
                    if self.buy_ticker_data:  # self.buy_ticker_data가 비어 있지 않은 경우
                        self.avg_buy_price = float(self.buy_ticker_data[0]['avg_buy_price'])
                        self.buy_ticker_order_books = pyupbit.get_orderbook(f"{self.target_ticker}")
                        self.buy_ticker_price = self.buy_ticker_order_books['orderbook_units'][0]['ask_price']
                        
                        self.profit_rate = ((self.buy_ticker_price - self.avg_buy_price) / self.avg_buy_price) * 100
                    else:
                        self.profit_rate = None 
                    
                    # -----------------------------------------------------------------------------------------------------------
                    if final_trend == 'down':
                        if self.profit_rate < self.stop_loss_threshold_panic:                          
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 추세가 하락장에서 패닉셀 상황이 발생해 투자 수익률 {self.profit_rate:.2f}%에서 진입 비율 {self.seed_ratio*100}%를 전량 매도합니다")
                            self.upbit.sell_market_order(self.target_ticker, self.buy_ticker_data[0]['balance'])
                            self.seed_ratio = 0.0
                            self.hold = False

                            print("+------------------+")
                            print("!!!   매도성공   !!!")
                            print("+------------------+")
                            
                        elif self.stop_loss_threshold_panic <= self.profit_rate < self.stop_loss_threshold and self.seed_ratio < 1.0 and close <= bband_lower and rsi <= 30 and ema_10 < ema_20 < ema_50:
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 추세가 하락장에 돌입한 상태이므로 rsi가 30 이하이며 이동평균선이 정렬되고, 볼린저밴드 하단을 터치한 최종저점구간에서 추가 매수를 진행합니다")
                            self.upbit.buy_market_order(self.target_ticker, self.seed_money)
                            self.seed_ratio = 1.0
                            
                            print("+------------------+")
                            print("!!! 추가매수성공 !!!")
                            print("+------------------+")
                            
                        elif self.profit_rate <= self.stop_loss_threshold and self.seed_ratio == 1.0 :                          
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 추세가 하락장에 돌입한 상태에 추가 시드가 존재하지않아 투자 수익률 {self.profit_rate:.2f}%에서 진입 비율 {self.seed_ratio*100}%를 전량 매도합니다")
                            self.upbit.sell_market_order(self.target_ticker, self.buy_ticker_data[0]['balance'])
                            self.seed_ratio = 0.0
                            self.hold = False
                        
                            print("+------------------+")
                            print("!!!   매도성공   !!!")
                            print("+------------------+")
                        
                        else :
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 추세가 하락장에 돌입한 상태에서 어떠한 조건에도 충족하지않아 Holding합니다")
                            
                            
                    elif final_trend == 'sideway':
                        if self.profit_rate >= self.take_profit_threshold_sideway and close >= bband_upper:
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 횡보장에서 최소 익절기준({self.take_profit_threshold_sideway})을 충족하고 종가({close})가 볼린저밴드의 상단({bband_upper:.2f})을 터치하여 진입 비율 {self.seed_ratio*100}%를 전량 매도합니다")
                            self.upbit.sell_market_order(self.target_ticker, self.buy_ticker_data[0]['balance'])
                            self.seed_ratio = 0.0
                            self.hold = False
                            
                            print("+------------------+")
                            print("!!!   매도성공   !!!")
                            print("+------------------+")

                        elif self.stop_loss_threshold <= self.profit_rate < self.take_profit_threshold_sideway and self.seed_ratio < 1.0 and close <= bband_lower and rsi <= 40 and ema_10 < ema_20:
                            print(f'{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 횡보장에서 일시적 과매도로 인해 이평선(단기 : {ema_10:.2f} < 중기 : {ema_20:.2f})과 rsi가 40 이하를 충족하고 종가({close})가 볼린저밴드의 하단({bband_lower:.2f})을 터치해 추가 매수를 진행합니다')
                            self.upbit.buy_market_order(self.target_ticker, self.seed_money)
                            self.seed_ratio = 1.0
                            
                            print("+------------------+")
                            print("!!! 추가매수성공 !!!")
                            print("+------------------+")
                            
                        elif self.profit_rate < self.stop_loss_threshold and self.seed_ratio == 1.0:
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 횡보장에 모든 시드가 진입됐음에도 손절기준({self.stop_loss_threshold})에 닿았기 때문에 시장을 이탈하기 위해서 진입 비율 {self.seed_ratio*100}%를 전량 매도합니다.")
                            self.upbit.sell_market_order(self.target_ticker, self.buy_ticker_data[0]['balance'])
                            self.seed_ratio = 0.0
                            self.hold = False
                            
                            print("+------------------+")
                            print("!!!   매도성공   !!!")
                            print("+------------------+")
                        else :
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 추세가 횡보장에 돌입한 상태에서 어떠한 조건에도 충족하지않아 Holding합니다")
                                
                            
                    elif final_trend == 'up':
                        if self.profit_rate >= self.take_profit_threshold_uptrend and (mom <= 0 or rsi >= 80):
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 상승장에서 최소 익절기준({self.take_profit_threshold_uptrend})을 충족하고 MOM이 0에 도달 혹은 RSI가 80을 돌파하여 단기 상승이 종료했음으로 해석해 진입 비율 {self.seed_ratio*100}%를 전량 매도합니다")
                            self.upbit.sell_market_order(self.target_ticker, self.buy_ticker_data[0]['balance'])
                            self.seed_ratio = 0.0
                            self.hold = False

                            print("+------------------+")
                            print("!!!   매도성공   !!!")
                            print("+------------------+")
                            
                        elif self.seed_ratio < 1.0 and self.profit_rate < self.take_profit_threshold_uptrend and (ema_10 < ema_20 < ema_50 and close <= bband_lower):
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 상승장에서 추격매수를 수행하기 위한 조건이 충족되어 추가 매수를 진행합니다")
                            self.upbit.buy_market_order(self.target_ticker, self.seed_money)
                            self.seed_ratio = 1.0
                            
                            print("+------------------+")
                            print("!!! 추가매수성공 !!!")
                            print("+------------------+")
                        
                        else :
                            print(f"{current_time} : 포지션 진입 비율 {self.seed_ratio * 100}% | 현재 수익률 : {self.profit_rate:.2f}% | 현재 추세가 상승장에 돌입한 상태에서 어떠한 조건에도 충족하지않아 Holding합니다")
                            
                
        except Exception as e:
            print(f"트레이딩 중 오류 발생: {e}")
         