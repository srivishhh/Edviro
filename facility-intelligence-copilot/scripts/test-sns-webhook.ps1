param()

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "FACILITY INTELLIGENCE COPILOT - SNS WEBHOOK TEST" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$EndpointUrl = "http://127.0.0.1:8000/api/v1/integrations/sns/test"

Write-Host "Calling local FastAPI test endpoint: $EndpointUrl"
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $EndpointUrl -Method Post -ContentType "application/json" -ErrorAction Stop

    Write-Host "SNS CONNECTION TEST" -ForegroundColor Green
    Write-Host "-------------------" -ForegroundColor Green
    Write-Host "Investigation ID: $($response.investigation_id)"
    Write-Host "SNS HTTP Status:  $($response.sns_status_code)"
    Write-Host "Result:           $($response.status)"
    Write-Host "Message:          Payload successfully delivered to SNS Workbench Webhook." -ForegroundColor Green
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    $errorBody = $_.ErrorDetails.Message
    if (-not $errorBody) {
        $errorBody = $_.Exception.Message
    }

    $invId = "INV-001"
    $snsCode = $statusCode
    $status = "failed"
    $errMsg = $errorBody

    try {
        $jsonErr = $errorBody | ConvertFrom-Json
        if ($jsonErr.investigation_id) { $invId = $jsonErr.investigation_id }
        if ($jsonErr.sns_status_code) { $snsCode = $jsonErr.sns_status_code }
        if ($jsonErr.status) { $status = $jsonErr.status }
        if ($jsonErr.error) { $errMsg = $jsonErr.error }
    } catch {
        # Fallback to defaults
    }

    Write-Host "SNS CONNECTION TEST" -ForegroundColor Yellow
    Write-Host "-------------------" -ForegroundColor Yellow
    Write-Host "Investigation ID: $invId"
    Write-Host "SNS HTTP Status:  $snsCode"
    Write-Host "Result:           $status"
    Write-Host "Message:          $errMsg" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
