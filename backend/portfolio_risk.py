"""Lightweight portfolio risk analysis for Market X-Ray.

This module uses historical daily returns. It describes historical co-movement,
not causal economic factors or a forecast of future losses.
"""
from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
import pandas as pd

from market_data import market_data_service


class PortfolioAnalysisError(ValueError):
    pass


def analyze_portfolio(holdings: List[Dict[str, Any]], period: str = "1y",
                     correlation_threshold: float = 0.65) -> Dict[str, Any]:
    if len(holdings) < 2:
        raise PortfolioAnalysisError("Add at least two holdings to analyze portfolio relationships.")
    if len(holdings) > 30:
        raise PortfolioAnalysisError("Market X-Ray supports up to 30 holdings in the MVP.")
    if not 0.1 <= correlation_threshold <= 0.95:
        raise PortfolioAnalysisError("Correlation threshold must be between 0.10 and 0.95.")

    cleaned = []
    seen = set()
    for item in holdings:
        ticker = str(item.get("ticker", "")).strip().upper()
        try:
            weight = float(item.get("weight", 0))
        except (TypeError, ValueError):
            raise PortfolioAnalysisError(f"Invalid weight for {ticker or 'an unnamed holding'}.")
        if not ticker or ticker in seen:
            raise PortfolioAnalysisError(f"Ticker is missing or duplicated: {ticker or '(blank)'}.")
        if not np.isfinite(weight) or weight < 0:
            raise PortfolioAnalysisError(f"Weight for {ticker} must be a non-negative number.")
        seen.add(ticker)
        cleaned.append({"ticker": ticker, "weight": weight})
    weight_total = sum(item["weight"] for item in cleaned)
    if weight_total <= 0:
        raise PortfolioAnalysisError("At least one holding must have a positive weight.")
    if sum(1 for item in cleaned if item["weight"] > 0) < 2:
        raise PortfolioAnalysisError("At least two holdings must have positive weights for portfolio risk analysis.")
    for item in cleaned:
        item["weight"] /= weight_total

    prices = {}
    sources = {}
    skipped = []
    for item in cleaned:
        ticker = item["ticker"]
        history = market_data_service.get_historical_data(ticker, period)
        if history is None or len(history.dates) < 30:
            skipped.append(ticker)
            continue
        series = pd.Series(history.close, index=pd.to_datetime(history.dates), name=ticker)
        series = series[~series.index.duplicated(keep="last")].sort_index()
        prices[ticker] = series
        sources[ticker] = history.source

    if len(prices) < 2:
        raise PortfolioAnalysisError(
            "At least two holdings need 30 or more daily observations. Unavailable: "
            + (", ".join(skipped) if skipped else "insufficient overlapping history")
        )

    price_frame = pd.concat(prices.values(), axis=1, join="inner").sort_index().dropna()
    if len(price_frame) < 30:
        raise PortfolioAnalysisError("Not enough overlapping daily price history. Try a longer period.")
    returns = price_frame.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    if len(returns) < 20:
        raise PortfolioAnalysisError("Not enough valid daily returns to estimate risk.")

    tickers = list(returns.columns)
    weights = np.array([next(item["weight"] for item in cleaned if item["ticker"] == ticker)
                        for ticker in tickers], dtype=float)
    weights /= weights.sum()
    corr = returns.corr().fillna(0.0)
    covariance = returns.cov().fillna(0.0).to_numpy()
    portfolio_variance = float(weights @ covariance @ weights)
    portfolio_vol = float(np.sqrt(max(portfolio_variance, 0.0)) * np.sqrt(252))
    marginal = covariance @ weights
    variance_contributions = weights * marginal
    contribution_total = float(variance_contributions.sum())
    contributions = {
        ticker: (float(variance_contributions[i] / contribution_total * 100)
                 if abs(contribution_total) > 1e-12 else 0.0)
        for i, ticker in enumerate(tickers)
    }

    # Connected components of the correlation graph, using absolute correlation.
    parent = {ticker: ticker for ticker in tickers}
    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    def union(a, b):
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    # Keep every pair for the graph. The UI can surface the strongest links even
    # when they fall below the user's threshold, including negative relationships.
    relationships = []
    for i, left in enumerate(tickers):
        for right in tickers[i + 1:]:
            value = float(corr.loc[left, right])
            strong_positive = value >= correlation_threshold
            if strong_positive:
                union(left, right)
            relationships.append({
                "source": left,
                "target": right,
                "correlation": round(value, 3),
                "strong": bool(abs(value) >= correlation_threshold),
                "same_direction": bool(value > 0),
            })
    groups: Dict[str, List[str]] = {}
    for ticker in tickers:
        groups.setdefault(find(ticker), []).append(ticker)

    clusters = []
    for index, members in enumerate(sorted(groups.values(), key=lambda group: -sum(
            next(item["weight"] for item in cleaned if item["ticker"] == t) for t in group)), 1):
        member_weights = np.array([weights[tickers.index(t)] for t in members])
        cluster_weight = float(member_weights.sum() * 100)
        # Risk contribution attributed to holdings in the cluster; signed contributions are preserved.
        cluster_risk = float(sum(contributions[t] for t in members))
        clusters.append({
            "id": index,
            "name": f"Risk cluster {index}" if len(members) > 1 else f"Less-connected: {members[0]}",
            "tickers": members,
            "portfolio_weight_pct": round(cluster_weight, 2),
            "risk_contribution_pct": round(cluster_risk, 2),
            "linked": len(members) > 1,
        })

    sensitivities = []
    for i, ticker in enumerate(tickers):
        if len(tickers) < 3:
            break
        remaining = [j for j in range(len(tickers)) if j != i]
        remaining_weights = weights[remaining]
        remaining_weights = remaining_weights / remaining_weights.sum()
        remaining_cov = covariance[np.ix_(remaining, remaining)]
        remaining_vol = float(np.sqrt(max(float(remaining_weights @ remaining_cov @ remaining_weights), 0.0)) * np.sqrt(252))
        change_pct = ((remaining_vol / portfolio_vol - 1) * 100) if portfolio_vol > 1e-12 else 0.0
        sensitivities.append({
            "ticker": ticker,
            "annualized_volatility_after_removal_pct": round(remaining_vol * 100, 2),
            "volatility_change_pct": round(change_pct, 2),
            "interpretation": "Estimated volatility falls" if change_pct < -0.5 else (
                "Estimated volatility rises" if change_pct > 0.5 else "Small estimated volatility change"
            ),
        })
    sensitivities.sort(key=lambda item: item["volatility_change_pct"])

    return {
        "period": period,
        "observations": int(len(returns)),
        "start_date": returns.index.min().strftime("%Y-%m-%d"),
        "end_date": returns.index.max().strftime("%Y-%m-%d"),
        "annualized_volatility_pct": round(portfolio_vol * 100, 2),
        "correlation_threshold": correlation_threshold,
        "normalized_weights": {ticker: round(float(weights[i]) * 100, 2) for i, ticker in enumerate(tickers)},
        "risk_contributions": {ticker: round(value, 2) for ticker, value in contributions.items()},
        "correlation_matrix": {row: {col: round(float(corr.loc[row, col]), 3) for col in tickers} for row in tickers},
        "relationships": relationships,
        # Annualized covariance lets the UI recalculate a hypothetical reweighting
        # locally without another network request or a second risk implementation.
        "annualized_covariance": {
            row: {col: round(float(covariance[i, j] * 252), 8)
                  for j, col in enumerate(tickers)}
            for i, row in enumerate(tickers)
        },
        "clusters": clusters,
        "removal_sensitivity": sensitivities,
        "providers": sources,
        "excluded_tickers": skipped,
        "limitations": [
            "Clusters link holdings with positive historical return correlation; they are not proven causal economic factors.",
            "Volatility and risk contributions are estimates from the selected historical window and may change.",
            "The removal comparison renormalizes remaining weights; it is not a trading recommendation.",
        ],
    }
