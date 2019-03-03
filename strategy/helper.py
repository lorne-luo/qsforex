from mt4.constants import OrderSide


def check_cross(data1, data2):
    if data1[-1] > data2[-1] and data1[-2] < data2[-1]:
        return OrderSide.BUY
    if data1[-1] < data2[-1] and data1[-2] > data2[-1]:
        return OrderSide.SELL


def check_reverse(data):
    if data[-1] > data[-2] < data[3]:
        return OrderSide.BUY
    if data[-1] < data[-2] > data[3]:
        return OrderSide.SELL
