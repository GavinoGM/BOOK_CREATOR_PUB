import streamlit as st
import requests
import json
import os
from datetime import datetime

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="BookCreator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stili CSS personalizzati
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2563EB;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-text {
        font-size: 1rem;
        color: #4B5563;
    }
    .chapter-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1F2937;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
    }
    .chapter-card {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #F9FAFB;
    }
    .chapter-card-generated {
        border-left: 5px solid #10B981;
    }
    .chapter-card-pending {
        border-left: 5px solid #EF4444;
    }
    .chapter-card-selected {
        border-left: 5px solid #3B82F6;
        background-color: #EFF6FF;
    }
    .progress-container {
        margin-top: 20px;
        padding: 10px;
        background-color: #F3F4F6;
        border-radius: 8px;
    }
    .metadata-box {
        background-color: #F3F4F6;
        border-radius: 5px;
        padding: 10px;
        margin-top: 10px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Inizializzazione dello stato dell'applicazione
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'config'
if 'book_structure' not in st.session_state:
    st.session_state.book_structure = None
if 'current_chapter' not in st.session_state:
    st.session_state.current_chapter = None
if 'generated_chapters' not in st.session_state:
    st.session_state.generated_chapters = {}

# Funzioni di utilità per le chiamate API
def call_anthropic_api(prompt, api_key):
    """Chiamata all'API di Anthropic (Claude)"""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except Exception as e:
        st.error(f"Errore nella chiamata API Anthropic: {str(e)}")
        return None

def call_openai_api(prompt, api_key):
    """Chiamata all'API di OpenAI (GPT)"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Errore nella chiamata API OpenAI: {str(e)}")
        return None

def generate_ai_response(prompt):
    """Genera una risposta dall'AI selezionata"""
    if st.session_state.ai_provider == "Anthropic":
        return call_anthropic_api(prompt, st.session_state.api_key)
    else:
        return call_openai_api(prompt, st.session_state.api_key)

def create_structure_prompt(title, theme, audience, style, goals):
    """Crea il prompt per generare la struttura del libro"""
    prompt = f"""
    Sei un esperto consulente editoriale. Aiutami a creare la struttura dettagliata per un libro non-fiction con le seguenti caratteristiche:

    - Titolo: {title}
    - Tema principale: {theme}
    - Pubblico target: {audience}
    - Stile di scrittura: {style}
    - Obiettivi del libro: {goals}

    Per favore, genera una struttura completa che includa:
    1. Un'introduzione convincente che presenti il tema e gli obiettivi del libro
    2. 6-10 capitoli logicamente organizzati, ciascuno con un titolo accattivante e una breve descrizione del contenuto (3-5 frasi)
    3. Una conclusione che riassuma i punti chiave e lasci il lettore con riflessioni significative

    La risposta dovrebbe essere strutturata in formato JSON come segue:
    {{
        "title": "Titolo del libro",
        "introduction": "Testo dell'introduzione...",
        "chapters": [
            {{
                "number": 1,
                "title": "Titolo del capitolo 1",
                "description": "Descrizione del capitolo..."
            }},
            ...
        ],
        "conclusion": "Testo della conclusione..."
    }}
    """
    return prompt

def create_chapter_prompt(book_info, chapter_info, key_points, length):
    """Crea il prompt per generare un capitolo specifico"""
    prompt = f"""
    Sei un autore di libri non-fiction esperto. Stai scrivendo un capitolo per il seguente libro:

    - Titolo del libro: {book_info['title']}
    - Tema principale: {book_info['theme']}
    - Pubblico target: {book_info['audience']}
    - Stile di scrittura: {book_info['style']}

    CAPITOLO DA SCRIVERE:
    - Numero: {chapter_info['number']}
    - Titolo: {chapter_info['title']}
    - Descrizione: {chapter_info['description']}
    
    Punti chiave da includere:
    {key_points if key_points else "Utilizza la tua creatività basandoti sulla descrizione del capitolo."}
    
    Lunghezza approssimativa: {length}
    
    Scrivi un capitolo completo, ben strutturato e coinvolgente. Includi esempi concreti, riferimenti pertinenti e, dove appropriato, aneddoti per illustrare i concetti. Assicurati che il capitolo mantenga uno stile coerente con il resto del libro e si colleghi logicamente ai capitoli precedenti e successivi.
    """
    return prompt

# Funzioni di navigazione
def go_to_structure():
    st.session_state.current_step = 'structure'

def go_to_content():
    st.session_state.current_step = 'content'

def go_to_export():
    st.session_state.current_step = 'export'

def go_back():
    if st.session_state.current_step == 'structure':
        st.session_state.current_step = 'config'
    elif st.session_state.current_step == 'content':
        st.session_state.current_step = 'structure'
    elif st.session_state.current_step == 'export':
        st.session_state.current_step = 'content'

# Schermata principale
st.markdown('<div class="main-header">📚 BookCreator</div>', unsafe_allow_html=True)

# Sidebar per la navigazione
with st.sidebar:
    st.markdown("### Navigazione")
    
    if st.button("1. Configurazione", disabled=st.session_state.current_step == 'config'):
        st.session_state.current_step = 'config'
    
    structure_disabled = st.session_state.current_step == 'config' and 'api_key' not in st.session_state
    if st.button("2. Struttura del libro", disabled=structure_disabled):
        st.session_state.current_step = 'structure'
    
    content_disabled = st.session_state.current_step in ['config', 'structure'] or not st.session_state.book_structure
    if st.button("3. Generazione contenuti", disabled=content_disabled):
        st.session_state.current_step = 'content'
    
    export_disabled = st.session_state.current_step in ['config', 'structure', 'content'] or not st.session_state.generated_chapters
    if st.button("4. Esporta libro", disabled=export_disabled):
        st.session_state.current_step = 'export'

# Logica per le diverse schermate
if st.session_state.current_step == 'config':
    st.markdown('<div class="section-header">Configurazione</div>', unsafe_allow_html=True)
    
    # Selezione del provider AI
    provider = st.selectbox(
        "Seleziona il provider AI",
        ["OpenAI", "Anthropic"],
        index=0
    )
    
    # Input API Key
    api_key = st.text_input(
        "Inserisci la tua API Key",
        type="password",
        help="La tua API key è memorizzata solo localmente nella sessione del browser"
    )
    
    if st.button("Salva configurazione"):
        if not api_key:
            st.error("Per favore, inserisci una API key valida")
        else:
            st.session_state.ai_provider = provider
            st.session_state.api_key = api_key
            st.success(f"Configurazione salvata! Provider: {provider}")
            st.session_state.current_step = 'structure'
            st.experimental_rerun()

elif st.session_state.current_step == 'structure':
    st.markdown('<div class="section-header">Definisci la struttura del tuo libro</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        book_title = st.text_input("Titolo del libro", key="book_title")
        book_theme = st.text_area("Tema principale", key="book_theme", height=100)
        book_audience = st.text_input("Pubblico target", key="book_audience")
    
    with col2:
        book_style = st.selectbox(
            "Stile di scrittura",
            ["Informativo", "Narrativo", "Accademico", "Persuasivo", "Divulgativo"],
            index=0,
            key="book_style"
        )
        book_goals = st.text_area("Scopo/Obiettivi del libro", key="book_goals", height=150)
    
    generate_btn = st.button("Genera struttura del libro")
    
    if generate_btn:
        if not book_title or not book_theme or not book_audience:
            st.error("Per favore, compila almeno il titolo, il tema e il pubblico target")
        else:
            with st.spinner("Generazione della struttura in corso..."):
                prompt = create_structure_prompt(book_title, book_theme, book_audience, book_style, book_goals)
                result = generate_ai_response(prompt)
                
                if result:
                    try:
                        # Estrai il JSON dalla risposta
                        json_str = result
                        if "```json" in result:
                            json_str = result.split("```json")[1].split("```")[0].strip()
                        elif "```" in result:
                            json_str = result.split("```")[1].strip()
                            
                        book_structure = json.loads(json_str)
                        
                        # Aggiungiamo informazioni aggiuntive
                        book_structure["theme"] = book_theme
                        book_structure["audience"] = book_audience
                        book_structure["style"] = book_style
                        book_structure["goals"] = book_goals
                        
                        st.session_state.book_structure = book_structure
                        st.success("Struttura del libro generata con successo!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Errore nell'elaborazione della risposta: {str(e)}")
                        st.write("Risposta ricevuta:")
                        st.write(result)
    
    # Visualizza la struttura se è stata generata
    if st.session_state.book_structure:
        st.markdown('<div class="section-header">Struttura del libro</div>', unsafe_allow_html=True)
        
        book = st.session_state.book_structure
        st.subheader(book["title"])
        
        # Editor per l'introduzione
        st.markdown("#### Introduzione")
        intro_tab1, intro_tab2 = st.tabs(["Visualizza", "Modifica"])
        with intro_tab1:
            st.write(book["introduction"])
        with intro_tab2:
            new_intro = st.text_area("Modifica introduzione", book["introduction"], height=200)
            if st.button("Salva introduzione"):
                st.session_state.book_structure["introduction"] = new_intro
                st.success("Introduzione aggiornata!")
                st.experimental_rerun()
        
        # Funzione per aggiungere un nuovo capitolo
        def add_new_chapter():
            new_number = len(book["chapters"]) + 1
            new_chapter = {
                "number": new_number,
                "title": f"Nuovo capitolo {new_number}",
                "description": "Descrizione del nuovo capitolo..."
            }
            st.session_state.book_structure["chapters"].append(new_chapter)
            st.success(f"Nuovo capitolo aggiunto: {new_chapter['title']}")
            st.experimental_rerun()
        
        # Funzione per riordinare i capitoli
        def reorder_chapters():
            # Aggiorna i numeri dei capitoli in base all'ordine attuale
            for i, chapter in enumerate(st.session_state.book_structure["chapters"]):
                chapter["number"] = i + 1
            st.success("Capitoli riordinati!")
            st.experimental_rerun()
        
        # Editor per i capitoli
        st.markdown("#### Capitoli")
        
        # Aggiungi pulsanti per aggiungere nuovo capitolo e riordinare
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("➕ Aggiungi capitolo"):
                add_new_chapter()
        with col2:
            if st.button("🔄 Riordina capitoli"):
                reorder_chapters()
        
        for i, chapter in enumerate(book["chapters"]):
            with st.expander(f"Capitolo {chapter['number']}: {chapter['title']}"):
                tab1, tab2 = st.tabs(["Visualizza", "Modifica"])
                
                with tab1:
                    st.write(chapter["description"])
                
                with tab2:
                    new_title = st.text_input("Titolo del capitolo", chapter["title"], key=f"title_{chapter['number']}")
                    new_desc = st.text_area("Descrizione", chapter["description"], key=f"desc_{chapter['number']}", height=150)
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if st.button("💾 Salva", key=f"save_{chapter['number']}"):
                            chapter["title"] = new_title
                            chapter["description"] = new_desc
                            st.success(f"Capitolo {chapter['number']} aggiornato!")
                            st.experimental_rerun()
                    
                    with col2:
                        if st.button("🗑️ Elimina", key=f"delete_{chapter['number']}"):
                            st.session_state.book_structure["chapters"].pop(i)
                            st.success(f"Capitolo {chapter['number']} eliminato!")
                            st.experimental_rerun()
                    
                    with col3:
                        move_options = ["Non spostare"]
                        if i > 0:
                            move_options.append("Sposta su")
                        if i < len(book["chapters"]) - 1:
                            move_options.append("Sposta giù")
                        
                        move_action = st.selectbox("Riordina", move_options, key=f"move_{chapter['number']}")
                        if move_action == "Sposta su" and st.button("✅ Conferma", key=f"confirm_up_{chapter['number']}"):
                            st.session_state.book_structure["chapters"][i], st.session_state.book_structure["chapters"][i-1] = st.session_state.book_structure["chapters"][i-1], st.session_state.book_structure["chapters"][i]
                            st.experimental_rerun()
                        elif move_action == "Sposta giù" and st.button("✅ Conferma", key=f"confirm_down_{chapter['number']}"):
                            st.session_state.book_structure["chapters"][i], st.session_state.book_structure["chapters"][i+1] = st.session_state.book_structure["chapters"][i+1], st.session_state.book_structure["chapters"][i]
                            st.experimental_rerun()
                    
                    # Opzione per ricreare il capitolo con AI
                    if st.button("🤖 Rigenera descrizione con AI", key=f"regenerate_{chapter['number']}"):
                        with st.spinner(f"Rigenerazione della descrizione del capitolo {chapter['number']}..."):
                            prompt = f"""
                            Sei un consulente editoriale esperto. Stai aiutando a scrivere una breve descrizione accattivante per
                            il capitolo '{new_title}' di un libro intitolato '{book["title"]}' sul tema '{book["theme"]}' 
                            per un pubblico '{book["audience"]}' in stile '{book["style"]}'.
                            
                            Scrivi solo una descrizione sintetica (3-5 frasi) che spieghi chiaramente di cosa tratterà questo capitolo.
                            La descrizione dovrebbe essere accattivante e informativa, e dovrebbe adattarsi al contesto generale del libro.
                            """
                            result = generate_ai_response(prompt)
                            if result:
                                chapter["description"] = result
                                st.success(f"Descrizione del capitolo {chapter['number']} rigenerata!")
                                st.experimental_rerun()

        # Editor per la conclusione
        st.markdown("#### Conclusione")
        concl_tab1, concl_tab2 = st.tabs(["Visualizza", "Modifica"])
        with concl_tab1:
            st.write(book["conclusion"])
        with concl_tab2:
            new_concl = st.text_area("Modifica conclusione", book["conclusion"], height=200)
            if st.button("Salva conclusione"):
                st.session_state.book_structure["conclusion"] = new_concl
                st.success("Conclusione aggiornata!")
                st.experimental_rerun()
        
        if st.button("Procedi alla generazione dei contenuti"):
            st.session_state.current_step = 'content'
            st.experimental_rerun()

elif st.session_state.current_step == 'content':
    st.markdown('<div class="section-header">Generazione dei contenuti</div>', unsafe_allow_html=True)
    
    if not st.session_state.book_structure:
        st.error("Nessuna struttura del libro trovata. Torna alla schermata precedente.")
    else:
        book = st.session_state.book_structure
        
        # Aggiunta di una panoramica visiva dello stato dei capitoli
        st.markdown("### Panoramica capitoli")
        
        # Layout a griglia per i capitoli
        cols = st.columns(3)
        for i, chapter in enumerate(book["chapters"]):
            chapter_key = f"chapter_{chapter['number']}"
            is_generated = chapter_key in st.session_state.generated_chapters
            
            with cols[i % 3]:
                container = st.container()
                container.markdown(f"**Cap. {chapter['number']}: {chapter['title']}**")
                
                # Indicatore visivo dello stato
                if is_generated:
                    container.markdown("🟢 **Completato**")
                    if st.session_state.current_chapter and st.session_state.current_chapter['number'] == chapter['number']:
                        container.markdown("🔍 **In modifica**")
                else:
                    container.markdown("🔴 **Non generato**")
                
                # Pulsanti per gestire il capitolo
                btn_col1, btn_col2 = container.columns(2)
                with btn_col1:
                    if st.button("✍️ Seleziona", key=f"select_ch_{chapter['number']}"):
                        st.session_state.current_chapter = chapter
                        st.experimental_rerun()
                with btn_col2:
                    if is_generated and st.button("👁️ Anteprima", key=f"preview_ch_{chapter['number']}"):
                        st.session_state.current_chapter = chapter
                        st.session_state.show_preview = True
                        st.experimental_rerun()
        
        st.markdown("---")
        
        # Area di lavoro del capitolo corrente
        if not st.session_state.current_chapter:
            st.session_state.current_chapter = book["chapters"][0]
        
        selected_chapter = st.session_state.current_chapter
        st.markdown(f"## Capitolo {selected_chapter['number']}: {selected_chapter['title']}")
        
        # Tabs per generazione e modifica
        gen_tab, edit_tab, style_tab = st.tabs(["Generazione", "Modifica", "Stile"])
        
        chapter_key = f"chapter_{selected_chapter['number']}"
        
        # Tab di generazione
        with gen_tab:
            st.markdown("#### Descrizione del capitolo")
            st.write(selected_chapter['description'])
            
            # Input per la generazione
            col1, col2 = st.columns([2, 1])
            
            with col1:
                key_points = st.text_area(
                    "Punti chiave da includere",
                    help="Inserisci punti chiave o dettagli specifici che vuoi includere nel capitolo",
                    height=150
                )
            
            with col2:
                length = st.select_slider(
                    "Lunghezza approssimativa",
                    options=["Breve", "Media", "Lunga"],
                    value="Media"
                )
                
                tone = st.selectbox(
                    "Tono del capitolo",
                    ["Informale", "Neutro", "Formale", "Accademico", "Conversazionale", "Motivazionale"],
                    index=1
                )
                
                examples = st.multiselect(
                    "Includi esempi di",
                    ["Casi di studio", "Aneddoti", "Statistiche", "Citazioni", "Esercizi pratici"]
                )
            
            # Miglioramento del prompt per la generazione con più opzioni
            def create_advanced_chapter_prompt(book_info, chapter_info, key_points, length, tone, examples):
                # Mappatura delle lunghezze a conteggi parole approssimativi
                length_map = {
                    "Breve": "800-1200 parole",
                    "Media": "1500-2500 parole",
                    "Lunga": "3000-4000 parole"
                }
                
                # Costruisci la stringa degli esempi richiesti
                examples_str = ""
                if examples:
                    examples_str = "Assicurati di includere i seguenti elementi:\n"
                    for example in examples:
                        examples_str += f"- {example}\n"
                
                prompt = f"""
                Sei un autore di libri non-fiction esperto. Stai scrivendo un capitolo per il seguente libro:

                - Titolo del libro: {book_info['title']}
                - Tema principale: {book_info['theme']}
                - Pubblico target: {book_info['audience']}
                - Stile di scrittura: {book_info['style']}

                CAPITOLO DA SCRIVERE:
                - Numero: {chapter_info['number']}
                - Titolo: {chapter_info['title']}
                - Descrizione: {chapter_info['description']}
                
                Punti chiave da includere:
                {key_points if key_points else "Utilizza la tua creatività basandoti sulla descrizione del capitolo."}
                
                Specifiche per il capitolo:
                - Lunghezza: {length_map[length]}
                - Tono: {tone}
                {examples_str}
                
                Scrivi un capitolo completo, ben strutturato e coinvolgente con titoli e sottotitoli. 
                Includi un'introduzione che presenti gli argomenti del capitolo e una conclusione 
                che riassuma i punti chiave. Utilizza un linguaggio chiaro e adatto al pubblico target.
                
                Formatta il capitolo in Markdown con # per i titoli principali e ## per i sottotitoli.
                """
                return prompt
            
            # Pulsante per generare o rigenerare
            gen_button_text = "Rigenera capitolo" if chapter_key in st.session_state.generated_chapters else "Genera capitolo"
            
            if st.button(gen_button_text, type="primary"):
                with st.spinner(f"Generazione del capitolo {selected_chapter['number']} in corso..."):
                    book_info = {
                        "title": book["title"],
                        "theme": book["theme"],
                        "audience": book["audience"],
                        "style": book["style"]
                    }
                    
                    prompt = create_advanced_chapter_prompt(book_info, selected_chapter, key_points, length, tone, examples)
                    result = generate_ai_response(prompt)
                    
                    if result:
                        st.session_state.generated_chapters[chapter_key] = {
                            "number": selected_chapter['number'],
                            "title": selected_chapter['title'],
                            "content": result,
                            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "metadata": {
                                "length": length,
                                "tone": tone,
                                "key_points": key_points,
                                "examples": examples
                            }
                        }
                        st.success(f"Capitolo {selected_chapter['number']} generato con successo!")
                        st.session_state.show_preview = True
                        st.experimental_rerun()
        
        # Tab di modifica
        with edit_tab:
            if chapter_key in st.session_state.generated_chapters:
                chapter_content = st.session_state.generated_chapters[chapter_key]["content"]
                
                # Editor per il contenuto del capitolo
                new_content = st.text_area(
                    "Modifica il contenuto del capitolo",
                    value=chapter_content,
                    height=600
                )
                
                if st.button("Salva modifiche", key="save_edit_content"):
                    st.session_state.generated_chapters[chapter_key]["content"] = new_content
                    st.session_state.generated_chapters[chapter_key]["last_edited"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success("Modifiche salvate con successo!")
                
                # Opzioni di modifica avanzata
                with st.expander("Opzioni avanzate"):
                    edit_option = st.selectbox(
                        "Scegli un'operazione",
                        ["Migliora la leggibilità", "Aggiungi esempi pratici", "Espandi una sezione", "Riassumi e condensa"]
                    )
                    
                    section = st.text_input("Specifica la sezione (opzionale)", 
                                           placeholder="Es. 'Introduzione' o lascia vuoto per tutto il capitolo")
                    
                    if st.button("Applica modifica AI"):
                        with st.spinner("Applicazione della modifica in corso..."):
                            # Creazione del prompt in base all'opzione selezionata
                            if edit_option == "Migliora la leggibilità":
                                edit_prompt = f"""
                                Migliora la leggibilità e la chiarezza di questo testo, mantenendo tutte le informazioni 
                                ma rendendo il linguaggio più scorrevole e accessibile:
                                
                                {new_content if not section else f"Concentrati su questa sezione: {section}"}
                                """
                            elif edit_option == "Aggiungi esempi pratici":
                                edit_prompt = f"""
                                Aggiungi esempi pratici, casi di studio o scenari realistici a questo testo per renderlo 
                                più concreto e applicabile:
                                
                                {new_content if not section else f"Concentrati su questa sezione: {section}"}
                                """
                            elif edit_option == "Espandi una sezione":
                                edit_prompt = f"""
                                Espandi e approfondisci questa sezione con maggiori dettagli, spiegazioni o contesto:
                                
                                {new_content if not section else f"Sezione da espandere: {section}"}
                                """
                            else:  # Riassumi e condensa
                                edit_prompt = f"""
                                Riassumi e condensa questo testo mantenendo tutti i punti chiave ma riducendo la verbosità:
                                
                                {new_content if not section else f"Concentrati su questa sezione: {section}"}
                                """
                            
                            result = generate_ai_response(edit_prompt)
                            
                            if result:
                                # Se è specificata una sezione, sostituisci solo quella parte
                                if section and section in new_content:
                                    modified_content = new_content.replace(section, result)
                                else:
                                    modified_content = result
                                
                                st.session_state.generated_chapters[chapter_key]["content"] = modified_content
                                st.session_state.generated_chapters[chapter_key]["last_edited"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                st.success("Modifica AI applicata con successo!")
                                st.experimental_rerun()
            else:
                st.info("Genera prima il contenuto del capitolo per poterlo modificare.")
        
        # Tab di stile
        with style_tab:
            if chapter_key in st.session_state.generated_chapters:
                st.write("Modifica lo stile e il formato del capitolo")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    style_option = st.selectbox(
                        "Stile di scrittura",
                        ["Attuale", "Più formale", "Più informale", "Più tecnico", "Più divulgativo", "Più narrativo", "Più conciso"]
                    )
                
                with col2:
                    format_option = st.selectbox(
                        "Formato struttura",
                        ["Attuale", "Più sottotitoli", "Più paragrafi", "Più elenchi puntati", "Più tabelle", "Format accademico"]
                    )
                
                if st.button("Applica stile", type="primary"):
                    with st.spinner("Applicazione del nuovo stile..."):
                        content = st.session_state.generated_chapters[chapter_key]["content"]
                        
                        style_prompt = f"""
                        Riformatta il seguente capitolo modificandone lo stile e il formato come indicato:
                        
                        Stile di scrittura: {style_option}
                        Formato struttura: {format_option}
                        
                        Mantieni tutte le informazioni e il contenuto originale, ma adatta la presentazione e il tono 
                        secondo le specifiche richieste. Assicurati che il risultato sia ben formattato in Markdown.
                        
                        Contenuto originale:
                        
                        {content}
                        """
                        
                        result = generate_ai_response(style_prompt)
                        
                        if result:
                            st.session_state.generated_chapters[chapter_key]["content"] = result
                            st.session_state.generated_chapters[chapter_key]["last_edited"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            st.success("Stile applicato con successo!")
                            st.experimental_rerun()
            else:
                st.info("Genera prima il contenuto del capitolo per poterlo modificare.")
        
        # Mostra l'anteprima se richiesto
        if 'show_preview' in st.session_state and st.session_state.show_preview and chapter_key in st.session_state.generated_chapters:
            st.markdown("---")
            st.markdown("### Anteprima del contenuto generato")
            
            preview_tabs = st.tabs(["Visualizzazione", "Markdown"])
            
            with preview_tabs[0]:
                st.markdown(st.session_state.generated_chapters[chapter_key]["content"])
                
                # Metadati del capitolo
                with st.expander("Informazioni sul capitolo"):
                    metadata = st.session_state.generated_chapters[chapter_key].get("metadata", {})
                    gen_time = st.session_state.generated_chapters[chapter_key]["generated_at"]
                    edit_time = st.session_state.generated_chapters[chapter_key].get("last_edited", "Mai")
                    
                    st.write(f"**Generato il:** {gen_time}")
                    st.write(f"**Ultima modifica:** {edit_time}")
                    
                    if metadata:
                        st.write(f"**Lunghezza:** {metadata.get('length', 'Non specificata')}")
                        st.write(f"**Tono:** {metadata.get('tone', 'Non specificato')}")
                    
                    # Calcolo statistiche del testo
                    content = st.session_state.generated_chapters[chapter_key]["content"]
                    words = len(content.split())
                    paragraphs = len([p for p in content.split("\n\n") if p.strip()])
                    
                    st.write(f"**Parole:** {words}")
                    st.write(f"**Paragrafi:** {paragraphs}")
            
            with preview_tabs[1]:
                st.code(st.session_state.generated_chapters[chapter_key]["content"], language="markdown")
            
            # Pulsante per chiudere l'anteprima
            if st.button("Chiudi anteprima"):
                st.session_state.show_preview = False
                st.experimental_rerun()
        
        # Pulsante per procedere all'esportazione
        st.markdown("---")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.session_state.generated_chapters:
                if st.button("Procedi all'esportazione", type="primary"):
                    st.session_state.current_step = 'export'
                    st.experimental_rerun()
            
        with col2:
            # Mostra progresso complessivo
            generated_count = len(st.session_state.generated_chapters)
            total_chapters = len(book["chapters"])
            progress = generated_count / total_chapters
            
            st.progress(progress)
            st.write(f"**Progresso:** {generated_count}/{total_chapters} capitoli completati ({int(progress*100)}%)")


elif st.session_state.current_step == 'export':
    st.markdown('<div class="section-header">Esporta il tuo libro</div>', unsafe_allow_html=True)
    
    if not st.session_state.book_structure or not st.session_state.generated_chapters:
        st.error("Nessun libro completo da esportare. Genera prima i contenuti.")
    else:
        book = st.session_state.book_structure
        
        # Controllo completezza
        total_chapters = len(book["chapters"])
        generated_chapters = len(st.session_state.generated_chapters)
        
        # Visualizzazione stato di completamento
        progress_percentage = int((generated_chapters / total_chapters) * 100)
        
        st.markdown(f"""
        <div class="progress-container">
            <h3>Stato del libro</h3>
            <p>Hai completato {generated_chapters} capitoli su {total_chapters} ({progress_percentage}%)</p>
        </div>
        """, unsafe_allow_html=True)
        
        if generated_chapters < total_chapters:
            missing_chapters = []
            for chapter in book["chapters"]:
                chapter_key = f"chapter_{chapter['number']}"
                if chapter_key not in st.session_state.generated_chapters:
                    missing_chapters.append(f"Capitolo {chapter['number']}: {chapter['title']}")
            
            st.warning("⚠️ Alcuni capitoli non sono ancora stati generati:")
            for missing in missing_chapters:
                st.markdown(f"- {missing}")
            
            st.markdown("Puoi procedere comunque all'esportazione, o tornare alla sezione dei contenuti per completare i capitoli mancanti.")
        
        # Creazione e organizzazione del libro completo
        st.markdown("### Anteprima del libro")
        
        # Preparazione metadati
        now = datetime.now().strftime("%Y-%m-%d")
        book_metadata = f"""---
title: "{book['title']}"
author: "Generato con BookCreator AI"
date: "{now}"
theme: "{book['theme']}"
audience: "{book['audience']}"
---

"""
        
        # Composizione del libro
        full_book = book_metadata + f"# {book['title']}\n\n"
        
        # Aggiunta tabella dei contenuti
        toc = "## Indice\n\n"
        toc += "- [Introduzione](#introduzione)\n"
        for chapter in book["chapters"]:
            chapter_slug = chapter['title'].lower().replace(' ', '-').replace('.', '').replace(',', '')
            toc += f"- [Capitolo {chapter['number']}: {chapter['title']}](#{chapter_slug})\n"
        toc += "- [Conclusione](#conclusione)\n\n"
        
        full_book += toc
        
        # Aggiungi l'introduzione
        full_book += "## Introduzione\n\n"
        full_book += f"{book['introduction']}\n\n"
        
        # Aggiungi i capitoli generati
        for chapter in book["chapters"]:
            chapter_key = f"chapter_{chapter['number']}"
            full_book += f"## Capitolo {chapter['number']}: {chapter['title']}\n\n"
            
            if chapter_key in st.session_state.generated_chapters:
                # Normalizza i livelli di intestazione per adattarsi alla struttura del documento
                chapter_content = st.session_state.generated_chapters[chapter_key]['content']
                # Converti intestazioni # in ###, ## in ####, ecc.
                chapter_content = chapter_content.replace('\n# ', '\n### ')
                chapter_content = chapter_content.replace('\n## ', '\n#### ')
                chapter_content = chapter_content.replace('\n### ', '\n##### ')
                
                full_book += f"{chapter_content}\n\n"
            else:
                full_book += "*Contenuto non ancora generato*\n\n"
        
        # Aggiungi la conclusione
        full_book += "## Conclusione\n\n"
        full_book += f"{book['conclusion']}\n\n"
        
        # Visualizzazione anteprima
        with st.expander("📖 Visualizza anteprima del libro", expanded=False):
            st.markdown(full_book)
        
        # Opzioni di esportazione
        st.markdown("### Esporta il libro")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Scarica libro in formato Markdown",
                data=full_book,
                file_name=f"{book['title'].replace(' ', '_')}.md",
                mime="text/markdown",
                help="Formato Markdown compatibile con la maggior parte degli editor di testo"
            )
        
        # Opzione per copiare negli appunti
        with col2:
            if st.button("📋 Copia negli appunti", help="Copia il contenuto del libro negli appunti per incollarlo altrove"):
                st.code(full_book, language="markdown")
                st.success("Il contenuto è stato formattato sopra. Selezionalo e copialo per incollarlo dove preferisci.")
        
        # Area per personalizzare l'esportazione
        st.markdown("### Personalizza l'esportazione")
        
        # Opzioni di personalizzazione
        include_options = st.multiselect(
            "Includi sezioni",
            ["Metadata", "Indice", "Introduzione", "Conclusione"],
            default=["Metadata", "Indice", "Introduzione", "Conclusione"],
            help="Seleziona quali sezioni includere nel documento esportato"
        )
        
        # Salvataggio del progetto
        st.markdown("### Salva il tuo progetto")
        
        if st.button("💾 Salva progetto", help="Salva il progetto per continuare in seguito"):
            # Creazione dell'oggetto progetto
            project_data = {
                "book_structure": st.session_state.book_structure,
                "generated_chapters": st.session_state.generated_chapters,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0"
            }
            
            # Converti in JSON
            project_json = json.dumps(project_data, indent=2)
            
            # Offri il download
            st.download_button(
                label="📥 Scarica file del progetto",
                data=project_json,
                file_name=f"BookCreator_{book['title'].replace(' ', '_')}.json",
                mime="application/json"
            )
            
            st.success("Progetto pronto per il download. Clicca sul pulsante qui sopra per scaricarlo.")
        
        # Caricamento progetto
        with st.expander("Carica progetto esistente"):
            uploaded_file = st.file_uploader("Seleziona un file di progetto .json", type=["json"])
            
            if uploaded_file is not None:
                try:
                    project_data = json.load(uploaded_file)
                    if st.button("Carica questo progetto"):
                        st.session_state.book_structure = project_data.get("book_structure")
                        st.session_state.generated_chapters = project_data.get("generated_chapters")
                        st.success("Progetto caricato con successo!")
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Errore nel caricamento del file: {str(e)}")
        
        # Statistiche del libro
        with st.expander("📊 Statistiche del libro"):
            # Calcola statistiche
            total_words = 0
            chapter_stats = []
            
            # Conta parole introduzione e conclusione
            intro_words = len(book['introduction'].split())
            conclusion_words = len(book['conclusion'].split())
            total_words += intro_words + conclusion_words
            
            # Conta parole nei capitoli
            for chapter in book["chapters"]:
                chapter_key = f"chapter_{chapter['number']}"
                if chapter_key in st.session_state.generated_chapters:
                    chapter_content = st.session_state.generated_chapters[chapter_key]['content']
                    word_count = len(chapter_content.split())
                    total_words += word_count
                    
                    chapter_stats.append({
                        "number": chapter['number'],
                        "title": chapter['title'],
                        "words": word_count,
                        "generated": True
                    })
                else:
                    chapter_stats.append({
                        "number": chapter['number'],
                        "title": chapter['title'],
                        "words": 0,
                        "generated": False
                    })
            
            # Visualizza statistiche
            st.write(f"**Parole totali**: {total_words}")
            st.write(f"**Capitoli**: {total_chapters}")
            st.write(f"**Introduzione**: {intro_words} parole")
            st.write(f"**Conclusione**: {conclusion_words} parole")
            
            # Tabella dei capitoli
            st.markdown("#### Statistiche per capitolo")
            
            chapter_data = []
            for cs in chapter_stats:
                status = "✅ Completato" if cs["generated"] else "❌ Non generato"
                chapter_data.append([
                    f"Cap. {cs['number']}",
                    cs['title'],
                    cs['words'],
                    status
                ])
            
            st.table(
                {"Numero": [c[0] for c in chapter_data],
                 "Titolo": [c[1] for c in chapter_data],
                 "Parole": [c[2] for c in chapter_data],
                 "Stato": [c[3] for c in chapter_data]}
            )
