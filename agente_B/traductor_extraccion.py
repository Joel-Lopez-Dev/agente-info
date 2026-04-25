import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


TRAINING_FIELDS = [
    "video_id",
    "upload_date",
    "timestamp",
    "duration",
    "creator_channel",
    "creator_handle",
    "title",
    "description",
    "hashtags_list",
    "hashtags_count",
    "mentions_list",
    "mentions_count",
    "music_track",
    "music_artist",
    "music_artists",
    "view_count",
    "like_count",
    "comment_count",
    "repost_count",
    "save_count",
    "comments_sample",
    "comments_sample_count",
    "source_url",
]


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_valid_tiktok_url(url: str) -> bool:
    pattern = re.compile(
        r"^https?://((www|m|vt|vm)\.)?tiktok\.com/.+",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))


def extract_video_id(url: str) -> str:
    match = re.search(r"/video/(\d+)", url)
    if not match:
        raise RuntimeError(
            "No se pudo extraer video_id de la URL. Usa una URL final que contenga /video/<id>."
        )
    return match.group(1)


def run_yt_dlp(
    url: str,
    cookies_browser: str = "chrome",
    cookies_file: str = "",
    use_browser_cookies: bool = True,
) -> dict:
    command = ["yt-dlp", "--dump-json", "--skip-download"]

    if cookies_file:
        command.extend(["--cookies", cookies_file])
    elif use_browser_cookies and cookies_browser:
        command.extend(["--cookies-from-browser", cookies_browser])

    command.append(url)

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "No se encontro 'yt-dlp' en el sistema. Instala yt-dlp y vuelve a intentarlo."
        ) from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(f"Error al ejecutar yt-dlp: {stderr}")

    raw_lines = [line for line in (result.stdout or "").splitlines() if line.strip()]
    if not raw_lines:
        raise RuntimeError("yt-dlp no devolvio metadatos JSON para la URL proporcionada.")

    # TikTok single-video URL should yield one JSON object.
    first_json_line = raw_lines[0]
    try:
        return json.loads(first_json_line)
    except json.JSONDecodeError as exc:
        raise RuntimeError("No se pudo decodificar el JSON de salida de yt-dlp.") from exc


def run_tiktokapi(
    url: str,
    ms_token: str = "",
    browser: str = "chromium",
    headless: bool = True,
    comments_per_video: int = 0,
    comments_headless: bool | None = None,
) -> dict:
    try:
        import asyncio
        from TikTokApi import TikTokApi
    except ImportError as exc:
        raise RuntimeError(
            "Faltan dependencias para source=tiktokapi. Instala requirements y playwright."
        ) from exc

    video_id = extract_video_id(url)

    async def _fetch() -> dict:
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[ms_token] if ms_token else None,
                num_sessions=1,
                sleep_after=3,
                browser=browser,
                headless=headless,
            )
            video = api.video(id=video_id, url=url)
            info = await video.info()
            payload = info if isinstance(info, dict) else {}

            # Optional public comments retrieval inspired by the upstream repo example.
            comments: list[dict[str, Any]] = []
            if comments_per_video > 0:
                try:
                    if comments_headless is not None and comments_headless != headless:
                        await api.close_sessions()
                        await api.create_sessions(
                            ms_tokens=[ms_token] if ms_token else None,
                            num_sessions=1,
                            sleep_after=3,
                            browser=browser,
                            headless=comments_headless,
                        )
                        video = api.video(id=video_id, url=url)

                    async for comment in video.comments(count=comments_per_video):
                        data = getattr(comment, "as_dict", {}) or {}
                        user = data.get("user") or {}
                        comments.append(
                            {
                                "id": data.get("cid"),
                                "text": data.get("text"),
                                "author": user.get("unique_id") or user.get("nickname"),
                                "author_id": user.get("uid"),
                                "likes": data.get("digg_count"),
                                "reply_count": data.get("reply_comment_total"),
                                "created_at": data.get("create_time"),
                            }
                        )
                        if len(comments) >= comments_per_video:
                            break
                except Exception as exc:
                    payload["comments_error"] = f"{type(exc).__name__}: {exc}"

            payload["comments"] = comments
            payload["comments_extracted_count"] = len(comments)
            return payload

    try:
        raw = asyncio.run(_fetch())
    except Exception as exc:
        raise RuntimeError(f"Error al extraer con TikTokApi: {exc}") from exc

    return map_tiktokapi_to_unified_schema(raw, url)


def map_tiktokapi_to_unified_schema(raw: dict, source_url: str) -> dict:
    author = raw.get("author") or {}
    stats = raw.get("stats") or raw.get("statistics") or {}
    music = raw.get("music") or {}

    created = raw.get("createTime")
    timestamp = None
    upload_date = None
    if created is not None:
        try:
            timestamp = int(created)
            upload_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y%m%d")
        except Exception:
            timestamp = None
            upload_date = None

    artist_name = music.get("authorName")
    artists = [artist_name] if artist_name else []
    comments = raw.get("comments") or []

    return {
        "id": raw.get("id"),
        "title": raw.get("desc") or "",
        "description": raw.get("desc") or "",
        "channel": author.get("nickname"),
        "uploader": author.get("uniqueId") or author.get("unique_id") or author.get("nickname"),
        "track": music.get("title"),
        "artist": artist_name,
        "artists": artists,
        "duration": raw.get("video", {}).get("duration") or raw.get("duration"),
        "timestamp": timestamp,
        "upload_date": upload_date,
        "view_count": stats.get("playCount") or stats.get("play_count"),
        "like_count": stats.get("diggCount") or stats.get("digg_count"),
        "comment_count": stats.get("commentCount") or stats.get("comment_count"),
        "repost_count": stats.get("shareCount") or stats.get("share_count"),
        "save_count": stats.get("collectCount") or stats.get("collect_count"),
        "comments": comments,
        "comments_extracted_count": raw.get("comments_extracted_count") or len(comments),
        "original_url": source_url,
        "webpage_url": source_url,
    }


def load_video_json_from_file(input_path: Path) -> dict:
    if not input_path.exists() or not input_path.is_file():
        raise RuntimeError(f"El archivo de entrada no existe: {input_path}")

    try:
        raw_text = input_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"No se pudo leer el archivo de entrada: {exc}") from exc

    if not raw_text:
        raise RuntimeError("El archivo de entrada esta vacio.")

    # Allows both a full JSON object file and a one-line dump-json style file.
    first_line = next((line for line in raw_text.splitlines() if line.strip()), "")
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        try:
            return json.loads(first_line)
        except json.JSONDecodeError as exc:
            raise RuntimeError("El archivo no contiene un JSON valido.") from exc


def save_raw_json(video_json: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_path.write_text(
            json.dumps(video_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(f"No se pudo guardar el JSON crudo: {exc}") from exc


def _serialize_nested(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def extract_hashtags(text: str) -> list[str]:
    return sorted({tag.lower() for tag in re.findall(r"#([\w_]+)", text)})


def extract_mentions(text: str) -> list[str]:
    return sorted({mention.lower() for mention in re.findall(r"@([A-Za-z0-9._]+)", text)})


def build_training_record(video_json: dict) -> dict:
    title = str(video_json.get("title") or "")
    description = str(video_json.get("description") or "")
    combined_text = f"{title} {description}".strip()

    hashtags = extract_hashtags(combined_text)
    mentions = extract_mentions(combined_text)
    comments = video_json.get("comments") or []
    comments_text = []
    for item in comments:
        if isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                comments_text.append(text.strip())

    return {
        "video_id": video_json.get("id"),
        "upload_date": video_json.get("upload_date"),
        "timestamp": video_json.get("timestamp"),
        "duration": video_json.get("duration"),
        "creator_channel": video_json.get("channel"),
        "creator_handle": video_json.get("uploader"),
        "title": title,
        "description": description,
        "hashtags_list": hashtags,
        "hashtags_count": len(hashtags),
        "mentions_list": mentions,
        "mentions_count": len(mentions),
        "music_track": video_json.get("track"),
        "music_artist": video_json.get("artist"),
        "music_artists": video_json.get("artists"),
        "view_count": video_json.get("view_count"),
        "like_count": video_json.get("like_count"),
        "comment_count": video_json.get("comment_count"),
        "repost_count": video_json.get("repost_count"),
        "save_count": video_json.get("save_count"),
        "comments_sample": comments_text,
        "comments_sample_count": video_json.get("comments_extracted_count")
        or len(comments_text),
        "source_url": video_json.get("original_url") or video_json.get("webpage_url"),
    }


def normalize_training_metadata(video_json: dict) -> pd.DataFrame:
    record = build_training_record(video_json)
    normalized = {key: _serialize_nested(value) for key, value in record.items()}
    return pd.DataFrame([normalized], columns=TRAINING_FIELDS)


def save_training_jsonl(video_json: dict, output_jsonl: Path) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    record = build_training_record(video_json)
    try:
        with output_jsonl.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False))
            file.write("\n")
    except OSError as exc:
        raise RuntimeError(f"No se pudo guardar JSONL de entrenamiento: {exc}") from exc


def save_dataset(df: pd.DataFrame, output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not output_csv.exists():
        df.to_csv(
            output_csv,
            mode="w",
            index=False,
            header=True,
            quoting=csv.QUOTE_ALL,
        )
        return

    # Merge old/new schemas to avoid data loss when yt-dlp exposes new keys.
    existing_df = pd.read_csv(output_csv, dtype=str)
    existing_cols = list(existing_df.columns)
    new_cols = list(df.columns)
    all_cols = existing_cols + [col for col in new_cols if col not in existing_cols]

    existing_df = existing_df.reindex(columns=all_cols)
    df = df.reindex(columns=all_cols)
    combined = pd.concat([existing_df, df], ignore_index=True)

    combined.to_csv(
        output_csv,
        mode="w",
        index=False,
        header=True,
        quoting=csv.QUOTE_ALL,
    )


def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        # The script still works if python-dotenv is not available.
        pass

    parser = argparse.ArgumentParser(
        description=(
            "Agente B (Traductor): convierte JSON de metadata TikTok a CSV; "
            "opcionalmente puede extraer el JSON desde una URL sin descargar video."
        )
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--input-json",
        default="",
        help=(
            "Ruta al JSON de entrada generado previamente por yt-dlp "
            "(modo recomendado del traductor)."
        ),
    )
    source_group.add_argument(
        "--url",
        default="",
        help=(
            "URL del video de TikTok para extraer JSON y traducirlo a CSV "
            "(modo opcional)."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent / "dataset" / "video_metadata_new.csv"),
        help="Ruta del CSV de salida (por defecto: agente_B/dataset/video_metadata_new.csv)",
    )
    parser.add_argument(
        "--source",
        choices=["ytdlp", "tiktokapi"],
        default="ytdlp",
        help="Fuente de extraccion cuando se usa --url (por defecto: ytdlp).",
    )
    parser.add_argument(
        "--cookies-file",
        default="",
        help=(
            "Archivo cookies.txt (formato Netscape). Si se define, tiene prioridad "
            "sobre --cookies-browser."
        ),
    )
    parser.add_argument(
        "--cookies-browser",
        default="chrome",
        help="Navegador para leer cookies (por defecto: chrome).",
    )
    parser.add_argument(
        "--no-browser-cookies",
        action="store_true",
        help="No intentar leer cookies del navegador.",
    )
    parser.add_argument(
        "--ms-token",
        default="",
        help="ms_token para sesion TikTokApi (opcional pero recomendado).",
    )
    parser.add_argument(
        "--tiktok-browser",
        default="chromium",
        help="Browser para TikTokApi (por defecto: chromium).",
    )
    parser.add_argument(
        "--tiktok-headless",
        action="store_true",
        help="Ejecutar TikTokApi en modo headless.",
    )
    parser.add_argument(
        "--comments-per-video",
        type=int,
        default=int(os.getenv("TIKTOK_COMMENTS_PER_VIDEO", "0")),
        help="Cantidad de comentarios publicos a extraer con source=tiktokapi (0 desactiva).",
    )
    parser.add_argument(
        "--tiktok-comments-headless",
        default="",
        help=(
            "Override para headless al extraer comentarios (true/false). "
            "Si se omite, usa TIKTOK_COMMENTS_HEADLESS o TIKTOK_HEADLESS."
        ),
    )
    parser.add_argument(
        "--save-raw-json",
        default="",
        help=(
            "Ruta opcional para guardar el JSON crudo extraido cuando se usa --url "
            "(ej: agente_B/raw/video_123.json)."
        ),
    )
    args = parser.parse_args()

    try:
        if args.input_json:
            video_json = load_video_json_from_file(Path(args.input_json))
        else:
            if not is_valid_tiktok_url(args.url):
                print("Error: la URL no parece ser valida para TikTok.", file=sys.stderr)
                return 1
            if args.source == "tiktokapi":
                env_ms_token = os.getenv("ms_token") or os.getenv("MS_TOKEN") or ""
                env_browser = os.getenv("TIKTOK_BROWSER") or "chromium"
                env_headless = env_bool("TIKTOK_HEADLESS", True)
                env_comments_headless = env_bool(
                    "TIKTOK_COMMENTS_HEADLESS",
                    False,
                )

                comments_headless_override = None
                if args.tiktok_comments_headless:
                    comments_headless_override = (
                        args.tiktok_comments_headless.strip().lower()
                        in {"1", "true", "yes", "on"}
                    )

                video_json = run_tiktokapi(
                    url=args.url,
                    ms_token=args.ms_token or env_ms_token,
                    browser=args.tiktok_browser or env_browser,
                    headless=args.tiktok_headless or env_headless,
                    comments_per_video=max(args.comments_per_video, 0),
                    comments_headless=(
                        comments_headless_override
                        if comments_headless_override is not None
                        else env_comments_headless
                    ),
                )
            else:
                video_json = run_yt_dlp(
                    url=args.url,
                    cookies_browser=args.cookies_browser,
                    cookies_file=args.cookies_file,
                    use_browser_cookies=not args.no_browser_cookies,
                )
            if args.save_raw_json:
                save_raw_json(video_json, Path(args.save_raw_json))

        training_df = normalize_training_metadata(video_json)
        save_dataset(training_df, Path(args.output))
    except Exception as exc:
        print(f"Fallo en Agente B: {exc}", file=sys.stderr)
        return 1

    print(f"Dataset CSV guardado correctamente en: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
