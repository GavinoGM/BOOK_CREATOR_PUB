import streamlit as st
import requests
import json
import os
from datetime import datetime
from openai import OpenAI
from anthropic import Anthropic

# Initialize AI clients
def init_openai_client():
    """Initialize OpenAI client using environment secret"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def init_anthropic_client():
    """Initialize Anthropic client using environment secret"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    return Anthropic(api_key=api_key)

# Page configuration
st.set_page_config(
    page_title="BookCreator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'config'
if 'book_structure' not in st.session_state:
    st.session_state.book_structure = None
if 'current_chapter' not in st.session_state:
    st.session_state.current_chapter = None
if 'generated_chapters' not in st.session_state:
    st.session_state.generated_chapters = {}
if 'ai_provider' not in st.session_state:
    st.session_state.ai_provider = 'OpenAI'
if 'ai_model' not in st.session_state:
    st.session_state.ai_model = {
        'OpenAI': 'gpt-4o',
        'Anthropic': 'claude-3-5-sonnet-20241022'
    }
# Add new session state variables for book details
if 'book_details' not in st.session_state:
    st.session_state.book_details = {
        'title': '',
        'theme': '',
        'audience': '',
        'style': 'Informative',
        'goals': ''
    }
# Add new session state variable for book content
if 'book_content' not in st.session_state:
    st.session_state.book_content = {}

# AI API Functions
def call_anthropic_api(prompt):
    """Call Anthropic (Claude) API"""
    try:
        client = init_anthropic_client()
        if not client:
            raise ValueError("Anthropic API key not found in environment")

        # Usa il modello selezionato dall'utente
        response = client.messages.create(
            model=st.session_state.ai_model['Anthropic'],
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        st.error(f"Error calling Anthropic API: {str(e)}")
        return None

def call_openai_api(prompt):
    """Call OpenAI (GPT) API"""
    try:
        client = init_openai_client()
        if not client:
            raise ValueError("OpenAI API key not found in environment")

        # Usa il modello selezionato dall'utente
        response = client.chat.completions.create(
            model=st.session_state.ai_model['OpenAI'],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error calling OpenAI API: {str(e)}")
        return None

def generate_ai_response(prompt):
    """Generate response from selected AI provider"""
    if st.session_state.ai_provider == "Anthropic":
        return call_anthropic_api(prompt)
    else:
        return call_openai_api(prompt)

# Prompt Generation Functions
def create_structure_prompt(title, theme, audience, style, goals):
    return f"""
    As an expert editorial consultant, help me create a detailed structure for a non-fiction book with these characteristics:

    - Title: {title}
    - Main Theme: {theme}
    - Target Audience: {audience}
    - Writing Style: {style}
    - Book Goals: {goals}

    Please generate a complete structure including:
    1. A compelling introduction presenting the theme and book objectives
    2. 6-10 logically organized chapters, each with an engaging title and brief content description (3-5 sentences)
    3. A conclusion summarizing key points and leaving readers with meaningful reflections

    Format the response in JSON as follows:
    {{
        "title": "Book Title",
        "introduction": "Introduction text...",
        "chapters": [
            {{
                "number": 1,
                "title": "Chapter 1 Title",
                "description": "Chapter description..."
            }},
            ...
        ],
        "conclusion": "Conclusion text..."
    }}
    """

def create_chapter_prompt(book_info, chapter_info, key_points, length, custom_content=None):
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
    """

    if custom_content:
        prompt += f"""

    Contenuto personalizzato da incorporare nel capitolo:
    {custom_content}

    Per favore, integra organicamente questo contenuto personalizzato nel capitolo, mantenendo uno stile coerente e fluido.
    """

    prompt += f"""

    Lunghezza approssimativa: {length}

    Scrivi un capitolo completo, ben strutturato e coinvolgente. Includi esempi concreti, riferimenti pertinenti e, dove appropriato, aneddoti per illustrare i concetti. Assicurati che il capitolo mantenga uno stile coerente con il resto del libro e si colleghi logicamente ai capitoli precedenti e successivi.

    Formatta il contenuto con titoli chiari usando la sintassi Markdown (##) per le sezioni principali e (###) per le sottosezioni.
    """
    return prompt

# Navigation Functions
def go_to_structure():
    st.session_state.current_step = 'structure'

def go_to_content():
    st.session_state.current_step = 'content'

def go_to_export():
    st.session_state.current_step = 'export'

def go_back():
    steps = {
        'structure': 'config',
        'content': 'structure',
        'export': 'content'
    }
    st.session_state.current_step = steps.get(st.session_state.current_step, 'config')

def add_new_chapter():
    """Add a new chapter to the book structure"""
    if st.session_state.book_structure:
        next_number = len(st.session_state.book_structure["chapters"]) + 1
        new_chapter = {
            "number": next_number,
            "title": f"New Chapter {next_number}",
            "description": "Description of the new chapter..."
        }
        st.session_state.book_structure["chapters"].append(new_chapter)
        st.rerun()

def reorder_chapters():
    """Reorder chapters and update their numbers"""
    if st.session_state.book_structure:
        # Update chapter numbers based on their current position
        for i, chapter in enumerate(st.session_state.book_structure["chapters"], 1):
            chapter["number"] = i
        st.success("Chapters reordered successfully!")
        st.rerun()

# Add the utility function after the other utility functions and before the main application
def update_chapter_info(chapter_number, title=None, description=None):
    """Update chapter information in both Book Structure and Content Generation"""
    # Update in Book Structure
    for chapter in st.session_state.book_structure["chapters"]:
        if chapter["number"] == chapter_number:
            if title:
                chapter["title"] = title
            if description:
                chapter["description"] = description
            break

    # Update in generated chapters if exists
    chapter_key = f"chapter_{chapter_number}"
    if chapter_key in st.session_state.generated_chapters:
        if title:
            st.session_state.generated_chapters[chapter_key]["title"] = title
        if description:
            st.session_state.generated_chapters[chapter_key]["description"] = description


# Main Application
st.title("📚 BookCreator")

# Sidebar Navigation
with st.sidebar:
    st.header("Navigation")

    if st.button("1. Configuration", disabled=st.session_state.current_step == 'config'):
        st.session_state.current_step = 'config'

    structure_disabled = st.session_state.current_step == 'config'
    if st.button("2. Book Structure", disabled=structure_disabled):
        st.session_state.current_step = 'structure'

    content_disabled = st.session_state.current_step in ['config', 'structure'] or not st.session_state.book_structure
    if st.button("3. Content Generation", disabled=content_disabled):
        st.session_state.current_step = 'content'

    export_disabled = st.session_state.current_step in ['config', 'structure'] or not st.session_state.book_content #Corrected line
    if st.button("4. Export Book", disabled=export_disabled):
        st.session_state.current_step = 'export'

# Configuration Screen
if st.session_state.current_step == 'config':
    st.header("Configuration")

    # Check API keys status
    openai_key = os.environ.get('OPENAI_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

    st.info("API keys are now stored securely in the application's environment.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### OpenAI API Status")
        if openai_key:
            st.success("✅ OpenAI API key is configured")
        else:
            st.error("❌ OpenAI API key is missing")

    with col2:
        st.markdown("#### Anthropic API Status")
        if anthropic_key:
            st.success("✅ Anthropic API key is configured")
        else:
            st.error("❌ Anthropic API key is missing")

    # Provider selection
    provider = st.selectbox(
        "Select AI Provider",
        ["OpenAI", "Anthropic"],
        index=0 if st.session_state.ai_provider == "OpenAI" else 1
    )

    # Model selection based on provider
    if provider == "OpenAI":
        model = st.selectbox(
            "Select OpenAI Model",
            ["gpt-4o", "gpt-4-turbo-preview", "gpt-4"],
            index=0 if st.session_state.ai_model['OpenAI'] == "gpt-4o" else (1 if st.session_state.ai_model['OpenAI'] == "gpt-4-turbo-preview" else 2),
            help="gpt-4o is the latest and most capable model"
        )
    else:
        model = st.selectbox(
            "Select Anthropic Model",
            ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229"],
            index=0 if st.session_state.ai_model['Anthropic'] == "claude-3-5-sonnet-20241022" else (1 if st.session_state.ai_model['Anthropic'] == "claude-3-opus-20240229" else 2),
            help="claude-3-5-sonnet-20241022 is the latest model"
        )

    if st.button("Save Configuration"):
        # Verify selected provider has its API key
        selected_key = openai_key if provider == "OpenAI" else anthropic_key
        if not selected_key:
            st.error(f"Cannot use {provider}: API key not configured")
        else:
            st.session_state.ai_provider = provider
            st.session_state.ai_model[provider] = model
            st.success(f"Configuration saved! Using {provider} ({model}) for text generation.")
            st.session_state.current_step = 'structure'
            st.rerun()

# Structure Screen
elif st.session_state.current_step == 'structure':
    st.header("Define Your Book Structure")

    # Add "New Book" button at the top
    if st.button("📖 Start New Book"):
        # Reset all book-related state
        st.session_state.book_structure = None
        st.session_state.current_chapter = None
        st.session_state.generated_chapters = {}
        st.session_state.book_details = {
            'title': '',
            'theme': '',
            'audience': '',
            'style': 'Informative',
            'goals': ''
        }
        st.session_state.book_content = {} # Reset book content as well
        st.success("Ready to start a new book!")
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        book_title = st.text_input("Book Title", value=st.session_state.book_details['title'])
        book_theme = st.text_area("Main Theme", value=st.session_state.book_details['theme'], height=100)
        book_audience = st.text_input("Target Audience", value=st.session_state.book_details['audience'])

    with col2:
        book_style = st.selectbox(
            "Writing Style",
            ["Informative", "Narrative", "Academic", "Persuasive", "Educational"],
            index=["Informative", "Narrative", "Academic", "Persuasive", "Educational"].index(st.session_state.book_details['style'])
        )
        book_goals = st.text_area("Book Goals", value=st.session_state.book_details['goals'], height=150)

    generate_btn = st.button("Generate Structure")
    if generate_btn:
        if not all([book_title, book_theme, book_audience]):
            st.error("Please fill in at least the title, theme, and target audience")
        else:
            # Save current values to session state
            st.session_state.book_details.update({
                'title': book_title,
                'theme': book_theme,
                'audience': book_audience,
                'style': book_style,
                'goals': book_goals
            })

            with st.spinner("Generating book structure..."):
                prompt = create_structure_prompt(book_title, book_theme, book_audience, book_style, book_goals)
                result = generate_ai_response(prompt)

                if result:
                    try:
                        # Extract JSON from response
                        json_str = result
                        if "```json" in result:
                            json_str = result.split("```json")[1].split("```")[0].strip()
                        elif "```" in result:
                            json_str = result.split("```")[1].strip()

                        book_structure = json.loads(json_str)

                        # Add additional information
                        book_structure["theme"] = book_theme
                        book_structure["audience"] = book_audience
                        book_structure["style"] = book_style
                        book_structure["goals"] = book_goals

                        st.session_state.book_structure = book_structure
                        st.success("Book structure generated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing the response: {str(e)}")
                        st.write("Received response:", result)

    if st.session_state.book_structure:
        st.header("Book Structure")
        book = st.session_state.book_structure

        st.subheader(book["title"])
        st.text_area("Introduction", book["introduction"], height=200)

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
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Elimina", key=f"delete_{chapter['number']}"):
                            st.session_state.book_structure["chapters"].pop(i)
                            st.success(f"Capitolo {chapter['number']} eliminato!")
                            st.rerun()

                    with col3:
                        move_options = ["Non spostare"]
                        if i > 0:
                            move_options.append("Sposta su")
                        if i < len(book["chapters"]) - 1:
                            move_options.append("Sposta giù")

                        move_action = st.selectbox("Riordina", move_options, key=f"move_{chapter['number']}")
                        if move_action == "Sposta su" and st.button("✅ Conferma", key=f"confirm_up_{chapter['number']}"):
                            st.session_state.book_structure["chapters"][i], st.session_state.book_structure["chapters"][i-1] = st.session_state.book_structure["chapters"][i-1], st.session_state.book_structure["chapters"][i]
                            st.rerun()
                        elif move_action == "Sposta giù" and st.button("✅ Conferma", key=f"confirm_down_{chapter['number']}"):
                            st.session_state.book_structure["chapters"][i], st.session_state.book_structure["chapters"][i+1] = st.session_state.book_structure["chapters"][i+1], st.session_state.book_structure["chapters"][i]
                            st.rerun()

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
                                st.rerun()

        st.text_area("Conclusion", book["conclusion"], height=200)

        if st.button("Proceed to Content Generation"):
            st.session_state.current_step = 'content'
            st.rerun()

# Content Generation Screen
elif st.session_state.current_step == 'content':
    st.header("Generate Content")

    if not st.session_state.book_structure:
        st.error("No book structure found. Please go back and create one.")
    else:
        book = st.session_state.book_structure

        # Chapter selection with improved UI
        st.markdown("### Select a Chapter to Generate")

        # Display chapters as cards
        chapters = book["chapters"]
        for chapter in chapters:
            chapter_key = f"chapter_{chapter['number']}"
            is_generated = chapter_key in st.session_state.generated_chapters

            # Create a card-like container for each chapter
            with st.container():
                st.markdown(f"""
                <div style="padding: 1rem; margin: 0.5rem 0; border: 1px solid #e0e0e0; border-radius: 5px; background: {'#f8f9fa' if not is_generated else '#e8f5e9'}">
                    <h4>Chapter {chapter['number']}: {chapter['title']}</h4>
                </div>
                """, unsafe_allow_html=True)

                # Display chapter information
                st.markdown("#### Chapter Details")
                chapter_title = st.text_input(
                    "Edit chapter title",
                    value=chapter["title"],
                    key=f"title_{chapter['number']}",
                    help="You can modify the chapter title before generation"
                )
                chapter_description = st.text_area(
                    "Edit description before generation",
                    value=chapter["description"],
                    key=f"description_{chapter['number']}",
                    help="You can modify the chapter description before generating the content"
                )

                # Add save button for chapter details
                if st.button("💾 Save Chapter Details", key=f"save_details_{chapter['number']}"):
                    update_chapter_info(
                        chapter['number'],
                        title=chapter_title,
                        description=chapter_description
                    )
                    st.success("Chapter details updated successfully!")
                    st.rerun()

                # Add regenerate description button
                if st.button("🤖 Regenerate Description", key=f"regen_desc_{chapter['number']}"):
                    with st.spinner("Regenerating chapter description..."):
                        prompt = f"""
                        You are an expert editorial consultant. Help write an engaging description for
                        the chapter '{chapter_title}' of a book titled '{book["title"]}' on the theme '{book["theme"]}' 
                        for an audience of '{book["audience"]}' in {book["style"]} style.

                        Write a concise description (3-5 sentences) that clearly explains what this chapter will cover.
                        The description should be engaging and informative, fitting the book's overall context.
                        """
                        result = generate_ai_response(prompt)
                        if result:
                            update_chapter_info(
                                chapter['number'],
                                description=result
                            )
                            st.success("Chapter description regenerated!")
                            st.rerun()


                col1, col2 = st.columns([3, 1])

                with col1:
                    # Generation options
                    if not is_generated:
                        key_points = st.text_area(
                            "Key Points",
                            help="Enter specific points you want to include in this chapter",
                            key=f"key_points_{chapter['number']}"
                        )

                        # Add custom content field
                        custom_content = st.text_area(
                            "Custom Content (Optional)",
                            help="Add any specific text, data, or information you want to include in this chapter",
                            key=f"custom_content_{chapter['number']}"
                        )

                        # Replace select_slider with a numeric slider for word count
                        word_count = st.slider(
                            "Chapter Length (words)",
                            min_value=500,
                            max_value=7000,
                            value=2000,
                            step=100,
                            key=f"length_{chapter['number']}",
                            help="Slide to set the approximate number of words for this chapter"
                        )
                        st.caption(f"Selected length: {word_count:,} words")

                with col2:
                    # Generation/View buttons
                    if is_generated:
                        if st.button("📝 Edit", key=f"edit_{chapter['number']}"):
                            st.session_state.current_chapter = chapter
                            st.rerun()
                    else:
                        if st.button("✨ Generate", key=f"generate_{chapter['number']}"):
                            with st.spinner(f"Generating chapter {chapter['number']}..."):
                                # Create a modified chapter info with updated title and description
                                chapter_info = chapter.copy()
                                chapter_info["title"] = chapter_title
                                chapter_info["description"] = chapter_description

                                prompt = create_chapter_prompt(
                                    book,
                                    chapter_info,
                                    st.session_state.get(f"key_points_{chapter['number']}", ""),
                                    f"{word_count} words",  # Pass exact word count to prompt
                                    st.session_state.get(f"custom_content_{chapter['number']}", None)  # Pass custom content
                                )
                                result = generate_ai_response(prompt)

                                if result:
                                    # Aggiorna sia la struttura del libro che i capitoli generati
                                    chapter_info = {
                                        "number": chapter['number'],
                                        "title": chapter_title,
                                        "description": chapter_description
                                    }

                                    # Aggiorna la struttura del libro
                                    update_chapter_info(
                                        chapter['number'],
                                        title=chapter_title,
                                        description=chapter_description
                                    )

                                    # Aggiorna i capitoli generati
                                    st.session_state.generated_chapters[chapter_key] = {
                                        "number": chapter['number'],
                                        "title": chapter_title,
                                        "content": result,
                                        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "metadata": {
                                            "word_count": word_count,
                                            "key_points": st.session_state.get(f"key_points_{chapter['number']}", ""),
                                            "custom_content": st.session_state.get(f"custom_content_{chapter['number']}", None)
                                        }
                                    }
                                    st.success(f"Chapter {chapter['number']} generated successfully!")
                                    st.session_state.current_chapter = chapter_info
                                    st.rerun()

                st.markdown("---")

        # Editor for generated content
        if st.session_state.current_chapter:
            current_chapter = st.session_state.current_chapter
            chapter_key = f"chapter_{current_chapter['number']}"

            if chapter_key in st.session_state.generated_chapters:
                st.header(f"Edit Chapter {current_chapter['number']}: {current_chapter['title']}")

                generated = st.session_state.generated_chapters[chapter_key]
                edited_content = st.text_area(
                    "Edit Content",
                    value=generated["content"],
                    height=400,
                    key=f"edit_content_{current_chapter['number']}"
                )

                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("💾 Save Changes"):
                        generated["content"] = edited_content
                        generated["last_edited"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.success("Changes saved successfully!")
                        st.rerun()
                with col2:
                    if st.button("🔄 Regenerate Chapter"):
                        st.session_state.generated_chapters.pop(chapter_key, None)
                        st.success("Chapter cleared. You can now regenerate it.")
                        st.rerun()
                with col3:
                    if st.button("📋 Copy to final book"):
                        st.session_state.book_content[current_chapter['number']] = {
                            'title': current_chapter['title'],
                            'content': edited_content,
                            'copied_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.success(f"Chapter {current_chapter['number']} copied to final book!")
                        st.rerun()

# Export Screen
elif st.session_state.current_step == 'export':
    st.header("Book")

    # If there are copied chapters, show them in order
    if st.session_state.book_content:
        book = st.session_state.book_structure

        # Show the introduction
        st.markdown("## Introduction")
        st.markdown(book['introduction'])
        st.markdown("---")

        # Sort chapters by number and show them
        sorted_chapters = dict(sorted(st.session_state.book_content.items()))
        for num, chapter in sorted_chapters.items():
            st.markdown(f"## Chapter {num}: {chapter['title']}")
            st.markdown(chapter['content'])
            st.markdown("---")

        # Show the conclusion
        st.markdown("## Conclusion")
        st.markdown(book['conclusion'])

        # Export options
        export_format = st.selectbox("Export Format", ["Markdown", "Plain Text"])

        # Prepare content for export
        export_content = f"# {book['title']}\n\n"
        export_content += "## Introduction\n" + book['introduction'] + "\n\n"

        for num, chapter in sorted_chapters.items():
            export_content += f"## Chapter {num}: {chapter['title']}\n"
            export_content += chapter['content'] + "\n\n"

        export_content += "## Conclusion\n" + book['conclusion']

        if st.download_button(
            "Download Book",
            data=export_content,
            file_name=f"{book['title'].lower().replace(' ', '_')}.{'md' if export_format == 'Markdown' else 'txt'}",
            mime="text/markdown" if export_format == "Markdown" else "text/plain"
        ):
            st.success("Book downloaded successfully!")
    else:
        st.info("No chapters have been copied to the final book yet. Go to Content Generation to copy chapters.")