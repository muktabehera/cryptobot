# Structure

##Main

<code>
while True:
    
    if market_is_open
        
        get_buying_power()
        set_position_size()
        check_if_position_exists(ticker)
        get_num_stocks_owned()
        get_current_ts()
        get_market_close_ts()
        get_bars(time_interval) # time_interval = "1 Minute"
        
        
        generate_signal()   # buy / sell
        
        if position_exists and sell_signal:
            sell_market(all_stocks_owned)
            get_avg_fill_price()
            
        elif no position_exists and buy_signal:
            buy_market(units_basedon_position_size)
            get_sell_price()
            
            profit = (sell_price - buy_price)* num_stocks_sold
            
            post_trade_to_slack()
    else:
        market_is_closed()
        sleep(60 sec)

</code>


 
