from flask import Flask, request, jsonify, render_template
import time
import requests
import whisper
import os
import sqlite3
from contextlib import contextmanager

app = Flask(__name__)

modelo_whisper = whisper.load_model("base")

API_KEY = ""

# ─── BANCO DE DADOS ──────────────────────────────────────────────────────────

DB_PATH = "mentor_maker.db"

def init_db():
    """
    Cria as tabelas se ainda não existirem.
    Chamado uma vez na inicialização do servidor.
    """
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS atendimentos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                grupo       INTEGER NOT NULL,
                inicio      REAL    NOT NULL,
                fim         REAL,
                conteudo    TEXT    DEFAULT 'inicio'
            );

            CREATE TABLE IF NOT EXISTS conversas (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                atendimento_id  INTEGER NOT NULL,
                grupo           INTEGER NOT NULL,
                papel           TEXT    NOT NULL,  -- 'aluno' ou 'tutor'
                mensagem        TEXT    NOT NULL,
                criado_em       REAL    NOT NULL,
                FOREIGN KEY (atendimento_id) REFERENCES atendimentos(id)
            );

            CREATE TABLE IF NOT EXISTS niveis_grupo (
                grupo       INTEGER PRIMARY KEY,
                nivel       INTEGER NOT NULL,
                atualizado  REAL    NOT NULL
            );
        """)

@contextmanager
def get_db():
    """Context manager que abre, entrega e fecha a conexão automaticamente."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # permite acessar colunas por nome
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── ESTADO EM MEMÓRIA (volátil — só para lógica de operação) ─────────────────
# O histórico de atendimentos e as conversas vão pro banco.
# Aqui ficam apenas os dados que precisam de velocidade máxima
# e que não precisam sobreviver a reinicializações.

estado_escuta = False

estado_sistema = {
    "modo": "idle",
    "grupo_atual": None,
    "fila": [],
    "urgente": None,
    "conteudo": "inicio",
}

estado_ia = {
    "pergunta": None,
    "resposta": None,
    "processando": False
}


# ─── HELPERS DE BANCO ────────────────────────────────────────────────────────

def _criar_registro_historico(grupo):
    """
    Abre um atendimento no banco se não houver nenhum aberto para o grupo.
    Retorna o id do registro criado (ou existente).
    """
    conteudo = estado_sistema.get("conteudo", "inicio")

    with get_db() as conn:
        # Verifica se já existe registro aberto
        row = conn.execute(
            "SELECT id FROM atendimentos WHERE grupo = ? AND fim IS NULL",
            (grupo,)
        ).fetchone()

        if row:
            return row["id"]

        cursor = conn.execute(
            "INSERT INTO atendimentos (grupo, inicio, conteudo) VALUES (?, ?, ?)",
            (grupo, time.time(), conteudo)
        )
        return cursor.lastrowid


def finalizar_atendimento(grupo, proximo_modo="ouvindo"):
    if grupo is None:
        return False
    try:
        grupo = int(grupo)
    except (TypeError, ValueError):
        return False

    _criar_registro_historico(grupo)

    with get_db() as conn:
        conn.execute(
            "UPDATE atendimentos SET fim = ? WHERE grupo = ? AND fim IS NULL",
            (time.time(), grupo)
        )
        conn.execute("DELETE FROM niveis_grupo WHERE grupo = ?", (grupo,))

    estado_sistema["grupo_atual"] = None
    estado_sistema["modo"] = proximo_modo
    return True


def _get_historico():
    """Retorna todos os atendimentos do banco como lista de dicts."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, grupo, inicio, fim, conteudo FROM atendimentos ORDER BY inicio ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def _salvar_mensagem_conversa(grupo, papel, mensagem):
    """Persiste uma linha de conversa vinculada ao atendimento aberto."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM atendimentos WHERE grupo = ? AND fim IS NULL ORDER BY inicio DESC LIMIT 1",
            (grupo,)
        ).fetchone()
        if not row:
            return
        conn.execute(
            "INSERT INTO conversas (atendimento_id, grupo, papel, mensagem, criado_em) VALUES (?,?,?,?,?)",
            (row["id"], grupo, papel, mensagem, time.time())
        )


# ─── IA ──────────────────────────────────────────────────────────────────────

def _nivel_grupo(grupo):
    with get_db() as conn:
        row = conn.execute(
            "SELECT nivel FROM niveis_grupo WHERE grupo = ?", (grupo,)
        ).fetchone()
    return row["nivel"] if row else "desconhecido"


def gerar_resposta_ia(pergunta, grupo):
    resposta = ""

    try:
        nivel = _nivel_grupo(grupo)

        prompt = f"""
        Grupo: {grupo}
        Nível: {nivel}

        Pergunta:
        {pergunta}
        """

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é a Léia, uma assistente educacional. "
                            "Explique de forma simples, curta e clara para alunos iniciantes, "
                            "dando uma direção para buscarem a própria resposta, ensine bem brevemente. "
                            "NUNCA use LaTeX, markdown matemático, símbolos especiais ou formatação técnica. "
                            "Escreva fórmulas de forma simples e legível em texto comum. "
                            "Exemplo correto: x = (-b +- raiz de b² - 4ac) / 2a "
                            "Responda em no máximo 2 frases."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=10
        )

        data = r.json()
        if "choices" in data:
            resposta = data["choices"][0]["message"]["content"].strip()
        else:
            print("Resposta inesperada da API:", data)
            resposta = ""

    except Exception as e:
        print("IA falhou, usando fallback:", e)

    if not resposta or len(resposta) < 5:
        pergunta_lower = pergunta.lower()

        if "força" in pergunta_lower:
            resposta = "Força é o que faz algo se mover. Exemplo: empurrar uma mesa faz ela andar."
        elif "energia" in pergunta_lower:
            resposta = "Energia é o que faz as coisas funcionarem. Exemplo: uma bateria liga um LED."
        elif "sensor" in pergunta_lower:
            resposta = "Sensor detecta algo, como distância ou luz."
        elif "movimento" in pergunta_lower:
            resposta = "Movimento é quando algo muda de posição."
        else:
            resposta = "Isso é um conceito de física. Tente testar na prática com objetos."

    # Persiste a troca no banco
    _salvar_mensagem_conversa(grupo, "aluno", pergunta)
    _salvar_mensagem_conversa(grupo, "tutor", resposta)

    print("\n--- IA DEBUG ---")
    print("Grupo:", grupo)
    print("Pergunta:", pergunta)
    print("Resposta:", resposta)
    print("----------------\n")

    return resposta


# ─── PÁGINAS ─────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ─── ESP32 ───────────────────────────────────────────────────────────────────

@app.route("/update")
def update():
    grupo = int(request.args.get("grupo"))
    nivel = int(request.args.get("nivel"))
    urgente = request.args.get("urgente") == "1"

    if urgente:
        estado_sistema["urgente"] = grupo
    else:
        na_fila = next(
            (item for item in estado_sistema["fila"] if item["grupo"] == grupo),
            None
        )
        if na_fila:
            na_fila["nivel"] = nivel
            na_fila["tempo"] = time.time()
        else:
            estado_sistema["fila"].append({
                "grupo": grupo,
                "nivel": nivel,
                "tempo": time.time(),
            })

        # Persiste nível no banco
        with get_db() as conn:
            conn.execute(
                """INSERT INTO niveis_grupo (grupo, nivel, atualizado)
                   VALUES (?, ?, ?)
                   ON CONFLICT(grupo) DO UPDATE SET nivel=excluded.nivel, atualizado=excluded.atualizado""",
                (grupo, nivel, time.time())
            )

    return jsonify({"ok": True})


# ─── PEPPER ──────────────────────────────────────────────────────────────────

@app.route("/next")
def next_group():
    if estado_sistema["urgente"] is not None:
        grupo = estado_sistema["urgente"]
        estado_sistema["urgente"] = None
        estado_sistema["grupo_atual"] = grupo
        estado_sistema["modo"] = "indo"
        _criar_registro_historico(grupo)
        return jsonify({"grupo": grupo})

    if estado_sistema["fila"]:
        proximo = max(estado_sistema["fila"], key=lambda x: (x["nivel"], -x["tempo"]))
        estado_sistema["fila"].remove(proximo)
        grupo = proximo["grupo"]
        estado_sistema["grupo_atual"] = grupo
        estado_sistema["modo"] = "indo"
        _criar_registro_historico(grupo)
        return jsonify({"grupo": grupo})

    return jsonify({"grupo": None})


@app.route("/fila_display")
def fila_display():
    itens = []

    if estado_sistema["urgente"] is not None:
        itens.append({
            "grupo": estado_sistema["urgente"],
            "nivel": 0,
            "tempo": time.time(),
            "urgente": True,
        })

    for item in estado_sistema["fila"]:
        itens.append({
            "grupo": item["grupo"],
            "nivel": item["nivel"],
            "tempo": item["tempo"],
            "urgente": False,
        })

    return jsonify(itens)


# ─── WHISPER / ÁUDIO ────────────────────────────────────────────────────────

@app.route("/audio", methods=["POST"])
def audio():
    try:
        if "audio" not in request.files:
            return jsonify({"ok": False, "erro": "Nenhum áudio enviado"}), 400

        audio_file = request.files["audio"]
        caminho = "temp_audio.webm"
        audio_file.save(caminho)

        print("\n--- TRANSCRIBINDO ÁUDIO ---")
        resultado = modelo_whisper.transcribe(caminho, language="pt")
        texto = resultado["text"].strip()
        print("Texto reconhecido:", texto)
        os.remove(caminho)

        estado_ia["pergunta"] = texto
        estado_ia["processando"] = True

        grupo_ativo = estado_sistema.get("grupo_atual") or 0
        resposta = gerar_resposta_ia(texto, grupo_ativo)

        estado_ia["resposta"] = resposta
        estado_ia["processando"] = False

        return jsonify({"ok": True, "texto": texto, "resposta": resposta})

    except Exception as e:
        print("ERRO WHISPER:", e)
        estado_ia["processando"] = False
        return jsonify({"ok": False, "erro": str(e)}), 500


# ─── PERGUNTA (IA) ───────────────────────────────────────────────────────────

@app.route("/pergunta", methods=["POST"])
def pergunta():
    data = request.get_json()
    texto = data.get("texto", "")
    grupo = int(data.get("grupo", 0))

    estado_ia["pergunta"] = texto
    estado_ia["processando"] = True

    resposta = gerar_resposta_ia(texto, grupo)

    estado_ia["resposta"] = resposta
    estado_ia["processando"] = False

    return jsonify({"ok": True, "resposta": resposta})


# ─── ATENDIMENTO ─────────────────────────────────────────────────────────────

@app.route("/atendimento_start")
def atendimento_start():
    grupo = int(request.args.get("grupo"))
    _criar_registro_historico(grupo)
    estado_sistema["grupo_atual"] = grupo
    estado_sistema["modo"] = "atendendo"
    return jsonify({"ok": True})


@app.route("/encerrar_manual", methods=["POST"])
def encerrar_manual():
    global estado_escuta

    grupo = estado_sistema.get("grupo_atual")
    if grupo is None:
        return jsonify({"ok": False, "erro": "Nenhum atendimento ativo"}), 400

    finalizado = finalizar_atendimento(grupo, proximo_modo="voltando")
    estado_escuta = False

    return jsonify({
        "ok": True,
        "grupo": grupo,
        "finalizado": finalizado,
        "modo": estado_sistema["modo"]
    })


@app.route("/retorno_concluido", methods=["POST"])
def retorno_concluido():
    global estado_escuta

    estado_escuta = True
    estado_sistema["modo"] = "ouvindo"
    estado_sistema["grupo_atual"] = None

    return jsonify({"ok": True, "modo": estado_sistema["modo"]})


# ─── ESTADO / CONSULTA ───────────────────────────────────────────────────────

@app.route("/estado_sistema")
def estado_sistema_api():
    return jsonify(estado_sistema)


@app.route("/ia_estado")
def ia_estado():
    return jsonify(estado_ia)


@app.route("/historico")
def historico():
    return jsonify(_get_historico())


@app.route("/historico/<int:atendimento_id>/conversas")
def historico_conversas(atendimento_id):
    """Retorna todas as mensagens de um atendimento específico."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT papel, mensagem, criado_em
               FROM conversas
               WHERE atendimento_id = ?
               ORDER BY criado_em ASC""",
            (atendimento_id,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/conteudo")
def conteudo():
    return jsonify({"conteudo": estado_sistema["conteudo"]})


@app.route("/resumo")
def resumo():
    historico_lista = _get_historico()
    total = len(historico_lista)
    finalizados = len([h for h in historico_lista if h["fim"] is not None])

    tempos = [
        h["fim"] - h["inicio"]
        for h in historico_lista
        if h["fim"] is not None
    ]
    tempo_medio = round(sum(tempos) / len(tempos)) if tempos else 0

    return jsonify({
        "total_atendimentos": total,
        "em_andamento": total - finalizados,
        "finalizados": finalizados,
        "tempo_medio_segundos": tempo_medio,
        "modo": estado_sistema["modo"],
        "grupo_atual": estado_sistema["grupo_atual"],
        "fila": estado_sistema["fila"],
        "urgente": estado_sistema["urgente"],
        "conteudo": estado_sistema["conteudo"],
        "ouvindo": estado_escuta
    })


@app.route("/estado", methods=["GET", "POST"])
def estado():
    global estado_escuta

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        estado_escuta = bool(data.get("ouvindo", False))
        if estado_sistema["modo"] in ["idle", "ouvindo"]:
            estado_sistema["modo"] = "ouvindo" if estado_escuta else "idle"

    return jsonify({"ouvindo": estado_escuta})


# ─── ESTATÍSTICAS EXTRAS (novas rotas para o dashboard) ─────────────────────

@app.route("/stats/por_grupo")
def stats_por_grupo():
    """Quantos atendimentos e tempo médio por grupo."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT
                   grupo,
                   COUNT(*) AS total,
                   COUNT(fim) AS finalizados,
                   AVG(CASE WHEN fim IS NOT NULL THEN fim - inicio END) AS tempo_medio
               FROM atendimentos
               GROUP BY grupo
               ORDER BY grupo""",
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/stats/linha_tempo")
def stats_linha_tempo():
    """Atendimentos agrupados por hora do dia (para gráfico de barras)."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT
                   CAST(strftime('%H', datetime(inicio, 'unixepoch', 'localtime')) AS INTEGER) AS hora,
                   COUNT(*) AS total
               FROM atendimentos
               GROUP BY hora
               ORDER BY hora"""
        ).fetchall()
    return jsonify([dict(r) for r in rows])


# ─── START ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
