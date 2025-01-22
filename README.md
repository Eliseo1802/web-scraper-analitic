# Documentación para el Web Scraper

Esta documentación explica la funcionalidad y los detalles de implementación del Web Scraper basado en Python escrito para la empresa Analitic durante la primera práctica universitaria de Eliseo Guarda Cortés.

El Web Scraper está diseñado para extraer artículos de noticias de varios sitios web y guardar los datos recopilados en un archivo CSV para fácil visualización.

## Tabla de contenido
- [Descripción general](#descripción-general)
- [Dependencias](#dependencias)
- [Constantes](#constantes)
- [Clase `WebScraper`](#clase-webscraper)
  - [`__init__(self, driver_path)`](#__init__self-driver_path)
  - [`_setup_driver(self)`](#_setup_driverself)
  - [`_scroll_to_bottom(self)`](#_scroll_to_bottomself)
  - [`_format_date(self, date)`](#_format_dateself-date)
  - [`_close_ads(self)`](#_close_adsself)
  - [`scrape_adnradio(self, query)`](#scrape_adnradioself-query)
  - [`scrape_biobiochile(self, query)`](#scrape_biobiochileself-query)
  - [`scrape_cooperativa(self, query)`](#scrape_cooperativaself-query)
  - [`scrape_duckduckgo(self, query)`](#scrape_duckduckgoself-query)
  - [`save_to_csv(self, filename)`](#save_to_csvself-filename)
  - [`close(self)`](#closeself)
- [Uso](#uso)
- [Manejo de errores](#manejo-de-errores)
- [Aplicación Flask](#aplicación-flask)

---

## Descripción general

Este scraper utiliza Selenium WebDriver para interactuar con páginas web de forma dinámica, manejando contenido cargado de forma diferida (lazy-loading) y extrayendo artículos de noticias de los siguientes sitios web:

- ADNRadio (adnradio.cl)
- BioBioChile (biobiochile.cl)
- Cooperativa (cooperativa.cl)
- DuckDuckGo (duckduckgo.com)

---

## Dependencias

Asegúrese de que los siguientes paquetes de Python estén instalados antes de ejecutar el script:

- `selenium`
- `fake_useragent`
- `pandas`
- `time`
- `re`

En caso de no tenerlos, instálalos utilizando:
```bash
pip install selenium fake-useragent pandas
```

---

## Constantes

El script tiene definido ciertas constantes para un fácil manejo de este:

- `MAX_QUERY_INPUT`: Máximo de caracteres permitidos para el término de búsqueda (predeterminado: 100).
- `MAX_NEWS_PER_SITE`: Número máximo de artículos para extraer de cada sitio web (predeterminado: 1000).
- `MONTH_MAPPING`: Un diccionario para asignar los nombres de los meses en español a valores numéricos.

---

## Clase `WebScraper`

### `__init__(self, driver_path)`
Inicializa el objeto `WebScraper`.

- **Parámetros:**
  - `driver_path`(str): Ruta de acceso al WebDriver ejecutable.
- **Atributos:**
  - `driver_path`: Ruta de acceso al WebDriver ejecutable.
  - `driver`: Instancia de WebDriver configurada para el scraping.
  - `data`: Lista para almacenar los datos extraídos.

### `_setup_driver(self)`
Configura el WebDriver con las opciones necesarias, las cuales incluyen:
- Modo sin interfaz gráfica para mejorar el rendimiento.
- Utilización de un directorio temporario para evitar problemas de espacio.
- Agente de usuario (User-Agent) personalizado para ayudar con el anonimato.

Retorna la instancia del WebDriver configurado.

### `_scroll_to_bottom(self)`
Maneja el desplazamiento de la página hasta la parte inferior de esta para tratar con la carga diferida de ciertos sitios web.

### `_format_date(self, date)`
Formatea las fechas dadas en formato `dd/mm/aaaa` o devuelve `None` si el formato no es válido. Maneja formatos de fecha en escritura en español como `Jueves 09 Enero, 2025`.

- **Parámetros:**
  - `date`(str): Fecha entregada para formatear.

### `_close_ads(self)`
Cierra anuncios emergentes si se detectan (específico de BioBioChile por el momento).

### `scrape_adnradio(self, query)`
Extrae artículos de noticias del sitio web ADNRadio.
- Extrae los títulos, fechas y URLs de las noticias encontradas.
- Maneja la paginación desplazándose hacia abajo y cargando contenido dinámicamente.

- **Parámetros:**
  - `query`(str): Término de búsqueda a ingresar a la página web.

### `scrape_biobiochile(self, query)`
Extrae artículos de noticias del sitio web BioBioChile.
- Extrae los títulos, fechas y URLs de las noticias encontradas.
- Maneja los distintos diseños internos de las noticias iniciales y posteriores.
- Trata con anuncios emergentes y contenido de carga diferida (lazy-loading).

- **Parámetros:**
  - `query`(str): Término de búsqueda a ingresar a la página web.

### `scrape_cooperativa(self, query)`
Extrae artículos de noticias del sitio web Cooperativa.
- Extrae los títulos, fechas y URLs de las noticias encontradas.
- Navega a través de páginas de resultados múltiples.

- **Parámetros:**
  - `query`(str): Término de búsqueda a ingresar a la página web.

### `scrape_duckduckgo(self, query)`
Extrae artículos de noticias del sitio web DuckDuckGo.
- Extrae los títulos y URLs de las noticias encontradas.
- Extracts titles and URLs (DuckDuckGo no proporciona fechas de publicación directamente).
- Carga dinámicamente más resultados utilizando el botón de "Cargar más".

- **Parámetros:**
  - `query`(str): Término de búsqueda a ingresar a la página web.

### `save_to_csv(self, filename)`
Guarda los datos extraídos en un archivo CSV mediante el paquete pandas.

- **Parámetros:**
  - `filename`(str): Nombre del archivo CSV donde se guardarán los datos.


### `close(self)`
Cierra la instancia del WebDriver y libera recursos.

---

## Uso

1. Actualice la constante `DRIVER_PATH` con la ruta de acceso a su ejecutable WebDriver
  1.1. Depende del browser que quiera utilizar puede necesitar un WebDriver distinto (chromedriver para Chrome, geckodriver para Firefox, etc.)
2. Ejecute el script e ingrese una consulta de búsqueda (limitada a 100 caracteres).
3. El script extraerá datos de los sitios web especificados y los guardará en un archivo CSV llamado `noticias_<query>.csv`.

Ejemplo de ejecución:
```bash
python web_scraper_analitic.py
```

---

## Manejo de errores

- El script utiliza bloques try-except para manejar excepciones como elementos faltantes o interacciones fallidas.
- Registra mensajes para indicar el progreso o errores, como:
  - "No se pudo cerrar el anuncio o no había ninguno."
  - "Se produjo un error al extraer datos de <site>: <error>."
- Si se produce un error, el script garantiza que WebDriver se cierre correctamente y se guarden los datos recopilados hasta el momento del error.

---

## Aplicación Flask

Se incluye una aplicación Flask (`app.py`) para proporcionar una interfaz web para el scraper.

### Rutas Flask

#### `/`
Representa la página de inicio (`index.html`).

#### `/scrape` (POST)
Acepta una consulta del usuario, activa el proceso de scraping para todos los sitios web compatibles y devuelve un archivo CSV con los datos extraídos.

---

Esta documentación proporciona una guía completa sobre la funcionalidad del script, lo que facilita su comprensión, modificación o ampliación.
