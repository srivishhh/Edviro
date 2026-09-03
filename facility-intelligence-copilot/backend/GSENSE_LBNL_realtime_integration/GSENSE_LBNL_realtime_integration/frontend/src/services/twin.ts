import { apiGet } from './api';
import type { TwinAsset } from '../types/twin';

export async function getTwinAssets(): Promise<TwinAsset[]> {
  return apiGet<TwinAsset[]>('/api/v1/twin/assets');
}

export async function getTwinAsset(assetId: number): Promise<TwinAsset> {
  return apiGet<TwinAsset>(`/api/v1/twin/assets/${assetId}`);
}
