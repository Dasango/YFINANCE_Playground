# YFinance Prediction Playground

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![React](https://img.shields.io/badge/react-18-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-005571?logo=fastapi)

## Overview

**YFinance Prediction Playground** is a professional-grade, real-time financial analytics dashboard designed to visualize and predict cryptocurrency market trends (BTC-USD).

At its core, it leverages a sophisticated **Deep Learning (LSTM)** model that performs **online learning**—continuously retraining on incoming data to adapt to market volatility in real-time. The backend, built with **FastAPI**, orchestrates data synchronization with Yahoo Finance, while the **React + Recharts** frontend delivers high-fidelity, interactive visualizations of historical performance and recursive future projections.

---

## Key Features

- **Real-Time Market Data**: Automatic synchronization with global market data feeds every minute.
- **Online Model Training**: The AI model evolves with the market, retraining instantly as new candles close.
- **Recursive Forecasting**: Generates multi-step future price trajectories using stochastic volatility injection.
- **Dynamic Visualization**: High-performance rendering of complex datasets, including historical "in-sample" predictions vs. actuals.

---

## API Endpoints

The system is powered by a robust REST API. Below are the primary endpoints exposed by the backend service.

<div align="center">

| Endpoint               | Method | Description                                                                                                                          | Payload / Response                 |
| :--------------------- | :----: | :----------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------- |
| **`/api/data`**        | `GET`  | **Historical Data Retrieval**<br>Fetches the last 2000 OHLCV market data points tailored for charting.                               | `JSON Array` (OHLCV Objects)       |
| **`/api/predict`**     | `GET`  | **Future Projections**<br>Calculates the next 5 predicted price points and returns current model training status.                    | `{ history, predictions, status }` |
| **`/api/predictions`** | `GET`  | **Model Evaluation**<br>Provides historical model inferences ("past predictions") for validating accuracy against real price action. | `JSON Array` (Datetime, Price)     |

</div>

---

## Getting Started

Follow this guide to run the full stack (Backend + Frontend) locally.

### Prerequisites

- **Python 3.8+**
- **Node.js 16+** & **npm**

### 1. Backend Setup (API & Model)

The backend handles data fetching, model inference, and training.

```bash
# Navigate to the project root (if not already there)
cd YFINANCE_Playground

# Create a virtual environment (Optional but Recommended)
python -m venv .venv

# Activate the virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
python backend/api.py
```

> The API will start at `http://localhost:8000`

### 2. Frontend Setup (Dashboard)

The frontend visualizes the data and interacts with the API.

```bash
# Open a new terminal and navigate to the project root
cd YFINANCE_Playground

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

> The application will assume the backend is running on `localhost:8000`. Open the link provided by Vite (usually `http://localhost:5173`) to view the dashboard.

---

## Tech Stack

- **Backend**: Python, FastAPI, TensorFlow/Keras, Pandas, Scikit-learn, YFinance.
- **Frontend**: React, Vite, TypeScript, Recharts, Lucide React.
- **Data Source**: Yahoo Finance Public API.

---

<div align="center">
  <sub>Built with <3 by David for Financial Intelligence</sub>
</div>
