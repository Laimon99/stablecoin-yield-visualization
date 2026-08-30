# Project Charter

## Title

The Price of Yield: Persistence, Mechanisms and TVL Response in Stablecoin DeFi.

## Context

DeFi interfaces often present stablecoin yield as a single annualized percentage. That percentage is easy to compare visually but difficult to interpret because it hides duration, TVL capacity, reward-token dependence, stablecoin peg risk and differences in protocol mechanisms.

## Primary Question

Are high stablecoin-denominated DeFi yields persistent and supported by durable activity, or are they temporary episodes associated with incentives, peg stress and volatile TVL?

## Secondary Questions

1. How long do high-yield APY episodes last?
2. How much observed yield comes from base APY versus reward APY?
3. How stable are top-yield pool rankings over 1, 7 and 30 days?
4. Are APY jumps followed by observed TVL increases and later APY compression?
5. Which pools clear transparent APY, persistence and TVL thresholds simultaneously?
6. How do APY and TVL behave around selected stablecoin depeg events?
7. Does persistence differ by pool type, chain, protocol category or stablecoin design?

## Audience

The primary academic audience is a university Data Visualization instructor and classmates. The
public portfolio audience includes data practitioners, reviewers and hiring teams interested in
reproducible analytics and responsible DeFi interpretation. The project assumes no need for
smart-contract engineering expertise.

## Contribution

The project reframes APY comparison as a multi-dimensional data story. Instead of ranking pools, it builds a reproducible pool-day dataset and shows that a quoted APY should be read together with persistence, capacity, reward composition and stablecoin risk.

## Unit of Analysis

- Primary entity: DeFi yield pool.
- Temporal unit: pool-day.
- Main analytical table: one row per pool per observed day.

## Period

The target period is the latest available historical window with at least 180 days of history per included pool, preferably 365-730 days and including at least one verified stress period. The actual freeze date and period will be filled after G1 source feasibility and data collection.

## Scope

Core population: stablecoin or yield-bearing stablecoin pools with observed APY and TVL history from verified public data providers.

Included categories:

1. Single-stable lending.
2. Stable-stable liquidity pool.
3. Yield-bearing stablecoin.
4. Vault or yield aggregator.
5. Leveraged or recursive strategy.
6. Incentive-driven pool.

## Exclusions

The core analysis excludes or separates:

- pools whose underlying assets are primarily volatile assets;
- pools with insufficient history;
- pools below the minimum TVL threshold for the selected analysis;
- duplicated pool representations after entity resolution;
- migrated or renamed pools that cannot be reconciled;
- observations with semantically ambiguous APY;
- observations where the source contract is unavailable or cannot be verified.

Every exclusion must be logged with a reason.

## Definition of Success

The project is successful when it produces a reproducible data story that:

- maps official course requirements;
- verifies current sources through official docs and live requests;
- preserves immutable raw data;
- documents a canonical schema and data dictionary;
- measures data quality;
- defines and tests high-yield episodes;
- validates at least three non-causal insights through robustness checks;
- exports final figures including a hero visualization;
- delivers a complete report, slide deck and oral defense notes;
- passes tests and `make reproduce-sample`;
- documents limitations and avoids financial recommendations.

## Main Risks

- DeFiLlama APY semantics may be ambiguous or revised.
- Base and reward APY coverage may be incomplete.
- CoinGecko public API rate limits may restrict full price history.
- Stablecoin ticker and bridged asset mapping may be ambiguous.
- TVL changes may be mistaken for capital flows.
- Depeg events may be sparse within the selected pool history.
- Audio course material is not locally transcribed.
