import os
import re
import unicodedata
import html
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt

from dotenv import load_dotenv
from wordcloud import WordCloud
from collections import Counter

# =========================================================
# CONFIGURAÇÃO DA API DO YOUTUBE
# =========================================================
# No computador, a chave pode ficar no arquivo .env.
# No Streamlit Community Cloud, cadastre a chave em Advanced settings > Secrets:
# YOUTUBE_API_KEY = "sua-chave"
load_dotenv()


def obter_chave_youtube():
    try:
        return st.secrets["YOUTUBE_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.getenv("YOUTUBE_API_KEY")


API_KEY = obter_chave_youtube()

if not API_KEY:
    st.error(
        "A chave da API do YouTube não foi configurada. "
        "No computador, use o arquivo .env. No Streamlit Cloud, use Secrets."
    )
    st.stop()

BASE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
BASE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
BASE_COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
BASE_BING_SEARCH = "https://www.bing.com/search"

# =========================================================
# CANAIS DE NOTÍCIAS E BLOGS DO CEARÁ
# =========================================================
# A comparação é feita após normalizar acentos e letras maiúsculas.
# Para incluir uma nova fonte, acrescente abaixo o nome exibido pelo YouTube.
FONTES_CEARA = {
    "Diário do Nordeste": [
        "Diário do Nordeste", "diariodonordeste"
    ],
    "O POVO": [
        "O POVO", "O POVO Online", "O POVO CBN"
    ],
    "TV Ceará": [
        "TV Ceará", "TVC Ceará"
    ],
    "TV Verdes Mares": [
        "TV Verdes Mares", "G1 Ceará", "G1 CE"
    ],
    "GCMAIS": [
        "GCMAIS", "TV Cidade Fortaleza", "Grupo Cidade de Comunicação"
    ],
    "Sistema Jangadeiro": [
        "TV Jangadeiro", "Jangadeiro", "Tribuna do Ceará"
    ],
    "Blog do Edison Silva": [
        "Blog do Edison Silva", "TV da Transparência"
    ],
    "Ceará Agora": [
        "Ceará Agora", "Ceara Agora"
    ],
    "CN7": [
        "CN7", "Portal CN7"
    ],
    "News Cariri": [
        "News Cariri"
    ],
    "Badalo": [
        "Badalo", "Portal Badalo"
    ],
    "Focus.Jor": [
        "Focus.Jor", "Focus Jor"
    ],
    "Blog do Kempes": [
        "Blog do Kempes"
    ],
    "Assembleia Legislativa do Ceará": [
        "Assembleia Legislativa do Ceará", "ALECE", "TV Assembleia Ceará"
    ],
    "Câmara Municipal de Fortaleza": [
        "Câmara Municipal de Fortaleza", "TV Fortaleza"
    ]
}

st.set_page_config(
    page_title="Eleições Ceará 2026",
    page_icon="🗳️",
    layout="wide"
)

# =========================================================
# ELEIÇÕES CEARÁ 2026
# =========================================================
CANDIDATOS = {
    "Ciro Gomes": {
        "queries": [
            "lançamento pré candidatura Ciro Gomes",
            "pré candidatura Ciro Gomes governo Ceará",
            "Ciro Gomes governador Ceará",
            "Ciro Gomes eleições Ceará 2026",
            "Ciro Gomes candidato governo Ceará"
        ],
        "required_any": ["ciro gomes", "ciro"],
        "accepted_any": [
            "governo", "governador", "ceara", "ceará", "eleicao",
            "eleições", "2026", "pre candidatura", "pré candidatura",
            "campanha", "pesquisa"
        ],
        "blocked_any": ["musica", "música", "clipe", "filme", "gameplay", "minecraft"]
    },

    "Elmano de Freitas": {
        "queries": [
            "Elmano de Freitas governo Ceará",
            "Elmano eleições Ceará 2026",
            "Elmano governador Ceará",
            "Elmano pesquisa eleitoral Ceará",
            "Elmano de Freitas campanha"
        ],
        "required_any": ["elmano", "elmano de freitas"],
        "accepted_any": [
            "governo", "governador", "ceara", "ceará", "eleicao",
            "eleições", "2026", "campanha", "pesquisa"
        ],
        "blocked_any": ["musica", "música", "clipe", "filme", "gameplay"]
    },

    "André Fernandes": {
        "queries": [
            "André Fernandes governo Ceará",
            "André Fernandes eleições Ceará",
            "André Fernandes candidato governador",
            "André Fernandes pesquisa eleitoral",
            "André Fernandes campanha Ceará"
        ],
        "required_any": ["andre fernandes", "andré fernandes"],
        "accepted_any": [
            "governo", "governador", "ceara", "ceará", "eleicao",
            "eleições", "2026", "campanha", "pesquisa"
        ],
        "blocked_any": ["musica", "música", "clipe", "filme", "gameplay"]
    },

    "Cid Gomes": {
        "queries": [
            "Cid Gomes eleições Ceará",
            "Cid Gomes governo Ceará",
            "Cid Gomes campanha",
            "Cid Gomes pesquisa eleitoral",
            "Cid Gomes senador Ceará"
        ],
        "required_any": ["cid gomes", "cid"],
        "accepted_any": [
            "governo", "governador", "ceara", "ceará", "eleicao",
            "eleições", "campanha", "pesquisa", "senador"
        ],
        "blocked_any": ["musica", "música", "clipe", "filme", "gameplay"]
    },

    "Camilo Santana": {
        "queries": [
            "Camilo Santana eleições Ceará",
            "Camilo Santana governo Ceará",
            "Camilo Santana campanha",
            "Camilo Santana pesquisa eleitoral",
            "Camilo Santana ministro educação Ceará"
        ],
        "required_any": ["camilo santana", "camilo"],
        "accepted_any": [
            "governo", "governador", "ceara", "ceará", "eleicao",
            "eleições", "campanha", "pesquisa", "ministro"
        ],
        "blocked_any": ["musica", "música", "clipe", "filme", "gameplay"]
    },

    "Governo Ceará 2026": {
        "queries": [
            "quem ganha governo Ceará 2026",
            "pesquisa governo Ceará 2026",
            "intenção de voto governo Ceará",
            "candidato governo Ceará 2026",
            "cenário eleitoral Ceará 2026"
        ],
        "required_any": [
            "governo ceara", "governo ceará",
            "governador ceara", "governador ceará"
        ],
        "accepted_any": [
            "eleicao", "eleições", "2026", "pesquisa",
            "intenção de voto", "campanha", "candidato"
        ],
        "blocked_any": ["musica", "música", "clipe", "filme", "gameplay"]
    }
}

STOPWORDS_PT = {
    "a", "o", "e", "da", "de", "do", "das", "dos",
    "um", "uma", "uns", "umas", "em", "no", "na", "nos", "nas",
    "para", "por", "com", "sem", "sobre", "entre", "contra",
    "eu", "tu", "ele", "ela", "eles", "elas", "nós", "nos",
    "voces", "vocês", "me", "te", "lhe", "lhes", "meu", "minha",
    "seu", "sua", "dele", "dela", "que", "como", "porque", "pq",
    "quando", "onde", "mais", "menos", "muito", "muita", "muitos",
    "muitas", "tambem", "também", "isso", "isto", "esse", "essa",
    "aquele", "aquela", "sim", "nao", "não", "ja", "já", "vou",
    "vai", "vc", "vcs", "ta", "tá", "to", "tô",
    "youtube", "video", "vídeo", "canal", "comentario", "comentário",
    "link", "live", "podcast", "stream",
    "governo", "governador", "campanha", "candidato", "candidata",
    "eleicao", "eleições", "politica", "política", "pesquisa",
    "debate", "voto", "votar", "prefeito", "presidente", "senador",
    "deputado", "ceara", "ceará", "fortaleza",
    "ciro", "gomes", "elmano", "freitas", "andre", "andré",
    "fernandes", "cid", "camilo", "santana",
    "2024", "2025", "2026",
    "bom", "boa", "otimo", "ótimo", "ruim", "melhor", "pior",
    "grande", "pequeno", "verdade", "verdadeiro", "falso", "fake"
}

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def normalizar_texto(texto: str) -> str:
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"http\S+", " ", texto)
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def contem_qualquer(texto: str, lista_termos: list[str]) -> bool:
    texto_norm = normalizar_texto(texto)
    return any(normalizar_texto(termo) in texto_norm for termo in lista_termos)


def score_texto(texto: str, termos: list[str]) -> int:
    texto_norm = normalizar_texto(texto)
    return sum(1 for termo in termos if normalizar_texto(termo) in texto_norm)


def identificar_fonte_ceara(nome_canal: str) -> str | None:
    """Retorna a fonte autorizada ou None quando o canal não é do Ceará."""
    canal_norm = normalizar_texto(nome_canal)

    for fonte, aliases in FONTES_CEARA.items():
        for alias in aliases:
            alias_norm = normalizar_texto(alias)

            if canal_norm == alias_norm or alias_norm in canal_norm:
                return fonte

    return None


def percentual(valor, total):
    """Calcula percentual para números simples ou colunas pandas."""
    if isinstance(total, (pd.Series, pd.DataFrame)):
        return (valor / total.replace(0, pd.NA)) * 100

    if total == 0:
        return 0

    return (valor / total) * 100


def classificar_sentimento(texto: str) -> str:
    texto = normalizar_texto(texto)

    negativos = [
        "corrupto", "corrupta", "ladr", "roubo", "fraude", "golpe",
        "vergonha", "absurdo", "absurda", "desastre", "pessimo",
        "péssimo", "revoltante", "revoltado", "revoltada",
        "mentiroso", "mentirosa", "incompetente", "indignado",
        "indignada", "crime", "triste", "odio", "ódio"
    ]

    positivos = [
        "bom", "boa", "otimo", "ótimo", "otima", "ótima",
        "excelente", "parabens", "parabéns", "justo", "justa",
        "correto", "correta", "apoio", "confio", "melhor",
        "preparado", "preparada", "capaz"
    ]

    if any(p in texto for p in negativos):
        return "negativo"

    if any(p in texto for p in positivos):
        return "positivo"

    return "neutro"




def score_sentimento(sentimento: str) -> int:
    """Converte sentimento em pontuação para o termômetro."""
    if sentimento == "positivo":
        return 1
    if sentimento == "negativo":
        return -1
    return 0


def gerar_nuvem_palavras_comentarios(df_comentarios: pd.DataFrame):
    if df_comentarios.empty or "comentario" not in df_comentarios.columns:
        return None

    textos_comentarios = " ".join(
        df_comentarios["comentario"].dropna().astype(str).tolist()
    )

    nomes_candidatos = " ".join(
        df_comentarios["candidato"].dropna().astype(str).tolist()
    )

    textos = textos_comentarios + " " + nomes_candidatos
    textos = normalizar_texto(textos)

    stopwords_nuvem = STOPWORDS_PT.copy()

    nomes_para_manter = {
        "ciro", "gomes",
        "elmano", "freitas",
        "andre", "fernandes",
        "cid",
        "camilo", "santana",
        "governo", "ceara"
    }

    stopwords_nuvem = stopwords_nuvem - nomes_para_manter

    palavras = [
        p for p in textos.split()
        if len(p) >= 3
        and p not in stopwords_nuvem
        and not p.isdigit()
    ]

    texto_final = " ".join(palavras).strip()

    if not texto_final:
        return None

    wc = WordCloud(
        width=1400,
        height=650,
        background_color="white",
        colormap="Oranges",
        collocations=False
    ).generate(texto_final)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")

    return fig


# =========================================================
# API YOUTUBE
# =========================================================
def buscar_videos_por_query(
    query,
    max_results=25,
    region_code="BR",
    relevance_language="pt",
    order="relevance"
):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "regionCode": region_code,
        "relevanceLanguage": relevance_language,
        "order": order,
        "key": API_KEY
    }

    resp = requests.get(BASE_SEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()

    return resp.json()


# =========================================================
# MENÇÕES DE CIRO E ELMANO NAS REDES — ÚLTIMAS 24 HORAS
# =========================================================
def _limpar_html(texto):
    texto = html.unescape(str(texto or ""))
    texto = re.sub(r"<[^>]+>", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _candidato_da_mencao(texto):
    texto_norm = normalizar_texto(texto)
    encontrados = []
    if "ciro" in texto_norm:
        encontrados.append("Ciro Gomes")
    if "elmano" in texto_norm:
        encontrados.append("Elmano de Freitas")
    return encontrados


@st.cache_data(ttl=900)
def buscar_mencoes_redes_24h(max_resultados_por_busca=50, region_code="BR"):
    """Busca Ciro e Elmano nas redes durante as 24 horas anteriores."""
    agora_utc = datetime.now(timezone.utc)
    inicio_utc = agora_utc - timedelta(hours=24)
    registros = []

    # YouTube: a API permite impor a janela exata de publicação.
    for candidato, consulta in {
        "Ciro Gomes": "Ciro Gomes Ceará",
        "Elmano de Freitas": "Elmano de Freitas Ceará"
    }.items():
        params = {
            "part": "snippet",
            "q": consulta,
            "type": "video",
            "maxResults": min(50, max_resultados_por_busca),
            "regionCode": region_code,
            "relevanceLanguage": "pt",
            "order": "date",
            "publishedAfter": inicio_utc.isoformat().replace("+00:00", "Z"),
            "publishedBefore": agora_utc.isoformat().replace("+00:00", "Z"),
            "key": API_KEY
        }
        try:
            resposta = requests.get(BASE_SEARCH_URL, params=params, timeout=30)
            resposta.raise_for_status()
            itens = resposta.json().get("items", [])
            ids = [
                item.get("id", {}).get("videoId", "")
                for item in itens
                if item.get("id", {}).get("videoId")
            ]
            detalhes = buscar_detalhes_videos(ids)
            for _, linha in detalhes.iterrows():
                texto = f"{linha.get('titulo', '')} {linha.get('descricao', '')}"
                if candidato not in _candidato_da_mencao(texto):
                    continue
                registros.append({
                    "rede": "YouTube",
                    "candidato": candidato,
                    "titulo": linha.get("titulo", ""),
                    "fonte": linha.get("canal", ""),
                    "publicado_em": linha.get("publicado_em"),
                    "views": int(linha.get("views", 0)),
                    "likes": int(linha.get("likes", 0)),
                    "comentarios": int(linha.get("comentarios", 0)),
                    "url": linha.get("url", ""),
                    "janela": "Últimas 24 horas"
                })
        except Exception as erro:
            print(f"[ERRO] Busca YouTube 24h para {candidato}: {erro}")

    # Instagram, X e TikTok: páginas públicas encontradas pelo índice da web.
    redes = {
        "Instagram": "instagram.com",
        "X": "x.com",
        "TikTok": "tiktok.com"
    }
    for rede, dominio in redes.items():
        for candidato, nome_busca in {
            "Ciro Gomes": '"Ciro Gomes"',
            "Elmano de Freitas": '"Elmano de Freitas"'
        }.items():
            consulta = f"site:{dominio} {nome_busca} Ceará"
            params = {
                "q": consulta,
                "format": "rss",
                "setlang": "pt-BR",
                "freshness": "Day",
                "count": min(50, max_resultados_por_busca)
            }
            try:
                resposta = requests.get(
                    BASE_BING_SEARCH,
                    params=params,
                    timeout=30,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                resposta.raise_for_status()
                raiz = ET.fromstring(resposta.content)
            except Exception as erro:
                print(f"[ERRO] Busca {rede} 24h para {candidato}: {erro}")
                continue

            for item in raiz.findall(".//item")[:max_resultados_por_busca]:
                titulo = _limpar_html(item.findtext("title", ""))
                resumo = _limpar_html(item.findtext("description", ""))
                url = item.findtext("link", "")
                texto = f"{titulo} {resumo}"
                if candidato not in _candidato_da_mencao(texto):
                    continue

                publicado = pd.to_datetime(
                    item.findtext("pubDate", ""), errors="coerce", utc=True
                )
                if pd.notna(publicado) and publicado < pd.Timestamp(inicio_utc):
                    continue

                registros.append({
                    "rede": rede,
                    "candidato": candidato,
                    "titulo": titulo,
                    "fonte": rede,
                    "publicado_em": publicado,
                    "views": 0,
                    "likes": 0,
                    "comentarios": 0,
                    "url": url,
                    "janela": "Últimas 24 horas"
                })

    colunas = [
        "rede", "candidato", "titulo", "fonte", "publicado_em",
        "views", "likes", "comentarios", "url", "janela"
    ]
    if not registros:
        return pd.DataFrame(columns=colunas)

    return (
        pd.DataFrame(registros, columns=colunas)
        .drop_duplicates(subset=["rede", "candidato", "url"], keep="first")
        .sort_values("publicado_em", ascending=False, na_position="last")
        .reset_index(drop=True)
    )


def buscar_detalhes_videos(video_ids):
    if not video_ids:
        return pd.DataFrame()

    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }

    resp = requests.get(BASE_VIDEOS_URL, params=params, timeout=30)
    resp.raise_for_status()

    registros = []

    for item in resp.json().get("items", []):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})

        registros.append({
            "video_id": item.get("id", ""),
            "titulo": snippet.get("title", ""),
            "descricao": snippet.get("description", ""),
            "canal": snippet.get("channelTitle", ""),
            "publicado_em": snippet.get("publishedAt", ""),
            "views": int(stats.get("viewCount", 0)) if "viewCount" in stats else 0,
            "likes": int(stats.get("likeCount", 0)) if "likeCount" in stats else 0,
            "comentarios": int(stats.get("commentCount", 0)) if "commentCount" in stats else 0,
            "url": f"https://www.youtube.com/watch?v={item.get('id', '')}"
        })

    df = pd.DataFrame(registros)

    if not df.empty:
        df["publicado_em"] = pd.to_datetime(df["publicado_em"], errors="coerce")

    return df


def buscar_comentarios(video_id, max_results=50):
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": max_results,
        "order": "relevance",
        "textFormat": "plainText",
        "key": API_KEY
    }

    try:
        resp = requests.get(BASE_COMMENTS_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    comentarios = []

    for item in data.get("items", []):
        try:
            snippet = item["snippet"]["topLevelComment"]["snippet"]

            comentarios.append({
                "video_id": video_id,
                "comentario": snippet.get("textDisplay", ""),
                "autor_comentario": snippet.get("authorDisplayName", ""),
                "like_comentario": int(snippet.get("likeCount", 0)),
                "publicado_em_comentario": snippet.get("publishedAt", "")
            })
        except Exception:
            continue

    return comentarios


# =========================================================
# FILTRO
# =========================================================
def validar_video_candidato(texto_base: str, regra: dict) -> tuple[bool, int]:
    if contem_qualquer(texto_base, regra["blocked_any"]):
        return False, 0

    tem_required = contem_qualquer(texto_base, regra["required_any"])
    tem_accepted = contem_qualquer(texto_base, regra["accepted_any"])

    if not tem_required or not tem_accepted:
        return False, 0

    score = (
        score_texto(texto_base, regra["required_any"]) * 3 +
        score_texto(texto_base, regra["accepted_any"]) * 2
    )

    return True, score


def coletar_videos_candidato(
    nome_candidato,
    regra_candidato,
    max_results_por_busca=20,
    region_code="BR",
    relevance_language="pt",
    order="relevance"
):
    todos = []

    for consulta in regra_candidato["queries"]:
        try:
            # Direciona a busca ao ecossistema jornalístico cearense.
            consulta_ceara = f"{consulta} Ceará notícias"

            data = buscar_videos_por_query(
                query=consulta_ceara,
                max_results=max_results_por_busca,
                region_code=region_code,
                relevance_language=relevance_language,
                order=order
            )

            video_ids = [
                item.get("id", {}).get("videoId")
                for item in data.get("items", [])
                if item.get("id", {}).get("videoId")
            ]

            df_det = buscar_detalhes_videos(video_ids)

            if df_det.empty:
                continue

            # Regra principal: somente canais e blogs autorizados do Ceará.
            df_det["fonte_ceara"] = df_det["canal"].apply(
                identificar_fonte_ceara
            )
            df_det = df_det[df_det["fonte_ceara"].notna()].copy()

            if df_det.empty:
                continue

            df_det["texto_base"] = (
                df_det["titulo"].fillna("") + " " +
                df_det["descricao"].fillna("")
            )

            df_det["candidato"] = nome_candidato
            df_det["consulta_usada"] = consulta_ceara

            flags = df_det["texto_base"].apply(
                lambda x: validar_video_candidato(x, regra_candidato)
            )

            df_det["aprovado"] = flags.apply(lambda x: x[0])
            df_det["score_candidato"] = flags.apply(lambda x: x[1])
            df_det = df_det[df_det["aprovado"]].copy()

            if not df_det.empty:
                todos.append(df_det)

        except Exception as e:
            print(f"[ERRO] Consulta '{consulta}' falhou: {e}")

    if not todos:
        return pd.DataFrame()

    df_final = pd.concat(todos, ignore_index=True)

    df_final = (
        df_final.sort_values(
            by=["views", "score_candidato", "likes", "comentarios"],
            ascending=[False, False, False, False]
        )
        .drop_duplicates(subset=["video_id"], keep="first")
        .reset_index(drop=True)
    )

    return df_final


# =========================================================
# CARGA DE DADOS
# =========================================================
@st.cache_data(ttl=1800)
def carregar_dados(
    max_results_por_busca=20,
    region_code="BR",
    relevance_language="pt",
    order="relevance"
):
    frames = []

    for nome_candidato, regra in CANDIDATOS.items():
        df = coletar_videos_candidato(
            nome_candidato=nome_candidato,
            regra_candidato=regra,
            max_results_por_busca=max_results_por_busca,
            region_code=region_code,
            relevance_language=relevance_language,
            order=order
        )

        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_videos = pd.concat(frames, ignore_index=True)

    ranking_candidato = (
        df_videos.groupby("candidato", as_index=False)
        .agg(
            quantidade_videos=("video_id", "count"),
            total_views=("views", "sum"),
            total_likes=("likes", "sum"),
            total_comentarios=("comentarios", "sum")
        )
        .sort_values(by=["total_views", "quantidade_videos"], ascending=[False, False])
        .reset_index(drop=True)
    )

    ranking_canais = (
        df_videos.groupby("canal", as_index=False)
        .agg(
            quantidade_videos=("video_id", "count"),
            total_views=("views", "sum")
        )
        .sort_values(by=["total_views", "quantidade_videos"], ascending=[False, False])
        .reset_index(drop=True)
    )

    return df_videos, ranking_candidato, ranking_canais


# =========================================================
# COMENTÁRIOS POR CANDIDATO
# =========================================================
@st.cache_data(ttl=1800)
def carregar_comentarios(
    df_videos,
    max_videos_por_candidato=5,
    max_comments_per_video=20
):
    if df_videos.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    comentarios_lista = []
    candidatos_unicos = df_videos["candidato"].unique()

    for candidato in candidatos_unicos:
        df_candidato = (
            df_videos[df_videos["candidato"] == candidato]
            .sort_values(
                by=["views", "likes", "comentarios"],
                ascending=[False, False, False]
            )
            .head(max_videos_por_candidato)
        )

        if df_candidato.empty:
            continue

        mapa_video_titulo = dict(zip(df_candidato["video_id"], df_candidato["titulo"]))
        mapa_video_canal = dict(zip(df_candidato["video_id"], df_candidato["canal"]))

        for video_id in df_candidato["video_id"]:
            comentarios = buscar_comentarios(
                video_id,
                max_results=max_comments_per_video
            )

            for c in comentarios:
                texto = c["comentario"]

                comentarios_lista.append({
                    "video_id": video_id,
                    "candidato": candidato,
                    "titulo_video": mapa_video_titulo.get(video_id, ""),
                    "canal": mapa_video_canal.get(video_id, ""),
                    "comentario": texto,
                    "sentimento": classificar_sentimento(texto),
                    "autor_comentario": c["autor_comentario"],
                    "like_comentario": c["like_comentario"],
                    "publicado_em_comentario": c["publicado_em_comentario"]
                })

    df_comentarios = pd.DataFrame(comentarios_lista)

    if df_comentarios.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    ranking_sentimento = (
        df_comentarios.groupby("sentimento", as_index=False)
        .agg(quantidade=("comentario", "count"))
        .sort_values(by="quantidade", ascending=False)
        .reset_index(drop=True)
    )

    ranking_sentimento_candidato = (
        df_comentarios.groupby(["candidato", "sentimento"], as_index=False)
        .agg(quantidade=("comentario", "count"))
    )

    sentimentos = ["positivo", "negativo", "neutro"]
    linhas_completas = []

    for cand in candidatos_unicos:
        for sent in sentimentos:
            filtro = ranking_sentimento_candidato[
                (ranking_sentimento_candidato["candidato"] == cand) &
                (ranking_sentimento_candidato["sentimento"] == sent)
            ]

            if filtro.empty:
                linhas_completas.append({
                    "candidato": cand,
                    "sentimento": sent,
                    "quantidade": 0
                })

    if linhas_completas:
        ranking_sentimento_candidato = pd.concat(
            [
                ranking_sentimento_candidato,
                pd.DataFrame(linhas_completas)
            ],
            ignore_index=True
        )

    # PERCENTUAL POR LINHA:
    # positivo soma 100%, neutro soma 100%, negativo soma 100%
    ranking_sentimento_candidato["percentual"] = (
        ranking_sentimento_candidato.groupby("sentimento")["quantidade"]
        .transform(
            lambda x: (
                (x / x.sum()) * 100
                if x.sum() > 0
                else 0
            )
        )
    )

    return df_comentarios, ranking_sentimento, ranking_sentimento_candidato


# =========================================================
# DASHBOARD
# =========================================================
st.title("🗳️ Eleições Ceará 2026")
st.markdown("""
Monitoramento político em **canais de notícias e blogs do Ceará**:
- Ciro Gomes
- Elmano de Freitas
- André Fernandes
- Cid Gomes
- Camilo Santana
- Governo do Ceará 2026

Somente vídeos publicados pelas fontes cearenses autorizadas entram nos gráficos.
""")

with st.sidebar:
    st.header("Filtros")

    region_code = st.selectbox("País", ["BR", "PT", "US"], index=0)
    relevance_language = st.selectbox("Idioma", ["pt", "en", "es"], index=0)
    order = st.selectbox("Ordenação da busca", ["relevance", "date"], index=0)
    max_results_por_busca = st.slider("Vídeos por consulta", 5, 50, 25)

    st.markdown("---")
    st.subheader("Comentários por candidato")

    max_videos_comentarios = st.slider("Vídeos por candidato", 1, 10, 5)
    max_comments_per_video = st.slider("Comentários por vídeo", 5, 50, 20)

    st.markdown("---")
    st.subheader("🌐 Redes — últimas 24 horas")
    incluir_redes_24h = st.checkbox(
        "Procurar Ciro e Elmano nas redes",
        value=True
    )
    max_resultados_redes_24h = st.slider(
        "Resultados por nome e rede",
        10,
        50,
        50,
        10
    )

    with st.expander("Fontes cearenses monitoradas"):
        for nome_fonte in FONTES_CEARA:
            st.write(f"• {nome_fonte}")

    st.markdown("---")
    st.subheader("⚔️ Comparação Dinâmica")

    candidato_a = st.selectbox(
    "Candidato A",
    list(CANDIDATOS.keys()),
    index=0
    )

    candidato_b = st.selectbox(
    "Candidato B",
    list(CANDIDATOS.keys()),
    index=1
    )

    periodo_dias = st.slider(
    "Período de análise (dias)",
    5,
    90,
    30
    )

    atualizar = st.button("Atualizar dados")

if atualizar:
    st.cache_data.clear()

try:
    df_videos, ranking_candidato, ranking_canais = carregar_dados(
        max_results_por_busca=max_results_por_busca,
        region_code=region_code,
        relevance_language=relevance_language,
        order=order
    )
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

if df_videos.empty:
    st.warning(
        "Nenhum vídeo dos canais e blogs autorizados do Ceará foi encontrado. "
        "Tente aumentar 'Vídeos por consulta' ou acrescente o nome do canal em FONTES_CEARA."
    )
    st.stop()

with st.spinner("Lendo comentários por candidato..."):
    df_comentarios, ranking_sentimento, ranking_sentimento_candidato = carregar_comentarios(
        df_videos=df_videos,
        max_videos_por_candidato=max_videos_comentarios,
        max_comments_per_video=max_comments_per_video
    )
    if df_comentarios.empty:
        df_comparacao = pd.DataFrame()
    else:
        df_comparacao = df_comentarios[
            df_comentarios["candidato"].isin([candidato_a, candidato_b])
        ].copy()

if incluir_redes_24h:
    with st.spinner("Procurando Ciro e Elmano nas redes nas últimas 24 horas..."):
        df_redes_24h = buscar_mencoes_redes_24h(
            max_resultados_por_busca=max_resultados_redes_24h,
            region_code=region_code
        )
else:
    df_redes_24h = pd.DataFrame()

# =========================================================
# CIRO E ELMANO NAS REDES — ÚLTIMAS 24 HORAS
# =========================================================
st.header("🌐 Ciro e Elmano nas redes — últimas 24 horas")
st.caption(
    "Busca adicional em YouTube, Instagram, X e TikTok. "
    "No YouTube, o período é aplicado diretamente pela API. Nas outras redes, "
    "entram somente páginas públicas recentes encontradas pelo índice da web."
)

if df_redes_24h.empty:
    st.info("Nenhuma publicação pública foi encontrada na janela das últimas 24 horas.")
else:
    resumo_redes_24h = (
        df_redes_24h.groupby(["rede", "candidato"], as_index=False)
        .agg(publicacoes=("url", "nunique"))
    )

    r1, r2, r3, r4 = st.columns(4)
    r1.metric(
        "Publicações únicas",
        f"{df_redes_24h['url'].nunique():,}".replace(",", ".")
    )
    r2.metric(
        "Menções a Ciro",
        f"{df_redes_24h.loc[df_redes_24h['candidato'] == 'Ciro Gomes', 'url'].nunique():,}".replace(",", ".")
    )
    r3.metric(
        "Menções a Elmano",
        f"{df_redes_24h.loc[df_redes_24h['candidato'] == 'Elmano de Freitas', 'url'].nunique():,}".replace(",", ".")
    )
    r4.metric(
        "Redes com resultado",
        f"{df_redes_24h['rede'].nunique():,}".replace(",", ".")
    )

    fig_redes_24h = px.bar(
        resumo_redes_24h,
        x="rede",
        y="publicacoes",
        color="candidato",
        barmode="group",
        text="publicacoes",
        title="Publicações encontradas por rede e candidato — últimas 24 horas"
    )
    fig_redes_24h.update_layout(
        xaxis_title="Rede",
        yaxis_title="Quantidade de publicações",
        legend_title="Candidato"
    )
    st.plotly_chart(fig_redes_24h, use_container_width=True)

    st.dataframe(
        df_redes_24h[
            [
                "rede", "candidato", "titulo", "fonte", "publicado_em",
                "views", "likes", "comentarios", "url"
            ]
        ],
        use_container_width=True,
        hide_index=True,
        height=500
    )

# =========================================================
# KPIs
# =========================================================
total_views = df_videos["views"].sum()
total_likes = df_videos["likes"].sum()
total_comentarios = df_videos["comentarios"].sum()

perc_likes = percentual(total_likes, total_views)
perc_comentarios = percentual(total_comentarios, total_views)
perc_engajamento = percentual(total_likes + total_comentarios, total_views)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total de Vídeos", f"{len(df_videos):,}".replace(",", "."))

c2.metric("Total de Curtidas", f"{int(total_likes):,}".replace(",", "."))

c3.metric("Total de Comentários", f"{int(total_comentarios):,}".replace(",", "."))

c4.metric("Total de Engajamento", f"{int(total_likes + total_comentarios):,}".replace(",", "."))

# =========================================================
# PERCENTUAIS
# =========================================================
ranking_candidato["perc_views"] = percentual(
    ranking_candidato["total_views"],
    ranking_candidato["total_views"].sum()
)

ranking_candidato["perc_likes"] = percentual(
    ranking_candidato["total_likes"],
    ranking_candidato["total_likes"].sum()
)

ranking_candidato["perc_comentarios"] = percentual(
    ranking_candidato["total_comentarios"],
    ranking_candidato["total_comentarios"].sum()
)

ranking_canais["perc_views"] = percentual(
    ranking_canais["total_views"],
    ranking_canais["total_views"].sum()
)

# =========================================================
# GRÁFICOS
# =========================================================
g1, g2 = st.columns(2)

with g1:
    st.subheader(" Percentual de Views por Candidato")

    fig1 = px.bar(
        ranking_candidato,
        x="candidato",
        y="perc_views",
        text=ranking_candidato["perc_views"].round(1).astype(str) + "%",
        color="candidato"
    )

    fig1.update_layout(
        xaxis_title="Candidato",
        yaxis_title="Percentual (%)"
    )

    st.plotly_chart(fig1, use_container_width=True)

with g2:
    st.subheader(" Percentual de Views por Canal")

    top_canais = ranking_canais.head(15).copy()

    fig2 = px.bar(
        top_canais,
        x="perc_views",
        y="canal",
        orientation="h",
        text=top_canais["perc_views"].round(1).astype(str) + "%"
    )

    fig2.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Percentual (%)",
        yaxis_title="Canal"
    )

    st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# MAPA DE CALOR COMENTÁRIOS %
# =========================================================
st.subheader(" Percentual de Comentários por Candidato")

heatmap_df = ranking_candidato[["candidato", "perc_comentarios"]].copy()

if not heatmap_df.empty:
    matriz_heatmap = pd.DataFrame(
        [heatmap_df["perc_comentarios"].tolist()],
        columns=heatmap_df["candidato"].tolist(),
        index=["Comentários (%)"]
    )

    fig3 = px.imshow(
        matriz_heatmap,
        text_auto=".1f",
        aspect="auto",
        labels=dict(x="Candidato", y="", color="%"),
        color_continuous_scale="Oranges"
    )

    st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# SENTIMENTO %
# =========================================================
st.subheader(" Distribuição percentual dos candidatos dentro de cada sentimento")

if not df_comentarios.empty:
    ranking_sentimento["percentual"] = percentual(
        ranking_sentimento["quantidade"],
        ranking_sentimento["quantidade"].sum()
    )

    c5, c6 = st.columns(2)

    with c5:
        fig4 = px.bar(
            ranking_sentimento,
            x="sentimento",
            y="percentual",
            text=ranking_sentimento["percentual"].round(1).astype(str) + "%",
            color="sentimento",
            color_discrete_map={
                "positivo": "green",
                "negativo": "red",
                "neutro": "lightgray"
            }
        )

        fig4.update_layout(
            xaxis_title="Sentimento",
            yaxis_title="Percentual (%)",
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        st.plotly_chart(fig4, use_container_width=True)

    with c6:
        pivot_sentimento = (
            ranking_sentimento_candidato
            .pivot_table(
                index="sentimento",
                columns="candidato",
                values="percentual",
                aggfunc="sum"
            )
            .fillna(0)
        )

        pivot_sentimento = pivot_sentimento.reindex(
            ["positivo", "neutro", "negativo"]
        )

        fig5 = px.imshow(
            pivot_sentimento,
            text_auto=".1f",
            aspect="auto",
            labels=dict(
                x="Candidato",
                y="Sentimento",
                color="%"
            ),
            color_continuous_scale="Oranges"
        )

        fig5.update_layout(
            title="Percentual por linha: cada sentimento soma 100%",
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        st.plotly_chart(fig5, use_container_width=True)

    # =========================================================
    # TERMÔMETRO DE SENTIMENTO DOS CANDIDATOS
    # =========================================================
    st.subheader("🌡️ Termômetro médio de sentimento por candidato")

    df_termometro = df_comentarios.copy()
    df_termometro["score_sentimento"] = df_termometro["sentimento"].apply(score_sentimento)

    termometro = (
        df_termometro
        .groupby("candidato", as_index=False)
        .agg(
            indice_medio=("score_sentimento", "mean"),
            comentarios_analisados=("comentario", "count")
        )
    )

    termometro["termometro"] = (termometro["indice_medio"] * 100).round(1)
    media_geral = termometro["termometro"].mean().round(1)

    col_t1, col_t2 = st.columns([1, 2])

    with col_t1:
        st.metric("Termômetro médio geral", f"{media_geral}%")

        if media_geral >= 25:
            st.success("Percepção geral positiva")
        elif media_geral <= -25:
            st.error("Percepção geral negativa")
        else:
            st.warning("Percepção geral neutra/dividida")

    with col_t2:
        termometro_plot = termometro.sort_values("termometro", ascending=True).copy()

        fig_termometro = px.bar(
            termometro_plot,
            x="termometro",
            y="candidato",
            orientation="h",
            text=termometro_plot["termometro"].astype(str) + "%",
            color="termometro",
            color_continuous_scale=["red", "lightgray", "green"],
            range_color=[-100, 100],
            title="Termômetro de sentimento por candidato"
        )

        fig_termometro.add_vline(
            x=0,
            line_width=2,
            line_dash="dash",
            line_color="black"
        )

        fig_termometro.update_layout(
            xaxis_title="Sentimento médio (-100 a +100)",
            yaxis_title="Candidato",
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        st.plotly_chart(fig_termometro, use_container_width=True)

    st.dataframe(
        termometro.sort_values("termometro", ascending=False),
        use_container_width=True
    )

    st.subheader("☁️ Nuvem de Palavras")

    fig_wc = gerar_nuvem_palavras_comentarios(df_comentarios)

    if fig_wc is not None:
        st.pyplot(fig_wc, use_container_width=True)
    else:
        st.info("Sem palavras suficientes para gerar a nuvem.")

    st.subheader("📋 Comentários Coletados")

    st.dataframe(
        df_comentarios[
            [
                "candidato",
                "titulo_video",
                "canal",
                "comentario",
                "sentimento",
                "autor_comentario",
                "like_comentario"
            ]
        ],
        use_container_width=True,
        height=500
    )

else:
    st.warning("Não foi possível carregar comentários.")
# =========================================================
# COMPARAÇÃO ENTRE CANDIDATOS
# =========================================================

st.header("⚔️ Comparação Estratégica")

# Mantém a comparação de canais disponível mesmo quando os vídeos não possuem
# comentários habilitados.
canais_comp = (
    df_videos[df_videos["candidato"].isin([candidato_a, candidato_b])]
    .groupby(["canal", "candidato"], as_index=False)
    .agg(
        videos=("video_id", "count"),
        views=("views", "sum"),
        likes=("likes", "sum"),
        comentarios=("comentarios", "sum")
    )
)

if not df_comparacao.empty:

    # --------------------------------------------------
    # SHARE OF VOICE
    # --------------------------------------------------
    st.subheader("📢 Share of Voice")

    share = (
        df_comparacao
        .groupby("candidato", as_index=False)
        .agg(
            mencoes=("comentario", "count")
        )
    )

    share["share"] = (
        share["mencoes"]
        /
        share["mencoes"].sum()
    ) * 100

    fig_share = px.pie(
        share,
        names="candidato",
        values="share",
        title="Participação nas menções"
    )

    st.plotly_chart(
        fig_share,
        use_container_width=True
    )

    # --------------------------------------------------
    # SENTIMENTO LÍQUIDO
    # --------------------------------------------------
    st.subheader("🌡️ Sentimento Líquido")

    sentimento_liquido = (
        df_comparacao
        .groupby(
            ["candidato", "sentimento"]
        )
        .size()
        .unstack(fill_value=0)
    )

    sentimento_liquido["sentimento_liquido"] = (
        (
            sentimento_liquido.get("positivo", 0)
            -
            sentimento_liquido.get("negativo", 0)
        )
        /
        sentimento_liquido.sum(axis=1)
    ) * 100

    st.dataframe(
        sentimento_liquido[
            ["sentimento_liquido"]
        ]
        .round(2)
    )

    # --------------------------------------------------
    # EVOLUÇÃO TEMPORAL
    # --------------------------------------------------
    st.subheader("📈 Evolução das Menções")

    temp = df_comparacao.copy()
##########################
# Correção fuso horário
###########################
    temp["data"] = (
    pd.to_datetime(
        temp["publicado_em_comentario"],
        errors="coerce",
        utc=True
    )
    .dt.date
)

    limite = (
    pd.Timestamp.now()
    - pd.Timedelta(days=periodo_dias)
).date()

    temp = temp[
    temp["data"] >= limite
]
#############################
# Fim
#############################
    evolucao = (
    temp
    .groupby(
        [
            "data",
            "candidato"
        ]
    )
    .size()
    .reset_index(name="comentarios")
)
    st.write("Candidatos na evolução:")
    st.write(evolucao["candidato"].value_counts())

    st.write(evolucao.head(20))

    fig_evolucao = px.line(
        evolucao,
        x="data",
        y="comentarios",
        color="candidato",
        markers=True
    )

    st.plotly_chart(
        fig_evolucao,
        use_container_width=True
    )

    # --------------------------------------------------
    # NARRATIVAS POSITIVAS
    # --------------------------------------------------
    st.subheader("✅ Narrativas Positivas")

    texto_pos = " ".join(
        df_comparacao[
            df_comparacao["sentimento"] == "positivo"
        ]["comentario"].astype(str)
    )

    palavras_pos = [
        p
        for p in normalizar_texto(
            texto_pos
        ).split()
        if len(p) > 3
        and p not in STOPWORDS_PT
    ]

    top_pos = pd.DataFrame(
        Counter(
            palavras_pos
        ).most_common(20),
        columns=["Palavra", "Frequência"]
    )

    st.dataframe(
        top_pos,
        use_container_width=True
    )

    # --------------------------------------------------
    # NARRATIVAS NEGATIVAS
    # --------------------------------------------------
    st.subheader("❌ Narrativas Negativas")

    texto_neg = " ".join(
        df_comparacao[
            df_comparacao["sentimento"] == "negativo"
        ]["comentario"].astype(str)
    )

    palavras_neg = [
        p
        for p in normalizar_texto(
            texto_neg
        ).split()
        if len(p) > 3
        and p not in STOPWORDS_PT
    ]

    top_neg = pd.DataFrame(
        Counter(
            palavras_neg
        ).most_common(20),
        columns=["Palavra", "Frequência"]
    )

    st.dataframe(
        top_neg,
        use_container_width=True
    )
############################################################
# Inserção do Novo Módulo
##########################################################
    # ==================================================
# INTELIGÊNCIA DE CANAIS
# ==================================================

    st.subheader("📺 Comparativo de Canais")

    canais_comp = (
    df_videos[
        df_videos["candidato"].isin(
            [
                candidato_a,
                candidato_b
            ]
        )
    ]
    .groupby(
        ["canal", "candidato"],
        as_index=False
    )
    .agg(
        videos=("video_id", "count"),
        views=("views", "sum"),
        likes=("likes", "sum"),
        comentarios=("comentarios", "sum")
    )
)
    fig_canais = px.bar(
        canais_comp,
        x="canal", 
        y="views",
        color="candidato",
        barmode="group",
        text="views",
        title="Views por canal"
)

    fig_canais.update_layout(
    xaxis_tickangle=-45,
    xaxis_title="Canal",
    yaxis_title="Views"
)

    st.plotly_chart(
    fig_canais,
    use_container_width=True
)
    st.subheader("🏆 Ranking de Canais")

    ranking_canais_comp = (
    canais_comp
    .sort_values(
        "views",
        ascending=False
    )
)

    st.dataframe(
    ranking_canais_comp[
        [
            "canal",
            "candidato",
            "videos",
            "views",
            "likes",
            "comentarios"
        ]
    ],
    use_container_width=True
)
    st.subheader("🤝 Canais em Comum")

canais_a = set(
    df_videos[
        df_videos["candidato"] == candidato_a
    ]["canal"]
)

canais_b = set(
    df_videos[
        df_videos["candidato"] == candidato_b
    ]["canal"]
)

canais_comum = sorted(
    list(
        canais_a.intersection(canais_b)
    )
)

st.metric(
    "Quantidade",
    len(canais_comum)
)

if canais_comum:

    st.dataframe(
        pd.DataFrame(
            canais_comum,
            columns=["Canal"]
        ),
        use_container_width=True
    )
else:
    st.info("Nenhum canal em comum.")
col1, col2 = st.columns(2)

with col1:

    exclusivos_a = sorted(
        list(
            canais_a - canais_b
        )
    )

    st.subheader(
        f"📢 Exclusivos de {candidato_a}"
    )

    st.dataframe(
        pd.DataFrame(
            exclusivos_a,
            columns=["Canal"]
        ),
        height=300,
        use_container_width=True
    )

with col2:

    exclusivos_b = sorted(
        list(
            canais_b - canais_a
        )
    )

    st.subheader(
        f"📢 Exclusivos de {candidato_b}"
    )

    st.dataframe(
        pd.DataFrame(
            exclusivos_b,
            columns=["Canal"]
        ),
        height=300,
        use_container_width=True
    )
    st.subheader("🚀 Canal Mais Influente")

    top_canal = (
    canais_comp
    .sort_values(
        "views",
        ascending=False
    )
    .groupby("candidato")
    .head(1)
)

    st.dataframe(
    top_canal[
        [
            "candidato",
            "canal",
            "views",
            "likes",
            "comentarios"
        ]
    ],
    use_container_width=True
)
    st.subheader("🔥 Heatmap Canal × Candidato")

    heat = (
    canais_comp
    .pivot_table(
        index="canal",
        columns="candidato",
        values="views",
        aggfunc="sum"
    )
    .fillna(0)
)

    fig_heat = px.imshow(
    heat,
    text_auto=True,
    aspect="auto",
    color_continuous_scale="Blues"
)

    st.plotly_chart(
    fig_heat,
    use_container_width=True
)

    # ==================================================
# INTELIGÊNCIA DE CANAIS
# ==================================================

    
    # --------------------------------------------------
    # TOP NOTÍCIAS
    # --------------------------------------------------
    st.subheader(" Notícias de Maior Repercussão")

    noticias = (
        df_videos[
            df_videos["candidato"].isin(
                [
                    candidato_a,
                    candidato_b
                ]
            )
        ]
        .sort_values(
            "views",
            ascending=False
        )
        .head(20)
    )

    st.dataframe(
        noticias[
            [
                "candidato",
                "titulo",
                "views",
                "likes",
                "comentarios",
                "url"
            ]
        ],
        use_container_width=True
    )

    # --------------------------------------------------
    # COMENTÁRIOS MAIS RELEVANTES
    # --------------------------------------------------
    st.subheader("💬 Comentários Mais Relevantes")

    comentarios_relevantes = (
        df_comparacao
        .sort_values(
            "like_comentario",
            ascending=False
        )
        .head(30)
    )

    st.dataframe(
        comentarios_relevantes[
            [
                "candidato",
                "comentario",
                "sentimento",
                "like_comentario"
            ]
        ],
        use_container_width=True
    )

    # --------------------------------------------------
    # RANKING DIGITAL
    # --------------------------------------------------
    st.subheader("🏆 Índice de Popularidade Digital")

    ipd = (
        df_videos[
            df_videos["candidato"].isin(
                [
                    candidato_a,
                    candidato_b
                ]
            )
        ]
        .groupby(
            "candidato",
            as_index=False
        )
        .agg(
            views=("views", "sum"),
            likes=("likes", "sum"),
            comentarios=("comentarios", "sum")
        )
    )

    ipd["ipd"] = (
        ipd["views"] * 0.20
        +
        ipd["likes"] * 0.40
        +
        ipd["comentarios"] * 0.40
    )

    fig_ipd = px.bar(
        ipd,
        x="candidato",
        y="ipd",
        color="ipd",
        text="ipd"
    )

    st.plotly_chart(
        fig_ipd,
        use_container_width=True
    )

    # --------------------------------------------------
    # CONCLUSÃO ESTRATÉGICA
    # --------------------------------------------------
    st.subheader("🤖 Conclusão Estratégica")

    lider_ipd = (
        ipd
        .sort_values(
            "ipd",
            ascending=False
        )
        .iloc[0]["candidato"]
    )

    lider_sentimento = (
        sentimento_liquido
        .sort_values(
            "sentimento_liquido",
            ascending=False
        )
        .index[0]
    )

    st.success(f"""
📊 O candidato com maior força digital é: {lider_ipd}

😊 O candidato com melhor sentimento líquido é: {lider_sentimento}

✅ Analise Share of Voice, Sentimento Líquido e Evolução Temporal
para identificar quem está ampliando influência digital
e quais narrativas estão impulsionando ou prejudicando
cada candidatura.
""")
# =========================================================
# TABELA FINAL
# =========================================================
st.subheader("📺 Vídeos Aprovados em Percentual")

df_exibir = df_videos[
    [
        "candidato",
        "titulo",
        "canal",
        "fonte_ceara",
        "views",
        "likes",
        "comentarios",
        "score_candidato",
        "consulta_usada",
        "publicado_em",
        "url"
    ]
].copy()

df_exibir["perc_views"] = percentual(df_exibir["views"], df_exibir["views"].sum())
df_exibir["perc_likes"] = percentual(df_exibir["likes"], df_exibir["likes"].sum())
df_exibir["perc_comentarios"] = percentual(
    df_exibir["comentarios"],
    df_exibir["comentarios"].sum()
)

df_exibir["publicado_em"] = df_exibir["publicado_em"].astype(str)

df_tabela_percentual = df_exibir[
    [
        "candidato",
        "titulo",
        "canal",
        "fonte_ceara",
        "perc_views",
        "perc_likes",
        "perc_comentarios",
        "score_candidato",
        "consulta_usada",
        "publicado_em",
        "url"
    ]
].copy()

df_tabela_percentual["perc_views"] = df_tabela_percentual["perc_views"].round(2)
df_tabela_percentual["perc_likes"] = df_tabela_percentual["perc_likes"].round(2)
df_tabela_percentual["perc_comentarios"] = df_tabela_percentual["perc_comentarios"].round(2)

st.dataframe(
    df_tabela_percentual.sort_values(
        by="perc_views",
        ascending=False
    ),
    use_container_width=True,
    height=650
)

