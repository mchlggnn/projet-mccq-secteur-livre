import pandas as pd
import pickle

with open("charagram-demo/charagram.pickle", "rb") as file:
    u = pickle._Unpickler(file)
    u.encoding = "latin1"
    p = u.load()
    print(type(p[0]))
