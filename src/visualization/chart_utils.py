"""Visualization utilities — styled charts cho EDA.

Đảm bảo nhất quán: cùng palette, font, grid style.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
from typing import Optional, List, Dict
import pandas as pd


# Color palette nhất quán
COLORS = {
    "primary": "#2563EB",      # Blue
    "secondary": "#10B981",    # Green
    "accent": "#F59E0B",       # Amber
    "danger": "#EF4444",       # Red
    "purple": "#8B5CF6",       # Purple
    "pink": "#EC4899",         # Pink
    "teal": "#14B8A6",         # Teal
    "gray": "#6B7280",         # Gray
    "dark": "#1F2937",         # Dark gray
    "light": "#F3F4F6",        # Light gray
}

PALETTE = [
    COLORS["primary"],
    COLORS["secondary"],
    COLORS["accent"],
    COLORS["danger"],
    COLORS["purple"],
    COLORS["pink"],
    COLORS["teal"],
    COLORS["gray"],
]

# Seaborn palette
sns.set_palette(PALETTE)
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 12
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.labelsize"] = 12
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["savefig.bbox"] = "tight"


def apply_style(ax, title: str, xlabel: str = "", ylabel: str = ""):
    """Apply consistent style to axis."""
    ax.set_title(title, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def styled_barplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = COLORS["primary"],
    horizontal: bool = False,
    figsize: tuple = (12, 6),
    sort: bool = True,
    top_n: Optional[int] = None,
    ax=None,
):
    """Styled bar plot with labels."""
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    df = data.copy()
    if sort:
        df = df.sort_values(y, ascending=horizontal)

    if top_n:
        if horizontal:
            df = df.tail(top_n)
        else:
            df = df.head(top_n)

    if horizontal:
        bars = ax.barh(df[x], df[y], color=color, edgecolor="white", height=0.7)
        for bar, val in zip(bars, df[y]):
            if isinstance(val, (int, float)):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                        f"{val:.1f}", va="center", fontsize=10)
    else:
        bars = ax.bar(df[x], df[y], color=color, edgecolor="white", width=0.7)
        for bar, val in zip(bars, df[y]):
            if isinstance(val, (int, float)):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f"{val:.1f}", ha="center", va="bottom", fontsize=10)

    apply_style(ax, title, xlabel, ylabel)
    if horizontal:
        ax.tick_params(axis="y", labelsize=10)
    else:
        ax.tick_params(axis="x", rotation=45, labelsize=10)

    return ax


def styled_boxplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    palette: list = None,
    figsize: tuple = (12, 6),
    ax=None,
):
    """Styled boxplot."""
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    sns.boxplot(data=data, x=x, y=y, palette=palette or PALETTE, ax=ax)
    apply_style(ax, title, xlabel, ylabel)
    ax.tick_params(axis="x", rotation=45)

    return ax


def styled_heatmap(
    data: pd.DataFrame,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    annot: bool = True,
    fmt: str = ".1f",
    cmap: str = "Blues",
    figsize: tuple = (10, 8),
    ax=None,
):
    """Styled heatmap."""
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    sns.heatmap(data, annot=annot, fmt=fmt, cmap=cmap, ax=ax,
                linewidths=0.5, cbar_kws={"shrink": 0.8})
    ax.set_title(title, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)

    return ax


def styled_barh(
    data: pd.DataFrame,
    y: str,
    x: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = COLORS["primary"],
    figsize: tuple = (12, 8),
    top_n: int = 20,
    ax=None,
):
    """Shortcut: horizontal bar chart (for top skills, etc)."""
    df = data.sort_values(x).tail(top_n)
    return styled_barplot(
        df, x=y, y=x,
        title=title, xlabel=xlabel, ylabel=ylabel,
        color=color, horizontal=True, figsize=figsize, ax=ax
    )


def styled_pie(
    data: pd.DataFrame,
    values: str,
    labels: str,
    title: str = "",
    figsize: tuple = (10, 8),
    colors: list = None,
    ax=None,
):
    """Styled pie chart."""
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    wedges, texts, autotexts = ax.pie(
        data[values],
        labels=data[labels],
        autopct="%1.1f%%",
        colors=colors or PALETTE,
        startangle=90,
        pctdistance=0.85,
    )
    for t in autotexts:
        t.set_fontsize(10)
    ax.set_title(title, fontweight="bold", pad=12)
    ax.axis("equal")

    return ax


def styled_countplot(
    data: pd.DataFrame,
    x: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Count",
    palette: list = None,
    figsize: tuple = (12, 6),
    ax=None,
):
    """Styled count plot."""
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    order = data[x].value_counts().index
    sns.countplot(data=data, x=x, order=order, palette=palette or PALETTE, ax=ax)
    apply_style(ax, title, xlabel, ylabel)
    ax.tick_params(axis="x", rotation=45)

    return ax


def styled_scatter(
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    palette: list = None,
    figsize: tuple = (12, 6),
    ax=None,
):
    """Styled scatter plot."""
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    sns.scatterplot(data=data, x=x, y=y, hue=hue,
                    palette=palette or PALETTE, alpha=0.6, ax=ax)
    apply_style(ax, title, xlabel, ylabel)

    return ax


def styled_kde(
    data: pd.DataFrame,
    x: str,
    hue: Optional[str] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Density",
    palette: list = None,
    figsize: tuple = (12, 6),
    ax=None,
):
    """Styled KDE plot."""
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    sns.kdeplot(data=data, x=x, hue=hue, fill=True,
                palette=palette or PALETTE, alpha=0.3, ax=ax)
    apply_style(ax, title, xlabel, ylabel)

    return ax


def styled_regplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple = (12, 6),
    ax=None,
):
    """Styled regression plot."""
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    sns.regplot(data=data, x=x, y=y, scatter_kws={"alpha": 0.4},
                line_kws={"color": COLORS["danger"]}, ax=ax)
    apply_style(ax, title, xlabel, ylabel)

    return ax


def save_chart(fig, filename: str, dir_path: str = "reports/figures"):
    """Save chart to file."""
    import os
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path