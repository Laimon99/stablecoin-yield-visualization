# Research Questions

## RQ1 - Persistence

How long does a high-yield APY episode last?

Primary metric: Kaplan-Meier survival estimate for high-yield episodes using APY >= 10 percent as the preregistered primary threshold.

Sensitivity: APY >= 5 percent, APY >= 20 percent and daily cross-sectional top 10 percent.

## RQ2 - Yield Composition

How much observed yield comes from base APY versus reward APY?

Primary metrics: median base APY, median reward APY, reward share and reward-share coverage.

## RQ3 - Ranking Stability

How much does the top-yield pool set change over time?

Primary metrics: top-10 and top-20 retention/churn after 1, 7 and 30 days.

## RQ4 - Capital Response

Are APY jumps followed by observed TVL increases and later APY compression?

Primary metrics: event-time APY, TVL change, log TVL change and compression at fixed horizons.

Important caveat: TVL change is not a direct capital-flow measure.

## RQ5 - Risk Frontier

Which pools clear APY, persistence and TVL thresholds simultaneously?

Primary output: joint threshold screen rather than a Pareto frontier or hidden risk score.

## RQ6 - Stablecoin Risk

How do APY and TVL behave around selected stablecoin depeg events?

Primary metrics: stablecoin price deviation from peg, pool exposure, APY and TVL in a [-30, +30] day event window.

## RQ7 - Protocol Structure

Does persistence vary by pool type, chain, protocol category or stablecoin design?

Primary metrics: survival curves and stratified persistence ratios.

## Preregistered Hypotheses

- H1: Higher APY episodes are shorter than moderate APY episodes in the observed sample.
- H2: Reward APY is less persistent than base APY where both fields are available.
- H3: APY jumps are associated with later observed TVL increases and APY compression, without implying causality.
- H4: Larger pools tend to have lower but more persistent APY.
- H5: Top-yield rankings have high churn over 7 and 30 days.
- H6: Stablecoin peg stress is associated with misleading headline yield and TVL interpretation.
