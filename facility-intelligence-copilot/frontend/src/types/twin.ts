export interface TwinRelationship {
  type: string;
  target: string;
}

export interface TwinCurrentState {
  temperature: number;
  energy_kw: number;
  pressure: number;
  airflow: number;
}

export interface TwinAsset {
  asset_id: number;
  status: string;
  health_score: number;
  current_state: TwinCurrentState;
  last_updated: string;
  relationships: TwinRelationship[];
}
