'''

positions are the account level
    > position check needs to be at the ticker level?

handled

position_qty for short sell is -ve. If you're using this to define a units_to_buy, make is absolute
x.__abs__()

handled

'''



# continue once a buy or sell order is place.. don't get hung up
#     - or wait for 10 retries and then continue

# max loss threshold per position - in the event of a market crash in long positions

# > add a $profit / PNL check for exit - DONE

# > mom indicator is very active!! - updated
# > bool_price_less_than_resistance needs to be more restrictive - Parked

# close positions end of day - Parked



##################
# Note:
##################

# checks - cannot open a short sell while a long buy order is open

##################
# Issues:
##################


# - opens new long buy orders when an unfilled / pending buy order already exists
# - opens multiple orders, while other unfilled buy orders exist, without taking cash into account.