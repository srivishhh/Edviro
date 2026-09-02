import { apiGet } from './api';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000';

export interface EvidenceItem {
    source: string;
    metric: string;
    value?: number | string;
    current_value?: number | string;
    baseline?: number | string;
    expected_range?: string;
    timestamp?: string;
    interpretation?: string;
    importance?: number;
}

export interface InvestigationResult {
    investigation_id: string;
    asset_id: number;
    alert_id: number;
    status: string;
    summary?: string;
    root_cause?: string;
    confidence?: string;
    severity?: string;
    evidence?: EvidenceItem[];
    observed?: string[];
    inferred?: string[];
    alternative_causes?: string[];
    affected_assets?: string[];
    recommended_actions?: string[];
    created_at: string;
}


export async function createInvestigation(assetId: number, alertId: number): Promise<InvestigationResult> {
    const url = `${API_BASE_URL}/api/v1/xray/investigations`;
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ asset_id: assetId, alert_id: alertId }),
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Request failed with status ${response.status}`);
    }

    return response.json();
}

export async function getInvestigation(investigationId: string): Promise<InvestigationResult> {
    return apiGet<InvestigationResult>(`/api/v1/xray/investigations/${investigationId}`);
}
