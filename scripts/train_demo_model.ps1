$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $steps = @(
        @{ Name = 'Generate balanced synthetic development data'; Script = 'ml_training\build_development_dataset.py' },
        @{ Name = 'Train the development Random Forest'; Script = 'ml_training\train_model.py' },
        @{ Name = 'Evaluate the development model'; Script = 'ml_training\evaluate_model.py' }
    )

    foreach ($step in $steps) {
        Write-Host "`n=== $($step.Name) ===" -ForegroundColor Cyan
        & py -3.13 $step.Script
        if ($LASTEXITCODE -ne 0) {
            throw "Step failed with exit code $LASTEXITCODE : $($step.Script)"
        }
    }

    Write-Host "`nDevelopment model training and evaluation completed." -ForegroundColor Green
    Write-Host 'This model uses synthetic data and is marked demo=true.' -ForegroundColor Yellow
}
finally {
    Pop-Location
}
