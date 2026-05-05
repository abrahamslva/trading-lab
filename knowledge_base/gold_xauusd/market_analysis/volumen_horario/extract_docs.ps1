Add-Type -AssemblyName System.IO.Compression.FileSystem

function Extract-DocxText {
    param([string]$path)
    $zip = [System.IO.Compression.ZipFile]::OpenRead($path)
    $entry = $zip.Entries | Where-Object { $_.FullName -eq "word/document.xml" }
    $stream = $entry.Open()
    $reader = New-Object System.IO.StreamReader($stream)
    $xml = $reader.ReadToEnd()
    $reader.Close()
    $zip.Dispose()
    $matches2 = [regex]::Matches($xml, '<w:t[^>]*>([^<]+)</w:t>')
    $text = ($matches2 | ForEach-Object { $_.Groups[1].Value }) -join ""
    return $text
}

$doc1 = Extract-DocxText "C:\Users\DELL\Desktop\investigacion xauusd.docx"
$doc2 = Extract-DocxText "C:\Users\DELL\Desktop\BIBLIA COMPLETA DEL TRADING EN ORO.docx"

Write-Host "Doc1 length: $($doc1.Length)"
Write-Host "Doc2 length: $($doc2.Length)"

$doc1 | Set-Content "C:\Users\DELL\Desktop\doc1_inv.txt" -Encoding UTF8
$doc2 | Set-Content "C:\Users\DELL\Desktop\doc2_biblia.txt" -Encoding UTF8

Write-Host "Files saved."
