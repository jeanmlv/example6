# example6

$env:THEA_API_KEY = Read-Host "Enter Thea API Key" -AsSecureString


$secureKey = Read-Host "Enter Thea API Key" -AsSecureString

$env:THEA_API_KEY = [System.Net.NetworkCredential]::new(
    "",
    $secureKey
).Password


if ($env:THEA_API_KEY) {
    Write-Host "API Key configured successfully!"
} else {
    Write-Host "API Key not configured."
}


python 00_test_thea_auth.py


import os
import truststore

truststore.inject_into_ssl()

import requests

python 01_extract_video_inventory_multistudy.py --mode test --study QUASAR --max-folders 30


