import streamlit as st
import pandas as pd

# Configuración para pantalla completa
st.set_page_config(layout="wide")

# Verificar si ya se mostró la nieve
if "nieve" not in st.session_state:
    st.session_state.nieve = False

# Mostrar copos de nieve solo al inicio
if not st.session_state.nieve:
        st.snow()
        st.session_state.nieve = True

# Función para validar texto
def validar_texto(texto):
    if any(char.isdigit() for char in texto):
        st.error("Este campo no puede contener números. Por favor, ingresa solo letras.")
        return ""
    return texto    

# Función para validar si los datos están completos, de la misma forma se maneja el disabled del botón
def datos_completos(costos, ofertas, demandas):
    # Revisar que no haya valores nulos o vacíos en la tabla de costos
    if costos.isnull().values.any() or ofertas.isnull().values.any() or (ofertas["Oferta"] <= 0).any() or demandas.isnull().values.any() or (demandas.loc["Demanda"] <= 0).any():
        return False
    return True

# Lógica para navegar entre páginas
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"  # Página inicial por defecto

# Página inicial
if st.session_state.pagina == "inicio":
    
    st.title("Problema de Transporte: Método Demaxmin")
    col1, espacio1, col2, espacio2, col3 = st.columns([1, 0.2, 1.5, 0.2, 2])

    with col1:
        st.header("Paso 1: Configuración")
        nombre_origenes = st.text_input("Ingresa el nombre de tus orígenes (por ejemplo: Fábrica):", "Fábrica")
        origenes = validar_texto(nombre_origenes)
        
        nombre_destinos = st.text_input("Ingresa el nombre de tus destinos (por ejemplo: Ciudad):", "Ciudad")
        destinos = validar_texto(nombre_destinos)

        num_suministros = st.number_input("¿Cuántos orígenes hay?", min_value=0, step=1, max_value=15)
        num_destinos = st.number_input("¿Cuántos destinos hay?", min_value=0, step=1, max_value=15)
        
        #st.subheader("Generar Datos Automáticamente")
        #st.button("Generar")
               
    # Paso 2: Llenado de datos
    with col2:
        if num_suministros > 0 and num_destinos > 0:
            st.header("Paso 2: Llenado de Datos")
            st.subheader("Tabla de Costos")
            
            default_costos = [[0 for _ in range(num_destinos)] for _ in range(num_suministros)]
            costos = st.data_editor(
                pd.DataFrame(
                    default_costos,
                    columns=[f"{destinos} {i+1}" for i in range(num_destinos)],
                    index=[f"{origenes} {i+1}" for i in range(num_suministros)],
                ),
                use_container_width=True,
            )
            
            st.subheader("Ofertas")
            default_ofertas = [0 for _ in range(num_suministros)]
            ofertas = st.data_editor(
                pd.DataFrame(
                    default_ofertas,
                    index=[f"{origenes} {i+1}" for i in range(num_suministros)],
                    columns=["Oferta"],
                ),
                use_container_width=True,
            )
            
            st.subheader("Demandas")
            default_demandas = [0 for _ in range(num_destinos)]
            demandas = st.data_editor(
                pd.DataFrame(
                    [default_demandas],
                    columns=[f"{destinos} {i+1}" for i in range(num_destinos)],
                    index=["Demanda"],
                ),
                use_container_width=True,
            )

    # Paso 3: Tabla Balanceada
    with col3:
        if num_suministros > 0 and num_destinos > 0:
            st.header("Paso 3: Tabla Balanceada")

            # Validación de datos
            if (ofertas["Oferta"] < 0).any() or (demandas.loc["Demanda"] < 0).any() or (costos < 0).any().any():
                st.error("Por favor, ingresa solo valores positivos")
                st.stop()

            # Agrega ofertas a el DF de costos
            costos["Oferta"] = ofertas["Oferta"]
            
            # Agrega demandas con 0 en cruce para el balanceo
            fila_demandas = list(demandas.loc["Demanda"]) + [0]
            costos.loc["Demanda"] = fila_demandas

            # Sumas de oferta y demanda
            suma_oferta = ofertas["Oferta"].sum()
            suma_demanda = demandas.loc["Demanda"].sum()

            # Balancear oferta y demanda
            if suma_oferta != suma_demanda:
                diferencia = abs(suma_oferta - suma_demanda)
                if suma_oferta > suma_demanda:
                    # Añadir columna ficticia (demanda extra)
                    costos[f"{destinos} F"] = [0] * num_suministros + [diferencia]
                    demandas.loc["Demanda", f"{destinos} F"] = diferencia
                else:
                    # Añadir fila ficticia (oferta extra)
                    costos.loc[f"{origenes} F"] = [0] * num_destinos + [diferencia]
                    ofertas.loc[f"{origenes} F", "Oferta"] = diferencia

                # Con esto nos aseguramos de que la oferta y la demanda se muestren siempre al final
                if "Oferta" in costos.columns:
                    costos = costos[[col for col in costos.columns if col != "Oferta"] + ["Oferta"]]
                if "Demanda" in costos.index:
                    costos = costos.loc[[idx for idx in costos.index if idx != "Demanda"] + ["Demanda"]]

            # Con esto nos aseguramos de mostrar la suma de oferta y demanda ya con los ficticios
            costos.loc["Demanda", "Oferta"] = suma_oferta if suma_oferta == suma_demanda else max(suma_oferta, suma_demanda)

            st.dataframe(costos, use_container_width=True)

            # Validar si el botón "Resolver" debe estar habilitado
            boton_habilitado = datos_completos(costos, ofertas, demandas)

            # Botón para resolver (habilitado solo si los datos están completos)
            if st.button("Resolver", disabled=not boton_habilitado):
                # Guardar en el estado de la sesión
                st.session_state.costos = costos # Guardamos los costos
                st.session_state.ofertas = ofertas # Guardamos las ofertas
                st.session_state.demandas = demandas # Guardamos los demandas
                st.session_state.destinos = destinos  # Guardamos los destinos
                st.session_state.origenes = origenes  # Guardamos los orígenes
                st.session_state.pagina = "Resolver"
                st.rerun()  # Recarga la página
    
# Página de resolución
elif st.session_state.pagina == "Resolver":
    st.title("Resolución del Problema de Transporte")
    col1, espacio, col2 = st.columns([1.5, 0.2, 1.5])

    with col1:
        st.subheader("Tabla de Costos")
        costos = st.session_state.costos
        ofertas = st.session_state.ofertas
        demandas = st.session_state.demandas
        destinos = st.session_state.destinos
        origenes = st.session_state.origenes
        
        st.dataframe(costos, use_container_width=True)
        st.success("¡Resolviendo el problema!")

    with col2:
    # Resolver la tabla
        st.subheader("Resolviendo la Tabla")

        # Hacer una copia de las tablas para trabajar
        costos, ofertas, demandas = st.session_state.costos.copy(), st.session_state.ofertas.copy(), st.session_state.demandas.copy()

        operaciones = []

        # Mientras haya ofertas o demandas que no sean cero
        while ofertas["Oferta"].sum() > 0 and demandas.loc["Demanda"].sum() > 0:
            # Filtrar las filas y columnas donde las ofertas o demandas son 0
            ofertas_filtradas = ofertas[ofertas["Oferta"] > 0]
            demandas_filtradas = demandas.loc[:, demandas.loc["Demanda"] > 0]

            # Filtrar costos mayores a 0
            costos_filtrados = costos.copy()
            costos_filtrados[costos_filtrados == 0] = float('inf')  # Ignorar ceros estableciendo un costo muy alto

            # Escoger la demanda más grande disponible
            demanda_mayor = demandas_filtradas.loc["Demanda"].idxmax()  # Nombre de la columna con mayor demanda
            destino = demanda_mayor

            # Escoger el costo más bajo en esa columna con oferta disponible
            costo_minimo = costos_filtrados[destino].loc[ofertas_filtradas.index].idxmin()  # Fila con menor costo

            # Obtener valores de oferta y demanda
            oferta_actual = ofertas.loc[costo_minimo, "Oferta"]
            demanda_actual = demandas.loc["Demanda", destino]

            # Asignar según las reglas
            if demanda_actual > oferta_actual:
                # Si la demanda es mayor que la oferta, asignamos toda la oferta y restamos de la demanda
                asignacion = int(oferta_actual)
                demandas.loc["Demanda", destino] -= asignacion
                ofertas.loc[costo_minimo, "Oferta"] = 0
            elif oferta_actual > demanda_actual:
                # Si la oferta es mayor que la demanda, asignamos toda la demanda y restamos de la oferta
                asignacion = int(demanda_actual)
                ofertas.loc[costo_minimo, "Oferta"] -= asignacion
                demandas.loc["Demanda", destino] = 0
            else:
                # Si oferta y demanda son iguales, asignamos toda la oferta (o demanda) y ambos se convierten en 0
                asignacion = int(oferta_actual)
                ofertas.loc[costo_minimo, "Oferta"] = 0
                demandas.loc["Demanda", destino] = 0

            # Actualizar directamente la tabla de costos con el valor de la asignación
            costo_actual = costos.loc[costo_minimo, destino]  # Obtener el costo actual
            costos.loc[costo_minimo, destino] = f"{int(costo_actual)}({asignacion})"  # Agregar costo y asignación entre paréntesis

            # Crear la tabla balanceada final, combinando las tres tablas: ofertas, demandas y costos
            tabla_final = pd.DataFrame(index=costos.index[:-1], columns=costos.columns[:-1])

            # Asignar los valores de ofertas, demandas y costos actualizados
            for costo_minimo in costos.index[:-1]:
                for destino in costos.columns[:-1]:
                    # Asignar el costo actualizado (con la asignación)
                    costo_actualizado = costos.loc[costo_minimo, destino]
                    tabla_final.loc[costo_minimo, destino] = costo_actualizado

            # Agregar la fila de ofertas y la columna de demandas
            tabla_final["Oferta"] = ofertas["Oferta"]
            tabla_final.loc["Demanda"] = demandas.loc["Demanda"]

            # Mostrar la tabla final
            st.dataframe(tabla_final, use_container_width=True)

        # Procesar los costos que son 0 al final
        for destino in demandas.columns[:-1]:
            for origen in ofertas.index[:-1]:
                if costos.loc[origen, destino] == 0:
                    # Revisar si todavía hay oferta y demanda en esa celda
                    oferta_actual = ofertas.loc[origen, "Oferta"]
                    demanda_actual = demandas.loc["Demanda", destino]

                    if oferta_actual > 0 and demanda_actual > 0:
                        asignacion = min(oferta_actual, demanda_actual)
                        ofertas.loc[origen, "Oferta"] -= asignacion
                        demandas.loc["Demanda", destino] -= asignacion

                        # Actualizar directamente la tabla de costos con la asignación
                        costos.loc[origen, destino] = f"0({asignacion})"

        # Calcular y mostrar el costo total Z al final
        total_costo = 0
        for costo_minimo in costos.index[:-1]:
            for destino in costos.columns[:-1]:
                costo_valor = costos.loc[costo_minimo, destino]

                if '(' in str(costo_valor):
                    try:
                        # Si tiene paréntesis, hacemos la multiplicación
                        costo_num, asignacion = costo_valor.split('(')
                        asignacion = asignacion.rstrip(')')  # Limpiar el paréntesis de la asignación

                        # Asegurarse de que los valores no sean vacíos
                        if costo_num.strip() and asignacion.strip():
                            costo_num = int(float(costo_num.strip()))  # Convertir a entero
                            asignacion = int(float(asignacion.strip()))  # Convertir a entero

                            operaciones.append(f"{costo_num}({asignacion})")
                            total_costo += costo_num * asignacion
                    except (ValueError, TypeError) as error:
                        # Mostrar error detallado de la excepción
                        st.error(f"Error al convertir los valores: costo_num='{costo_num}' asignacion='{asignacion}'. Excepción: {error}")
                        
        # Mostrar la expresión de Z
        st.write("Z = " + " + ".join(operaciones))

        # Mostrar solo el resultado final Z
        st.write(f"Z = {int(total_costo)}")
            
        if st.button("Regresar"):
            st.session_state.pagina = "inicio"
            st.rerun()

        st.subheader("Autores")
        with st.expander("Autores"):
            st.write("Jeizer Oswaldo Guzmán Chablé")
            st.write("Jothan Kaleb Gopar Toledo")
            st.write("Fernado de Jesus Sánchez Villanueva")
            st.write("Rodrigo González López")