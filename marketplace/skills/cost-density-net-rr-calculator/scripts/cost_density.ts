/**
 * Cost Density Model - TypeScript Implementation
 *
 * Calculates transaction cost impact on risk-reward ratios using the
 * Geometry of Advantage Decay model.
 *
 * Reference:
 *   Sukhov, S. "Geometry of Advantage Decay: A Quantitative Model for
 *   Risk-Reward Degradation in High-Friction Trading Environments"
 */

interface CostDensityInput {
  /** Gross risk-reward target (Target/Stop), e.g., 3.0 */
  RR_g: number;
  /** Stop-loss size in pips/points */
  P: number;
  /** Round-turn commission per lot (account currency), e.g., 7.0 */
  c: number;
  /** Average round-trip spread (pips/points), e.g., 1.5 */
  s: number;
  /** Value per pip per lot (account currency per pip), e.g., 10 */
  V: number;
  /** Fixed risk per trade (optional, cancels out in RR_net) */
  R?: number;
}

interface CostDensityOutput {
  /** Cost Density = (c/V + s) in pips-equivalent */
  cost_density: number;
  /** Load coefficient x = (1/P) * (c/V + s) */
  x: number;
  /** Net risk-reward after costs: (RR_g - x)/(1 + x) */
  RR_net: number;
  /** Relative efficiency loss vs RR_g */
  Loss_RR: number;
  /** Minimum win rate for breakeven given x */
  WR_min: number;
  /** Half-life stop size where RR_net = 0.5*RR_g */
  P_critical: number;
  /** Friction zone: "normal" or "high_friction" */
  zone: "normal" | "high_friction";
  /** Explanation notes */
  notes: string[];
}

interface GridConfig {
  /** Minimum stop-loss for sweep */
  P_min?: number;
  /** Maximum stop-loss for sweep */
  P_max?: number;
  /** Number of steps in sweep */
  steps?: number;
}

interface SweepResult {
  P: number;
  x: number;
  RR_net: number;
  WR_min: number;
  Loss_RR: number;
}

interface SweepOutput {
  cost_density: number;
  P_critical: number;
  thresholds: Record<string, number>;
  summary_table: SweepResult[];
  full_results: SweepResult[];
  notes: string[];
}

/**
 * Round a number to specified decimal places
 */
function round(value: number, decimals: number): number {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
}

/**
 * Compute cost density metrics for a single parameter set.
 */
export function computeSingle(input: CostDensityInput): CostDensityOutput {
  const { RR_g, P, c, s, V } = input;

  // Validate inputs
  if (RR_g < 0) {
    throw new Error("RR_g must be non-negative");
  }
  if (P <= 0) {
    throw new Error("P (stop-loss) must be positive");
  }
  if (V <= 0) {
    throw new Error("V (pip value) must be positive");
  }
  if (c < 0) {
    throw new Error("c (commission) must be non-negative");
  }
  if (s < 0) {
    throw new Error("s (spread) must be non-negative");
  }

  // Core calculations
  const cost_density = c / V + s;
  const x = cost_density / P;
  const RR_net = (RR_g - x) / (1 + x);
  const Loss_RR = RR_g > 0 ? (x * (RR_g + 1)) / (RR_g * (1 + x)) : 0;
  const WR_min = (1 + x) / (1 + RR_g);
  const P_critical = RR_g > 0 ? (cost_density * (RR_g + 2)) / RR_g : Infinity;

  // Determine zone
  const zone: "normal" | "high_friction" =
    P < P_critical ? "high_friction" : "normal";

  // Generate notes
  const notes: string[] = [
    `成本密度 ${round(cost_density, 2)} pips = 佣金等效 ${round(c / V, 2)} + 點差 ${s}`,
    `淨 RR 從 ${RR_g} 降至 ${round(RR_net, 2)}，損失 ${round(Loss_RR * 100, 1)}%`,
    `需 ${round(WR_min * 100, 1)}% 勝率才能打平`,
  ];

  if (zone === "high_friction") {
    notes.push(
      `警告：停損 ${P} < 臨界值 ${round(P_critical, 1)}，處於高摩擦區`
    );
  }

  return {
    cost_density: round(cost_density, 4),
    x: round(x, 4),
    RR_net: round(RR_net, 4),
    Loss_RR: round(Loss_RR, 4),
    WR_min: round(WR_min, 4),
    P_critical: round(P_critical, 4),
    zone,
    notes,
  };
}

/**
 * Sweep over a range of stop-loss values.
 */
export function sweepStoploss(
  RR_g: number,
  c: number,
  s: number,
  V: number,
  grid?: GridConfig
): SweepOutput {
  const config: Required<GridConfig> = {
    P_min: grid?.P_min ?? 1,
    P_max: grid?.P_max ?? 100,
    steps: grid?.steps ?? 20,
  };

  // Validate grid
  if (config.P_min <= 0) {
    throw new Error("P_min must be positive");
  }
  if (config.P_max <= config.P_min) {
    throw new Error("P_max must be greater than P_min");
  }
  if (config.steps < 3 || config.steps > 2000) {
    throw new Error("steps must be between 3 and 2000");
  }

  // Generate P values
  const P_values: number[] = [];
  for (let i = 0; i < config.steps; i++) {
    const P =
      config.P_min + (i * (config.P_max - config.P_min)) / (config.steps - 1);
    P_values.push(P);
  }

  // Compute for each P
  const cost_density = c / V + s;
  const results: SweepResult[] = P_values.map((P) => {
    const x = cost_density / P;
    const RR_net = (RR_g - x) / (1 + x);
    const WR_min = (1 + x) / (1 + RR_g);
    const Loss_RR = RR_g > 0 ? (x * (RR_g + 1)) / (RR_g * (1 + x)) : 0;

    return {
      P: round(P, 2),
      x: round(x, 4),
      RR_net: round(RR_net, 3),
      WR_min: round(WR_min, 4),
      Loss_RR: round(Loss_RR, 4),
    };
  });

  // Find thresholds
  const thresholds: Record<string, number> = {};

  // P where RR_net > 0
  for (const r of results) {
    if (r.RR_net > 0) {
      thresholds["P_breakeven"] = r.P;
      break;
    }
  }

  // P where WR_min crosses specific levels
  for (const targetWr of [0.35, 0.4, 0.5]) {
    for (const r of results) {
      if (r.WR_min <= targetWr) {
        thresholds[`P_WR_${Math.round(targetWr * 100)}`] = r.P;
        break;
      }
    }
  }

  // P where Loss_RR crosses specific levels
  for (const targetLoss of [0.2, 0.4, 0.6]) {
    for (const r of results) {
      if (r.Loss_RR <= targetLoss) {
        thresholds[`P_Loss_${Math.round(targetLoss * 100)}`] = r.P;
        break;
      }
    }
  }

  // Summary table
  const indices = [
    0,
    Math.floor(results.length / 4),
    Math.floor(results.length / 2),
    Math.floor((3 * results.length) / 4),
    results.length - 1,
  ];
  const summary_table = indices
    .filter((i) => i < results.length)
    .map((i) => results[i]);

  // Calculate P_critical
  const P_critical =
    RR_g > 0 ? (cost_density * (RR_g + 2)) / RR_g : Infinity;

  return {
    cost_density: round(cost_density, 4),
    P_critical: round(P_critical, 4),
    thresholds,
    summary_table,
    full_results: results,
    notes: [
      `成本密度 = ${round(cost_density, 2)} pips`,
      `臨界停損 P_critical = ${round(P_critical, 2)} pips`,
      `掃描範圍：${config.P_min} - ${config.P_max} pips，${config.steps} 步`,
    ],
  };
}

// Example usage (uncomment to run with ts-node or bun)
// const result = computeSingle({
//   RR_g: 3.0,
//   P: 20,
//   c: 7.0,
//   s: 1.5,
//   V: 10.0,
// });
// console.log(JSON.stringify(result, null, 2));
