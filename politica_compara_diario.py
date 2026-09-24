import os
import re
import unicodedata
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
import plotly.express as px

from dotenv import load_dotenv
# Gerado as Senhas
##################### Gerar Senhas
# ============================================================
# CONFIGURAÇÃO ÚNICA DO STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Classificação de Risco COVID",
    page_icon="🩺",
    layout="wide"
)
# ============================================================
# LOGIN
# ============================================================
def carregar_usuarios():

    try:
        return st.secrets["usuarios"]

    except Exception:
        return None
def normalizar_usuario(texto):
    """Normaliza o usuário para aceitar João, joao, JOAO etc."""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")

def autenticar(usuario, senha):

    usuarios = carregar_usuarios()

    if usuarios is None:
        return False, "Usuários ainda não configurados no Streamlit Secrets."

    usuario_digitado = normalizar_usuario(usuario)
    usuario_encontrado = None

    # Procura o usuário sem diferenciar maiúsculas/minúsculas
    # e sem diferenciar acentos.
    for chave in usuarios:
        if normalizar_usuario(chave) == usuario_digitado:
            usuario_encontrado = chave
            break

    if usuario_encontrado is None:
        return False, "Usuário ou senha inválidos."

    try:
        senha_correta = str(usuarios[usuario_encontrado]["senha"])
    except Exception:
        return False, "Configuração de senha inválida no Streamlit Secrets."

    if hmac.compare_digest(str(senha), senha_correta):

        nome = str(
            usuarios[usuario_encontrado].get(
                "nome",
                usuario_encontrado
            )
        )

        return True, nome

    return False, "Usuário ou senha inválidos."
# ============================================================
# CONTROLE DA SESSÃO
# ============================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False


# ============================================================
# TELA DE LOGIN
# ============================================================

if not st.session_state.autenticado:

    st.title("🔐 Acesso ao sistema")

    st.write(
        "Digite seu usuário e sua senha para continuar."
    )

    usuario = st.text_input(
        "Usuário",
        placeholder="Digite seu usuário"
    )

    senha = st.text_input(
        "Senha",
        type="password",
        placeholder="Digite sua senha"
    )

    if st.button(
        "Entrar",
        use_container_width=True,
        type="primary"
    ):

        if not usuario or not senha:

            st.warning(
                "Informe o usuário e a senha."
            )

        else:

            sucesso, resultado = autenticar(
                usuario,
                senha
            )

            if sucesso:

                st.session_state.autenticado = True
                st.session_state.usuario = usuario
                st.session_state.nome_usuario = resultado

                st.rerun()

            else:

                st.error(resultado)

    # Impede que o restante do aplicativo apareça
    st.stop()


# ============================================================
# USUÁRIO LOGADO
# ============================================================

nome_usuario = st.session_state.get(
    "nome_usuario",
    st.session_state.get("usuario", "")
)


# ============================================================
# BOTÃO SAIR
# ============================================================

with st.sidebar:

    st.success(
        f"👤 Usuário: {nome_usuario}"
    )

    if st.button(
        "🚪 Sair",
        use_container_width=True
    ):

        st.session_state.autenticado = False

        st.session_state.pop(
            "usuario",
            None
        )

        st.session_state.pop(
            "nome_usuario",
            None
        )

        st.rerun()
# Senha Gerada
# =========================================================
# CONFIGURAÇÃO
# =========================================================
load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("Defina YOUTUBE_API_KEY no arquivo .env")

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
    page_title="Instituto Inteligência de Dados (IID)-Eleições Ceará 2026",
    page_icon="🗳️",
    layout="wide"
)

# =========================================================
# INSTITUO INTELIGÊNCIA DE DADOS (IID)-ELEIÇÕES CEARÁ 2026
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

    # Percentual de sentimento dentro de cada candidato.
    ranking_sentimento_candidato["percentual"] = (
        ranking_sentimento_candidato.groupby("candidato")["quantidade"]
        .transform(
            lambda x: (x / x.sum() * 100) if x.sum() > 0 else 0
        )
    )

    return df_comentarios, ranking_sentimento, ranking_sentimento_candidato



# =========================================================
# DASHBOARD SIMPLIFICADO
# =========================================================

st.set_page_config(
    page_title="Instituto Inteligência de Dados (IID)-Eleições Ceará 2026",
    page_icon="🗳️",
    layout="wide"
)

st.title("🗳️ Instituto Inteligência de Dados (IID)-Eleições Ceará 2026")
st.caption(
    "Monitoramento de vídeos de canais e blogs cearenses autorizados pelo sistema."
)

with st.sidebar:
    st.header("Configurações")

    max_results_por_busca = st.slider(
        "Vídeos por consulta",
        min_value=5,
        max_value=50,
        value=25
    )

    max_videos_comentarios = st.slider(
        "Vídeos analisados por candidato",
        min_value=1,
        max_value=10,
        value=5
    )

    max_comments_per_video = st.slider(
        "Comentários por vídeo",
        min_value=5,
        max_value=50,
        value=20
    )

    atualizar = st.button("🔄 Atualizar dados")

if atualizar:
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------
# CARREGAMENTO
# ---------------------------------------------------------
try:
    with st.spinner("Buscando vídeos no YouTube..."):
        df_videos, ranking_candidato, _ = carregar_dados(
            max_results_por_busca=max_results_por_busca,
            region_code="BR",
            relevance_language="pt",
            order="relevance"
        )
except Exception as e:
    st.error(f"Erro ao carregar vídeos: {e}")
    st.stop()

if df_videos.empty:
    st.warning("Nenhum vídeo encontrado.")
    st.stop()

with st.spinner("Analisando comentários e sentimentos..."):
    df_comentarios, _, ranking_sentimento_candidato = carregar_comentarios(
        df_videos=df_videos,
        max_videos_por_candidato=max_videos_comentarios,
        max_comments_per_video=max_comments_per_video
    )

# ---------------------------------------------------------
# TOTAIS
# ---------------------------------------------------------
total_videos = len(df_videos)
total_likes = int(df_videos["likes"].sum())
total_comentarios = int(df_videos["comentarios"].sum())
total_engajamento = total_likes + total_comentarios

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "🎥 Total de Vídeos",
    f"{total_videos:,}".replace(",", ".")
)

c2.metric(
    "👍 Total de Curtidas",
    f"{total_likes:,}".replace(",", ".")
)

c3.metric(
    "💬 Total de Comentários",
    f"{total_comentarios:,}".replace(",", ".")
)

c4.metric(
    "🔥 Total de Engajamento",
    f"{total_engajamento:,}".replace(",", ".")
)

st.markdown("---")

# ---------------------------------------------------------
# IID — TERMÔMETRO DE SENTIMENTO
# ---------------------------------------------------------
st.subheader("Termômetro médio por candidato-Instituto Inteligência de Dados")

if not df_comentarios.empty:
    df_termometro = df_comentarios.copy()
    df_termometro["score_sentimento"] = df_termometro["sentimento"].apply(
        score_sentimento
    )

    termometro = (
        df_termometro
        .groupby("candidato", as_index=False)
        .agg(
            indice_medio=("score_sentimento", "mean"),
            comentarios_analisados=("comentario", "count")
        )
    )

    termometro["termometro"] = (
        termometro["indice_medio"] * 100
    ).round(1)

    termometro_plot = termometro.sort_values(
        "termometro",
        ascending=True
    ).copy()

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

    st.plotly_chart(
        fig_termometro,
        use_container_width=True
    )
else:
    st.info(
        "Não foram encontrados comentários suficientes para gerar o termômetro."
    )


# ---------------------------------------------------------
# GRÁFICO 2 — HEATMAP DE SENTIMENTO
# ---------------------------------------------------------
st.subheader("😊 Sentimento dos Comentários")

if not df_comentarios.empty:
    # Mantém exatamente a mesma estrutura visual.
    # A única mudança é a normalização: agora cada LINHA
    # (positivo, neutro e negativo) soma 100% entre os candidatos.
    pivot_sentimento = (
        ranking_sentimento_candidato
        .pivot_table(
            index="sentimento",
            columns="candidato",
            values="quantidade",
            aggfunc="sum",
            fill_value=0
        )
        .reindex(["positivo", "neutro", "negativo"])
    )

    pivot_sentimento = (
        pivot_sentimento
        .div(
            pivot_sentimento.sum(axis=1).replace(0, pd.NA),
            axis=0
        )
        .fillna(0)
        * 100
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

    st.plotly_chart(
        fig5,
        use_container_width=True
    )
else:
    st.info(
        "Não foram encontrados comentários suficientes para gerar o gráfico de sentimento."
    )

