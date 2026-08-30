param(
    [string]$InputPptx = "outputs/presentation/stablecoin_yield_presentation.pptx",
    [string]$OutputDir = "outputs/presentation/powerpoint_preview",
    [string]$OutputPdf = "outputs/presentation/stablecoin_yield_presentation.pdf",
    [int]$Width = 1600,
    [int]$Height = 900
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))

function Resolve-ProjectPath([string]$PathValue) {
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $root $PathValue))
}

$inputPath = Resolve-ProjectPath $InputPptx
$outputPath = Resolve-ProjectPath $OutputDir
$pdfPath = Resolve-ProjectPath $OutputPdf
$rootPrefix = $root.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
if (-not $outputPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "PowerPoint preview output must remain inside the project root: $outputPath"
}
if (-not $pdfPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "PowerPoint PDF output must remain inside the project root: $pdfPath"
}
if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) {
    throw "Presentation not found: $inputPath"
}

New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path -Parent $pdfPath) -Force | Out-Null
$powerPoint = $null
$presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $presentation = $powerPoint.Presentations.Open($inputPath, $true, $true, $false)
    for ($index = 1; $index -le $presentation.Slides.Count; $index += 1) {
        $fileName = "slide-{0:D2}.png" -f $index
        $slidePath = Join-Path $outputPath $fileName
        if (Test-Path -LiteralPath $slidePath) {
            Remove-Item -LiteralPath $slidePath -Force
        }
        $presentation.Slides.Item($index).Export($slidePath, "PNG", $Width, $Height)
    }
    if (Test-Path -LiteralPath $pdfPath) {
        Remove-Item -LiteralPath $pdfPath -Force
    }
    $presentation.SaveAs($pdfPath, 32)
    $metadata = [ordered]@{
        renderer = "Microsoft PowerPoint"
        renderer_version = $powerPoint.Version
        source = $inputPath
        pdf = $pdfPath
        slide_count = $presentation.Slides.Count
        width = $Width
        height = $Height
        rendered_at_utc = [DateTime]::UtcNow.ToString("o")
    }
    $metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputPath "render_metadata.json") -Encoding utf8
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
    }
    if ($null -ne $powerPoint) {
        $powerPoint.Quit()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Output "powerpoint_preview=$outputPath"
Write-Output "powerpoint_pdf=$pdfPath"
