# Sports Betting Strategy Development Platform Architecture

## Overview

Local Python platform designed for researching sports betting strategies.  
The system ingests match data, enriches it with structured features, runs deterministic strategies, and evaluates performance.

The architecture is organised into distinct layers so that data ingestion, modelling, strategy execution, and evaluation remain separable.

## Core Layers

### API Layer

Location:
apps/api

Responsibilities:

- Match ingestion
- Bet placement and settlement
- Feature enrichment management
- Strategy scoring endpoints
- Experiment orchestration

Framework:

FastAPI

Primary file:

apps/api/main.py

### Service Layer

Location:

apps/api/services

Purpose:

Encapsulate reusable logic that should not live inside API routes.

Current services:

feature_scoring.py

Function:

calculate_player_score(match_id, player_name)

Deterministic scoring rule:

score = (opponent_ranking - player_ranking) + recent_wins + head_to_head_wins

This layer allows the same scoring logic to be used by:

- API routes
- strategy backtests
- experiment sweeps
- candidate selection pipelines

### Data Layer

Database:

SQLite

Location:

data/processed/app.db

Core tables:

slates  
matches  
bets  
player_match_features

Feature rows are created automatically when matches are ingested.

### Strategy Research Layer

Location:

strategies/

Responsibilities:

- Deterministic strategy backtests
- Parameter sweep experiments
- ROI and performance measurement

### Worker Layer

Location:

workers/

Future responsibilities:

- data ingestion automation
- feature enrichment pipelines
- scheduled model updates

### Testing Layer

Location:

tests/

Contains verification scripts and regression tests.

### Utility Scripts

Location:

scripts/

Example:

test_feature_scoring.py

Used to manually verify service behaviour during development.

## Data Flow

1. Match slate ingested through API
2. Matches stored in SQLite
3. Feature rows created automatically
4. Feature enrichment performed
5. Feature completeness validated
6. Feature scoring service calculates deterministic player score
7. Strategy engine consumes scores for bet selection

## Stage Progression

Stage 1 – Development environment  
Stage 2 – API + database schema  
Stage 3 – Bet settlement and reporting  
Stage 4 – Strategy research framework  
Stage 5 – Experiment engine  
Stage 6 – Feature enrichment system  
Stage 7 – Feature scoring service layer
