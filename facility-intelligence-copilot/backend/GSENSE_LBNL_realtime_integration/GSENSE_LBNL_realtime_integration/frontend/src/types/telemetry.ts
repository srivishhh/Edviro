export interface TelemetryPoint {
  timestamp: string;
  temperature: number;
  energy_kw: number;
  pressure: number;
  airflow: number;
}
