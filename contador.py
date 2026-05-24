import streamlit as st
from model import BlackjackModel
import pandas as pd

# 1. Configuração da Página (Mobile Friendly)
st.set_page_config(page_title="Elite Counter", page_icon="🃏", layout="centered")

# 2. Iniciar a "Memória" do App (Session State)
if 'contador' not in st.session_state:
    st.session_state.contador = BlackjackModel()

app_model = st.session_state.contador

# 3. Cabeçalho e Painel de Controle
st.title("Elite Card Counter")

col_power, col_undo, col_reset = st.columns(3)
with col_power:
    is_power = st.toggle("Power BJ", value=(app_model.game_mode == 'power'))
    if is_power and app_model.game_mode == 'standard':
        app_model.reset_shoe('power')
        st.rerun()
    elif not is_power and app_model.game_mode == 'power':
        app_model.reset_shoe('standard')
        st.rerun()

with col_undo:
    if st.button("↩️ Undo", use_container_width=True):
        app_model.undo_last()
        st.rerun()
        
with col_reset:
    if st.button("🔄 Reset", type="primary", use_container_width=True):
        app_model.reset_shoe('power' if is_power else 'standard')
        st.rerun()

# 4. Painel Principal de Estatísticas
st.markdown("---")
tc_val = app_model.true_count
tc_color = "normal" if -1 < tc_val < 2 else ("inverse" if tc_val >= 2 else "off")

col1, col2, col3 = st.columns(3)
col1.metric("Running Count", app_model.running_count)
col2.metric("True Count", f"{tc_val:.2f}", delta="EV+" if tc_val >= 2 else None, delta_color=tc_color)
col3.metric("Decks Left", f"{app_model.decks_remaining:.2f}")
st.markdown("---")

# 5. Modo de Inserção (Abas)
tab_simple, tab_complex, tab_stats = st.tabs(["⚡ Simple Mode", "🎴 Complex", "📊 Side Bets"])

# ABA 1: Simple Mode (Botões Gigantes)
with tab_simple:
    c1, c2, c3 = st.columns(3)
    
    # Textos dinâmicos: Se Power BJ estiver ligado, removemos o 9 e o 10 da tela!
    texto_zero = "0\n(7 e 8)" if is_power else "0\n(7 a 9)"
    texto_menos = "➖ -1\n(J, Q, K, A)" if is_power else "➖ -1\n(10 a A)"
    
    if c1.button("➕ +1\n(2 a 6)", use_container_width=True):
        app_model.process_simple(1)
        st.rerun()
    if c2.button(texto_zero, use_container_width=True):
        app_model.process_simple(0)
        st.rerun()
    if c3.button(texto_menos, use_container_width=True):
        app_model.process_simple(-1)
        st.rerun()

# ==========================================
# ABA 2: NOVO COMPLEX MODE (OTIMIZADO PARA MOBILE)
# ==========================================
with tab_complex:
    st.markdown("<p style='text-align: center; color: #888; font-size: 14px;'>1. Selecione o Naipe</p>", unsafe_allow_html=True)
    
    # Seletor Horizontal de Naipes
    simbolos_map = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
    naipe_selecionado = st.radio(
        "Naipe", 
        ['Hearts', 'Diamonds', 'Clubs', 'Spades'], 
        horizontal=True, 
        label_visibility="collapsed",
        format_func=lambda x: f"{simbolos_map[x]} {x}"
    )
    
    st.markdown("<p style='text-align: center; color: #888; font-size: 14px;'>2. Toque na Carta</p>", unsafe_allow_html=True)
    
    simbolo_atual = simbolos_map[naipe_selecionado]
    
    # Grid dinâmico de 13 botões (muda dependendo do naipe escolhido)
    cols = st.columns(4)
    for i, val in enumerate(app_model.VALORES_STANDARD):
        is_disabled = (is_power and val in ['9', '10'])
        
        # O botão exibe a carta + o naipe selecionado atualmente
        if cols[i % 4].button(f"{val} {simbolo_atual}", key=f"btn_{val}", disabled=is_disabled, use_container_width=True):
            app_model.process_card(val, naipe_selecionado)
            st.rerun()

# ABA 3: Side Bets e Composição
with tab_stats:
    val_counts, suit_counts, suit_percs = app_model.get_stats()
    
    st.subheader("Flush 21+3 (Suit Concentration)")
    df_suits = pd.DataFrame([
        {"Suit": f"{simbolos_map[s]} {s}", "Left": count, "%": f"{suit_percs[s]:.1f}%"}
        for s, count in suit_counts.items()
    ])
    st.dataframe(df_suits, use_container_width=True, hide_index=True)
    
    for s, p in suit_percs.items():
        if p >= 29.5:
            st.success(f"🔥 Aposta Paralela de Flush recomendada para {s} ({p:.1f}%)")

    # ==========================================
    # NOVO: MÓDULO BUST IT DUPLO (Rápido vs Jackpot)
    # ==========================================
    st.markdown("---")
    st.subheader("💥 Bust It (Quebra do Dealer)")
    
    total_cartas = sum(val_counts.values())
    if total_cartas > 0:
        # 1. RADAR DE QUEBRA RÁPIDA (+EV Padrão, Geralmente 3 cartas)
        # No Power BJ, o '10' estará naturalmente zerado
        cartas_pesadas = val_counts['K'] + val_counts['Q'] + val_counts['J'] + val_counts['10']
        bust_perc = (cartas_pesadas / total_cartas) * 100
        baseline_pesadas = 27.2 if is_power else 30.7
        gatilho_ev = baseline_pesadas + 4.0 
        
        # 2. RADAR DE QUEBRA LONGA (Jackpot, 5+ cartas)
        # Usamos 2 a 5 pois são as cartas que mantêm o dealer "vivo" pedindo mais
        micro_cartas = val_counts['2'] + val_counts['3'] + val_counts['4'] + val_counts['5']
        micro_perc = (micro_cartas / total_cartas) * 100
        baseline_micro = 36.3 if is_power else 30.7 # No Power BJ já há uma concentração maior natural de baixas
        gatilho_jackpot = baseline_micro + 5.0
        
        # Display dos dois Radares
        col_b1, col_b2 = st.columns(2)
        
        delta_pesadas = "normal" if bust_perc > baseline_pesadas else "inverse"
        col_b1.metric("Densidade Figuras\n(Rápida)", f"{bust_perc:.1f}%", f"{bust_perc - baseline_pesadas:.1f}% vs Inicial", delta_color=delta_pesadas)
        
        delta_micro = "normal" if micro_perc > baseline_micro else "inverse"
        col_b2.metric("Densidade 2 a 5\n(Jackpot)", f"{micro_perc:.1f}%", f"{micro_perc - baseline_micro:.1f}% vs Inicial", delta_color=delta_micro)
        
        # Lógica dos Alarmes
        if bust_perc >= gatilho_ev or app_model.true_count >= 5.0:
            st.success(f"🚨 ALERTA BUST RÁPIDO: Baralho lotado de figuras. Alta chance do dealer estourar rapidamente com 3 cartas. Aposta +EV segura.")
            
        elif micro_perc >= gatilho_jackpot or app_model.true_count <= -4.0:
            st.warning(f"🎰 ALERTA BUST JACKPOT: Baralho inundado de cartas baixas. O dealer pedirá muitas cartas. Se quebrar, pagará um multiplicador GIGANTE. (Aviso: Alta Variância/Risco!).")
            
        else:
            st.info(f"🔒 Aguarde. O baralho está neutro. Nenhuma das densidades de quebra foi atingida.")
