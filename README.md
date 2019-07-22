# Structure

## Main

```
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

```

## Strategies:

### PREV DAY HIGH LOW - [ref](https://www.youtube.com/watch?v=kMAxntMXMvQ)

```
    # Get high and low of previous day (for ui, use a 30 min chart)

    # if current day's open is below / breaks below the prev day low

        # get high and low of today's 30 min open candle
        # if current day's price breaks above30 min open candle's high, buy, keep a small buffer
        # if current day's price breaks below 30 min open candle's  low, sell

    # if 30 min open candle is above the prev day high

        # get high and low of today's 30 min open candle
        # if current day's price breaks above 30 min open candle's high, buy with small buffer
        # if current day's price breaks below 30 min open candle's low, sell
```

### VOLUME TRADED STRATEGY:

```
    # check previous day's volume traded data
    # if this volume is covered within 2 hours of market open - stock will go up
    # if stock is trending upwards - price momentum to continue
    # if negative then downwards
``` 

### PREV CLOSE STRATEGY:

```
    # get value for previous day close
    # identify today's 15m bar which cuts the previous close
    # get the high and low of the 15m bar
    # trade the breakout
    #        > if current price goes above high, buy 1m
    #        > if current prices goes below low, sell 1m
    # target 0.3 % either way
```

