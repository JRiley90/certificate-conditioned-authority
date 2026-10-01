#!/usr/bin/env python3
"""
EXPERIMENT 3: DETERMINISTIC MATCHED BENCHMARK
Friction-Saturated Longitudinal Vehicle Toy Benchmark.
"""
import numpy as np
def run_experiment_3_reproducible(n_episodes=500, master_seed=20261001):
    np.random.seed(master_seed)
    dt = 0.1
    steps_per_ep = 50
    x_wall = 15.0
    g = 9.81
    baselines = ["A_Unconstrained", "B_PointFilter", "C_StaticNRCB", "D_ThresholdSupervisor", "E_CCA"]
    results = {
        b: {
            "violations": 0,
            "episodes": n_episodes,
            "l_revoke_cf": [],
            "interventions": 0
        } for b in baselines
    }
    for ep in range(n_episodes):
        ep_seed = master_seed + ep
        has_drift = (ep % 10 < 3)
        drift_step = 10 if has_drift else 9999
        for b_name in baselines:
            np.random.seed(ep_seed)
            x = np.random.uniform(0.0, 1.0)
            v = np.random.uniform(2.0, 2.5)
            status = "VALID"
            breaches = 0
            a_g_revoked = False
            t_revoke = None
            for step in range(steps_per_ep):
                t = step * dt
                mu = 0.15 if (has_drift and step >= drift_step) else 0.80
                max_traction = mu * g
                u_prop = 1.5
                if b_name == "A_Unconstrained":
                    a_cmd = u_prop
                elif b_name == "B_PointFilter":
                    if x + v * 1.5 >= x_wall - 1.0:
                        a_cmd = -1.2
                        results[b_name]["interventions"] += 1
                    else:
                        a_cmd = u_prop
                elif b_name == "C_StaticNRCB":
                    if x + v * 2.0 >= x_wall - 0.5:
                        a_cmd = -2.5
                        results[b_name]["interventions"] += 1
                    else:
                        a_cmd = u_prop
                elif b_name == "D_ThresholdSupervisor":
                    if (x_wall - x) < 6.0:
                        a_cmd = -2.5
                        results[b_name]["interventions"] += 1
                    else:
                        a_cmd = u_prop
                elif b_name == "E_CCA":
                    residual = 0.40 if (has_drift and step >= drift_step) else 0.02
                    if residual > 0.15:
                        status = "SUSPECT"
                        breaches += 1
                    if breaches >= 3 and not a_g_revoked:
                        status = "INVALID"
                        a_g_revoked = True
                        t_revoke = t
                    if a_g_revoked:
                        a_cmd = -1.2
                    else:
                        buffer = 2.5 if status == "SUSPECT" else 1.5
                        if x + v * buffer >= x_wall:
                            a_cmd = -1.0
                            results[b_name]["interventions"] += 1
                        else:
                            a_cmd = u_prop
                if a_cmd < -max_traction:
                    a_actual = -0.05 * g
                else:
                    a_actual = a_cmd
                v = max(0.0, v + a_actual * dt)
                x = x + v * dt
                if x >= x_wall:
                    results[b_name]["violations"] += 1
                    break
            if b_name == "E_CCA" and has_drift and t_revoke is not None:
                np.random.seed(ep_seed)
                x_cf = np.random.uniform(0.0, 1.0)
                v_cf = np.random.uniform(2.0, 2.5)
                t_cf_boundary = None
                for step_cf in range(steps_per_ep):
                    mu_cf = 0.15 if step_cf >= drift_step else 0.80
                    max_tr_cf = mu_cf * g
                    a_cf = min(1.5, max_tr_cf)
                    v_cf = max(0.0, v_cf + a_cf * dt)
                    x_cf = x_cf + v_cf * dt
                    if x_cf >= x_wall:
                        t_cf_boundary = step_cf * dt
                        break
                if t_cf_boundary is not None:
                    results[b_name]["l_revoke_cf"].append(t_cf_boundary - t_revoke)
    print("================ EXPERIMENT 3 EXECUTION REPORT ================")
    for b in baselines:
        v = results[b]["violations"]
        tot = results[b]["episodes"]
        print(f"Baseline {b:<23}: Violations: {v:>3}/{tot} ({v/tot*100:>5.1f}%) | Interventions: {results[b]['interventions']}")
    leads = results["E_CCA"]["l_revoke_cf"]
    if len(leads) > 0:
        print(f"\nCCA Counterfactual Lead Time (L_revoke_cf):")
        print(f"  Mean Lead Time: {np.mean(leads):.3f} s (std: {np.std(leads):.3f})")
        print(f"  Min Lead Time:  {np.min(leads):.3f} s")
        print(f"  Positive Fraction (L > 0): {np.mean(np.array(leads) > 0)*100:.1f}%")
    print("=================================================================\n")
if __name__ == "__main__":
    run_experiment_3_reproducible()
