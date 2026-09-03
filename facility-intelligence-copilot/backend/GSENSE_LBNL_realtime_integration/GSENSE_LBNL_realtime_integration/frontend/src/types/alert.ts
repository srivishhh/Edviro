export interface Alert {
  id: number;
  asset_id: number;
  alert_type: string;
  severity: string;
  message: string;
  anomaly_score: number;
  detected_at: string;
  status: string;
}

export interface AlertUpdate {
  status: string;
}
