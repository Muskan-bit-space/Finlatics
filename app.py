from fastapi import FastAPI, HTTPException
from ml import predict_next_day_return

app = FastAPI(
    title="QuantNova ML Engine",
    description="Machine learning service for market analytics",
    version="1.0"
)


@app.get("/predict")
def predict(ticker: str):
    """
    Return the predicted next-day return for a stock ticker.
    """
    result = predict_next_day_return(ticker.upper())

    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Not enough market data to generate prediction"
        )

    return {
        "ticker": ticker.upper(),
        "predicted_return": round(result, 6)
    }
