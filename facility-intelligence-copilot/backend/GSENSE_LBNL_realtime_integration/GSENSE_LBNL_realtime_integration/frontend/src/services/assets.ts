import { apiGet } from './api';
import type { Asset } from '../types/asset';

export async function getAssets(): Promise<Asset[]> {
  return apiGet<Asset[]>('/api/v1/assets');
}

export async function getAsset(id: number): Promise<Asset> {
  return apiGet<Asset>(`/api/v1/assets/${id}`);
}
