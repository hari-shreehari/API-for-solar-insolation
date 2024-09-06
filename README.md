# API-for-solar-insolation

Endpoint to generate solar insolation value based on time for the Ahmedabad region.

## Endpoints

### `/get-data/`
- **Description**: Weather Data Retrieval and Solar Insolation Prediction Endpoint
- **Method**: POST
- **Request Body Sample**:
  ```json
  {
    "year": 2012,
    "month": 9,
    "day": 11,
    "hour": 14
  }

