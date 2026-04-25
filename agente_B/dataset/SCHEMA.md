# Esquema del Dataset - Agente B

Archivo objetivo: `video_metadata.csv`

Cada fila representa un video de TikTok procesado por el Agente B.

Columnas:
- Se conserva la mayor cantidad posible de claves devueltas por yt-dlp.
- Las columnas prioritarias de negocio se colocan al inicio:
	- `id`: identificador unico del video.
	- `title`: titulo del video.
	- `description`: descripcion o caption del video.
	- `view_count`: numero de visualizaciones.
	- `like_count`: numero de likes.
	- `repost_count`: numero de reposts (si existe en metadatos).
	- `comment_count`: numero de comentarios.
	- `upload_date`: fecha de subida en formato de origen de yt-dlp (usualmente `YYYYMMDD`).
- El resto de campos se agregan como columnas adicionales (por ejemplo `channel`, `duration`, `thumbnails`, `formats`, etc.).
- Si un campo es anidado (`dict` o `list`), se serializa en texto JSON dentro de la celda.

Notas:
- El CSV usa `quoting=csv.QUOTE_ALL` para encapsular todos los valores entre comillas.
- El script agrega nuevas filas al archivo, permitiendo construir historial para futuros re-entrenamientos.
- Si aparecen nuevas claves en extracciones futuras, el dataset evoluciona y agrega columnas nuevas sin perder filas anteriores.
