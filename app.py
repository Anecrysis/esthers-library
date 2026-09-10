import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Esther's Library", page_icon="📚", layout="wide")

# 2. Estilos CSS personalizados (Fondo de Gatos y Mariposas)
def apply_custom_styles():
    st.markdown("""
    <style>
    /* 1. Fondo base morado */
    .stApp {
        background-color: #6a4c93;
        background-attachment: fixed;
    }

    /* 2. Capa de Gatos (Siluetas repetidas) */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        /* Este código dibuja una silueta de gato sutil en patrón */
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 100 100'%3E%3Ctext y='50' font-size='40' opacity='0.15'%3E🐱%3C/text%3E%3C/svg%3E");
        background-repeat: repeat;
        pointer-events: none;
        z-index: 0;
    }

    /* 3. Asegurar que el contenido esté por encima de los gatos */
    .stApp > div {
        position: relative;
        z-index: 1;
    }

    .main-title {
        color: #ffffff;
        text-align: center;
        font-family: 'Georgia', serif;
        text-shadow: 2px 2px 4px #000000;
        padding: 20px;
        background: rgba(106, 76, 147, 0.8);
        border-radius: 15px;
        position: relative;
        z-index: 2;
    }

    .book-card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 8px solid #ffb7c5;
        color: #2d3436;
        position: relative;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
        z-index: 2;
    }
    
    /* Decoración extra en las tarjetas */
    .book-card::after { content: '🐱'; position: absolute; bottom: 10px; right: 15px; font-size: 20px; opacity: 0.5; }
    .book-card::before { content: '🦋'; position: absolute; top: 10px; right: 15px; font-size: 20px; opacity: 0.5; }
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

# Función auxiliar para procesar imágenes a base64
def process_image(image_file):
    if image_file:
        img = Image.open(image_file)
        img.thumbnail((300, 300))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=40)
        return base64.b64encode(buf.getvalue()).decode()
    return ""

# 4. Interfaz Principal
def main():
    st.markdown('<h1 class="main-title">🦋 Esther\'s Library 🦋</h1>', unsafe_allow_html=True)
    
    menu = ["Mi Biblioteca", "Agregar Libro", "Buscar", "Estadísticas", "Gestionar"]
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
                cover = st.selectbox("Tapa", ["Dura", "Blanda", "eBook"])
                origin = st.selectbox("Origen", ["Comprado", "Regalado", "Prestado"])
                start_date = st.date_input("Inicio")
                end_date = st.date_input("Fin")
            notes = st.text_area("Notas", max_chars=240)
            rating = st.select_slider("Rating", options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"])
            
            uploaded_photo = st.file_uploader("Cargar imagen desde la fototeca", type=["png", "jpg", "jpeg"])
            camera_photo = st.camera_input("O tomar foto con la cámara")
            
            submit = st.form_submit_button("Guardar")
            
            if submit and title:
                photo_source = uploaded_photo if uploaded_photo is not None else camera_photo
                photo_str = process_image(photo_source)
                
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

    elif choice == "Estadísticas":
        st.markdown("### 📊 Mis Logros de Lectura")
        if not df.empty:
            df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
            df_stats = df.dropna(subset=['end_date'])
            
            df_stats['Año'] = df_stats['end_date'].dt.year
            df_stats['Mes_Num'] = df_stats['end_date'].dt.month
            
            años_disponibles = sorted(df_stats['Año'].unique().astype(int), reverse=True)
            año_sel = st.selectbox("Selecciona el año para revisar", años_disponibles)
            
            df_year = df_stats[df_stats['Año'] == año_sel]
            
            meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            lecturas_por_mes = df_year.groupby('Mes_Num').size().reindex(range(1, 13), fill_value=0)
            lecturas_df = pd.DataFrame({'Mes': meses_nombres, 'Libros': lecturas_por_mes.values})
            
            mes_actual = datetime.now().month
            libros_mes_actual = lecturas_por_mes[mes_actual] if año_sel == datetime.now().year else 0
            
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Total del año", f"{len(df_year)} libros")
            col_m2.metric("Leídos este mes", f"{libros_mes_actual} libros")
            
            st.bar_chart(lecturas_df.set_index('Mes'), color="#ffb7c5")
            
            if len(df_year) > 0:
                st.write(f"✨ En {año_sel}, tu mes más lector fue **{meses_nombres[lecturas_por_mes.argmax()]}**.")
        else:
            st.info("Aún no hay suficientes datos para generar estadísticas. ¡Sigue leyendo!")

    elif choice == "Buscar":
        st.markdown("### 🔍 Buscador")
        query = st.text_input("Buscar título o autor")
        if query:
            res = df[df['title'].astype(str).str.contains(query, case=False) | df['author'].astype(str).str.contains(query, case=False)]
            st.table(res[['title', 'author', 'rating']])

    elif choice == "Gestionar":
        st.markdown("### ⚙️ Administrar Biblioteca")
        if not df.empty:
            tab_eliminar, tab_editar = st.tabs(["🗑️ Eliminar Libro", "✏️ Editar Libro"])
            
            with tab_eliminar:
                for index, row in df.iterrows():
                    col_txt, col_btn = st.columns([4, 1])
                    with col_txt: st.write(f"**{row['title']}** - {row['author']}")
                    with col_btn:
                        if st.button("Eliminar", key=f"del_{index}"):
                            new_df = df.drop(index)
                            conn.update(worksheet="Libros", data=new_df)
                            st.rerun()

            with tab_editar:
                opciones_libros = {f"{row['title']} ({row.get('author', 'Sin autor')})": idx for idx, row in df.iterrows()}
                libro_sel_nombre = st.selectbox("Selecciona el libro a modificar", list(opciones_libros.keys()))
                
                if libro_sel_nombre:
                    idx = opciones_libros[libro_sel_nombre]
                    libro = df.loc[idx]
                    
                    with st.form("form_editar_libro"):
                        st.markdown(f"#### Editando: *{libro['title']}*")
                        col1, col2 = st.columns(2)
                        with col1:
                            new_title = st.text_input("Título", value=str(libro['title']))
                            new_author = st.text_input("Autor", value=str(libro.get('author', '')))
                            
                            genres = ["Novela", "Fantasía", "Romance", "Misterio", "Historia", "Poesía", "Otro"]
                            current_genre = str(libro.get('genre', 'Novela'))
                            genre_idx = genres.index(current_genre) if current_genre in genres else 0
                            new_genre = st.selectbox("Género", genres, index=genre_idx)
                            
                            try: default_pages = int(libro.get('pages', 1))
                            except: default_pages = 1
                            new_pages = st.number_input("Páginas", min_value=1, step=1, value=default_pages)
                        
                        with col2:
                            covers = ["Dura", "Blanda", "eBook"]
                            current_cover = str(libro.get('cover_type', 'Dura'))
                            cover_idx = covers.index(current_cover) if current_cover in covers else 0
                            new_cover = st.selectbox("Tapa", covers, index=cover_idx)
                            
                            origins = ["Comprado", "Regalado", "Prestado"]
                            current_origin = str(libro.get('origin', 'Comprado'))
                            origin_idx = origins.index(current_origin) if current_origin in origins else 0
                            new_origin = st.selectbox("Origen", origins, index=origin_idx)
                            
                            def parse_date(d_str):
                                try: return datetime.strptime(str(d_str), "%Y-%m-%d").date()
                                except: return datetime.now().date()
                                
                            new_start_date = st.date_input("Inicio", value=parse_date(libro.get('start_date')))
                            new_end_date = st.date_input("Fin", value=parse_date(libro.get('end_date')))

                        new_notes = st.text_area("Notas", value=str(libro.get('notes', '')), max_chars=240)
                        
                        ratings = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]
                        current_rating = str(libro.get('rating', '⭐'))
                        rating_idx = ratings.index(current_rating) if current_rating in ratings else 0
                        new_rating = st.select_slider("Rating", options=ratings, value=ratings[rating_idx])
                        
                        # Mostrar la imagen actual si la hay
                        current_photo = libro.get('photo', '')
                        if current_photo and str(current_photo) != "nan" and str(current_photo).strip() != "":
                            st.write("Imagen actual:")
                            try: st.image(base64.b64decode(str(current_photo)), width=150)
                            except: pass
                        else:
                            st.info("Este libro no tiene imagen asignada.")

                        edit_uploaded_photo = st.file_uploader("Actualizar/Añadir foto desde la fototeca", type=["png", "jpg", "jpeg"], key="edit_up")
                        edit_camera_photo = st.camera_input("Actualizar/Añadir foto desde la cámara", key="edit_cam")
                        
                        submit_edit = st.form_submit_button("Guardar Cambios")

                        if submit_edit:
                            photo_source = edit_uploaded_photo if edit_uploaded_photo is not None else edit_camera_photo
                            if photo_source is not None:
                                final_photo_str = process_image(photo_source)
                            else:
                                final_photo_str = str(libro.get('photo', ''))

                            df.at[idx, 'title'] = new_title
                            df.at[idx, 'author'] = new_author
                            df.at[idx, 'genre'] = new_genre
                            df.at[idx, 'pages'] = new_pages
                            df.at[idx, 'cover_type'] = new_cover
                            df.at[idx, 'origin'] = new_origin
                            df.at[idx, 'start_date'] = str(new_start_date)
                            df.at[idx, 'end_date'] = str(new_end_date)
                            df.at[idx, 'notes'] = new_notes
                            df.at[idx, 'rating'] = new_rating
                            df.at[idx, 'photo'] = final_photo_str

                            conn.update(worksheet="Libros", data=df)
                            st.success("¡Libro actualizado correctamente!")
                            st.rerun()

if __name__ == "__main__":
    main()
