import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


DB_HOST = os.getenv("DB_HOST", "dataiesb.iesbtech.com.br")
DB_NAME = os.getenv("DB_NAME", "2422120014_Gustavo")
DB_USER = os.getenv("DB_USER", "2422120014_Gustavo")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
UMIDADE_ALERTA = 60
TEMPERATURA_MIN_ALERTA = 25
TEMPERATURA_MAX_ALERTA = 30
DURACAO_ALERTA_HORAS = 6
HORAS_PREVISAO = 6


def carregar_dados():
    if not DB_PASSWORD:
        raise RuntimeError("Defina DB_PASSWORD no ambiente.")

    url = URL.create(
        "postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )
    engine = create_engine(url, connect_args={"connect_timeout": 10})
    try:
        with engine.connect() as conexao:
            dados = pd.read_sql_query(
                text("SELECT id, temperatura, umidade, dispositivo, data FROM public.leituras_esp32_dht22"),
                conexao,
            )
    finally:
        engine.dispose()

    dados["data"] = pd.to_datetime(dados["data"], dayfirst=True, errors="coerce")
    dados["temperatura"] = pd.to_numeric(dados["temperatura"], errors="coerce")
    dados["umidade"] = pd.to_numeric(dados["umidade"], errors="coerce")
    return dados.dropna(subset=["data", "temperatura", "umidade"]).sort_values("data")


def selecionar_leitura(dados, data_escolhida, hora_escolhida):
    """Escolhe a última leitura que não ultrapassa o horário solicitado."""
    if dados.empty or not data_escolhida or not hora_escolhida:
        return None
    momento = pd.Timestamp(f"{data_escolhida} {hora_escolhida}")
    anteriores = dados.loc[dados["data"] <= momento]
    return None if anteriores.empty else anteriores.iloc[-1]

app = Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server = app.server
app.title = "Clima do Armário | Monitoramento"

cores = {
    "fundo": "#f7f8f4",
    "texto": "#263f39",
    "secundario": "#6e8079",
    "temperatura": "#db956d",
    "umidade": "#62a995",
    "alerta": "#ac6749",
    "alerta_fundo": "#fff3e9",
    "ok": "#418c76",
    "ok_fundo": "#e9f5ef",
}

ESTILO_CARTAO = {
    "backgroundColor": "white",
    "borderRadius": "20px",
    "padding": "22px 24px",
    "border": "1px solid #e7eee9",
    "boxShadow": "0 8px 26px rgba(41, 73, 61, 0.045)",
}


def cartao_metrica(titulo, valor, unidade, variante="neutro", detalhe=None):
    return html.Div(
        [
            html.Div(
                [
                    html.Span("◌" if variante == "umidade" else "°", className="metric-icon"),
                    html.Span(titulo, className="metric-label"),
                ],
                className="metric-top",
            ),
            html.Div([html.Span(valor), html.Small(unidade)], className="metric-value"),
            html.Div(detalhe or "No período selecionado", className="metric-detail"),
        ],
        className=f"metric-card metric-card--{variante}",
    )


def cabecalho_secao(rotulo, titulo, descricao=None):
    return html.Div(
        [
            html.Div(rotulo, className="section-kicker"),
            html.H2(titulo, className="section-title"),
            html.P(descricao, className="section-description") if descricao else None,
        ],
        className="section-header",
    )


def cartao_grafico(titulo, descricao, figura, legenda=False, variante="temperatura"):
    return html.Div(
        [
            html.Div([html.H3(titulo), html.P(descricao)], className="chart-heading"),
            html.Div(
                [
                    html.Span([html.I(className="legend-line legend-line--solid"), "Leituras recentes"]),
                    html.Span([html.I(className="legend-line legend-line--dashed"), "Projeção de 6h"]),
                ],
                className=f"chart-legend chart-legend--{variante}",
            ) if legenda else None,
            dcc.Graph(figure=figura, config={"displayModeBar": False, "responsive": True}, className="chart-graph"),
        ],
        className="chart-card",
    )


def servir_layout():
    try:
        dados_iniciais = carregar_dados()
    except Exception:
        dados_iniciais = pd.DataFrame(columns=["data", "temperatura", "umidade", "dispositivo"])
    primeiro_dia = dados_iniciais["data"].min().date() if not dados_iniciais.empty else None
    ultimo_dia = dados_iniciais["data"].max().date() if not dados_iniciais.empty else None
    ultima_leitura = dados_iniciais.iloc[-1] if not dados_iniciais.empty else None
    ultima_data = ultima_leitura["data"].strftime("%d/%m/%Y às %H:%M") if ultima_leitura is not None else "Aguardando conexão"

    return html.Div(
        [
            html.Div(
                [
                    html.Header(
                        [
                            html.Div(
                                [
                                    html.Div("CA", className="brand-mark"),
                                    html.Div(
                                        [
                                            html.Div("CLIMA DO ARMÁRIO", className="brand-name"),
                                            html.Div("Painel de monitoramento", className="brand-caption"),
                                        ]
                                    ),
                                ],
                                className="brand",
                            ),
                            html.Div([html.Span(className="status-dot"), "ESP32 · DHT22"], className="sensor-badge"),
                        ],
                        className="topbar",
                    ),
                    html.Section(
                        [
                            html.Div(
                                [
                                    html.Div("UM AMBIENTE SOB CUIDADO", className="eyebrow"),
                                    html.H1("Tudo em equilíbrio, em um só lugar."),
                                    html.P("Acompanhe temperatura, umidade e tendências do seu armário com leituras simples de entender."),
                                    html.Div([html.Span(className="latest-dot"), "Última leitura: ", html.Strong(ultima_data)], className="latest-pill"),
                                ],
                                className="hero-copy",
                            ),
                            html.Div(
                                [
                                    html.Div("TEMPERATURA + UMIDADE", className="hero-illustration-label"),
                                    html.Div([html.Span("°", className="hero-degree"), html.Span("◌", className="hero-circle")], className="hero-symbols"),
                                    html.Div("Um olhar atento ao seu espaço", className="hero-illustration-foot"),
                                ],
                                className="hero-illustration",
                                **{"aria-hidden": "true"},
                            ),
                        ],
                        className="hero",
                    ),
                    html.Div(
                        [
                            html.Div("VISÃO GERAL", className="section-kicker"),
                            html.H2("Explore as leituras", className="page-heading"),
                            html.P("Escolha uma visão para acompanhar o ambiente do armário.", className="page-subheading"),
                        ],
                        className="page-intro",
                    ),
                    dcc.Tabs(
                        id="abas",
                        value="graficos",
                        children=[
                            dcc.Tab(label="Gráficos", value="graficos", className="app-tab", selected_className="app-tab app-tab--selected"),
                            dcc.Tab(label="Alertas e previsão", value="alertas", className="app-tab", selected_className="app-tab app-tab--selected"),
                            dcc.Tab(label="Monitoramento", value="monitoramento", className="app-tab", selected_className="app-tab app-tab--selected"),
                        ],
                        className="app-tabs",
                    ),
                    html.Div(
                        [
                            html.Div([html.Div("PERÍODO", className="filter-kicker"), html.H3("Selecione as datas")], className="filter-title"),
                            html.Div(
                                [
                                    html.Label("Intervalo de análise", htmlFor="date-range", className="filter-label"),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        min_date_allowed=primeiro_dia,
                                        max_date_allowed=ultimo_dia,
                                        start_date=primeiro_dia,
                                        end_date=ultimo_dia,
                                        display_format="DD/MM/YYYY",
                                        start_date_placeholder_text="Início",
                                        end_date_placeholder_text="Fim",
                                        number_of_months_shown=2,
                                        minimum_nights=0,
                                    ),
                                ],
                                className="filter-control",
                            ),
                        ],
                        id="periodo-geral",
                        className="filter-panel",
                    ),
                    html.Div(
                        [
                            html.Div([html.Div("CONSULTA PONTUAL", className="filter-kicker"), html.H3("Escolha um momento")], className="filter-title"),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label("Data", htmlFor="monitor-date", className="filter-label"),
                                            dcc.DatePickerSingle(
                                                id="monitor-date",
                                                date=ultima_leitura["data"].date() if ultima_leitura is not None else None,
                                                min_date_allowed=primeiro_dia,
                                                max_date_allowed=ultimo_dia,
                                                display_format="DD/MM/YYYY",
                                            ),
                                        ],
                                        className="filter-control",
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Horário", htmlFor="monitor-time", className="filter-label"),
                                            dcc.Input(
                                                id="monitor-time",
                                                type="time",
                                                value=ultima_leitura["data"].strftime("%H:%M") if ultima_leitura is not None else None,
                                                step=60,
                                                className="time-input",
                                            ),
                                        ],
                                        className="filter-control",
                                    ),
                                ],
                                className="monitor-controls",
                            ),
                        ],
                        id="controles-monitoramento",
                        className="filter-panel",
                        style={"display": "none"},
                    ),
                    dcc.Loading(html.Main(id="conteudo-aba", className="tab-content"), type="circle", color=cores["umidade"]),
                    html.Footer("Clima do Armário  ·  Leituras do sensor ESP32 + DHT22", className="footer"),
                ],
                className="app-container",
            ),
        ],
        className="app-background",
    )



app.layout = servir_layout

def criar_grafico_diario(dados, coluna, titulo, cor, unidade):
    medias_diarias = (
        dados.assign(dia=dados["data"].dt.date)
        .groupby("dia", as_index=False)[["temperatura", "umidade"]]
        .mean()
    )
    figura = px.line(
        medias_diarias,
        x="dia",
        y=coluna,
        color_discrete_sequence=[cor],
        markers=True,
    )
    figura.update_traces(
        line={"width": 3, "shape": "spline"},
        marker={"size": 7, "line": {"width": 2, "color": "white"}},
        hovertemplate=f"%{{x|%d/%m/%Y}}<br>%{{y:.2f}} {unidade}<extra></extra>",
    )
    figura.update_layout(
        template="plotly_white",
        height=310,
        showlegend=False,
        font={"family": "Segoe UI, Arial, sans-serif", "color": cores["secundario"], "size": 12},
        margin={"l": 42, "r": 15, "t": 20, "b": 45},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title=None,
        hovermode="x unified",
        hoverlabel={"bgcolor": "white", "font": {"color": cores["texto"]}},
    )
    figura.update_xaxes(showgrid=False, tickformat="%d/%m", nticks=6, linecolor="#e4ebe6", ticks="outside", tickcolor="#e4ebe6")
    figura.update_yaxes(gridcolor="#edf2ee", zeroline=False, ticksuffix=f" {unidade}")
    return figura


def criar_grafico_previsao(dados, coluna, titulo, cor, unidade):
    recentes = dados.tail(12).copy()
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=recentes["data"],
            y=recentes[coluna],
            mode="lines+markers",
            name="Leituras recentes",
            line={"color": cor, "width": 3},
            marker={"size": 6},
        )
    )

    if len(recentes) >= 3:
        horas = (recentes["data"] - recentes["data"].min()).dt.total_seconds() / 3600
        valores = recentes[coluna].to_numpy(dtype=float)
        inclinacao, intercepto = np.polyfit(horas, valores, 1)
        hora_atual = float(horas.iloc[-1])
        previsao_x = [recentes["data"].iloc[-1], recentes["data"].iloc[-1] + pd.Timedelta(hours=HORAS_PREVISAO)]
        previsao_y = [
            float(valores[-1]),
            float(intercepto + inclinacao * (hora_atual + HORAS_PREVISAO)),
        ]
        figura.add_trace(
            go.Scatter(
                x=previsao_x,
                y=previsao_y,
                mode="lines+markers",
                name=f"Projeção ({HORAS_PREVISAO}h)",
                line={"color": cor, "width": 3, "dash": "dash"},
                marker={"size": 7, "symbol": "circle-open"},
            )
        )

    figura.update_layout(
        template="plotly_white",
        height=310,
        showlegend=False,
        font={"family": "Segoe UI, Arial, sans-serif", "color": cores["secundario"], "size": 12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 42, "r": 15, "t": 20, "b": 58},
        xaxis_title=None,
        yaxis_title=None,
        hovermode="x unified",
        hoverlabel={"bgcolor": "white", "font": {"color": cores["texto"]}},
    )
    figura.update_xaxes(showgrid=False, tickformat="%d/%m %H:%M", nticks=5, tickangle=-25, automargin=True, linecolor="#e4ebe6")
    figura.update_yaxes(gridcolor="#edf2ee", zeroline=False, ticksuffix=f" {unidade}")
    return figura


def estado_alerta(dados):
    if dados.empty:
        return "sem_dados", "Não há leituras no período selecionado.", ""

    # Conta o trecho contínuo mais recente em que ambas as condições ocorrem.
    trecho = []
    for _, linha in dados.sort_values("data", ascending=False).iterrows():
        dentro_das_condicoes = (
            linha["umidade"] >= UMIDADE_ALERTA
            and TEMPERATURA_MIN_ALERTA <= linha["temperatura"] <= TEMPERATURA_MAX_ALERTA
        )
        if not dentro_das_condicoes:
            break
        if trecho and (trecho[-1]["data"] - linha["data"]).total_seconds() > 3600:
            break
        trecho.append(linha)

    if not trecho:
        return (
            "normal",
            "As leituras mais recentes não atendem simultaneamente aos critérios de temperatura e umidade do alerta.",
            "Continue acompanhando as medições. Como prevenção, mantenha o armário seco e ventilado.",
        )

    duracao = (trecho[0]["data"] - trecho[-1]["data"]).total_seconds() / 3600
    if duracao >= DURACAO_ALERTA_HORAS:
        return (
            "risco",
            f"Condição favorável à proliferação de mofo detectada por aproximadamente {duracao:.1f} horas: temperatura entre {TEMPERATURA_MIN_ALERTA} e {TEMPERATURA_MAX_ALERTA} °C e umidade em {UMIDADE_ALERTA}% ou mais.",
            "Abra a porta do armário para ventilar. Se possível, faça isso quando o ar do cômodo estiver mais seco.",
        )

    return (
        "atencao",
        f"Condição de atenção há {duracao:.1f} horas: temperatura entre {TEMPERATURA_MIN_ALERTA} e {TEMPERATURA_MAX_ALERTA} °C e umidade em {UMIDADE_ALERTA}% ou mais.",
        "Abra a porta do armário para ventilar e continue acompanhando a umidade.",
    )


def resumo_previsao(dados):
    recentes = dados.tail(12)
    if len(recentes) < 3:
        return "São necessárias pelo menos três leituras para estimar a tendência recente."

    horas = (recentes["data"] - recentes["data"].min()).dt.total_seconds() / 3600
    previsoes = {}
    descricoes = {}
    for coluna, nome, limite_estavel in [
        ("temperatura", "temperatura", 0.2),
        ("umidade", "umidade", 0.2),
    ]:
        valores = recentes[coluna].to_numpy(dtype=float)
        inclinacao, intercepto = np.polyfit(horas, valores, 1)
        valor_futuro = float(intercepto + inclinacao * (float(horas.iloc[-1]) + HORAS_PREVISAO))
        previsoes[coluna] = max(0.0, min(100.0, valor_futuro))
        if inclinacao > limite_estavel:
            descricoes[nome] = "aumentando"
        elif inclinacao < -limite_estavel:
            descricoes[nome] = "diminuindo"
        else:
            descricoes[nome] = "praticamente estável"

    texto = (
        f"Nas últimas horas, a temperatura está {descricoes['temperatura']} e a umidade está {descricoes['umidade']}. "
        f"Mantida essa tendência, em cerca de {HORAS_PREVISAO} horas a estimativa é "
        f"{previsoes['temperatura']:.1f} °C e {previsoes['umidade']:.1f}% de umidade."
    )
    return texto


def conteudo_graficos(dados):
    inicio = dados["data"].min().strftime("%d/%m/%Y")
    fim = dados["data"].max().strftime("%d/%m/%Y")
    return html.Div(
        [
            cabecalho_secao("PANORAMA", "Como está o seu armário?", f"Resumo de {inicio} a {fim}."),
            html.Div(
                [
                    cartao_metrica("Temperatura média", f"{dados['temperatura'].mean():.2f}", "°C", "temperatura"),
                    cartao_metrica("Temperatura máxima", f"{dados['temperatura'].max():.2f}", "°C", "temperatura"),
                    cartao_metrica("Umidade média", f"{dados['umidade'].mean():.2f}", "%", "umidade"),
                    cartao_metrica("Umidade máxima", f"{dados['umidade'].max():.2f}", "%", "umidade"),
                ],
                className="metrics-grid",
            ),
            cabecalho_secao("EVOLUÇÃO", "Acompanhe as mudanças", "Médias diárias calculadas a partir das leituras selecionadas."),
            html.Div(
                [
                    cartao_grafico("Temperatura", "Média por dia · °C", criar_grafico_diario(dados, "temperatura", "", cores["temperatura"], "°C")),
                    cartao_grafico("Umidade", "Média por dia · %", criar_grafico_diario(dados, "umidade", "", cores["umidade"], "%")),
                ],
                className="charts-grid",
            ),
            html.Div(f"{len(dados)} leituras no período  ·  Sensor: {', '.join(sorted(dados['dispositivo'].astype(str).unique()))}", className="data-note"),
        ]
    )


def conteudo_alertas(dados):
    nivel, mensagem, recomendacao = estado_alerta(dados)
    status = {
        "risco": ("Alerta de mofo", "Atenção necessária", "alerta"),
        "atencao": ("Atenção à umidade", "Acompanhe de perto", "alerta"),
        "normal": ("Ambiente acompanhado", "Sem alerta no momento", "normal"),
        "sem_dados": ("Sem leituras", "Escolha outro período", "normal"),
    }
    titulo, etiqueta, classe = status[nivel]
    return html.Div(
        [
            cabecalho_secao("CUIDADO CONTÍNUO", "Alertas e previsão", "Uma leitura clara das condições recentes do armário."),
            html.Div(
                [
                    html.Div([html.Span(className="alert-dot"), etiqueta], className="alert-badge"),
                    html.H3(titulo),
                    html.P(mensagem, className="alert-message"),
                    html.P(recomendacao, className="alert-recommendation") if recomendacao else None,
                ],
                className=f"alert-panel alert-panel--{classe}",
            ),
            html.Div(
                [
                    html.Div("PRÓXIMAS HORAS", className="section-kicker"),
                    html.H3("Tendência de 6 horas"),
                    html.P(resumo_previsao(dados), className="forecast-copy"),
                    html.Div("Estimativa linear das até 12 leituras mais recentes. É uma tendência, não uma garantia.", className="forecast-note"),
                ],
                className="forecast-panel",
            ),
            html.Div(
                [
                    cartao_grafico("Temperatura", "Leituras recentes e tendência · °C", criar_grafico_previsao(dados, "temperatura", "", cores["temperatura"], "°C"), True, "temperatura"),
                    cartao_grafico("Umidade", "Leituras recentes e tendência · %", criar_grafico_previsao(dados, "umidade", "", cores["umidade"], "%"), True, "umidade"),
                ],
                className="charts-grid",
            ),
        ]
    )


def conteudo_monitoramento(dados, data_escolhida, hora_escolhida):
    leitura = selecionar_leitura(dados, data_escolhida, hora_escolhida)
    if leitura is None:
        return html.Div(
            [cabecalho_secao("LEITURA PONTUAL", "Um momento do seu armário"),
             html.Div("Não há leitura anterior ao horário selecionado.", className="empty-state")]
        )

    momento = leitura["data"].strftime("%d/%m/%Y às %H:%M")
    return html.Div(
        [
            cabecalho_secao("LEITURA PONTUAL", "Um momento do seu armário", "Selecione a data e a hora para consultar a última medição disponível até esse instante."),
            html.Div(
                [
                    html.Div([html.Span(className="reading-dot"), "LEITURA ENCONTRADA"], className="reading-eyebrow"),
                    html.H3(momento),
                    html.P("Se não existir medição exatamente no horário escolhido, mostramos a anterior mais próxima."),
                ],
                className="reading-banner",
            ),
            html.Div(
                [
                    cartao_metrica("Temperatura", f"{leitura['temperatura']:.2f}", "°C", "temperatura", momento),
                    cartao_metrica("Umidade", f"{leitura['umidade']:.2f}", "%", "umidade", momento),
                ],
                className="metrics-grid metrics-grid--two",
            ),
        ]
    )



@app.callback(
    Output("conteudo-aba", "children"),
    Output("controles-monitoramento", "style"),
    Output("periodo-geral", "style"),
    Input("abas", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("monitor-date", "date"),
    Input("monitor-time", "value"),
)
def atualizar_dashboard(aba, data_inicio, data_fim, data_monitor, hora_monitor):
    estilo_monitor = {"display": "flex" if aba == "monitoramento" else "none"}
    estilo_periodo = {"display": "none" if aba == "monitoramento" else "flex"}
    try:
        dados = carregar_dados()
    except Exception:
        return html.Div("Não foi possível consultar o banco de dados. Verifique a conexão e as configurações.", style=ESTILO_CARTAO), estilo_monitor, estilo_periodo

    if aba == "monitoramento":
        if not dados.empty and (not data_monitor or not hora_monitor):
            ultima = dados.iloc[-1]["data"]
            data_monitor = data_monitor or ultima.date().isoformat()
            hora_monitor = hora_monitor or ultima.strftime("%H:%M")
        return conteudo_monitoramento(dados, data_monitor, hora_monitor), estilo_monitor, estilo_periodo

    if data_inicio:
        dados = dados[dados["data"] >= pd.Timestamp(data_inicio)]
    if data_fim:
        dados = dados[dados["data"] < pd.Timestamp(data_fim) + pd.Timedelta(days=1)]

    if dados.empty:
        return html.Div("Nenhuma leitura no período selecionado.", style=ESTILO_CARTAO), estilo_monitor, estilo_periodo
    if aba == "alertas":
        return conteudo_alertas(dados), estilo_monitor, estilo_periodo
    return conteudo_graficos(dados), estilo_monitor, estilo_periodo


if __name__ == "__main__":
    app.run(debug=False)
