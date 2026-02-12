import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de la página
st.set_page_config(page_title="Esther's Library", page_icon="📚", layout="wide")

# 2. Estilos CSS
def apply_custom_styles():
    st.markdown("""
    <style>
    .stApp { background-color: #6a4c93; background-image: url("https://www.transparenttextures.com/patterns/cubes.png"); }
    .main-title { color: #ffffff; text-align: center; font-family: 'Georgia', serif; text-shadow: 2px 2px 4px #000000; padding: 20px; background: rgba(106, 76, 147, 0.8); border-radius: 15px; }
    .book-card { background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; margin-bottom: 20px; border-left: 8px solid #ffb7c5; color: #2d3436; position: relative; box-shadow: 5px 5px 15px rgba(0,0,0,0.3); }
    .book-card::after { content: '🐱'; position: absolute; bottom: 10px; right: 15px; font-size: 20px; }
    .book-card::before { content: '🦋'; position: absolute; top: 10px; right: 15px; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# 3. Conexión
conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

def load_data():
    try:
        df = conn.read(worksheet="Libros", ttl="0")
        return df.dropna(subset=['title'])
    except:
        return pd.DataFrame(columns=["id", "title", "author", "genre", "pages", "start_date", "end_date", "cover_type", "origin", "publisher", "notes", "rating", "photo"])

# 4. Interfaz Principal
def main():
    st.markdown('<h1 class="main-title">🦋 Esther\'s Library 🦋</h1>', unsafe_allow_html=True)
    
    menu = ["Mi Biblioteca", "Agregar Libro", "Buscar", "Gestionar"]
    choice = st.sidebar.selectbox("Menú de Navegación", menu)
    
    df = load_data()

    if choice == "Mi Biblioteca":
        st.markdown("### 📖 Mi Colección")
        if not df.empty:
            for _, row in df.iterrows():
                with st.container():
                    st.markdown(f"""<div class="book-card">
                        <h2 style='margin:0;'>{row['title']}</h2>
                        <p><b>Autor:</b> {row.get('author', '-')} | <b>Género:</b> {row.get('genre', '-')} </p>
                        <p><b>Calificación:</b> {row.get('rating', '⭐')}</p>
                        <p style='font-style: italic;'>"{row.get('notes', '')}"</p>
                        <hr><p style='font-size: 0.8em;'>Tapa {row.get('cover_type', '-')} | {row.get('pages', 0)} págs</p>
                    </div>""", unsafe_allow_html=True)
                    photo = row.get('photo', '')
                    if photo and str(photo) != "nan" and str(photo).strip() != "":
                        try: st.image(base64.b64decode(str(photo)), width=250)
                        except: pass
        else:
            st.info("Biblioteca vacía.")

    elif choice == "Agregar Libro":
        st.markdown("### ✨ Registrar nuevo tesoro")
        with st.form("form_libro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Título *")
                author = st.text_input("Autor")
                genre = st.selectbox("Género", ["Novela", "Fantasía", "Romance", "Misterio", "Historia", "Poesía", "Otro"])
                pages = st.number_input("Páginas", min_value=1, step=1)
            with col2:
                cover = st.selectbox("Tapa", ["Dura", "Blanda"])
                origin = st.selectbox("Origen", ["Comprado", "Regalado"])
                start_date = st.date_input("Inicio")
                end_date = st.date_input("Fin")
            notes = st.text_area("Notas", max_chars=240)
            rating = st.select_slider("Rating", options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"])
            camera_photo = st.camera_input("Foto")
            submit = st.form_submit_button("Guardar")
            
            if submit and title:
                photo_str = ""
                if camera_photo:
                    img = Image.open(camera_photo)
                    img.thumbnail((300, 300))
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=40)
                    photo_str = base64.b64encode(buf.getvalue()).decode()
                
                new_row = pd.DataFrame([{
                    "id": len(df) + 1, "title": title, "author": author, "genre": genre, 
                    "pages": pages, "start_date": str(start_date), "end_date": str(end_date),
                    "cover_type": cover, "origin": origin, "publisher": "", "notes": notes, 
                    "rating": rating, "photo": photo_str
                }])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Libros", data=updated_df)
                st.success("¡Guardado!")
                st.rerun()

    elif choice == "Buscar":
        st.markdown("### 🔍 Buscador")
        query = st.text_input("Buscar título o autor")
        if query:
            res = df[df['title'].astype(str).str.contains(query, case=False) | df['author'].astype(str).str.contains(query, case=False)]
            st.table(res[['title', 'author', 'rating']])

    elif choice == "Gestionar":
        st.markdown("### ⚙️ Administrar Biblioteca")
        st.write("Aquí puedes eliminar libros de la base de datos.")
        
        if not df.empty:
            for index, row in df.iterrows():
                col_txt, col_btn = st.columns([4, 1])
                with col_txt:
                    st.write(f"**{row['title']}** - {row['author']}")
                with col_btn:
                    if st.button("Eliminar", key=f"del_{index}"):
                        # Borrar la fila y actualizar
                        new_df = df.drop(index)
                        conn.update(worksheet="Libros", data=new_df)
                        st.warning(f"Libro '{row['title']}' eliminado.")
                        st.rerun()
        else:
            st.info("No hay libros para gestionar.")

if __name__ == "__main__":
    main()
