import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression


def load_market_data(ticker: str):
    """
    Fetch recent daily stock prices.
    We keep the window short to avoid overfitting
    and keep predictions responsive.
    """
    return yf.download(
        ticker,
        period="6mo",
        interval="1d",
        progress=False
    )


def prepare_features(price_data: pd.DataFrame, lookback: int = 5):
    """
    Convert price history into a supervised learning problem.
    Each row represents recent price behaviour,
    and the target is the next-day return.
    """
    price_data["daily_return"] = price_data["Close"].pct_change()
    price_data = price_data.dropna()

    X, y = [], []

    for i in range(len(price_data) - lookback):
        X.append(price_data["daily_return"].iloc[i:i + lookback].values)
        y.append(price_data["daily_return"].iloc[i + lookback])

    return pd.DataFrame(X), pd.Series(y)


def predict_next_day_return(ticker: str):
    """
    Train a lightweight regression model
    and predict the next day's return.
    """
    data = load_market_data(ticker)

    if data is None or len(data) < 15:
        return None

    X, y = prepare_features(data)

    model = LinearRegression()
    model.fit(X, y)

    latest_window = X.iloc[-1].values.reshape(1, -1)
    prediction = model.predict(latest_window)[0]

    return float(prediction)
