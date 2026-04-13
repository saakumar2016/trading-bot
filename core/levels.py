def get_levels(df):
    recent = df.tail(80)

    support = round(recent.nsmallest(5, 'Low')['Low'].mean(), 2)
    resistance = round(recent.nlargest(5, 'High')['High'].mean(), 2)

    return support, resistance