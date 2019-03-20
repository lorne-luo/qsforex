from utils.singleton import SingletonDecorator
from .fxcm.account import FXCM
from .oanda.account import OANDA

SingletonFXCM = SingletonDecorator(FXCM)


SingletonOANDA = SingletonDecorator(OANDA)
