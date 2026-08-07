# Génère les sources d'assets natifs (assets/) attendues par @capacitor/assets
# à partir de l'icône PWA existante (public/icon-512.png).
#
# L'icône PWA est un carré plein : utilisée telle quelle en foreground d'icône
# adaptative Android, ses bords seraient rognés par les masques du launcher.
# On la réduit donc dans la zone sûre, sur un fond uni de la même teinte.

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root 'public\icon-512.png'
$outDir = Join-Path $root 'assets'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$src = [System.Drawing.Image]::FromFile($source)
Write-Host "Source: $source ($($src.Width)x$($src.Height))"

# Teinte du fond de l'icône, échantillonnée hors du glyphe
$bmpSrc = New-Object System.Drawing.Bitmap $src
$brand = $bmpSrc.GetPixel([int]($src.Width * 0.5), [int]($src.Height * 0.06))
Write-Host ("Couleur de marque detectee: #{0:X2}{1:X2}{2:X2}" -f $brand.R, $brand.G, $brand.B)

function New-Canvas([int]$size, [System.Drawing.Color]$background) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = 'AntiAlias'
    $g.InterpolationMode = 'HighQualityBicubic'
    $g.PixelOffsetMode = 'HighQuality'
    if ($background -ne [System.Drawing.Color]::Empty) { $g.Clear($background) }
    return @($bmp, $g)
}

function Save-Png($bmp, [string]$path) {
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Host "  -> $path"
}

# 1. Icône legacy pleine (1024x1024)
$r = New-Canvas 1024 ([System.Drawing.Color]::Empty)
$r[1].DrawImage($src, 0, 0, 1024, 1024)
Save-Png $r[0] (Join-Path $outDir 'icon-only.png')
$r[1].Dispose(); $r[0].Dispose()

# 2. Foreground adaptatif : glyphe contenu dans la zone sûre (66% du canevas)
$r = New-Canvas 1024 ([System.Drawing.Color]::Empty)
$inset = [int](1024 * 0.19)
$r[1].DrawImage($src, $inset, $inset, 1024 - 2 * $inset, 1024 - 2 * $inset)
Save-Png $r[0] (Join-Path $outDir 'icon-foreground.png')
$r[1].Dispose(); $r[0].Dispose()

# 3. Background adaptatif : aplat de la couleur de marque
$r = New-Canvas 1024 $brand
Save-Png $r[0] (Join-Path $outDir 'icon-background.png')
$r[1].Dispose(); $r[0].Dispose()

# 4/5. Splash screens (2732x2732, logo centré à ~22%)
function New-Splash([System.Drawing.Color]$background, [string]$name) {
    $size = 2732
    $r = New-Canvas $size $background
    $logo = [int]($size * 0.22)
    $pos = [int](($size - $logo) / 2)
    $r[1].DrawImage($src, $pos, $pos, $logo, $logo)
    Save-Png $r[0] (Join-Path $outDir $name)
    $r[1].Dispose(); $r[0].Dispose()
}
New-Splash ([System.Drawing.ColorTranslator]::FromHtml('#f9fafb')) 'splash.png'
New-Splash ([System.Drawing.ColorTranslator]::FromHtml('#111827')) 'splash-dark.png'

$bmpSrc.Dispose(); $src.Dispose()
Write-Host "Assets sources generes dans $outDir"
