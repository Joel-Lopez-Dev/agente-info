# Guía Rápida: Ambiente y Pruebas de Agentes B y D

## 1. Crear y activar ambiente virtual (Windows PowerShell)

1. Ir a la raíz del proyecto:

   D:\404

2. Crear ambiente virtual:

   py -m venv .venv

3. Activar ambiente virtual:

   .\.venv\Scripts\Activate.ps1

4. Actualizar pip:

   py -m pip install --upgrade pip

5. Instalar dependencias:

   py -m pip install -r requirements.txt

6. Verificar dependencias principales:

   py -m pip show pandas
   py -m pip show yt-dlp
   py -m pip show TikTokApi

7. Solo si usaras source=tiktokapi, instalar navegador de Playwright:

   py -m playwright install chromium

## 2. Pruebas del Agente B (Traductor)

### 2.1 Prueba principal con URL valida (source=ytdlp)

Primero generar un JSON de ejemplo desde TikTok (sin descargar video):

yt-dlp --cookies-from-browser chrome --dump-json --skip-download "https://www.tiktok.com/@webcamsdemexico/video/7628412115493162258" > agente_B/salida.txt

Luego traducir JSON a CSV con Agente B (modo principal):

py agente_B/traductor_extraccion.py --input-json "agente_B/salida.txt"

Comando:

py agente_B/traductor_extraccion.py --url "https://www.tiktok.com/@webcamsdemexico/video/7628412115493162258" --source ytdlp

Resultado esperado:
- Mensaje de éxito indicando que se guardaron metadatos.
- Archivo CSV actualizado en agente_B/dataset/video_metadata.csv.

### 2.2 Prueba principal con URL valida (source=tiktokapi)

Comando (si tienes ms_token):

py agente_B/traductor_extraccion.py --url "https://www.tiktok.com/@webcamsdemexico/video/7628412115493162258" --source tiktokapi --ms-token "TU_MS_TOKEN"

Comando (sin ms_token, puede fallar segun sesion/captcha):

py agente_B/traductor_extraccion.py --url "https://www.tiktok.com/@webcamsdemexico/video/7628412115493162258" --source tiktokapi

### 2.3 Verificar dataset generado

Comandos:

Get-ChildItem agente_B/dataset
Get-Content agente_B/dataset/video_metadata_new.csv -TotalCount 2

Resultado esperado:
- Debe existir video_metadata_new.csv.
- Debe verse encabezado con muchas columnas y al menos una fila de datos.

### 2.4 Prueba de manejo de error (URL invalida)

Comando:

py agente_B/traductor_extraccion.py --url "https://google.com"

Resultado esperado:
- Error indicando que la URL no parece válida para TikTok.
- Código de salida distinto de 0.

### 2.5 Prueba con salida personalizada (opcional)

Comando:

py agente_B/traductor_extraccion.py --url "https://www.tiktok.com/@webcamsdemexico/video/7628412115493162258" --output "agente_B/dataset/video_metadata_new.csv"

Tambien en modo traductor:

py agente_B/traductor_extraccion.py --input-json "agente_B/salida.txt" --output "agente_B/dataset/video_metadata_new.csv"

## 3. Pruebas del Agente D (Intérprete)

### 3.1 Crear JSON de ejemplo para diagnóstico

Comando:

@'
{
  "riesgo_detectado": ["violencia", "lenguaje_ofensivo"],
  "score": 0.83,
  "detalle": {
    "confidence": 0.79,
    "categoria": "alto"
  }
}
'@ | Set-Content -Path agente_D/ejemplo_clasificacion.json -Encoding UTF8

### 3.2 Ejecutar diagnóstico

Comando:

py agente_D/interprete_diagnostico.py agente_D/ejemplo_clasificacion.json

Resultado esperado:
- Se imprime un Resumen de Diagnóstico.
- Se imprime una Recomendación para el Usuario.
- Se imprime Ajuste sugerido para Buddy.

### 3.3 Guardar reporte a archivo (opcional)

Comando:

py agente_D/interprete_diagnostico.py agente_D/ejemplo_clasificacion.json --output agente_D/reporte.txt

Verificar archivo:

Get-Content agente_D/reporte.txt -TotalCount 30

### 3.4 Prueba de error por JSON inexistente

Comando:

py agente_D/interprete_diagnostico.py agente_D/no_existe.json

Resultado esperado:
- Error indicando que el archivo JSON de entrada no existe.
- Código de salida distinto de 0.

## 4. Comprobación rápida de sintaxis

Comandos:

py -m py_compile agente_B/traductor_extraccion.py
py -m py_compile agente_D/interprete_diagnostico.py

Resultado esperado:
- Sin errores de compilación.

## 5. Notas útiles

- Agente B no descarga archivos de video porque usa --skip-download.
- El CSV de Agente B conserva gran parte del JSON de yt-dlp en columnas dinámicas.
- Si aparece un error de ejecución por yt-dlp, confirmar instalación y versión:

  py -m yt_dlp --version
