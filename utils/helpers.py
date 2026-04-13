def val(x):
    try:
        return float(x)
    except:
        return x.item()