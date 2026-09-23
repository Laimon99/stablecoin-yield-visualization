"""Static slide graphics rebuilt from published aggregate tables."""
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import PercentFormatter


def render_published_static(root: Path, output: Path) -> None:
    survival = pd.read_csv(root / 'outputs/tables/episode_survival.csv')
    events = pd.read_csv(root / 'outputs/tables/apy_tvl_event_response.csv')
    depeg = pd.read_csv(root / 'outputs/tables/depeg_event_study.csv')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': '#14213D', 'axes.labelcolor': '#667085', 'xtick.color': '#667085', 'ytick.color': '#667085'})

    def theme(ax):
        ax.spines[['top', 'right']].set_visible(False)
        ax.spines[['bottom', 'left']].set_color('#DCE4F2')
        ax.grid(color='#DCE4F2', linewidth=.6)
        ax.set_axisbelow(True)

    fig, ax = plt.subplots(figsize=(9.975, 4.675))
    fig.subplots_adjust(left=.085, right=.98, bottom=.16, top=.87)
    ax.fill_between(survival.duration_days, survival.ci_lower, survival.ci_upper, step='post', color='#8B5CF6', alpha=.18, label='95% pointwise interval')
    ax.step(survival.duration_days, survival.survival, where='post', color='#6941C6', linewidth=2.2, label='Kaplan-Meier S(t)')
    ax.set(xlim=(0, 100), ylim=(0, 1), xlabel='Episode duration t (calendar days)', ylabel='Probability of duration > t')
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    theme(ax)
    ax.legend(loc='upper right', frameon=False, fontsize=10)
    inset = ax.inset_axes([.55, .39, .4, .31])
    inset.step(survival.duration_days, survival.survival, where='post', color='#176B87', linewidth=1.5)
    inset.set(xlim=(100, survival.duration_days.max()), ylim=(0, .022), title='Full observed tail')
    inset.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    inset.tick_params(labelsize=8)
    theme(inset)
    day30 = survival.loc[survival.duration_days <= 30].iloc[-1]
    caption = (f'{int(survival.iloc[0].at_risk):,} episodes   |   S(30) = {day30.survival:.2%}'
               f'   |   95% CI: {day30.ci_lower*100:.2f}-{day30.ci_upper*100:.2f}%')
    fig.text(.085, .95, caption, fontsize=12, weight='bold', color='#6941C6')
    fig.savefig(output / 'survival_static.png', dpi=200)
    plt.close(fig)
    specifications = [
        (events, 'median_apy', 'event_apy.png', '#4F7CFF', 'APY (%)', (0, 21)),
        (events, 'median_tvl_index', 'event_tvl.png', '#159E94', 'TVL index', (0.9, 1.8)),
        (depeg, 'price_usd', 'depeg_price.png', '#E74C88', 'Price (USD)', (0.95, 1.01)),
        (depeg, 'median_apy', 'depeg_apy.png', '#4F7CFF', 'APY (%)', None),
    ]
    for frame, column, filename, color, ylabel, limits in specifications:
        selected = frame.loc[frame.event_time_day >= -7]
        fig, ax = plt.subplots(figsize=(7.1, 2.125))
        fig.subplots_adjust(left=.10, right=.98, bottom=.29, top=.95)
        ax.plot(selected.event_time_day, selected[column], color=color, linewidth=2, marker='o', markersize=2.5)
        ax.axvline(0, color='#667085', linestyle='--', linewidth=.8)
        if column in ['median_tvl_index', 'price_usd']:
            ax.axhline(1, color='#667085', linestyle=':', linewidth=.8)
        ax.set(xlim=(-7, 30), xticks=[-7, 0, 7, 14, 21, 30], xlabel='Days relative to event', ylabel=ylabel)
        if limits:
            ax.set_ylim(*limits)
        theme(ax)
        fig.savefig(output / filename, dpi=220)
        plt.close(fig)
