Add-Type -AssemblyName System.Drawing

$files = @('01_home.png', '02_road_search.png', '04_result_1.png', '06_map_search.png')

foreach ($file in $files) {
    $srcPath = "C:\Users\ant19\projects\propedia\screenshots\$file"

    # 7인치 (1200x1920)
    $dst7Path = "C:\Users\ant19\projects\propedia\screenshots\tablet_7inch\$file"
    $img = [System.Drawing.Image]::FromFile($srcPath)
    $newImg7 = New-Object System.Drawing.Bitmap(1200, 1920)
    $graphics7 = [System.Drawing.Graphics]::FromImage($newImg7)
    $graphics7.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics7.DrawImage($img, 0, 0, 1200, 1920)
    $newImg7.Save($dst7Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics7.Dispose()
    $newImg7.Dispose()

    # 10인치 (1600x2560)
    $dst10Path = "C:\Users\ant19\projects\propedia\screenshots\tablet_10inch\$file"
    $newImg10 = New-Object System.Drawing.Bitmap(1600, 2560)
    $graphics10 = [System.Drawing.Graphics]::FromImage($newImg10)
    $graphics10.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics10.DrawImage($img, 0, 0, 1600, 2560)
    $newImg10.Save($dst10Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics10.Dispose()
    $newImg10.Dispose()

    $img.Dispose()
    Write-Host "Resized: $file"
}

Write-Host "All tablet screenshots created!"
