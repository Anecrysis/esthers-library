import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64


# Page Config
st.set_page_config(
    page_title="Esther's Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Apply Custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Helper function to convert image to base64
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def main():
    st.markdown('<h1 class="main-title">🦋 Esther\'s Library 🦋</h1>', unsafe_allow_html=True)

    # Sidebar Navigation
    menu = ["Mi Biblioteca", "Agregar Libro", "Buscar & Filtrar"]
    choice = st.sidebar.selectbox("Menú", menu)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🌸 Estadísticas")
    books_df = get_books()
    st.sidebar.info(f"Total de libros: {len(books_df)}")

    if choice == "Mi Biblioteca":
        st.markdown("## 📖 Colección Actual")
        
        # Display books in a grid
        books = get_books()
        if not books.empty:
            cols = st.columns(3)
            for index, row in books.iterrows():
                with cols[index % 3]:
                    with st.container():
                        st.markdown(f"""
                        <div class="book-card">
                            <div class="icon-cat">🐱</div>
                            <div class="icon-butterfly">🦋</div>
                            <div class="book-title">{row['title']}</div>
                            <div class="book-meta">👤 {row['author']}</div>
                            <div class="book-meta">📚 {row['genre']} | {row['pages']} págs</div>
                            <div class="book-meta">⭐ {get_star_rating_html(row['rating'])}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display Image if available
                        if row['photo']:
                            try:
                                # Start of Base64 check (if it's not base64, might be a URL or path, but we expect base64)
                                image_bytes = base64.b64decode(row['photo'])
                                st.image(image_bytes, use_container_width=True)
                            except:
                                # If it fails, maybe it is empty or invalid
                                pass

                        # Expandable details
                        with st.expander("Ver detalles"):
                            st.write(f"**Editorial:** {row['publisher']}")
                            st.write(f"**Origen:** {row['origin']}")
                            st.write(f"**Tapa:** {row['cover_type']}")
                            st.write(f"**Fechas:** {row['start_date']} - {row['end_date']}")
                            st.write(f"**Notas:** {row['notes']}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Borrar", key=f"del_{row['id']}"):
                                    delete_book(row['id'])
                                    st.rerun()
                            with col2:
                                # Edit placeholder
                                pass 

        else:
            st.info("Tu biblioteca está vacía. ¡Agrega algunos libros!")

    elif choice == "Agregar Libro":
        st.markdown("## ✨ Agregar Nuevo Libro")
        
        with st.form("add_book_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Título *")
                author = st.text_input("Autor")
                genre = st.selectbox("Género", ["Ficción", "No Ficción", "Fantasía", "Ciencia Ficción", "Misterio", "Romance", "Biografía", "Historia", "Otro"])
                pages = st.number_input("Páginas", min_value=1)
                publisher = st.text_input("Editorial")
                origin = st.selectbox("Origen", ["Comprado", "Regalado", "Prestado", "Biblioteca"])

            with col2:
                cover_type = st.select_slider("Tipo de Tapa", options=["Blanda", "Dura"])
                start_date = st.date_input("Fecha Inicio")
                end_date = st.date_input("Fecha Fin")
                rating = st.slider("Calificación", 1, 5, 3)
                
            notes = st.text_area("Observaciones", max_chars=240)
            
            # Photo Input
            photo_source = st.radio("Foto del libro", ["Subir archivo", "Tomar foto"])
            photo_data = ""
            
            if photo_source == "Subir archivo":
                uploaded_file = st.file_uploader("Elige una imagen", type=['jpg', 'png', 'jpeg'])
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    photo_data = image_to_base64(image)
            else:
                camera_input = st.camera_input("Tomar foto")
                if camera_input:
                    image = Image.open(camera_input)
                    photo_data = image_to_base64(image)

            submitted = st.form_submit_button("Guardar en la Biblioteca")
            
            if submitted:
                if title:
                    book_data = {
                        "title": title,
                        "author": author,
                        "genre": genre,
                        "pages": pages,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "cover_type": cover_type,
                        "origin": origin,
                        "publisher": publisher,
                        "notes": notes,
                        "rating": rating,
                        "photo": photo_data
                    }
                    success, msg = add_book(book_data)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("El título es obligatorio.")

    elif choice == "Buscar & Filtrar":
        st.markdown("## 🔍 Buscar en la Biblioteca")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            filter_by = st.selectbox("Filtrar por", ["Mostrar Todo", "Título", "Autor", "Género"])
        with col2:
            if filter_by != "Mostrar Todo":
                filter_value = st.text_input(f"Escribe el {filter_by}")
            else:
                filter_value = None
                
        if st.button("Buscar") or filter_by == "Mostrar Todo":
            results = get_books(filter_by, filter_value)
            
            if not results.empty:
                for index, row in results.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="book-card" style="display: flex; align-items: center; justify-content: space-between;">
                            <div>
                                <div class="book-title">{row['title']}</div>
                                <div class="book-meta">{row['author']} | {row['genre']}</div>
                            </div>
                            <div>
                                {get_star_rating_html(row['rating'])}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("No se encontraron libros.")

if __name__ == "__main__":

    main()

