# GSENSE 3.0 — Tabular ML Pipeline & Surrogate State Predictors

## 1. Pipeline Overview
The machine learning subsystem in GSENSE 3.0 provides two high-performance models trained on commercial air handler data from Lawrence Berkeley National Laboratory (LBNL):
1. **HVAC Fault Classifier**: Identifies mechanical and sensor degradation classes.
2. **Counterfactual State Regressor**: Predicts continuous thermodynamic state shifts under candidate interventions.

---

## 2. Feature Definitions & Engineering

### Base Sensors
- `oa_temp`: Outdoor Air Temperature (°C)
- `ra_temp`: Return Air Temperature (°C)
- `ma_temp`: Mixed Air Temperature (°C)
- `sa_temp`: Supply Air Temperature (°C)
- `zone_temp`: Zone Average Temperature (°C)
- `oa_dmpr`: Outdoor Air Damper Command (%)
- `chwc_vlv`: Chilled Water Cooling Coil Valve (%)
- `hw_vlv`: Hot Water Heating Coil Valve (%)
- `sf_spd`: Supply Fan Speed / VFD Frequency (%)
- `sa_cfm`: Volumetric Airflow Rate (CFM)
- `sa_sp`: Supply Duct Static Pressure (in. w.g.)
- `power`: Total AHU Electrical Power (kW)

### Derived Physical Features
- `delta_t_coil = ma_temp - sa_temp`
- `delta_t_mixed = oa_temp - ra_temp`
- `mixed_air_ratio = (ma_temp - ra_temp) / (oa_temp - ra_temp)`
- `thermal_load_proxy = sa_cfm * |ra_temp - sa_temp| * 0.000316`
- `airflow_per_speed = sa_cfm / sf_spd`
- `sp_per_speed = sa_sp / sf_spd`
- `damper_cooling_fight`: Boolean proxy when damper ingests hot air while cooling valve is open.

---

## 3. Model Architecture & Performance Metrics

### Fault Classifier (`HistGradientBoostingClassifier`)
- **Classes**: `nominal`, `damper_stuck`, `coil_fouling_or_leakage`, `fan_belt_slip`, `static_pressure_surge`
- **Evaluation Accuracy**: `0.9998`
- **Macro F1 Score**: `0.9998`
- **Artifact**: `backend/ml/artifacts/fault_classifier.joblib`

### Counterfactual State Regressors (`HistGradientBoostingRegressor`)
- **Target `zone_temp`**: RMSE `0.0829°C`, MAE `0.0636°C`, $R^2 = 0.9973$
- **Target `sa_temp`**: RMSE `0.3107°C`, MAE `0.2064°C`, $R^2 = 0.9971$
- **Target `sa_cfm`**: RMSE `2.418 CFM`, MAE `2.076 CFM`, $R^2 = 1.0000$
- **Target `power`**: RMSE `0.0663 kW`, MAE `0.0498 kW`, $R^2 = 0.9993$
- **Artifact**: `backend/ml/artifacts/state_regressors.joblib`
