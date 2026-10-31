#Requires -Version 5.1
<#
.SYNOPSIS
    親亡き後支援データベースのデスクトップショートカットを作成します。
    カスタムアイコン（盾+ハートのモチーフ）を自動生成し、
    ショートカットに設定します。

.DESCRIPTION
    - start.bat へのショートカットをデスクトップに作成
    - stop.bat へのショートカットもデスクトップに作成
    - カスタム .ico ファイルを assets/ に生成
    - 管理者権限は不要

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\create-desktop-shortcut.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─── パス定義 ─────────────────────────────────────────
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$AssetsDir  = Join-Path $ProjectDir "assets"
$StartBat   = Join-Path $ProjectDir "start.bat"
$StopBat    = Join-Path $ProjectDir "stop.bat"
$Desktop    = [Environment]::GetFolderPath("Desktop")

# アイコンファイルパス
$StartIconPath = Join-Path $AssetsDir "oyagami-start.ico"
$StopIconPath  = Join-Path $AssetsDir "oyagami-stop.ico"

# assets ディレクトリ作成
if (-not (Test-Path $AssetsDir)) {
    New-Item -ItemType Directory -Path $AssetsDir -Force | Out-Null
}

# ─── アイコン生成関数 ──────────────────────────────────
function New-AppIcon {
    param(
        [string]$OutPath,
        [string]$Type  # "start" or "stop"
    )

    Add-Type -AssemblyName System.Drawing

    # 複数サイズの ICO を作成（256, 48, 32, 16）
    $sizes = @(256, 48, 32, 16)
    $images = @()

    foreach ($size in $sizes) {
        $bmp = New-Object System.Drawing.Bitmap($size, $size)
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $g.Clear([System.Drawing.Color]::Transparent)

        $scale = $size / 256.0

        if ($Type -eq "start") {
            # ── 起動アイコン: 盾 + ハート ──
            # 背景の丸（濃い青紫）
            $bgBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 79, 70, 229))
            $g.FillEllipse($bgBrush, 8 * $scale, 8 * $scale, 240 * $scale, 240 * $scale)

            # 盾の形（白）
            $shieldBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 255, 255))
            $shieldPoints = @(
                [System.Drawing.PointF]::new(128 * $scale,  40 * $scale),  # 上中央
                [System.Drawing.PointF]::new(200 * $scale,  70 * $scale),  # 右上
                [System.Drawing.PointF]::new(200 * $scale, 140 * $scale),  # 右中
                [System.Drawing.PointF]::new(128 * $scale, 216 * $scale),  # 下中央
                [System.Drawing.PointF]::new( 56 * $scale, 140 * $scale),  # 左中
                [System.Drawing.PointF]::new( 56 * $scale,  70 * $scale)   # 左上
            )
            $g.FillPolygon($shieldBrush, $shieldPoints)

            # ハートマーク（ピンク）
            $heartBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 236, 72, 153))
            $heartSize = 36 * $scale
            # 左の丸
            $g.FillEllipse($heartBrush, (95 * $scale), (90 * $scale), $heartSize, $heartSize)
            # 右の丸
            $g.FillEllipse($heartBrush, (125 * $scale), (90 * $scale), $heartSize, $heartSize)
            # 下の三角
            $heartTriangle = @(
                [System.Drawing.PointF]::new( 93 * $scale, 112 * $scale),
                [System.Drawing.PointF]::new(163 * $scale, 112 * $scale),
                [System.Drawing.PointF]::new(128 * $scale, 160 * $scale)
            )
            $g.FillPolygon($heartBrush, $heartTriangle)

            # DB アイコン（小さな楕円 x2、盾の下部）
            $dbPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 79, 70, 229)), (3 * $scale)
            $g.DrawEllipse($dbPen, (104 * $scale), (165 * $scale), (48 * $scale), (14 * $scale))
            $g.DrawArc($dbPen, (104 * $scale), (175 * $scale), (48 * $scale), (14 * $scale), 0, 180)

            $bgBrush.Dispose()
            $shieldBrush.Dispose()
            $heartBrush.Dispose()
            $dbPen.Dispose()
        }
        else {
            # ── 停止アイコン: 赤い丸 + 白い四角 ──
            $bgBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 220, 38, 38))
            $g.FillEllipse($bgBrush, 8 * $scale, 8 * $scale, 240 * $scale, 240 * $scale)

            $stopBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 255, 255))
            $g.FillRectangle($stopBrush, 88 * $scale, 88 * $scale, 80 * $scale, 80 * $scale)

            $bgBrush.Dispose()
            $stopBrush.Dispose()
        }

        $g.Dispose()
        $images += $bmp
    }

    # ICO ファイル書き出し
    # ICO format: Header (6 bytes) + Directory entries (16 bytes each) + Image data (PNG)
    $ms = New-Object System.IO.MemoryStream

    # 各画像を PNG バイト列に変換
    $pngDataList = @()
    foreach ($img in $images) {
        $pngMs = New-Object System.IO.MemoryStream
        $img.Save($pngMs, [System.Drawing.Imaging.ImageFormat]::Png)
        $pngDataList += , $pngMs.ToArray()
        $pngMs.Dispose()
    }

    $bw = New-Object System.IO.BinaryWriter($ms)

    # ICO Header
    $bw.Write([int16]0)           # Reserved
    $bw.Write([int16]1)           # Type: ICO
    $bw.Write([int16]$sizes.Count) # Number of images

    # Directory entries のオフセット計算
    $dataOffset = 6 + ($sizes.Count * 16)  # Header + Directory

    for ($i = 0; $i -lt $sizes.Count; $i++) {
        $sz = $sizes[$i]
        $pngData = $pngDataList[$i]

        $bw.Write([byte]$(if ($sz -ge 256) { 0 } else { $sz }))  # Width
        $bw.Write([byte]$(if ($sz -ge 256) { 0 } else { $sz }))  # Height
        $bw.Write([byte]0)      # Color palette
        $bw.Write([byte]0)      # Reserved
        $bw.Write([int16]1)     # Color planes
        $bw.Write([int16]32)    # Bits per pixel
        $bw.Write([int32]$pngData.Length)  # Image data size
        $bw.Write([int32]$dataOffset)       # Offset to image data
        $dataOffset += $pngData.Length
    }

    # Image data (PNG)
    foreach ($pngData in $pngDataList) {
        $bw.Write($pngData)
    }

    $bw.Flush()
    [System.IO.File]::WriteAllBytes($OutPath, $ms.ToArray())

    $bw.Dispose()
    $ms.Dispose()
    foreach ($img in $images) { $img.Dispose() }
}

# ─── ショートカット作成関数 ────────────────────────────
function New-Shortcut {
    param(
        [string]$Name,
        [string]$TargetPath,
        [string]$IconPath,
        [string]$Description,
        [string]$WorkingDir
    )

    $ShortcutPath = Join-Path $Desktop "$Name.lnk"

    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $TargetPath
    $Shortcut.WorkingDirectory = $WorkingDir
    $Shortcut.Description = $Description

    if (Test-Path $IconPath) {
        $Shortcut.IconLocation = "$IconPath, 0"
    }

    $Shortcut.Save()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($WScriptShell) | Out-Null

    return $ShortcutPath
}

# ─── メイン処理 ────────────────────────────────────────
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "  親亡き後支援DB - デスクトップショートカット作成" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""

# 前提ファイル確認
if (-not (Test-Path $StartBat)) {
    Write-Host "[ERROR] start.bat が見つかりません: $StartBat" -ForegroundColor Red
    exit 1
}

# アイコン生成
Write-Host "[ICON] 起動アイコンを生成中..." -ForegroundColor Cyan
New-AppIcon -OutPath $StartIconPath -Type "start"
Write-Host "[OK]   $StartIconPath" -ForegroundColor Green

Write-Host "[ICON] 停止アイコンを生成中..." -ForegroundColor Cyan
New-AppIcon -OutPath $StopIconPath -Type "stop"
Write-Host "[OK]   $StopIconPath" -ForegroundColor Green
Write-Host ""

# ショートカット作成
Write-Host "[LINK] 起動ショートカットを作成中..." -ForegroundColor Cyan
$startLink = New-Shortcut `
    -Name "親なき後支援DB 起動" `
    -TargetPath $StartBat `
    -IconPath $StartIconPath `
    -Description "親亡き後支援データベース（Neo4j + API + フロントエンド）を一括起動します" `
    -WorkingDir $ProjectDir
Write-Host "[OK]   $startLink" -ForegroundColor Green

if (Test-Path $StopBat) {
    Write-Host "[LINK] 停止ショートカットを作成中..." -ForegroundColor Cyan
    $stopLink = New-Shortcut `
        -Name "親なき後支援DB 停止" `
        -TargetPath $StopBat `
        -IconPath $StopIconPath `
        -Description "親亡き後支援データベースの全サービスを停止します" `
        -WorkingDir $ProjectDir
    Write-Host "[OK]   $stopLink" -ForegroundColor Green
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "  デスクトップにショートカットを作成しました" -ForegroundColor Magenta
Write-Host ""
Write-Host "  起動: 「親なき後支援DB 起動」 をダブルクリック" -ForegroundColor White
Write-Host "  停止: 「親なき後支援DB 停止」 をダブルクリック" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""
