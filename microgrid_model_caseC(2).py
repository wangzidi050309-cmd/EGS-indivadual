import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# =========================
# LOAD DATA
# =========================

file_path = os.path.join(os.path.expanduser("~"), "Desktop", "caseC_community_microgrid_hourly.csv")
df = pd.read_csv(file_path)

# =========================
# PARAMETERS
# =========================

capacity = 10  # kWh
max_power = 5  # kW
eta_ch = 0.95
eta_dis = 0.95
dt = 1  # hour

# =========================
# =========================
# MODEL 1: WITH BATTERY
# =========================
# =========================

soc = 0.5 * capacity

soc_list = []
grid_import = []
grid_export = []
charge_list = []
discharge_list = []
energy_balance_error = []

for t in range(len(df)):
    pv = df.loc[t, "pv_kw"]
    load = df.loc[t, ["load1_kw", "load2_kw", "load3_kw"]].sum()

    charge = 0
    discharge = 0
    imp = 0
    exp = 0

    if pv >= load:
        surplus = pv - load

        charge = min(surplus, max_power, (capacity - soc) / (eta_ch * dt))
        soc += charge * eta_ch * dt

        exp = surplus - charge

    else:
        deficit = load - pv

        discharge = min(deficit, max_power, soc * eta_dis / dt)
        soc -= discharge / eta_dis * dt

        imp = deficit - discharge

    soc_list.append(soc)
    grid_import.append(imp)
    grid_export.append(exp)
    charge_list.append(charge)
    discharge_list.append(discharge)

    # Energy balance check
    lhs = pv + imp + discharge
    rhs = load + charge + exp
    energy_balance_error.append(lhs - rhs)

# Store results
df["soc"] = soc_list
df["grid_import_batt"] = grid_import
df["grid_export_batt"] = grid_export
df["charge"] = charge_list
df["discharge"] = discharge_list
df["energy_balance_error"] = energy_balance_error

# Cost with battery
df["cost_batt"] = (
    df["grid_import_batt"] * df["import_tariff_gbp_per_kwh"]
    - df["grid_export_batt"] * df["export_price_gbp_per_kwh"]
)

total_cost_batt = df["cost_batt"].sum()

# =========================
# =========================
# MODEL 2: NO BATTERY (BASELINE)
# =========================
# =========================

grid_import_nb = []
grid_export_nb = []

for t in range(len(df)):
    pv = df.loc[t, "pv_kw"]
    load = df.loc[t, ["load1_kw", "load2_kw", "load3_kw"]].sum()

    if pv >= load:
        imp = 0
        exp = pv - load
    else:
        imp = load - pv
        exp = 0

    grid_import_nb.append(imp)
    grid_export_nb.append(exp)

df["grid_import_nb"] = grid_import_nb
df["grid_export_nb"] = grid_export_nb

# Cost without battery
df["cost_nb"] = (
    df["grid_import_nb"] * df["import_tariff_gbp_per_kwh"]
    - df["grid_export_nb"] * df["export_price_gbp_per_kwh"]
)

total_cost_nb = df["cost_nb"].sum()

# =========================
# VERIFICATION
# =========================

print("\n===== VERIFICATION CHECKS =====")

print("Max energy balance error:", np.max(np.abs(df["energy_balance_error"])))
print("Min SOC:", np.min(df["soc"]))
print("Max SOC:", np.max(df["soc"]))

if np.min(df["soc"]) >= 0 and np.max(df["soc"]) <= capacity:
    print("SOC bounds check: PASSED")
else:
    print("SOC bounds check: FAILED")

# =========================
# RESULTS COMPARISON
# =========================

print("\n===== RESULTS COMPARISON =====")

print(f"Cost WITH battery (£): {total_cost_batt:.2f}")
print(f"Cost WITHOUT battery (£): {total_cost_nb:.2f}")

savings = total_cost_nb - total_cost_batt
print(f"Cost Savings (£): {savings:.2f}")

# Energy totals
print(f"\nTotal Import WITH battery (kWh): {df['grid_import_batt'].sum():.2f}")
print(f"Total Import WITHOUT battery (kWh): {df['grid_import_nb'].sum():.2f}")

print(f"Total Export WITH battery (kWh): {df['grid_export_batt'].sum():.2f}")
print(f"Total Export WITHOUT battery (kWh): {df['grid_export_nb'].sum():.2f}")

# =========================
# PLOTS
# =========================

plt.figure()
plt.plot(df["soc"])
plt.title("Battery SOC")
plt.xlabel("Time")
plt.ylabel("kWh")
plt.grid()

plt.figure()
plt.plot(df["cost_batt"].cumsum(), label="With Battery")
plt.plot(df["cost_nb"].cumsum(), label="No Battery")
plt.legend()
plt.title("Cumulative Cost Comparison")
plt.xlabel("Time")
plt.ylabel("£")
plt.grid()

plt.figure()
plt.plot(df["grid_import_batt"], label="Import (Battery)")
plt.plot(df["grid_import_nb"], label="Import (No Battery)")
plt.legend()
plt.title("Grid Import Comparison")
plt.xlabel("Time")
plt.ylabel("kW")
plt.grid()

plt.show()

# =========================
# SAVE RESULTS
# =========================

output_path = os.path.join(os.path.expanduser("~"), "Desktop", "microgrid_results_full.csv")
df.to_csv(output_path, index=False)

print("\nResults saved as: microgrid_results_full.csv")