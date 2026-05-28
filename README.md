# 🌐 SportsScraper: Comparador de Ofertas Deportivas

Descripción: Plataforma de metabúsqueda y comparación de precios en tiempo real para el sector retail textil. El sistema utiliza técnicas avanzadas de Web Scraping para centralizar la oferta de diversas plataformas de e-commerce, permitiendo a los usuarios optimizar sus costos mediante la transparencia de datos.

### 👥 Integrantes

Luisa Fernanda Arenas Pachon – 1202807
Juan Miguel Trujillo Garcia - 1202774
Oscar Javier Fernández Bernal – 1202786

### 🎯 1. Objetivo General

Diseñar y desarrollar un sistema integral de metabúsqueda y comparación de precios para el sector retail textil, basado en técnicas avanzadas de Web Scraping, con el fin de centralizar la oferta de diversas plataformas de e-commerce en una interfaz única que facilite la toma de decisiones informadas mediante la transparencia de datos y la optimización de costos para el usuario.


### 🌍 2. Contexto de Uso

¿Quién va a usar el sistema? Consumidores de moda y ropa deportiva en Colombia que buscan comparar precios de marcas reconocidas sin navegar individualmente en cada tienda.

¿Cómo se va a utilizar el sistema? El usuario ingresa una referencia o categoría en la barra de búsqueda; el sistema consulta los motores de extracción y despliega una cuadrícula comparativa con precios, disponibilidad de tallas y enlaces directos de compra.

### 📋 3. Requerimientos del Sistema

#### 3.1 Requerimientos Funcionales

RF01: Extracción asíncrona de datos (precio, tallas, envío) de sitios como Zalando o Google Shopping.

RF02: Normalización de datos para unificar diferentes formatos de moneda y unidades.

RF03: Algoritmo de Product Matching para agrupar referencias idénticas de distintos proveedores.

RF04: Filtros avanzados por rango de precio, marca y disponibilidad de stock.

#### 3.2 Requerimientos No Funcionales
RNF01: Interfaz Responsive Design adaptada a dispositivos móviles y escritorio.

RNF02: Arquitectura de Single Page Application (SPA) para navegación fluida.

RNF03: Manejo de concurrencia para soportar múltiples peticiones de scraping simultáneas.

RNF04: Cumplimiento de políticas de robots.txt para un scraping ético.

### 🧠 4. Diagramas UML

#### 🔍 CU1: Buscar Prenda
El usuario busca un artículo específico para centralizar y comparar las opciones disponibles en el mercado.

#### 🛤️ Secuencia de Pasos
Entrada: El usuario ingresa un término (ej. "Tenis Running") en la Interfaz de Búsqueda.

Petición: La Interfaz envía la consulta al Controlador de Búsqueda.

Consulta: El Controlador solicita a la Base de Datos los registros que coincidan con el nombre o categoría.

Respuesta: La Base de Datos devuelve una lista de Productos Maestros.

Salida: El Controlador organiza los resultados por relevancia y los entrega a la Interfaz para su visualización final.

graph TD
    A[Inicio] --> B[Ingresar texto de búsqueda]
    B --> C{¿Existen resultados?}
    C -- No --> D[Mostrar mensaje: 'No encontrado']
    D --> E[Sugerir categorías similares]
    C -- Sí --> F[Recuperar miniaturas y rangos de precios]
    F --> G[Mostrar lista de resultados]
    G --> H[Fin]

![Diagrama](img/dig_sec_1.png)
![Diagrama](img/caso_uso_1.png)
![Diagrama](img/dig_base_datos_1.png)

#### 💰 CU2: Comparar Precios
Funcionalidad núcleo: Permite al usuario identificar la oferta más competitiva mediante la centralización de datos de múltiples tiendas.

#### 🛤️ Secuencia de Pasos
Selección: El usuario selecciona un producto específico de la lista de resultados.

Petición: La Interfaz solicita al Gestor de Comparación las ofertas vinculadas.

Consulta: El Gestor filtra la tabla Ofertas mediante el ID_Producto.

Respuesta: La Base de Datos retorna precios, tiendas y enlaces (Zalando, ASOS, etc.).

Procesamiento: El Gestor ordena las ofertas de menor a mayor precio.

Salida: La Interfaz renderiza la tabla comparativa siguiendo el diseño del prototipo de Figma.

graph TD
    A[Inicio] --> B[Cargar ficha de producto]
    B --> C[Consultar ofertas activas]
    C --> D{¿Hay más de una tienda?}
    D -- Sí --> E[Calcular precio mínimo]
    E --> F[Resaltar oferta con Badge: 'Precio más bajo']
    D -- No --> G[Mostrar precio único]
    G --> H[Habilitar opción: 'Avisarme cuando baje']
    F --> I[Fin]
    H --> I

![Diagrama](img/dig_sec_2.png)
![Diagrama](img/caso_uso_2.png)
![Diagrama](img/dig_base_datos_2.png)


#### 🔔 CU3: Configurar Alerta de Precio
El usuario desea ser notificado de manera proactiva cuando el motor de scraping detecte una rebaja por debajo de un umbral específico.

#### 🛤️ Secuencia de Pasos
Interacción: El usuario hace clic en el botón "Seguir precio" dentro de la ficha del producto.

Entrada: La Interfaz solicita al usuario el umbral de precio (precio objetivo) deseado para la notificación.

Registro: El Gestor de Alertas crea una entrada en la tabla Alertas, vinculando el ID_Usuario con el ID_Producto.

Confirmación: El sistema genera un mensaje de éxito y confirma la suscripción al usuario.

graph TD
    A[Inicio] --> B[Seleccionar 'Favorito/Alerta']
    B --> C{¿Usuario logueado?}
    C -- No --> D[Redirigir a Registro/Login]
    D --> B
    C -- Sí --> E[Solicitar umbral de precio]
    E --> F[Guardar parámetro de alerta en BD]
    F --> G[Suscribir ID a cambios de precio]
    G --> H[Mostrar confirmación]
    H --> I[Fin]

![Diagrama](img/dig_sec_3.png)
![Diagrama](img/caso_uso_3.png)
![Diagrama](img/dig_base_datos_3.png)


#### ⚙️ CU4: Ejecutar Extracción (Scraping)
Proceso de backend encargado de la recolección, limpieza y persistencia de datos provenientes de las plataformas de retail externas.

#### 🛤️ Secuencia de Pasos
Disparo: El Planificador de Tareas (Cron Job) inicia el Motor de Scraping en intervalos programados.

Anonimización: El Motor solicita una URL rotativa al Gestor de Proxies para evitar bloqueos por IP.

Renderizado: Un Navegador Headless (como Playwright o Puppeteer) carga la página y extrae el HTML dinámico (DOM).

Parsing: El Parser identifica y extrae selectores específicos para precio, stock y tallas.

Validación: El Validador asegura que los datos sean íntegros (ej. que el precio sea un valor numérico positivo).

Persistencia: El sistema guarda o actualiza la información en la Base de Datos central.

graph TD
    A[Inicio] --> B[Acceder a URL de Tienda]
    B --> C{¿Carga exitosa?}
    C -- No --> D[Solicitar nuevo Proxy]
    D --> B
    C -- Sí --> E[Extraer Nombre, Precio y Talla]
    E --> F[Limpiar y Normalizar Datos]
    F --> G{¿El precio cambió?}
    G -- Sí --> H[Registrar en Historial y Disparar Alertas]
    G -- No --> I[Actualizar Fecha de Verificación]
    H --> J[Fin]
    I --> J

![Diagrama](img/dig_sec_4.png)
![Diagrama](img/caso_uso_4.png)
![Diagrama](img/dig_base_datos_4.png)

#### 🧠 CU5: Mapear Productos (Entity Matching)
Lógica de normalización y agrupación encargada de identificar artículos idénticos provenientes de distintas fuentes para ofrecer una comparativa unificada.

#### 🛤️ Secuencia de Pasos
Recepción: El Normalizador recibe un "Producto Extraído" (dato crudo) del motor de scraping.

Búsqueda: El Normalizador solicita al Motor de Similitud buscar coincidencias potenciales en la Base de Datos.

Análisis: El Motor ejecuta algoritmos de comparación de texto (como Levenstein o Jaro-Winkler) sobre los campos Marca + Modelo.

Vinculación: Si el puntaje de coincidencia (score) es superior al 90%, el sistema vincula la nueva oferta al Producto Maestro ya existente.

Creación: Si no se detectan coincidencias suficientes, se genera un nuevo registro de Producto Maestro en el catálogo.

graph TD
    A[Inicio] --> B[Recibir dato crudo del Scraper]
    B --> C[Comparar Marca + Modelo con BD]
    C --> D{¿Similitud > 90%?}
    D -- Sí --> E[Vincular oferta al ID existente]
    E --> F[Actualizar rango de precios]
    D -- No --> G[Crear nueva categoría de Producto Maestro]
    G --> H[Asignar ID único de visualización]
    F --> I[Fin]
    H --> I

![Diagrama](img/dig_sec_5.png)
![Diagrama](img/caso_uso_5.png)
![Diagrama](img/dig_base_datos_5.png)

### 🎨 5. URL del Prototipo

Se ha diseñado una interfaz moderna y deportiva centrada en la facilidad de navegación.

<p align="center">
  <img src="assets/figma-preview.png" width="600" title="Vista previa del prototipo en Figma">
</p>

[Ver prototipo completo en Figma](https://www.figma.com/design/OlscT9RxvE8jPj4fcqBwKJ/Prototipo-Final?node-id=0-1&t=L0Y4juUF77l6IfoN-1)

### 🗄️ 6. Diseño de Base de Datos

El sistema utiliza una arquitectura de base de datos relacional (RDBMS) diseñada para gestionar la alta volatilidad de precios y permitir la unificación de productos (Entity Matching) desde múltiples fuentes.

<p align="center">
<img src="img/image_816388.png" alt="Modelo Entidad-Relación" width="80%">
</p>

<table align="center">
<tr>
<th bgcolor="#1a1a1a"><font color="white">Entidad</font></th>
<th bgcolor="#1a1a1a"><font color="white">📍 Función en el Sistema</font></th>
<th bgcolor="#1a1a1a"><font color="white">🔑 Atributos Clave</font></th>
</tr>
<tr>
<td><b>Producto_Maestro</b></td>
<td>Centraliza la información única de una prenda para evitar duplicidad.</td>
<td><code>ID_Producto</code>, <code>Nombre</code>, <code>Marca</code></td>
</tr>
<tr>
<td><b>Ofertas</b></td>
<td>Almacena los datos dinámicos (precios) capturados por el scraper.</td>
<td><code>Precio</code>, <code>Stock</code>, <code>URL_Tienda</code></td>
</tr>
<tr>
<td><b>Tiendas</b></td>
<td>Catálogo de plataformas indexadas (Zalando, Adidas, etc.).</td>
<td><code>ID_Tienda</code>, <code>Nombre</code>, <code>Logo_URL</code></td>
</tr>
<tr>
<td><b>Usuarios</b></td>
<td>Gestión de perfiles y credenciales para personalización.</td>
<td><code>ID_Usuario</code>, <code>Email</code>, <code>Password</code></td>
</tr>
<tr>
<td><b>Alertas</b></td>
<td>Vincula usuarios con productos para seguimiento de rebajas.</td>
<td><code>ID_Alerta</code>, <code>Precio_Objetivo</code></td>
</tr>
</table>

<p align="center">
<i><b>Nota Técnica:</b> Se implementó una relación 1:N entre Producto y Ofertas para permitir comparativas multi-tienda en tiempo real.</i>
</p>

### 🧩 7. Documentación del Sistema
/css: Estilos modulares y variables de diseño (Layout, Colores).

/img: Contiene imagenes del proyecto

/js: Lógica del Scraper, manipulación del DOM y consumo de APIs.

/assets: Recursos gráficos, iconos y logos vectoriales.

### 🚀 8. Instalación y Vista Previa
Debido a que el proyecto se encuentra en su fase de Prototipado de Alta Fidelidad (Frontend), no se requieren instalaciones complejas de servidor o bases de datos para visualizar la interfaz.

<table align="center">
<tr>
<th bgcolor="#1a1a1a"><font color="white">Paso</font></th>
<th bgcolor="#1a1a1a"><font color="white">📂 Acción</font></th>
<th bgcolor="#1a1a1a"><font color="white">💻 Instrucción</font></th>
</tr>
<tr>
<td align="center"><b>1</b></td>
<td><b>Descarga</b></td>
<td>Clonar el repositorio o descargar el archivo <code>.zip</code> del proyecto.</td>
</tr>
<tr>
<td align="center"><b>2</b></td>
<td><b>Descompresión</b></td>
<td>Extraer los archivos asegurando que las carpetas <code>/css</code> y <code>/assets</code> mantengan su posición.</td>
</tr>
<tr>
<td align="center"><b>3</b></td>
<td><b>Ejecución</b></td>
<td>Abrir el archivo <code>index.html</code> en cualquier navegador moderno (Chrome, Edge, Firefox).</td>
</tr>
</table>

🛠️ Especificaciones Técnicas del Front
Estructura: HTML5 Semántico.

Estilos: CSS3 con arquitectura modular (vinculado en el < head>).

Interactividad: JavaScript ES6 para simulaciones de filtrado y navegación.

Assets: Iconografía y recursos optimizados en formato SVG/PNG.
#   B a c k e n d _ S p o r t s S c r a p e r  
 