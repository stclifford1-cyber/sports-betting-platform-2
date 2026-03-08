# Data Model

## Overview

The platform stores operational betting data and structured player features in a local SQLite database.

Database file:

data/processed/app.db

The schema supports match ingestion, bet tracking, feature enrichment, and deterministic strategy evaluation.

## Tables

### slates

Represents a batch of matches ingested together.

Fields

id – primary key  
source – data origin identifier  
created_at – timestamp

Purpose

Tracks ingestion events and data provenance.

---

### matches

Stores individual matches available for betting or analysis.

Fields

id – primary key  
slate_id – reference to slates table  
player_1 – first competitor  
player_2 – second competitor  
tournament – tournament name  
start_time – scheduled match time  
odds_player_1 – bookmaker odds  
odds_player_2 – bookmaker odds  
status – pending or completed  
winner – match winner  
completed_at – settlement timestamp

Purpose

Core entity representing a betting opportunity.

---

### bets

Stores strategy or manual bet placements.

Fields

id – primary key  
match_id – reference to matches table  
selected_player – chosen competitor  
stake – bet size  
odds_taken – odds at bet time  
status – open, won, lost  
profit_loss – result amount  
settled_at – settlement timestamp

Purpose

Allows evaluation of betting strategies through historical results.

---

### player_match_features

Stores structured modelling features for each player in a match.

Fields

id – primary key  
match_id – reference to matches table  
player_name – player identifier

surface – playing surface

player_ranking – global ranking  
opponent_ranking – opponent ranking

recent_wins – wins in recent matches  
recent_losses – losses in recent matches

head_to_head_wins – wins against opponent  
head_to_head_losses – losses against opponent

notes – optional manual notes

created_at – record creation timestamp  
updated_at – last modification timestamp

Purpose

Represents the structured feature set used by the strategy engine.

Each match creates two feature rows automatically.

---

## Feature Completeness

A match is considered ready for modelling when all required feature fields are populated for both players.

Required fields

surface  
player_ranking  
opponent_ranking  
recent_wins  
recent_losses  
head_to_head_wins  
head_to_head_losses

API endpoint

/matches/features/complete

Returns matches whose feature rows are fully populated.

---

## Deterministic Feature Score

Stage 7 introduces the first scoring rule:

score = (opponent_ranking - player_ranking)
        + recent_wins
        + head_to_head_wins

This score provides a simple deterministic ranking between players before more advanced models are introduced.

Service implementation

apps/api/services/feature_scoring.py
