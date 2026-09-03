import { API_BASE_URL } from './api';

export interface SNSTestResponse {
  status: string;
  sns_status_code: number;
  investigation_id?: string;
  detail?: string;
}

export interface SNSEventPayload {
  investigation_id: string;
  facility_id: string;
  facility_name: string;
  asset_id: string;
  asset_name: string;
  metric: string;
  current_value: number;
  unit: string;
  timestamp: string;
}

export async function testSNSWebhook(): Promise<SNSTestResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/integrations/sns/test`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'SNS Webhook test failed' }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function sendSNSEvent(payload: SNSEventPayload): Promise<SNSTestResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/integrations/sns/events`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to send SNS event' }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}
