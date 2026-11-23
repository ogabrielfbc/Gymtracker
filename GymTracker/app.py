from flask import Flask, request
import mysql.connector
from datetime import timedelta, datetime
from flask import jsonify, Response
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import os
import json
import csv
import io
import zipfile
import html

app = Flask(__name__)

conexao = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="gymtracker"
)
exercicios = {
    "Peito": [
        "Supino Reto",
        "Supino Inclinado",
        "Crucifixo",
        "Cross Over"
    ],

    "Costas": [
        "Puxada Frontal",
        "Remada Curvada",
        "Remada Baixa",
        "Pulldown"
    ],

    "Pernas": [
        "Agachamento",
        "Leg Press",
        "Cadeira Extensora",
        "Mesa Flexora"
    ],

    "Ombros": [
        "Desenvolvimento",
        "Elevação Lateral",
        "Elevação Frontal",
        "Remada Alta"
    ],

    "Bíceps": [
        "Rosca Direta",
        "Rosca Alternada",
        "Rosca Martelo"
    ],

    "Tríceps": [
        "Triceps Pulley",
        "Triceps Testa",
        "Triceps Banco"
    ]
}

cursor = conexao.cursor()

APP_VERSION = "0.3.0"
UPDATE_MANIFEST_URL = os.getenv("GYMTRACKER_UPDATE_MANIFEST_URL", "")
EXERCISE_API_URL = "https://oss.exercisedb.dev/api/v1/exercises"

cursor.execute("""
CREATE TABLE IF NOT EXISTS notificacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(40) NOT NULL,
    titulo VARCHAR(180) NOT NULL,
    mensagem TEXT NOT NULL,
    chave_unica VARCHAR(190) NOT NULL UNIQUE,
    criada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lida TINYINT(1) NOT NULL DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS fichas_treino (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    descricao TEXT,
    criada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ficha_exercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL,
    exercicio VARCHAR(160) NOT NULL,
    grupo_muscular VARCHAR(80),
    series INT NOT NULL DEFAULT 3,
    repeticoes INT NOT NULL DEFAULT 10,
    descanso_segundos INT NOT NULL DEFAULT 60,
    FOREIGN KEY (ficha_id) REFERENCES fichas_treino(id) ON DELETE CASCADE
)
""")
conexao.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS configuracoes (
    id INT PRIMARY KEY,
    meta_semanal INT NOT NULL DEFAULT 5
)
""")

cursor.execute("""
INSERT IGNORE INTO configuracoes (id, meta_semanal)
VALUES (1, 5)
""")
conexao.commit()
def calcular_sequencia():

    cursor.execute("""
    SELECT DISTINCT data_treino
    FROM treinos
    WHERE concluido = 1
    AND data_treino IS NOT NULL
    ORDER BY data_treino DESC
    """)

    datas = cursor.fetchall()

    if not datas:
        return 0

    dias = []

    for data in datas:
        if data[0] is not None:
            dias.append(data[0])

    sequencia = 1

    for i in range(len(dias) - 1):

        if dias[i] - dias[i + 1] == timedelta(days=1):
            sequencia += 1
        else:
            break

    return sequencia 

def calcular_melhor_sequencia():

    cursor.execute("""
    SELECT DISTINCT data_treino
    FROM treinos
    WHERE concluido = 1
    AND data_treino IS NOT NULL
    ORDER BY data_treino
    """)

    datas = cursor.fetchall()

    if not datas:
        return 0

    dias = []

    for data in datas:
        if data[0] is not None:
            dias.append(data[0])
    if len(dias)==0:
        return 0       

    melhor = 1
    atual = 1

    for i in range(len(dias) - 1):

        if dias[i + 1] - dias[i] == timedelta(days=1):
            atual += 1

            if atual > melhor:
                melhor = atual

        else:
            atual = 1
    return melhor
@app.route("/")
def home():
    return f"""
    <h1>GymTracker</h1>
    <p>Versão {APP_VERSION}</p>
    <h2>Menu</h2>
    <ul>
        <li><a href="/cadastrar">Cadastrar treino</a></li>
        <li><a href="/dashboard">Dashboard</a></li>
        <li><a href="/treinos">Ver treinos</a></li>
        <li><a href="/meta_semanal">Meta semanal</a></li>
        <li><a href="/evolucao">Evolução de carga</a></li>
        <li><a href="/estatisticas">Estatísticas</a></li>
        <li><a href="/agenda">Agenda de treinos</a></li>
        <li><a href="/agenda_semana">Agenda da semana</a></li>
        <li><a href="/notificacoes">Central de notificações</a></li>
        <li><a href="/exercicios">Pesquisar exercícios</a></li>
        <li><a href="/fichas">Fichas de treino</a></li>
        <li><a href="/cronometro">Cronômetro de descanso</a></li>
        <li><a href="/exportar">Exportar dados</a></li>
        <li><a href="/atualizacoes">Versão e atualizações</a></li>
    </ul>
    <p id="aviso-notificacao">Para receber alertas do navegador, permita notificações quando solicitado.</p>
    <button type="button" onclick="ativarNotificacoes()">Ativar notificações do navegador</button>
    <script>
    function ativarNotificacoes() {{
        if (!('Notification' in window)) {{ alert('Este navegador não oferece notificações.'); return; }}
        Notification.requestPermission().then(function(permissao) {{
            alert(permissao === 'granted' ? 'Notificações ativadas.' : 'Permissão não concedida. Os avisos continuam na central do GymTracker.');
        }});
    }}
    const avisosVistos = new Set();
    async function consultarAvisos() {{
        try {{
            const resposta = await fetch('/api/notificacoes_pendentes');
            const dados = await resposta.json();
            if ('Notification' in window && Notification.permission === 'granted') {{
                dados.forEach(function(aviso) {{
                    if (!avisosVistos.has(aviso.id)) {{
                        avisosVistos.add(aviso.id);
                        new Notification(aviso.titulo, {{ body: aviso.mensagem }});
                    }}
                }});
            }}
        }} catch (erro) {{}}
    }}
    consultarAvisos();
    setInterval(consultarAvisos, 30000);
    </script>
    """


@app.route("/dashboard")
def dashboard():

   cursor.execute("""
   SELECT COUNT(*)
   FROM treinos
   """)
   total = cursor.fetchone()[0]

   cursor.execute("""
   SELECT COUNT(*)
   FROM treinos
   WHERE concluido = 1
   """)
   concluidos = cursor.fetchone()[0]

   cursor.execute("""
   SELECT COUNT(*)
   FROM treinos
   WHERE concluido = 0
   OR concluido IS NULL
   """)
   pendentes = cursor.fetchone()[0]

   cursor.execute("""
   SELECT COUNT(*)
   FROM agenda_treinos
   """)
   
   agendados = cursor.fetchone()[0]

   cursor.execute("""
   SELECT grupo_muscular, data_agendada, horario
   FROM agenda_treinos
   WHERE data_agendada >= CURDATE()
   AND (concluido = 0 OR concluido IS NULL)
   ORDER BY data_agendada ASC, horario ASC
   LIMIT 1
   """)
   proximo_treino = cursor.fetchone()
   cursor.execute("""
   SELECT meta_semanal
   FROM configuracoes
   WHERE id = 1
   """)
   resultado_meta = cursor.fetchone()
   meta = resultado_meta[0] if resultado_meta else 5

   cursor.execute("""
   SELECT COUNT(*)
   FROM treinos
   WHERE concluido = 1
   AND data_treino IS NOT NULL
   AND YEARWEEK(data_treino, 1) = YEARWEEK(CURDATE(), 1)
   """)
   feitos_semana = cursor.fetchone()[0]
   percentual_meta = min(round(feitos_semana / meta * 100), 100) if meta > 0 else 0

   cursor.execute("""
   SELECT exercicio, COUNT(*)
   FROM treinos
   GROUP BY exercicio 
   ORDER BY COUNT(*) DESC
   LIMIT 1
   """)
   mais_realizado = cursor.fetchone()
   exercicio = "Nenhum"
  

   if mais_realizado:
       exercicio = mais_realizado[0]

   sequencia = calcular_sequencia()
   melhor_sequencia = calcular_melhor_sequencia()
   return f"""
       <h1> 🏋️ Dashboard</h1>

        <p>🏋 Exercícios registrados: {total}</p>
        <p>✅ Concluídos: {concluidos}</p>
        <p>❌ Pendentes: {pendentes}</p>
        <p>📅 Treinos agendados: {agendados}</p>

        <h2>➡️ Próximo treino</h2>
        {f"<p>🏋️ {proximo_treino[0]} - {proximo_treino[1].strftime('%d/%m/%Y')} às {str(proximo_treino[2])[:5]}</p>" if proximo_treino else "<p>Nenhum próximo treino programado.</p>"}
        <p><a href="/agenda">Ver agenda completa</a></p>
        <p><a href="/agenda_semana">🗓️ Ver agenda da semana</a></p>

        <p>🎯 Meta semanal: {feitos_semana}/{meta} treinos concluídos ({percentual_meta}%)</p>
        <p><a href="/meta_semanal">Alterar meta semanal</a></p>

        <p>📈 Exercício mais realizado: {exercicio}</p>
        
        <p>🔥 Sequência Atual: {sequencia}</p>

        <p>🏆 Melhor Sequência: {melhor_sequencia} dias</p>
        <p><a href="/notificacoes">Abrir central de notificações</a></p>
        <button type="button" onclick="ativarNotificacoes()">Ativar notificações do navegador</button>
        <script>
        function ativarNotificacoes() {{
            if (!('Notification' in window)) {{ alert('Este navegador não oferece notificações.'); return; }}
            Notification.requestPermission().then(function(permissao) {{
                alert(permissao === 'granted' ? 'Notificações ativadas.' : 'Permissão não concedida.');
            }});
        }}
        const avisosVistos = new Set();
        async function consultarAvisos() {{
            try {{
                const resposta = await fetch('/api/notificacoes_pendentes');
                const dados = await resposta.json();
                if ('Notification' in window && Notification.permission === 'granted') {{
                    dados.forEach(function(aviso) {{
                        if (!avisosVistos.has(aviso.id)) {{
                            avisosVistos.add(aviso.id);
                            new Notification(aviso.titulo, {{ body: aviso.mensagem }});
                        }}
                    }});
                }}
            }} catch (erro) {{}}
        }}
        consultarAvisos();
        setInterval(consultarAvisos, 30000);
        </script>
        <br>
        <a href="/">⬅ Voltar</a>
        """
@app.route("/meta_semanal", methods=["GET", "POST"])
def meta_semanal():
    if request.method == "POST":
        try:
            meta = int(request.form["meta"])
            if meta < 1 or meta > 7:
                return "A meta deve ser entre 1 e 7 treinos por semana. <a href='/meta_semanal'>Voltar</a>", 400
        except (ValueError, KeyError):
            return "Informe um número válido. <a href='/meta_semanal'>Voltar</a>", 400

        cursor.execute("""
        UPDATE configuracoes
        SET meta_semanal = %s
        WHERE id = 1
        """, (meta,))
        conexao.commit()
        return "Meta semanal atualizada! " \
        "<a href='/dashboard'>Voltar ao Dashboard</a>"

    cursor.execute("""
    SELECT meta_semanal
    FROM configuracoes
    WHERE id = 1
    """)
    resultado_meta = cursor.fetchone()
    meta = resultado_meta[0] if resultado_meta else 5

    return f"""
    <h1>Meta semanal</h1>
    <p>Escolha quantos treinos concluídos você quer fazer por semana (1 a 7).</p>
    <form method="POST" action="/meta_semanal">
        <label for="meta"
        >Treinos por semana:</label>
        <input type="number" 
        id="meta" name="meta" min="1" max="7" 
        value="{meta}" required>
        <button type="submit">Salvar meta</button>
    </form>
    <p><a href="/dashboard">Voltar ao Dashboard</a></p>
    """


@app.route("/treinos")
def treinos():

    grupo = request.args.get("grupo", "")
    status = request.args.get("status", "")
    data_inicial = request.args.get("data_inicial", "")
    data_final = request.args.get("data_final", "")
    busca = request.args.get("exercicio", "").strip()

    condicoes = []
    parametros = []

    if grupo:
        condicoes.append("grupo_muscular = %s")
        parametros.append(grupo)

    if status == "1":
        condicoes.append("concluido = 1")

    elif status == "0":
        condicoes.append("(concluido = 0 OR concluido IS NULL)")

    if data_inicial:
        condicoes.append("data_treino >= %s")
        parametros.append(data_inicial)

    if data_final:
        condicoes.append("data_treino <= %s")
        parametros.append(data_final)

    if busca:
        condicoes.append("exercicio LIKE %s")
        parametros.append("%" + busca + "%")

    sql = """
    SELECT id, grupo_muscular, exercicio, carga, data_treino,
           duracao_min, concluido
    FROM treinos
    """

    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)

    sql += """
    ORDER BY data_treino DESC, id DESC
    """

    cursor.execute(sql, tuple(parametros))
    dados = cursor.fetchall()

    html = f"""
    <h1>📋 Treinos Cadastrados</h1>

    <form method="GET" action="/treinos">

        Grupo muscular:
        <select name="grupo">
            <option value="">Todos</option>
    """

    for nome_grupo in exercicios:
        selecionado = "selected" if grupo == nome_grupo else ""
        html += f'<option value="{nome_grupo}" {selecionado}>{nome_grupo}</option>'

    html += f"""
        </select>

        <br><br>

        Status:
        <select name="status">
            <option value="">Todos</option>
            <option value="1" {"selected" 
        if status == "1" 
        else ""}>Concluído</option>
            <option value="0" {"selected" 
        if status == "0" 
        else ""}>Pendente</option>
        </select>

        <br><br>

        Data inicial:
        <input type="date" 
        name="data_inicial" 
        value="{data_inicial}">

        Data final:
        <input type="date" 
        name="data_final" 
        value="{data_final}">

        <br><br>

        Pesquisar exercício:
        <input type="text" 
        name="exercicio" 
        value="{busca}" 
        placeholder="Nome do exercício">

        <button type="submit"
        >Filtrar</button>
        <a 
        href="/treinos">Limpar filtros</a>

    </form>

    <p>Resultados encontrados: {len(dados)}</p>

    <table border="1" cellpadding="10">
        <tr>
            <th>ID</th>
            <th>Grupo</th>
            <th>Exercício</th>
            <th>Carga</th>
            <th>Data</th>
            <th>Duração</th>
            <th>Status</th>
            <th>Ações</th>
        </tr>
    """

    for treino in dados:

        if treino[6] == 1:
            texto_status = "✅ Concluído"
            texto_botao = "❌ Desfazer"
        else:
            texto_status = "❌ Pendente"
            texto_botao = "✅ Concluir"

        html += f"""
        <tr>
            <td>{treino[0]}</td>
            <td>{treino[1]}</td>
            <td>{treino[2]}</td>
            <td>{treino[3]} kg</td>
            <td>{treino[4] or ''}</td>
            <td>{treino[5] or 0} min</td>
            <td>{texto_status}</td>
            <td>
                <button onclick="window.location.
                href='/editar/{treino[0]}'">✏️ Editar
                </button>
                <button onclick="window.location.
                href='/excluir/{treino[0]}'">🗑️ Excluir
                </button>
                <button onclick="window.location.
                href='/alternar_status/{treino[0]}'">{texto_botao}
                </button>
            </td>
        </tr>
        """

    html += """
    </table>

    <br><br>

    <a href="/">⬅ Voltar</a>
    """

    return html


@app.route("/alternar_status/<int:id>")
def alternar_status(id):

    cursor.execute("""
    UPDATE treinos
    SET concluido = NOT COALESCE(concluido,0) 
    WHERE id = %s
    """, (id,))

    conexao.commit()

    return """
    <script>
    window.location.href='/treinos';
    </script>
    """
@app.route("/excluir/<int:id>")
def excluir(id):

    cursor.execute("""
    DELETE FROM treinos
    WHERE id = %s
    """, (id,))

    conexao.commit()

    return """
    <h2>🗑️ Treino excluído com sucesso!</h2>

    <br><br>

    <button onclick="window.location.href='/treinos'">
        📋 Ver Treinos
    </button>

    <br><br>

    <button onclick="window.location.href='/'">
        🏠 Menu Principal
    </button>
    """

@app.route('/editar/<int:id>')
def editar(id):
    cursor.execute("""
        SELECT id, exercicio, carga, series, repeticoes
        FROM treinos
        WHERE id = %s
    """, (id,))

    treino = cursor.fetchone()

    if treino is None:
        return "Treino não encontrado", 404

    return f"""
    <h1>✏️ Editar Treino</h1>

    <p>Exercício: {treino[1]}</p>

    <form action="/atualizar/{id}" method="POST">

        <label>Carga:</label>
        <input
            type="number"
            name="carga"
            value="{treino[2]}"
            required
        >

        <br><br>

        <label>Séries:</label>
        <input
            type="number"
            name="series"
            value="{treino[3]}"
            required
        >

        <br><br>

        <label>Repetições:</label>
        <input
            type="number"
            name="repeticoes"
            value="{treino[4]}"
            required
        >

        <br><br>

        <button type="submit">
            Salvar Alterações
        </button>

    </form>

    <br><br>

    <a href="/">⬅ Voltar</a>
    """

@app.route("/atualizar/<int:id>", methods=["POST"])
def atualizar(id):

    carga = request.form["carga"]
    series = request.form["series"]
    repeticoes = request.form["repeticoes"]

    cursor.execute("""
    UPDATE treinos
    SET carga = %s,
        series = %s,
        repeticoes = %s
    WHERE id = %s
    """,
    (
        carga,
        series,
        repeticoes,
        id
    ))

    conexao.commit()

    return """
    <h2>✅ Treino atualizado com sucesso!</h2>

    <br><br>

    <button onclick="window.location.href='/treinos'">
        📋 Ver Treinos
    </button>

    <br><br>

    <button onclick="window.location.href='/'">
        🏠 Menu Principal
    </button>
    """
@app.route("/cadastrar")
def cadastrar():
    return """
    <h1>➕ Cadastrar Treino</h1>
    <form action= "/salvar" method  ="POST">

    Grupo Muscular:
    <select name="grupo_muscular" id="grupo_muscular">

    <option>Peito</option>
    <option>Costas</option>
    <option>Pernas</option>
    <option>Ombros</option>
    <option>Bíceps</option>
    <option>Tríceps</option>

</select>

<br><br>

    Exercicio:
    <select name="exercicio" id="exercicio" >
    </select>

<br><br>
    <br><br>

    Carga:
    <input type="number" name="carga">
    <br><br>

    Séries:
    <input type="number" name="series">
    <br><br>

    Repetições:
    <input type="number" name="repeticoes">
    <br><br>

    Data do Treino:

    <input type="date"  name="data_treino">

    <br><br>

    Duração (minutos):
    <input type="number" name="duracao_min">
    <br><br>

    Observações:

    <br>
    <textarea
    name="observacoes"
    rows="4"
    cols="40">
    </textarea>

    <br><br>

    <br><br>
    
    
    <br><br>
    

    <button type="submit">
    Salvar
    </button>
    <script>

const exercicios = {

    "Peito": [
        "Supino Reto",
        "Supino Inclinado",
        "Crucifixo",
        "Cross Over"
    ],

    "Costas": [
        "Puxada Frontal",
        "Remada Curvada",
        "Remada Baixa",
        "Pulldown"
    ],

    "Pernas": [
        "Agachamento",
        "Leg Press",
        "Cadeira Extensora",
        "Mesa Flexora"
    ],

    "Ombros": [
        "Desenvolvimento",
        "Elevação Lateral",
        "Elevação Frontal",
        "Remada Alta"
    ],

    "Bíceps": [
        "Rosca Direta",
        "Rosca Alternada",
        "Rosca Martelo"
    ],

    "Tríceps": [
        "Triceps Pulley",
        "Triceps Testa",
        "Triceps Banco"
    ]
};

const grupo = document.getElementById("grupo_muscular");
const exercicio = document.getElementById("exercicio");

function atualizarExercicios() {

    exercicio.innerHTML = "";

    const lista = exercicios[grupo.value];

    lista.forEach(item => {

        const option = document.createElement("option");

        option.value = item;
        option.textContent = item;

        exercicio.appendChild(option);

    });
}

grupo.addEventListener("change", atualizarExercicios);

atualizarExercicios();

</script>
    </form>
    <br><br>
    <a href="/">⬅ Voltar</a>
    """
@app.route("/salvar", methods=["POST"])
def salvar():

    exercicio= request.form["exercicio"]
    carga= request.form["carga"]
    series = request.form["series"]
    repeticoes = request.form["repeticoes"]
    grupo_muscular = request.form["grupo_muscular"]
    data_treino = request.form["data_treino"]
    duracao_min = request.form["duracao_min"]
    observacoes= request.form["observacoes"]
    

    cursor.execute("""
    INSERT INTO treinos
    (exercicio,
        carga,
        series,
        repeticoes, 
        grupo_muscular, 
        data_treino,
        duracao_min,
        observacoes
        )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """,
    (
        exercicio,carga,series,repeticoes, grupo_muscular, data_treino,
        duracao_min, observacoes

    ))
    conexao.commit()

    return """
<h2>✅ Treino salvo com sucesso!</h2>

<button onclick="window.location.href='/treinos'">
    📋 Ver Treinos
</button>

<br><br>

<button onclick="window.location.href='/'">
    🏠 Menu Principal
</button>
"""
@app.route("/evolucao")
def evolucao():

    cursor.execute("""
    SELECT DISTINCT exercicio
    FROM treinos
    WHERE exercicio IS NOT NULL
    ORDER BY exercicio
    """)

    lista_exercicios = cursor.fetchall()
    escolhido = request.args.get("exercicio", "")

    html = """
    <h1>📈 Evolução de carga</h1>

    <form method="GET" action="/evolucao">
        Escolha o exercício:
        <select name="exercicio" required>
            <option value="">Selecione</option>
    """

    for linha in lista_exercicios:
        nome = linha[0]
        selecionado = "selected" if nome == escolhido else ""
        html += f'<option value="{nome}" {selecionado}>{nome}</option>'

    html += """
        </select>
        <button type="submit">Consultar</button>
    </form>
    """

    if escolhido:

        cursor.execute("""
        SELECT data_treino, carga
        FROM treinos
        WHERE exercicio = %s
        AND data_treino IS NOT NULL
        ORDER BY data_treino, id
        """, (escolhido,))

        registros = cursor.fetchall()
        html += f"<h2>{escolhido}</h2>"

        if registros:

            for registro in registros:
                data = registro[0]
                carga = registro[1] or 0

                if hasattr(data, "strftime"):
                    data = data.strftime("%d/%m/%Y")

                html += f"<p>{data}: {carga} kg</p>"

            primeira_carga = float(registros[0][1] or 0)
            ultima_carga = float(registros[-1][1] or 0)
            diferenca = ultima_carga - primeira_carga

            if diferenca > 0:
                sinal = "+"
            else:
                sinal = ""

            html += f"<p>Evolução total: {sinal}{diferenca:g} kg</p>"

        else:
            html += "<p>Esse exercício ainda não tem registros com data.</p>"

    html += """
    <br>
    <a href="/">⬅ Voltar</a>
    """

    return html


@app.route("/estatisticas")
def estatisticas():

    cursor.execute("""
    SELECT COUNT(*)
    FROM treinos
    WHERE concluido = 1
    """)
    total_concluidos = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM treinos
    WHERE concluido = 1
    AND YEAR(data_treino) = YEAR(CURDATE())
    AND MONTH(data_treino) = MONTH(CURDATE())
    """)
    total_mes = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(DISTINCT exercicio)
    FROM treinos
    WHERE exercicio IS NOT NULL
    """)
    exercicios_diferentes = cursor.fetchone()[0]

    cursor.execute("""
    SELECT MAX(carga)
    FROM treinos
    """)
    maior_carga = cursor.fetchone()[0] or 0

    cursor.execute("""
    SELECT AVG(duracao_min), SUM(duracao_min)
    FROM treinos
    WHERE concluido = 1
    """)
    duracao = cursor.fetchone()

    media_duracao = round(float(duracao[0] or 0), 1)
    tempo_total = int(duracao[1] or 0)

    cursor.execute("""
    SELECT SUM(carga * series * repeticoes)
    FROM treinos
    WHERE concluido = 1
    """)
    volume_total = cursor.fetchone()[0] or 0

    cursor.execute("""
    SELECT grupo_muscular, COUNT(*)
    FROM treinos
    WHERE concluido = 1
    GROUP BY grupo_muscular
    ORDER BY COUNT(*) DESC
    """)
    grupos = cursor.fetchall()

    cursor.execute("""
    SELECT exercicio, COUNT(*)
    FROM treinos
    GROUP BY exercicio
    ORDER BY COUNT(*) DESC
    LIMIT 1
    """)
    mais_realizado = cursor.fetchone()

    exercicio_top = "Nenhum"

    if mais_realizado:
        exercicio_top = f"{mais_realizado[0]} ({mais_realizado[1]} registros)"

    return_html = f"""
    <h1>📊 Estatísticas básicas</h1>

    <p>✅ Total de treinos concluídos: {total_concluidos}</p>
    <p>📅 Treinos concluídos no mês atual: {total_mes}</p>
    <p>🏋️ Exercícios diferentes: {exercicios_diferentes}</p>
    <p>💪 Maior carga registrada: {maior_carga} kg</p>
    <p>⏱️ Média de duração por treino concluído: {media_duracao} minutos</p>
    <p>⌛ Tempo total de treinos concluídos: {tempo_total} minutos</p>
    <p>📦 Volume total (carga x séries x repetições): {volume_total}</p>
    <p>🔥 Exercício mais realizado: {exercicio_top}</p>

    <h2>Treinos concluídos por grupo muscular</h2>
    """

    if grupos:
        for grupo in grupos:
            return_html += f"<p>{grupo[0] or 'Sem grupo'}: {grupo[1]}</p>"
    else:
        return_html += "<p>Nenhum treino concluído ainda.</p>"

    return_html += """
    <br>
    <a href="/">⬅ Voltar</a>
    """

    return return_html

@app.route("/agenda")
def agenda():

    cursor.execute("""
    SELECT
        id,
        dia_semana,
        grupo_muscular,
        data_agendada,
        horario,
        observacoes,
        concluido
    FROM agenda_treinos
    ORDER BY data_agendada ASC, horario ASC
    """)

    agendamentos = cursor.fetchall()

    html = """
    <h1>📅 Agenda de Treinos</h1>

    <button onclick="window.location.href='/agendar'">
        ➕ Novo agendamento
    </button>

    <br><br>

    <table border="1" cellpadding="10">

        <tr>
            <th>ID</th>
            <th>Dia da semana</th>
            <th>Grupo muscular</th>
            <th>Data</th>
            <th>Horário</th>
            <th>Observações</th>
            <th>Status</th>
            <th>Ações</th>
        </tr>
    """

    if agendamentos:

        for agendamento in agendamentos:

            id_agendamento = agendamento[0]
            dia_semana = agendamento[1] or ""
            grupo_muscular = agendamento[2] or ""
            data_agendada = agendamento[3]
            horario = agendamento[4]
            observacoes = agendamento[5] or ""
            concluido = agendamento[6]

            if data_agendada:
                data_formatada = data_agendada.strftime("%d/%m/%Y")
            else:
                data_formatada = "Sem data"

            if horario:
                horario_formatado = str(horario)[:5]
            else:
                horario_formatado = "Sem horário"

            if concluido == 1:
                status = "✅ Concluído"
            else:
                status = "⌛ Pendente"

            html += f"""
            <tr>
                <td>{id_agendamento}</td>
                <td>{dia_semana}</td>
                <td>{grupo_muscular}</td>
                <td>{data_formatada}</td>
                <td>{horario_formatado}</td>
                <td>{observacoes}</td>
                <td>{status}</td>
                <td>
                    <a href="/registrar_agendamento/{id_agendamento}">Registrar treino</a><br>
                    <a href="/editar_agendamento/{id_agendamento}">Editar</a><br>
                    <a href="/excluir_agendamento/{id_agendamento}" onclick="return confirm('Excluir este agendamento?')">Excluir</a>
                </td>
            </tr>
            """

    else:

        html += """
        <tr>
            <td colspan="8">
                Nenhum treino agendado.
            </td>
        </tr>
        """

    html += """
    </table>

    <br><br>

    <a href="/">⬅ Voltar</a>
    """

    return html
@app.route("/agenda_semana")
def agenda_semana():
    hoje = datetime.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    cursor.execute("""
    SELECT dia_semana, grupo_muscular, data_agendada,
           horario, observacoes, concluido
    FROM agenda_treinos
    WHERE data_agendada BETWEEN %s AND %s
    ORDER BY data_agendada ASC, horario ASC
    """, (inicio_semana, fim_semana))
    agendamentos = cursor.fetchall()

    html = f"""
    <h1>🗓️ Agenda da semana</h1>
    <p>De {inicio_semana.strftime('%d/%m/%Y')} até {fim_semana.strftime('%d/%m/%Y')}</p>
    <table border="1" cellpadding="10">
        <tr><th>Dia</th><th>Data</th><th>Grupo muscular</th><th>Horário</th><th>Observações</th><th>Status</th></tr>
    """

    if agendamentos:
        for agendamento in agendamentos:
            dia_semana = agendamento[0] or ""
            grupo_muscular = agendamento[1] or ""
            data_agendada = agendamento[2]
            horario = str(agendamento[3])[:5] if agendamento[3] else "Sem horário"
            observacoes = agendamento[4] or ""
            concluido = agendamento[5]
            data_formatada = data_agendada.strftime("%d/%m/%Y") if data_agendada else "Sem data"
            status = "✅ Concluído" if concluido == 1 else "⌛ Pendente"
            if not dia_semana and data_agendada:
                dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
                dia_semana = dias[data_agendada.weekday()]
            html += f"""<tr><td>{dia_semana}</td><td>{data_formatada}</td><td>{grupo_muscular}</td><td>{horario}</td><td>{observacoes}</td><td>{status}</td></tr>"""
    else:
        html += "<tr><td colspan='6'>Nenhum treino agendado para esta semana.</td></tr>"

    html += """
    </table><br><br>
    <a href="/agenda">📅 Agenda completa</a><br><br>
    <a href="/dashboard">📊 Voltar ao Dashboard</a><br><br>
    <a href="/">⬅ Voltar ao menu</a>
    """
    return html


@app.route("/agendar")
def agendar():
    return """
    <h1>📅 Agendar Treino</h1>

    <form action="/salvar_agendamento" method="POST">
        <label for="grupo_muscular">Grupo muscular:</label>
        <select name="grupo_muscular" id="grupo_muscular" required>
            <option value="">Selecione</option>
            <option value="Peito">Peito</option>
            <option value="Costas">Costas</option>
            <option value="Pernas">Pernas</option>
            <option value="Ombros">Ombros</option>
            <option value="Bíceps">Bíceps</option>
            <option value="Tríceps">Tríceps</option>
        </select>

        <br><br>

        <label for="data_agendada">Data do treino:</label>
        <input type="date" name="data_agendada" id="data_agendada" required>

        <br><br>

        <label for="horario">Horário:</label>
        <input type="time" name="horario" id="horario" required>

        <br><br>

        <label for="observacoes">Observações:</label><br>
        <textarea name="observacoes" id="observacoes" rows="4" cols="40"></textarea>

        <br><br>
        <button type="submit">Salvar agendamento</button>
    </form>

    <br><br>
    <a href="/agenda">⬅ Voltar para a Agenda</a>
    <br><br>
    <a href="/">⬅ Voltar para o Menu</a>
    """


@app.route("/salvar_agendamento", methods=["POST"])
def salvar_agendamento():
    grupo_muscular = request.form["grupo_muscular"]
    data_agendada = request.form["data_agendada"]
    horario = request.form["horario"]
    observacoes = request.form.get("observacoes", "")

    data_objeto = datetime.strptime(data_agendada, "%Y-%m-%d").date()
    dias = [
        "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
        "Sexta-feira", "Sábado", "Domingo"
    ]
    dia_semana = dias[data_objeto.weekday()]

    cursor.execute("""
    INSERT INTO agenda_treinos
        (dia_semana, grupo_muscular, data_agendada, horario, observacoes, concluido)
    VALUES (%s, %s, %s, %s, %s, 0)
    """, (dia_semana, grupo_muscular, data_agendada, horario, observacoes))
    conexao.commit()

    return """
    <h2>✅ Treino agendado com sucesso!</h2>
    <a href="/agenda">Ver agenda</a><br><br>
    <a href="/agenda_semana">Ver agenda da semana</a><br><br>
    <a href="/">Voltar ao menu</a>
    """


@app.route("/registrar_agendamento/<int:id>", methods=["GET", "POST"])
def registrar_agendamento(id):
    cursor.execute("""
    SELECT grupo_muscular, data_agendada, observacoes, concluido
    FROM agenda_treinos
    WHERE id = %s
    """, (id,))
    agendamento = cursor.fetchone()

    if not agendamento:
        return "Agendamento não encontrado.", 404

    if agendamento[3] == 1:
        return """
        <h2>Este agendamento já foi concluído.</h2>
        <a href="/agenda">Voltar para a agenda</a>
        """

    if request.method == "POST":
        exercicio = request.form["exercicio"]
        carga = request.form["carga"]
        series = request.form["series"]
        repeticoes = request.form["repeticoes"]
        duracao_min = request.form.get("duracao_min") or 0
        observacoes = request.form.get("observacoes", "")

        cursor.execute("""
        INSERT INTO treinos
            (exercicio, carga, series, repeticoes, grupo_muscular,
             data_treino, duracao_min, observacoes, concluido)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, (
            exercicio, carga, series, repeticoes, agendamento[0],
            agendamento[1], duracao_min, observacoes
        ))

        cursor.execute("""
        UPDATE agenda_treinos
        SET concluido = 1
        WHERE id = %s
        """, (id,))
        conexao.commit()

        return """
        <h2>✅ Treino cadastrado e agendamento concluído automaticamente!</h2>
        <a href="/treinos">Ver treinos cadastrados</a><br><br>
        <a href="/agenda">Voltar para a agenda</a>
        """

    grupo = agendamento[0] or ""
    data = agendamento[1].strftime("%Y-%m-%d") if agendamento[1] else ""
    observacoes = agendamento[2] or ""
    opcoes = "".join(
        f'<option value="{nome}">{nome}</option>'
        for nome in exercicios.get(grupo, [])
    )

    return f"""
    <h1>🏋️ Registrar treino agendado</h1>
    <p>Grupo muscular: {grupo}</p>
    <p>Data: {data}</p>

    <form method="POST">
        <label>Exercício:</label>
        <select name="exercicio" required>{opcoes}</select><br><br>

        <label>Carga (kg):</label>
        <input type="number" name="carga" min="0" step="any" required><br><br>

        <label>Séries:</label>
        <input type="number" name="series" min="1" required><br><br>

        <label>Repetições:</label>
        <input type="number" name="repeticoes" min="1" required><br><br>

        <label>Duração (minutos):</label>
        <input type="number" name="duracao_min" min="0" value="0"><br><br>

        <label>Observações:</label><br>
        <textarea name="observacoes" rows="4" cols="40">{observacoes}</textarea><br><br>

        <button type="submit">Salvar treino e concluir agendamento</button>
    </form>
    <br><a href="/agenda">Cancelar e voltar</a>
    """


@app.route("/editar_agendamento/<int:id>", methods=["GET", "POST"])
def editar_agendamento(id):
    cursor.execute("""
    SELECT dia_semana, grupo_muscular, data_agendada, horario, observacoes
    FROM agenda_treinos
    WHERE id = %s
    """, (id,))
    agendamento = cursor.fetchone()

    if not agendamento:
        return "Agendamento não encontrado.", 404

    if request.method == "POST":
        grupo_muscular = request.form["grupo_muscular"]
        data_agendada = request.form["data_agendada"]
        horario = request.form["horario"]
        observacoes = request.form.get("observacoes", "")
        data_objeto = datetime.strptime(data_agendada, "%Y-%m-%d").date()
        dias = [
            "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
            "Sexta-feira", "Sábado", "Domingo"
        ]

        cursor.execute("""
        UPDATE agenda_treinos
        SET dia_semana = %s,
            grupo_muscular = %s,
            data_agendada = %s,
            horario = %s,
            observacoes = %s
        WHERE id = %s
        """, (
            dias[data_objeto.weekday()], grupo_muscular, data_agendada,
            horario, observacoes, id
        ))
        conexao.commit()

        return """
        <h2>✅ Agendamento atualizado!</h2>
        <a href="/agenda">Voltar para a agenda</a>
        """

    grupo = agendamento[1] or ""
    data = agendamento[2].strftime("%Y-%m-%d") if agendamento[2] else ""
    horario = str(agendamento[3])[:5] if agendamento[3] else ""
    observacoes = agendamento[4] or ""
    grupos_html = "".join(
        f'<option value="{nome}" {"selected" if nome == grupo else ""}>{nome}</option>'
        for nome in exercicios
    )

    return f"""
    <h1>✏️ Editar agendamento</h1>
    <form method="POST">
        <label>Grupo muscular:</label>
        <select name="grupo_muscular" required>{grupos_html}</select><br><br>
        <label>Data:</label>
        <input type="date" name="data_agendada" value="{data}" required><br><br>
        <label>Horário:</label>
        <input type="time" name="horario" value="{horario}" required><br><br>
        <label>Observações:</label><br>
        <textarea name="observacoes" rows="4" cols="40">{observacoes}</textarea><br><br>
        <button type="submit">Salvar alterações</button>
    </form>
    <br><a href="/agenda">Cancelar e voltar</a>
    """


@app.route("/excluir_agendamento/<int:id>")
def excluir_agendamento(id):
    cursor.execute("""
    DELETE FROM agenda_treinos
    WHERE id = %s
    """, (id,))
    conexao.commit()

    return """
    <h2>🗑️ Agendamento excluído.</h2>
    <a href="/agenda">Voltar para a agenda</a><br><br>
    <a href="/">Voltar ao menu</a>
    """


@app.route("/notificacoes")
def notificacoes():
    verificar_lembretes()
    cursor.execute("""
    SELECT id, tipo, titulo, mensagem, criada_em, lida
    FROM notificacoes
    ORDER BY criada_em DESC, id DESC
    LIMIT 100
    """)
    avisos = cursor.fetchall()
    html_pagina = "<h1>Central de notificações</h1>"
    html_pagina += "<p>Os lembretes de horário são verificados enquanto o GymTracker está aberto e também ao abrir esta página.</p>"
    if avisos:
        for aviso in avisos:
            id_aviso, tipo, titulo, mensagem, criada_em, lida = aviso
            estado = "Lida" if lida else "Não lida"
            data = criada_em.strftime("%d/%m/%Y %H:%M") if criada_em else ""
            html_pagina += f"<section><h3>{html.escape(titulo)} ({estado})</h3><p>{html.escape(mensagem)}</p><small>{html.escape(tipo)} — {data}</small>"
            if not lida:
                html_pagina += f"<form method='POST' action='/notificacoes/{id_aviso}/ler'><button type='submit'>Marcar como lida</button></form>"
            html_pagina += "</section><hr>"
    else:
        html_pagina += "<p>Nenhuma notificação por enquanto.</p>"
    html_pagina += "<p><a href='/'>Voltar ao menu</a></p>"
    return html_pagina


def verificar_lembretes():
    agora = datetime.now()
    cursor.execute("""
    SELECT id, grupo_muscular, data_agendada, horario
    FROM agenda_treinos
    WHERE data_agendada = %s
      AND (concluido = 0 OR concluido IS NULL)
    ORDER BY horario
    """, (agora.date(),))
    agendamentos = cursor.fetchall()
    for agendamento in agendamentos:
        id_agendamento, grupo, data, horario = agendamento
        horario_texto = str(horario)[:5] if horario else "horário não informado"
        mensagem_dia = f"Você tem treino de {grupo or 'musculação'} hoje, às {horario_texto}."
        cursor.execute("""
        INSERT IGNORE INTO notificacoes (tipo, titulo, mensagem, chave_unica)
        VALUES ('treino', 'Treino agendado para hoje', %s, %s)
        """, (mensagem_dia, f"agendamento_{id_agendamento}_dia"))
        if horario and horario <= agora.time().replace(microsecond=0):
            mensagem_horario = f"Está na hora do treino de {grupo or 'musculação'}, agendado para hoje às {horario_texto}."
            cursor.execute("""
            INSERT IGNORE INTO notificacoes (tipo, titulo, mensagem, chave_unica)
            VALUES ('treino', 'Está na hora do treino', %s, %s)
            """, (mensagem_horario, f"agendamento_{id_agendamento}_horario"))
    conexao.commit()


@app.route("/notificacoes/<int:id>/ler", methods=["POST"])
def marcar_notificacao_lida(id):
    cursor.execute("""
    UPDATE notificacoes
    SET lida = 1
    WHERE id = %s
    """, (id,))
    conexao.commit()
    return "<p>Notificação marcada como lida.</p><a href='/notificacoes'>Voltar à central</a>"


@app.route("/api/notificacoes_pendentes")
def api_notificacoes_pendentes():
    verificar_lembretes()
    cursor.execute("""
    SELECT id, titulo, mensagem
    FROM notificacoes
    WHERE lida = 0
      AND criada_em >= DATE_SUB(NOW(), INTERVAL 2 MINUTE)
    ORDER BY criada_em DESC
    """)
    dados = cursor.fetchall()
    return jsonify([
        {"id": aviso[0], "titulo": aviso[1], "mensagem": aviso[2]}
        for aviso in dados
    ])


@app.route("/exercicios")
def pesquisar_exercicios():
    termo = request.args.get("q", "").strip()
    resultados = []
    erro_api = ""
    if termo:
        try:
            parametros = urlencode({"search": termo, "limit": 12})
            requisicao = Request(
                f"{EXERCISE_API_URL}?{parametros}",
                headers={"User-Agent": "GymTracker/0.3"}
            )
            with urlopen(requisicao, timeout=5) as resposta:
                conteudo = json.loads(resposta.read().decode("utf-8"))
            if isinstance(conteudo, list):
                resultados = conteudo
            elif isinstance(conteudo, dict):
                resultados = conteudo.get("data", conteudo.get("results", conteudo.get("exercises", [])))
                if isinstance(resultados, dict):
                    resultados = resultados.get("data", [])
        except (URLError, HTTPError, TimeoutError, ValueError, OSError):
            erro_api = "Não foi possível consultar a biblioteca de GIFs agora. Você ainda pode pesquisar vídeos pelo link abaixo."

    pagina = "<h1>Pesquisar exercícios</h1>"
    pagina += "<form method='GET' action='/exercicios'><label>Nome do exercício:</label> <input name='q' value='" + html.escape(termo, quote=True) + "' required><button type='submit'>Pesquisar</button></form>"
    if termo:
        pagina += f"<p><a target='_blank' rel='noopener' href='https://www.youtube.com/results?search_query={quote(termo + ' exercício execução correta')}'>Ver vídeos no YouTube sobre {html.escape(termo)}</a></p>"
        if erro_api:
            pagina += f"<p>{html.escape(erro_api)}</p>"
        if resultados:
            for item in resultados[:12]:
                nome = str(item.get("name", "Exercício"))
                alvo = str(item.get("target", item.get("targetMuscle", "Não informado")))
                equipamento = str(item.get("equipment", "Não informado"))
                gif = item.get("gifUrl") or item.get("gif_url") or item.get("imageUrl")
                instrucoes = item.get("instructions", [])
                pagina += f"<h2>{html.escape(nome)}</h2><p>Músculo-alvo: {html.escape(alvo)}</p><p>Equipamento: {html.escape(equipamento)}</p>"
                if gif:
                    pagina += f"<p><img src='{html.escape(str(gif), quote=True)}' alt='Demonstração de {html.escape(nome, quote=True)}' width='300'></p>"
                if isinstance(instrucoes, list) and instrucoes:
                    pagina += "<ol>" + "".join(f"<li>{html.escape(str(passo))}</li>" for passo in instrucoes) + "</ol>"
                pagina += "<hr>"
        elif not erro_api:
            pagina += "<p>Nenhum exercício foi encontrado na API para esse termo. Tente outro nome ou use a busca de vídeos.</p>"
    pagina += "<p><a href='/'>Voltar ao menu</a></p>"
    return pagina


@app.route("/fichas", methods=["GET", "POST"])
def fichas():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        if not nome:
            return "Informe o nome da ficha. <a href='/fichas'>Voltar</a>", 400
        cursor.execute("""
        INSERT INTO fichas_treino (nome, descricao)
        VALUES (%s, %s)
        """, (nome, descricao))
        conexao.commit()
        return "<p>Ficha criada.</p><a href='/fichas'>Ver fichas</a>"

    cursor.execute("""
    SELECT id, nome, descricao
    FROM fichas_treino
    ORDER BY criada_em DESC, id DESC
    """)
    lista = cursor.fetchall()
    pagina = "<h1>Fichas de treino</h1><form method='POST'><label>Nome:</label><input name='nome' required><br><br><label>Descrição:</label><textarea name='descricao'></textarea><br><button type='submit'>Criar ficha</button></form><hr>"
    if lista:
        for ficha in lista:
            pagina += f"<h2>{html.escape(ficha[1])}</h2><p>{html.escape(ficha[2] or '')}</p><a href='/fichas/{ficha[0]}'>Abrir ficha</a> | <a href='/fichas/{ficha[0]}/excluir' onclick=\"return confirm('Excluir esta ficha?')\">Excluir</a><hr>"
    else:
        pagina += "<p>Nenhuma ficha criada.</p>"
    pagina += "<p><a href='/'>Voltar ao menu</a></p>"
    return pagina


@app.route("/fichas/<int:id>", methods=["GET", "POST"])
def detalhes_ficha(id):
    cursor.execute("SELECT id, nome, descricao FROM fichas_treino WHERE id = %s", (id,))
    ficha = cursor.fetchone()
    if not ficha:
        return "Ficha não encontrada.", 404
    if request.method == "POST":
        exercicio = request.form.get("exercicio", "").strip()
        grupo = request.form.get("grupo_muscular", "").strip()
        try:
            series = int(request.form.get("series", "3"))
            repeticoes = int(request.form.get("repeticoes", "10"))
            descanso = int(request.form.get("descanso_segundos", "60"))
            if not exercicio or min(series, repeticoes, descanso) < 0 or series < 1 or repeticoes < 1:
                raise ValueError
        except ValueError:
            return "Confira o exercício, séries, repetições e descanso. <a href='/fichas/" + str(id) + "'>Voltar</a>", 400
        cursor.execute("""
        INSERT INTO ficha_exercicios
            (ficha_id, exercicio, grupo_muscular, series, repeticoes, descanso_segundos)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (id, exercicio, grupo, series, repeticoes, descanso))
        conexao.commit()
        return f"<p>Exercício adicionado.</p><a href='/fichas/{id}'>Voltar à ficha</a>"

    cursor.execute("""
    SELECT id, exercicio, grupo_muscular, series, repeticoes, descanso_segundos
    FROM ficha_exercicios
    WHERE ficha_id = %s
    ORDER BY id
    """, (id,))
    itens = cursor.fetchall()
    pagina = f"<h1>Ficha: {html.escape(ficha[1])}</h1><p>{html.escape(ficha[2] or '')}</p><h2>Adicionar exercício</h2>"
    pagina += f"<form method='POST'><label>Exercício:</label><input name='exercicio' required><br><label>Grupo muscular:</label><input name='grupo_muscular'><br><label>Séries:</label><input type='number' name='series' min='1' value='3' required><br><label>Repetições:</label><input type='number' name='repeticoes' min='1' value='10' required><br><label>Descanso (segundos):</label><input type='number' name='descanso_segundos' min='0' value='60' required><br><button type='submit'>Adicionar</button></form><h2>Exercícios da ficha</h2>"
    if itens:
        pagina += "<ol>"
        for item in itens:
            pagina += f"<li>{html.escape(item[1])} — {html.escape(item[2] or '')}, {item[3]} séries x {item[4]} repetições, descanso {item[5]}s <a href='/ficha_exercicio/{item[0]}/excluir' onclick=\"return confirm('Remover exercício?')\">Remover</a></li>"
        pagina += "</ol>"
        pagina += f"<form method='POST' action='/iniciar_ficha/{id}'><button type='submit'>Criar treinos pendentes a partir desta ficha</button></form>"
    else:
        pagina += "<p>Adicione pelo menos um exercício para iniciar a ficha.</p>"
    pagina += "<p><a href='/fichas'>Voltar às fichas</a></p>"
    return pagina


@app.route("/fichas/<int:id>/excluir")
def excluir_ficha(id):
    cursor.execute("DELETE FROM fichas_treino WHERE id = %s", (id,))
    conexao.commit()
    return "<p>Ficha excluída.</p><a href='/fichas'>Voltar às fichas</a>"


@app.route("/ficha_exercicio/<int:id>/excluir")
def excluir_exercicio_ficha(id):
    cursor.execute("SELECT ficha_id FROM ficha_exercicios WHERE id = %s", (id,))
    linha = cursor.fetchone()
    if not linha:
        return "Exercício não encontrado na ficha.", 404
    ficha_id = linha[0]
    cursor.execute("DELETE FROM ficha_exercicios WHERE id = %s", (id,))
    conexao.commit()
    return f"<p>Exercício removido.</p><a href='/fichas/{ficha_id}'>Voltar à ficha</a>"


@app.route("/iniciar_ficha/<int:id>", methods=["POST"])
def iniciar_ficha(id):
    cursor.execute("""
    SELECT exercicio, grupo_muscular, series, repeticoes
    FROM ficha_exercicios
    WHERE ficha_id = %s
    ORDER BY id
    """, (id,))
    itens = cursor.fetchall()
    if not itens:
        return "Esta ficha não tem exercícios.", 400
    hoje = datetime.now().date()
    for item in itens:
        cursor.execute("""
        INSERT INTO treinos
            (exercicio, carga, series, repeticoes, grupo_muscular, data_treino, duracao_min, observacoes, concluido)
        VALUES (%s, 0, %s, %s, %s, %s, 0, %s, 0)
        """, (item[0], item[2], item[3], item[1], hoje, f"Criado pela ficha {id}; informe a carga ao editar."))
    conexao.commit()
    return "<p>Treinos pendentes criados a partir da ficha.</p><a href='/treinos'>Ver treinos</a>"


@app.route("/cronometro")
def cronometro():
    return """
    <h1>Cronômetro de descanso</h1>
    <label>Descanso em segundos:</label>
    <input type="number" id="segundos" min="1" value="60">
    <p id="tempo">01:00</p>
    <button onclick="iniciar()">Iniciar</button>
    <button onclick="pausar()">Pausar</button>
    <button onclick="reiniciar()">Reiniciar</button>
    <script>
    let restante = 60;
    let intervalo = null;
    function mostrar() {
        const min = Math.floor(restante / 60).toString().padStart(2, '0');
        const seg = (restante % 60).toString().padStart(2, '0');
        document.getElementById('tempo').textContent = min + ':' + seg;
    }
    function iniciar() {
        if (intervalo !== null) return;
        if (restante <= 0) restante = Math.max(1, parseInt(document.getElementById('segundos').value || '60'));
        intervalo = setInterval(function() {
            restante -= 1; mostrar();
            if (restante <= 0) {
                clearInterval(intervalo); intervalo = null;
                if ('Notification' in window && Notification.permission === 'granted') new Notification('Descanso finalizado', {body: 'Hora de continuar sua série.'});
                else alert('Descanso finalizado!');
            }
        }, 1000);
    }
    function pausar() { if (intervalo !== null) { clearInterval(intervalo); intervalo = null; } }
    function reiniciar() { pausar(); restante = Math.max(1, parseInt(document.getElementById('segundos').value || '60')); mostrar(); }
    document.getElementById('segundos').addEventListener('change', reiniciar);
    mostrar();
    </script>
    <p><a href='/'>Voltar ao menu</a></p>
    """


@app.route("/exportar")
def exportar_dados():
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as arquivo_zip:
        for tabela in ("treinos", "agenda_treinos", "notificacoes", "fichas_treino", "ficha_exercicios"):
            try:
                cursor.execute(f"SELECT * FROM {tabela}")
                linhas = cursor.fetchall()
                colunas = [coluna[0] for coluna in cursor.description]
                texto = io.StringIO()
                escritor = csv.writer(texto)
                escritor.writerow(colunas)
                for linha in linhas:
                    escritor.writerow([valor.isoformat() if hasattr(valor, "isoformat") else valor for valor in linha])
                arquivo_zip.writestr(f"{tabela}.csv", texto.getvalue().encode("utf-8-sig"))
            except Exception:
                conexao.rollback()
    memoria.seek(0)
    return Response(
        memoria.getvalue(),
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment; filename=gymtracker_backup.zip"}
    )


@app.route("/atualizacoes")
def atualizacoes():
    pagina = f"<h1>Versão e atualizações</h1><p>Versão instalada: {APP_VERSION}</p>"
    if not UPDATE_MANIFEST_URL:
        pagina += "<p>A verificação automática de versões ainda não está configurada. Para ativá-la, configure a variável de ambiente GYMTRACKER_UPDATE_MANIFEST_URL com a URL de um arquivo JSON publicado pelo responsável pelo projeto.</p>"
    else:
        try:
            requisicao = Request(UPDATE_MANIFEST_URL, headers={"User-Agent": "GymTracker/0.3"})
            with urlopen(requisicao, timeout=5) as resposta:
                manifesto = json.loads(resposta.read().decode("utf-8"))
            versao_nova = str(manifesto.get("version", ""))
            notas = str(manifesto.get("notes", "Há uma nova versão disponível."))
            url_nova = str(manifesto.get("url", ""))
            def versao_tuple(valor):
                return tuple(int(parte) for parte in valor.split(".") if parte.isdigit())
            if versao_nova and versao_tuple(versao_nova) > versao_tuple(APP_VERSION):
                cursor.execute("""
                INSERT IGNORE INTO notificacoes (tipo, titulo, mensagem, chave_unica)
                VALUES ('atualizacao', 'Atualização disponível', %s, %s)
                """, (f"Versão {versao_nova}: {notas} {url_nova}".strip(), f"atualizacao_{versao_nova}"))
                conexao.commit()
                pagina += f"<p>Nova versão disponível: {html.escape(versao_nova)}</p><p>{html.escape(notas)}</p>"
                if url_nova.startswith("https://"):
                    pagina += f"<p><a href='{html.escape(url_nova, quote=True)}' target='_blank' rel='noopener'>Abrir atualização</a></p>"
            else:
                pagina += "<p>Você está usando a versão mais recente informada pelo manifesto.</p>"
        except (URLError, HTTPError, TimeoutError, ValueError, OSError, TypeError):
            pagina += "<p>Não foi possível verificar a versão agora. Confira a URL do manifesto e tente novamente.</p>"
    pagina += "<p><a href='/notificacoes'>Abrir central de notificações</a></p><p><a href='/'>Voltar ao menu</a></p>"
    return pagina


if __name__ == "__main__":
    app.run(debug=True)