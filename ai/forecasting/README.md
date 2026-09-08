# Forecasting

## Initial Use Cases

- Sales forecasting
- Inventory demand
- Stock-out risk
- Revenue projections
- Customer retention indicators

## Requirements

Forecast outputs should contain:

- forecast
- confidence
- model/version
- source period
- generated_at
- assumptions

## Rule

Forecasts are advisory and must not silently mutate authoritative business state.
