import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de la página
st.set_page_config(
    page_title="Esther's Library",
    page_icon="📚",
    layout="wide"
)

# 2. Estilos CSS personalizados (Gatos, Mariposas y fondo morado)
def apply_custom_styles():
    st.markdown("""
    <style>
    .stApp {
        background-color: #6a4c93; /* Morado principal */
        background-image: url("https://www.transparenttextures.com/patterns/cubes.png");
    }
    .main-title {
        color: #ffffff;
        text-align: center;
        font-family: 'Georgia', serif;
        text-shadow: 2px 2px 4px #000000;
        padding: 20px;
        background: rgba(106, 76, 147, 0.8);
        border-radius: 15px;
    }
    .book-card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 8px solid #ffb7c5; /* Rosa mariposa */
        color: #2d3436;
        position: relative;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
    }
    .book-card::after {
        content: '🐱';
        position: absolute;
        bottom: 10px;
        right: 15px;
        font-size: 20px;
    }
    .book-card::before {
        content: '🦋';
        position: absolute;
        top: 10px;
        right: 15px;
        font-size: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# 3. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

def load_data():
    try:
        # Intenta leer la hoja "Libros"
        return conn.read(worksheet="Libros", ttl="0")
    except Exception:
        # Si falla o no existe, devuelve un DataFrame vacío con las columnas correctas
        return pd.DataFrame(columns=[
            "id", "title", "author", "genre", "pages", "start_date", 
            "end_date", "cover_type", "origin", "publisher", "notes", "rating", "photo"
        ])

# 4. Interfaz Principal
def main():
    st.markdown('<h1 class="main-title">🦋 Esther\'s Library 🦋</h1>', unsafe_allow_html=True)
    
    # Menú lateral
    menu = ["Mi Biblioteca", "Agregar Libro", "Buscar"]
    choice = st.sidebar.selectbox("Menú de Navegación", menu)
    
    # Cargar datos actuales
    df = load_data()

    if choice == "Agregar Libro":
        st.markdown("### ✨ Registrar nuevo tesoro")
        with st.form("form_libro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Título del libro (Obligatorio) *")
                author = st.text_input("Autor")
                genre = st.selectbox("Género", ["Novela", "Fantasía", "Romance", "Misterio", "Historia", "Poesía", "Otro"])
                pages = st.number_input("Número de páginas", min_value=1, step=1)
            with col2:
                cover = st.selectbox("Tipo de Tapa", ["Dura", "Blanda"])
                origin = st.selectbox("¿Cómo llegó a ti?", ["Comprado", "Regalado"])
                start_date = st.date_input("Fecha de inicio")
                end_date = st.date_input("Fecha de fin")
            notes = st.text_area("Observaciones (máx. 240 car.)", max_chars=240)
            rating = st.select_slider("Calificación", options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"])
            camera_photo = st.camera_input("Captura la portada")
            
            submit = st.form_submit_button("Guardar en la Biblioteca")
            
            if submit:
                if title:
                    photo_str = ""
                    # Procesar foto con compresión fuerte para Google Sheets
                    photo_str = ""
                    if camera_photo:
                        img = Image.open(camera_photo)
                        
                        # 1. Redimensionar la imagen para que sea pequeña (max 300px)
                        img.thumbnail((300, 300)) 
                        
                        # 2. Guardar con compresión JPEG alta
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=40) # Calidad al 40% para ahorrar espacio
                        
                        # 3. Convertir a texto
                        photo_str = base64.b64encode(buf.getvalue()).decode()
                        
                        # Verificación de seguridad: si aún así es muy larga, avisar
                        if len(photo_str) > 49000:
                            st.warning("La foto es demasiado compleja, se guardará sin imagen para evitar errores.")
                            photo_str = ""
                    
                    new_book_data = {
                        "id": len(df) + 1,
                        "title": str(title),
                        "author": str(author),
                        "genre": str(genre),
                        "pages": int(pages),
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "cover_type": str(cover),
                        "origin": str(origin),
                        "publisher": "",
                        "notes": str(notes),
                        "rating": str(rating),
                        "photo": str(photo_str)
                    }
                    
                    try:
                        updated_df = pd.concat([df, pd.DataFrame([new_book_data])], ignore_index=True)
                        conn.update(worksheet="Libros", data=updated_df)
                        st.success(f"¡'{title}' guardado! 🌸")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
                else:
                    st.error("Por favor, introduce al menos el título.")
    elif choice == "Buscar":
        st.markdown("### 🔍 Buscador")
        search_term = st.text_input("Busca por título o autor")
        
        if search_term:
            # Convertimos las columnas a string y manejamos valores vacíos (NaN) con fillna
            # Esto evita el error "Can only use .str accessor with string values!"
            mask = (
                df['title'].astype(str).str.contains(search_term, case=False, na=False) | 
                df['author'].astype(str).str.contains(search_term, case=False, na=False)
            )
            results = df[mask]
            
            if not results.empty:
                st.write(f"Se encontraron {len(results)} resultados:")
                # Mostramos solo las columnas interesantes para que no sea un lío
                st.table(results[['title', 'author', 'genre', 'rating']])
            else:
                st.warning("No hay coincidencias para esa búsqueda.")

if __name__ == "__main__":
    main()








