export interface Asset {
  id: number;
  asset_code: string;
  name: string;
  asset_type: string;
  status: string;
  health_score: number;
  building_id: number | null;
  floor_id: number | null;
}
