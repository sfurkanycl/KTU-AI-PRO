$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
try {
    $inkAssembly = Join-Path ${env:CommonProgramFiles} 'Microsoft Shared/Ink/Microsoft.Ink.dll'
    Add-Type -Path $inkAssembly
    Add-Type -AssemblyName System.Drawing
    Add-Type -ReferencedAssemblies $inkAssembly -TypeDefinition @'
public static class NumberInkReader {
    public static string Read(Microsoft.Ink.Ink ink) {
        var recognizers = new Microsoft.Ink.Recognizers();
        Microsoft.Ink.Recognizer selected = null;
        foreach (Microsoft.Ink.Recognizer recognizer in recognizers) {
            if (recognizer.Languages.Length > 0) { selected = recognizer; break; }
        }
        if (selected == null) return "";
        using (var context = selected.CreateRecognizerContext()) {
            context.Factoid = Microsoft.Ink.Factoid.Number;
            context.Strokes = ink.Strokes;
            Microsoft.Ink.RecognitionStatus status;
            var result = context.Recognize(out status);
            return result == null ? "" : result.TopString;
        }
    }
}
'@
    $payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
    $ink = New-Object Microsoft.Ink.Ink
    foreach ($stroke in $payload.strokes) {
        $points = @($stroke | ForEach-Object {
            [System.Drawing.Point]::new([int]($_[0] * 26.458), [int]($_[1] * 26.458))
        })
        if ($points.Count -ge 2) {
            $null = $ink.CreateStroke([System.Drawing.Point[]]$points)
        }
    }
    if ($ink.Strokes.Count -eq 0) { throw 'No strokes' }
    $recognized = [NumberInkReader]::Read($ink)
    if (-not $recognized) { throw 'Recognition unavailable' }
    @{text = $recognized} | ConvertTo-Json -Compress
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    @{error = 'El yazisi taninamadi. Windows el yazisi bilesenlerini kontrol et veya rakami yeniden yaz.'} | ConvertTo-Json -Compress
    exit 1
} finally {
    if ($ink) { $ink.Dispose() }
}
