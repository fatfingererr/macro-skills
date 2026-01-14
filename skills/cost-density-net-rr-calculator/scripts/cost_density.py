"""
Cost Density Model - Python Implementation

Calculates transaction cost impact on risk-reward ratios using the
Geometry of Advantage Decay model.

Reference:
    Sukhov, S. "Geometry of Advantage Decay: A Quantitative Model for
    Risk-Reward Degradation in High-Friction Trading Environments"
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import json


@dataclass
class CostDensityInput:
    """Input parameters for cost density calculation."""
    RR_g: float      # Gross risk-reward target (Target/Stop)
    P: float         # Stop-loss size in pips/points
    c: float         # Round-turn commission per lot (account currency)
    s: float         # Average round-trip spread (pips/points)
    V: float         # Value per pip per lot (account currency per pip)
    R: Optional[float] = None  # Fixed risk per trade (optional, cancels out)


@dataclass
class CostDensityOutput:
    """Output from cost density calculation."""
    cost_density: float    # (c/V + s) in pips-equivalent
    x: float               # Load coefficient = cost_density / P
    RR_net: float          # Net risk-reward after costs
    Loss_RR: float         # Relative efficiency loss vs RR_g
    WR_min: float          # Minimum win rate for breakeven
    P_critical: float      # Half-life stop size
    zone: str              # "normal" or "high_friction"
    notes: List[str]       # Explanation notes


@dataclass
class GridConfig:
    """Configuration for grid sweep."""
    P_min: float = 1.0
    P_max: float = 100.0
    steps: int = 20


def compute_single(
    RR_g: float,
    P: float,
    c: float,
    s: float,
    V: float,
    R: Optional[float] = None
) -> CostDensityOutput:
    """
    Compute cost density metrics for a single parameter set.

    Args:
        RR_g: Gross risk-reward target (e.g., 3.0)
        P: Stop-loss size in pips (e.g., 20)
        c: Round-turn commission per lot (e.g., 7.0)
        s: Average spread in pips (e.g., 1.5)
        V: Value per pip per lot (e.g., 10.0)
        R: Fixed risk per trade (optional, cancels out)

    Returns:
        CostDensityOutput with all computed metrics
    """
    # Validate inputs
    if RR_g < 0:
        raise ValueError("RR_g must be non-negative")
    if P <= 0:
        raise ValueError("P (stop-loss) must be positive")
    if V <= 0:
        raise ValueError("V (pip value) must be positive")
    if c < 0:
        raise ValueError("c (commission) must be non-negative")
    if s < 0:
        raise ValueError("s (spread) must be non-negative")

    # Core calculations
    cost_density = (c / V) + s
    x = cost_density / P
    RR_net = (RR_g - x) / (1 + x)
    Loss_RR = (x * (RR_g + 1)) / (RR_g * (1 + x)) if RR_g > 0 else 0
    WR_min = (1 + x) / (1 + RR_g)
    P_critical = cost_density * (RR_g + 2) / RR_g if RR_g > 0 else float('inf')

    # Determine zone
    zone = "high_friction" if P < P_critical else "normal"

    # Generate notes
    notes = [
        f"成本密度 {cost_density:.2f} pips = 佣金等效 {c/V:.2f} + 點差 {s:.2f}",
        f"淨 RR 從 {RR_g:.2f} 降至 {RR_net:.2f}，損失 {Loss_RR*100:.1f}%",
        f"需 {WR_min*100:.1f}% 勝率才能打平"
    ]

    if zone == "high_friction":
        notes.append(f"警告：停損 {P:.1f} < 臨界值 {P_critical:.1f}，處於高摩擦區")

    return CostDensityOutput(
        cost_density=round(cost_density, 4),
        x=round(x, 4),
        RR_net=round(RR_net, 4),
        Loss_RR=round(Loss_RR, 4),
        WR_min=round(WR_min, 4),
        P_critical=round(P_critical, 4),
        zone=zone,
        notes=notes
    )


def sweep_stoploss(
    RR_g: float,
    c: float,
    s: float,
    V: float,
    grid: Optional[GridConfig] = None
) -> Dict[str, Any]:
    """
    Sweep over a range of stop-loss values.

    Args:
        RR_g, c, s, V: Same as compute_single
        grid: Grid configuration (optional)

    Returns:
        Dictionary with sweep results, thresholds, and summary table
    """
    if grid is None:
        grid = GridConfig()

    # Validate grid
    if grid.P_min <= 0:
        raise ValueError("P_min must be positive")
    if grid.P_max <= grid.P_min:
        raise ValueError("P_max must be greater than P_min")
    if not (3 <= grid.steps <= 2000):
        raise ValueError("steps must be between 3 and 2000")

    # Generate P values (linear space)
    P_values = [
        grid.P_min + i * (grid.P_max - grid.P_min) / (grid.steps - 1)
        for i in range(grid.steps)
    ]

    # Compute for each P
    cost_density = (c / V) + s
    results = []
    for P in P_values:
        x = cost_density / P
        RR_net = (RR_g - x) / (1 + x)
        WR_min = (1 + x) / (1 + RR_g)
        Loss_RR = (x * (RR_g + 1)) / (RR_g * (1 + x)) if RR_g > 0 else 0

        results.append({
            "P": round(P, 2),
            "x": round(x, 4),
            "RR_net": round(RR_net, 3),
            "WR_min": round(WR_min, 4),
            "Loss_RR": round(Loss_RR, 4)
        })

    # Find thresholds
    thresholds = {}

    # P where RR_net > 0
    for r in results:
        if r["RR_net"] > 0:
            thresholds["P_breakeven"] = r["P"]
            break

    # P where WR_min crosses specific levels
    for target_wr in [0.35, 0.40, 0.50]:
        for r in results:
            if r["WR_min"] <= target_wr:
                thresholds[f"P_WR_{int(target_wr*100)}"] = r["P"]
                break

    # P where Loss_RR crosses specific levels
    for target_loss in [0.20, 0.40, 0.60]:
        for r in results:
            if r["Loss_RR"] <= target_loss:
                thresholds[f"P_Loss_{int(target_loss*100)}"] = r["P"]
                break

    # Summary table (select representative points)
    indices = [0, len(results)//4, len(results)//2, 3*len(results)//4, len(results)-1]
    summary_table = [results[i] for i in indices if i < len(results)]

    # Calculate P_critical
    P_critical = cost_density * (RR_g + 2) / RR_g if RR_g > 0 else float('inf')

    return {
        "cost_density": round(cost_density, 4),
        "P_critical": round(P_critical, 4),
        "thresholds": thresholds,
        "summary_table": summary_table,
        "full_results": results,
        "notes": [
            f"成本密度 = {cost_density:.2f} pips",
            f"臨界停損 P_critical = {P_critical:.2f} pips",
            f"掃描範圍：{grid.P_min} - {grid.P_max} pips，{grid.steps} 步"
        ]
    }


def to_json(output: CostDensityOutput) -> str:
    """Convert output to JSON string."""
    return json.dumps({
        "cost_density": output.cost_density,
        "x": output.x,
        "RR_net": output.RR_net,
        "Loss_RR": output.Loss_RR,
        "WR_min": output.WR_min,
        "P_critical": output.P_critical,
        "zone": output.zone,
        "notes": output.notes
    }, ensure_ascii=False, indent=2)


# Example usage
if __name__ == "__main__":
    # XAU/USD example from the paper
    result = compute_single(
        RR_g=3.0,
        P=20,
        c=7.0,
        s=1.5,
        V=10.0
    )
    print("Single computation:")
    print(to_json(result))
    print()

    # Sweep example
    sweep_result = sweep_stoploss(
        RR_g=3.0,
        c=7.0,
        s=1.5,
        V=10.0,
        grid=GridConfig(P_min=5, P_max=50, steps=10)
    )
    print("Sweep results:")
    print(json.dumps(sweep_result, ensure_ascii=False, indent=2))
