# Run this from PowerShell:
# cd "C:\Users\Bassam Khalid\Desktop\Image Cap"
# .\scripts\download_images.ps1

$corpusDir = "C:\Users\Bassam Khalid\Desktop\Image Cap\corpus"
New-Item -ItemType Directory -Force -Path $corpusDir | Out-Null

# Picsum Photos - free, no API key, real photos, 400x300
# Each number gives a different photo
$images = @{
    "fox1.jpg"   = "https://picsum.photos/seed/fox1/400/300"
    "fox2.jpg"   = "https://picsum.photos/seed/fox2/400/300"
    "fox3.jpg"   = "https://picsum.photos/seed/fox3/400/300"
    "fox4.jpg"   = "https://picsum.photos/seed/fox4/400/300"
    "fox5.jpg"   = "https://picsum.photos/seed/fox5/400/300"
    "fox6.jpg"   = "https://picsum.photos/seed/fox6/400/300"
    "fox7.jpg"   = "https://picsum.photos/seed/fox7/400/300"
    "fox8.jpg"   = "https://picsum.photos/seed/fox8/400/300"
    "fox9.jpg"   = "https://picsum.photos/seed/fox9/400/300"
    "fox10.jpg"  = "https://picsum.photos/seed/fox10/400/300"
    "wolf1.jpg"  = "https://picsum.photos/seed/wolf1/400/300"
    "wolf2.jpg"  = "https://picsum.photos/seed/wolf2/400/300"
    "wolf3.jpg"  = "https://picsum.photos/seed/wolf3/400/300"
    "wolf4.jpg"  = "https://picsum.photos/seed/wolf4/400/300"
    "wolf5.jpg"  = "https://picsum.photos/seed/wolf5/400/300"
    "wolf6.jpg"  = "https://picsum.photos/seed/wolf6/400/300"
    "wolf7.jpg"  = "https://picsum.photos/seed/wolf7/400/300"
    "wolf8.jpg"  = "https://picsum.photos/seed/wolf8/400/300"
    "wolf9.jpg"  = "https://picsum.photos/seed/wolf9/400/300"
    "wolf10.jpg" = "https://picsum.photos/seed/wolf10/400/300"
    "dog1.jpg"   = "https://picsum.photos/seed/dog1/400/300"
    "dog2.jpg"   = "https://picsum.photos/seed/dog2/400/300"
    "dog3.jpg"   = "https://picsum.photos/seed/dog3/400/300"
    "dog4.jpg"   = "https://picsum.photos/seed/dog4/400/300"
    "dog5.jpg"   = "https://picsum.photos/seed/dog5/400/300"
    "dog6.jpg"   = "https://picsum.photos/seed/dog6/400/300"
    "dog7.jpg"   = "https://picsum.photos/seed/dog7/400/300"
    "dog8.jpg"   = "https://picsum.photos/seed/dog8/400/300"
    "dog9.jpg"   = "https://picsum.photos/seed/dog9/400/300"
    "dog10.jpg"  = "https://picsum.photos/seed/dog10/400/300"
    "bear1.jpg"  = "https://picsum.photos/seed/bear1/400/300"
    "bear2.jpg"  = "https://picsum.photos/seed/bear2/400/300"
    "bear3.jpg"  = "https://picsum.photos/seed/bear3/400/300"
    "bear4.jpg"  = "https://picsum.photos/seed/bear4/400/300"
    "bear5.jpg"  = "https://picsum.photos/seed/bear5/400/300"
    "bear6.jpg"  = "https://picsum.photos/seed/bear6/400/300"
    "bear7.jpg"  = "https://picsum.photos/seed/bear7/400/300"
    "bear8.jpg"  = "https://picsum.photos/seed/bear8/400/300"
    "bear9.jpg"  = "https://picsum.photos/seed/bear9/400/300"
    "bear10.jpg" = "https://picsum.photos/seed/bear10/400/300"
    "deer1.jpg"  = "https://picsum.photos/seed/deer1/400/300"
    "deer2.jpg"  = "https://picsum.photos/seed/deer2/400/300"
    "deer3.jpg"  = "https://picsum.photos/seed/deer3/400/300"
    "deer4.jpg"  = "https://picsum.photos/seed/deer4/400/300"
    "deer5.jpg"  = "https://picsum.photos/seed/deer5/400/300"
    "deer6.jpg"  = "https://picsum.photos/seed/deer6/400/300"
    "deer7.jpg"  = "https://picsum.photos/seed/deer7/400/300"
    "deer8.jpg"  = "https://picsum.photos/seed/deer8/400/300"
    "deer9.jpg"  = "https://picsum.photos/seed/deer9/400/300"
    "deer10.jpg" = "https://picsum.photos/seed/deer10/400/300"
}

$i = 1
$total = $images.Count
foreach ($entry in $images.GetEnumerator()) {
    $dest = Join-Path $corpusDir $entry.Key
    if (Test-Path $dest) {
        Write-Host "[$i/$total] Skipping $($entry.Key) (exists)"
    } else {
        Write-Host "[$i/$total] Downloading $($entry.Key)..."
        try {
            Invoke-WebRequest -Uri $entry.Value -OutFile $dest -UseBasicParsing
            Write-Host "  OK"
        } catch {
            Write-Host "  FAILED: $_"
        }
    }
    $i++
}

$count = (Get-ChildItem $corpusDir -Filter "*.jpg").Count
Write-Host "`nDone! $count images in $corpusDir"
