import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import portfolio_risk


class FakeHistory:
    def __init__(self, ticker, dates, close, source="fixture"):
        self.ticker = ticker
        self.dates = dates
        self.close = close
        self.source = source


def test_market_xray_returns_clusters_and_risk_metrics():
    dates = [str(d.date()) for d in __import__("pandas").bdate_range("2024-01-01", periods=80)]
    rng = np.random.default_rng(7)
    base = rng.normal(0.0005, 0.01, len(dates))
    other = rng.normal(0.0002, 0.008, len(dates))
    prices_a = (100 * np.cumprod(1 + base)).tolist()
    prices_b = (70 * np.cumprod(1 + (base * 0.9 + rng.normal(0, 0.001, len(dates))))).tolist()
    prices_c = (50 * np.cumprod(1 + other)).tolist()

    fixtures = {
        "AAA": FakeHistory("AAA", dates, prices_a),
        "BBB": FakeHistory("BBB", dates, prices_b),
        "CCC": FakeHistory("CCC", dates, prices_c),
    }

    with patch.object(portfolio_risk.market_data_service, "get_historical_data",
                      side_effect=lambda ticker, period: fixtures.get(ticker)):
        result = portfolio_risk.analyze_portfolio([
            {"ticker": "AAA", "weight": 50},
            {"ticker": "BBB", "weight": 30},
            {"ticker": "CCC", "weight": 20},
        ], correlation_threshold=0.5)

    assert result["observations"] > 20
    assert result["annualized_volatility_pct"] >= 0
    assert set(result["normalized_weights"]) == {"AAA", "BBB", "CCC"}
    assert len(result["removal_sensitivity"]) == 3
    assert "clusters" in result
    assert all("risk_contribution_pct" in cluster for cluster in result["clusters"])
    # The relationship graph receives every pair, not only edges over the threshold.
    assert len(result["relationships"]) == 3
    assert all("correlation" in edge and "strong" in edge for edge in result["relationships"])
    assert set(result["annualized_covariance"]) == {"AAA", "BBB", "CCC"}
    assert set(result["annualized_covariance"]["AAA"]) == {"AAA", "BBB", "CCC"}


def test_market_xray_rejects_duplicate_tickers():
    with patch.object(portfolio_risk.market_data_service, "get_historical_data"):
        try:
            portfolio_risk.analyze_portfolio([
                {"ticker": "AAA", "weight": 50},
                {"ticker": "AAA", "weight": 50},
            ])
        except portfolio_risk.PortfolioAnalysisError as exc:
            assert "duplicated" in str(exc)
        else:
            raise AssertionError("Expected duplicate tickers to be rejected")


def test_market_data_falls_back_when_yahoo_fails():
    import pandas as pd
    from market_data import MarketDataService, MarketDataError

    service = MarketDataService()
    frame = pd.DataFrame(
        {"Open": [10.0, 11.0], "High": [11.0, 12.0], "Low": [9.0, 10.0],
         "Close": [10.5, 11.5], "Volume": [100, 120]},
        index=pd.to_datetime(["2025-01-01", "2025-01-02"]),
    )
    with patch.object(service, "_fetch_chart_data", side_effect=MarketDataError("blocked", 502)), \
         patch.object(service, "_fetch_twelvedata_history", return_value=frame), \
         patch.object(service, "_fetch_fmp_history", return_value=None):
        result_frame, provider = service._historical_dataframe("AAA", "1y")
    assert provider == "twelvedata"
    assert len(result_frame) == 2


def test_cors_setting_accepts_comma_separated_origins():
    from config import Settings
    configured = Settings(cors_origins="http://localhost:3000,http://127.0.0.1:3000")
    assert configured.cors_origin_list == ["http://localhost:3000", "http://127.0.0.1:3000"]
