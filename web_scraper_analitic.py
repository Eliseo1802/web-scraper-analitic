from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import pandas as pd
import time
import re

# Constantes.
MAX_QUERY_INPUT = 100 # Cantidad de caracteres máximos permitidos.
MAX_NEWS_PER_SITE = 10000 # Cantidad de noticias máximas por sitio web.
MONTH_MAPPING = { # Diccionario de meses para el formateo de fechas.
    "Enero": "01",
    "Febrero": "02",
    "Marzo": "03",
    "Abril": "04",
    "Mayo": "05",
    "Junio": "06",
    "Julio": "07",
    "Agosto": "08",
    "Septiembre": "09",
    "Octubre": "10",
    "Noviembre": "11",
    "Diciembre": "12"
}


class WebScraper:
    def __init__(self, driver_path): # Inicializador de la clase WebScraper.
        self.driver_path = driver_path # Ruta de acceso al controlador del browser.
        self.driver = self._setup_driver() # Inicializador del controlador.
        self.data = [] # Lista para guardar los datos extraídos.

    def _setup_driver(self): # Método para configurar el controlador.
        options = Options() # Inicializar opciones para configurar el controlador.
        
        options.add_argument("--headless=new") # Sin interfaz visual.
        options.add_argument("--disable-gpu") # Antes se necesitaba para la interfaz headless pero ahora parece que no, lo dejé por si acaso.
        options.add_argument("--disable-dev-shm-usage") # Utiliza un directorio temporario para evitar problemas de espacio.
        options.add_argument("--window-size=1920,1080") # Asegura que BioBioChile cargue correctamente más resultados debido a que usa lazy-loading en su sitio web.
        
        # Utilizar User-Agents distintos por cada ejecución del código.
        ua = UserAgent(os={"Windows", "Linux", "Ubuntu"})
        options.add_argument(f"user-agent={ua.random}")

        return webdriver.Chrome(service=Service(self.driver_path), options=options)

    def _scroll_to_bottom(self): # Método para desplazarse hasta el fondo de la página para tratar con el lazy-loading.
        last_height = self.driver.execute_script("return document.body.scrollHeight") # Obtiene la altura actual de la página.
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Se desplaza al fondo de la página.
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight") # Obtiene la altura nueva de la página.
            if new_height == last_height: # Compara la primera altura a la segunda y si son iguales es porque ya está al fondo.
                break
            last_height = new_height

    def _format_date(self, date): # Método para formatear la fecha a dd/mm/aaaa o retorna None si es inválido.
        try:
            # Fecha coincide con el formato dd/mm/aaaa.
            match = re.search(r"\d{1,2}/\d{1,2}/\d{4}", date)
            if match:
                return match.group()

            # Fecha coincide con el formato de fecha en español (ej: Jueves 09 Enero, 2025).
            match = re.search(r"(\w+)\s(\d{1,2})\s(\w+),\s(\d{4})", date)
            if match:
                day = match.group(2)
                month = MONTH_MAPPING.get(match.group(3), "01") # El valor predeterminado es "01" si el mes no es válido.
                year = match.group(4)
                return f"{day}/{month}/{year}"
            
            return None  # Retorna None si no se encuentra una fecha válida.
        except Exception:
            return None
    
    def _close_ads(self): # Método para cerrar un anuncio detectado en la página (solo lo necesita BioBioChile por ahora).       
        try:
            # Localiza y cambia al iframe (marco donde se encuentra el anuncio).
            ad_iframe = self.driver.find_element(By.XPATH, "//iframe[contains(@id, 'google_ads_iframe')]")
            self.driver.switch_to.frame(ad_iframe)
            
            # Localiza y presiona el botón de cerrar anuncio.
            close_button = self.driver.find_element(By.XPATH, "//*[@id='btnClose']")
            close_button.click()
            print("Anuncio cerrado exitosamente.")
            
            # Vuelve al contenido principal (marco donde se encuentra la página normal).
            self.driver.switch_to.default_content()
        except Exception as e:
            print(f"No se pudo cerrar el anuncio o no había ninguno: {e}")
            self.driver.switch_to.default_content()

    def scrape_adnradio(self, query): # Método principal para scrapear el sitio web ADNRadio (adnradio.cl).
        url = f"https://www.adnradio.cl/buscador/?q={query.strip().replace(r' ','%20')}"
        self.driver.get(url) # Abre el URL.
        print("= = = Entrando a ADNRadio = = =") # Visualizador arbitrario para la consola, solo para saber si está funcionando.
        time.sleep(3)
        
        count = 0 # Contador de noticias extraídas.
        
        try:
            while count < MAX_NEWS_PER_SITE: # Loop para extraer noticias solo hasta el límite establecido.
                articles = self.driver.find_elements(By.XPATH, "//*[@id='fusion-app']/main/section[2]/div/div/div") # Encuentra todas las noticias presentes en el sitio.
                if not articles: # Si no encuentra más noticias, termina.
                    print("Búsqueda por ADNRadio finalizada.")
                    break

                for article in articles: # Loop por cada noticia de todas las noticias encontradas.
                    try:
                        title = article.find_element(By.XPATH, ".//article/div/header/h3/a") # Extrae el elemento del título.
                        date = article.find_element(By.XPATH, ".//article/div/div/p[2]") # Primer caso: Extrae el elemento de la fecha cuando la noticia SI tiene autor.
                        if not date.text:
                            date = article.find_element(By.XPATH, ".//article/div/div/p[1]") # Segundo caso: Extrae el elemento de la fecha cuando la noticia NO tiene autor.

                        self.data.append({ # Se agregan los datos de arriba a la lista de datos extraídos.
                            "Title": title.text,
                            "Date": self._format_date(date.text),
                            "URL": title.get_attribute("href"), # El URL está en el mismo elemento que el título, se extrae el atributo href.
                            "Website": "ADNRadio"
                        })
                        count += 1 # Aumenta el contador de noticias extraídas.
                        
                        if len(self.data) % (MAX_NEWS_PER_SITE/4) == 0: # Visualizador arbitrario de cuántas noticias lleva, solamente para saber si sigue funcionando.
                            print(f"{len(self.data)} noticias extraídas...")
                    except Exception:
                        continue

                # Desplaza la página hasta la parte inferior para cargar más resultados.
                previous_height = self.driver.execute_script("return document.body.scrollHeight")
                self._scroll_to_bottom()
                
                # Espera a que el sitio web cargue más noticias.
                time.sleep(3)

                # Comprueba si la altura del desplazamiento ha cambiado.
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                if current_height == previous_height: # Cuando bajas al fondo cargan automáticamente más noticias, si no pasa es porque terminó. 
                    print("Búsqueda por ADNRadio finalizada.")
                    break # No hay más noticias para cargar.

        except Exception as e:
            print(f"Se produjo un error al extraer datos de ADNRadio: {e}")

    def scrape_biobiochile(self, query): # Método principal para scrapear el sitio web BioBioChile (biobiochile.cl).
        url = f"https://www.biobiochile.cl/buscador.shtml?s={query.strip().replace(r' ','+')}"
        self.driver.get(url) # Abre el URL.
        print("= = = Entrando a BioBioChile = = =") # Visualizador arbitrario para la consola, solo para saber si está funcionando.
        time.sleep(3)
        self._close_ads() # Cierra el anuncio que sale al inicio. De igual forma, si esperas 30 segundos el anuncio desaparece por si solo.
        
        current_count = 0 # Contador de noticias extraídas.
        xpath_count = 1 # Índice para las noticias después de las primeras 20.
        base_xpath = "/html/body/main/div[2]/section/div/div/div/div/" # Parte del XPath que comparten el título, fecha y url.
        count_xpath = "/html/body/main/div[1]/div/div/div[2]" # XPath del número de noticias en la página de resultados.
        button_xpath = "/html/body/main/div[2]/section/div/div/div/div/div/div[2]/button" # XPath del botón para cargar más resultados.

        try:
            max_articles = int(re.search(r"\d+", self.driver.find_element(By.XPATH, count_xpath).text).group()) # Busca el elemento que muestra la cantidad de noticias acerca del término buscado.

            if max_articles > MAX_NEWS_PER_SITE: # Limita la cantidad de noticias a leer si esta sobrepasa el máximo.
                max_articles = MAX_NEWS_PER_SITE
            
            while current_count < max_articles:
                if current_count < 20: 
                    for i in range(1, 21): # Loop para las primeras 20 noticias. Estos tienen un XPath distinto a todo el resto.
                        if current_count >= max_articles: # Si el contador de noticias sobrepasa el máximo este se detiene.
                            break
                        try:
                            url = self.driver.find_element(By.XPATH, f"{base_xpath}a[{i}]") # Extrae el elemento del url.
                            title = self.driver.find_element(By.XPATH, f"{base_xpath}a[{i}]/article/div[2]/h2") # Extrae el elemento del título.
                            date = self.driver.find_element(By.XPATH, f"{base_xpath}a[{i}]/article/div[2]/div") # Extrae el elemento de la fecha.
                            
                            self.data.append({ # Se agregan los datos de arriba a la lista de datos extraídos.
                                "Title": title.text,
                                "Date": self._format_date(date.text),
                                "URL": url.get_attribute("href"),
                                "Website": "BioBioChile"
                            })
                            
                            if len(self.data) % (MAX_NEWS_PER_SITE/4) == 0: # Visualizador arbitrario de cuántas noticias lleva, solamente para saber si sigue funcionando.
                                print(f"{len(self.data)} noticias extraídas...")
                            
                            current_count += 1 # Aumenta el contador de noticias extraídas.
                        except:
                            break

                for i in range(1, 21): # Loop para el resto de noticias.
                    if current_count >= max_articles: # Si el contador de noticias sobrepasa el máximo este se detiene.
                        break
                    try:
                        url = self.driver.find_element(By.XPATH, f"{base_xpath}div/div[1]/div[{xpath_count}]/a") # Extrae el elemento del url.
                        title = self.driver.find_element(By.XPATH, f"{base_xpath}div/div[1]/div[{xpath_count}]/a/article/div[2]/h2") # Extrae el elemento del título.
                        date = self.driver.find_element(By.XPATH, f"{base_xpath}div/div[1]/div[{xpath_count}]/a/article/div[2]/div") # Extrae el elemento de la fecha.

                        self.data.append({ # Se agregan los datos de arriba a la lista de datos extraídos.
                            "Title": title.text,
                            "Date": self._format_date(date.text),
                            "URL": url.get_attribute("href"),
                            "Website": "BioBioChile"
                        })
                        
                        if len(self.data) % (MAX_NEWS_PER_SITE/4) == 0: # Visualizador arbitrario de cuántas noticias lleva, solamente para saber si sigue funcionando.
                            print(f"{len(self.data)} noticias extraídas...")
                        
                        xpath_count += 1 # Aumenta el índice para buscar la siguiente noticia.
                        current_count += 1 # Aumenta el contador de noticias extraídas.
                    except:
                        break

                self._scroll_to_bottom() # Para poder presionar el botón de cargar más resultados este tiene que estar cargado (que se pueda ver la gráfica del botón).
                try: # Presiona el botón de cargar más resultados.
                    load_more_button = self.driver.find_element(By.XPATH, button_xpath)
                    load_more_button.click()
                    time.sleep(2)
                except: # Si no encuentra ningún botón, es porque terminó.
                    print("Búsqueda por BioBioChile finalizada.")
                    break
        except Exception as e:
            print(f"Se produjo un error al extraer datos de BioBioChile: {e}")

    def scrape_cooperativa(self, query): # Método principal para scrapear el sitio web Cooperativa (cooperativa.cl)
        url = "https://www.cooperativa.cl/"
        self.driver.get(url) # Abre el URL.
        print("= = = Entrando a Cooperativa = = =") # Visualizador arbitrario para la consola, solo para saber si está funcionando.
        time.sleep(15) # Tiene un tiempo más largo debido a que cuando estuve haciendo las pruebas finales el servidor del sitio web estaba bastante lento y le costaba cargar.
        # A veces presenta un anuncio pero esperando el tiempo de espera anterior este desaparece.
        
        count = 0 # Contador de noticias extraídas.
        base_xpath = "//*[@id='contenedor-pagina']/section/div/section/article[" # Parte del XPath compartido por el título, fecha y url.
        page_xpath = "//*[@id='contenedor-pagina']/section/div/section/div[2]/a[" # Parte del XPath de los botones para cambiar de página de resultados.
        
        try:
            # Encuentra y presiona el elemento de la lupa para habilitar la barra de búsqueda, si no es presionado no funciona.
            lupa = self.driver.find_element(By.XPATH, "//*[@id='buscador_media']/p/a") 
            lupa.click()

            # Encuentra e ingresa a la barra de búsqueda el término a buscar dentro del sitio web.
            search_bar = self.driver.find_element(By.CSS_SELECTOR, "input.buscador-input") 
            search_bar.send_keys(query)
            search_bar.send_keys(Keys.RETURN)
            time.sleep(2)

            page = 1 # Contador para moverse por el índice de las páginas.
            while count < MAX_NEWS_PER_SITE: # Loop para extraer noticias solo hasta el límite establecido.
                for i in range(1, 16):
                    try:
                        url_element = self.driver.find_element(By.XPATH, f"{base_xpath}{i}]/a") # Extrae el elemento del url.
                        title = self.driver.find_element(By.XPATH, f"{base_xpath}{i}]/a/h3") # Extrae el elemento del título.
                        date = self.driver.find_element(By.XPATH, f"{base_xpath}{i}]/a/div/div/time") # Extrae el elemento de la fecha.

                        # Eliminar el número inicial y las comillas que encierra al título.
                        title = re.sub(r'^\"?\d+\s+', '', title.text).strip('"')
                        
                        self.data.append({ # Se agregan los datos de arriba a la lista de datos extraídos.
                            "Title": title,
                            "Date": self._format_date(date.text),
                            "URL": url_element.get_attribute("href"),
                            "Website": "Cooperativa"
                        })
                        count += 1 # Aumenta el contador de noticias extraídas.
                        
                        if len(self.data) % (MAX_NEWS_PER_SITE/4) == 0: # Visualizador arbitrario de cuántas noticias lleva, solamente para saber si sigue funcionando.
                            print(f"{len(self.data)} noticias extraídas...")
                        
                        if count >= MAX_NEWS_PER_SITE: # Si el contador de noticias sobrepasa el máximo este se detiene.
                            break
                    except:
                        break
                
                if page <= 5: # El XPath de las primeras 5 páginas mantienen un incremento en el índice, pero de la sexta para adelante es siempre el mismo.
                    next_page_xpath = f"{page_xpath}{page}]"
                else:
                    next_page_xpath = f"{page_xpath}6]"
                
                try: # Encuentra y presiona el botón de la página siguiente.
                    next_page_button = self.driver.find_element(By.XPATH, next_page_xpath)
                    self.driver.execute_script("arguments[0].click();", next_page_button)
                    page += 1
                    time.sleep(2)
                except:
                    print("Búsqueda por Cooperativa finalizada.")
                    break

        except Exception as e:
            print(f"Se produjo un error al extraer datos de Cooperativa: {e}")
    
    def scrape_duckduckgo(self, query): # Método principal para scrapear el sitio web DuckDuckGo (duckduckgo.com)
        url = f"https://duckduckgo.com/?q={query.strip().replace(r' ','+')}&kl=cl-es&iar=news&ia=news"
        self.driver.get(url) # Abre el URL.
        print("= = = Entrando a DuckDuckGo = = =") # Visualizador arbitrario para la consola, solo para saber si está funcionando.
        time.sleep(3)
        
        count = 0 # Contador de noticias extraídas.
        load_button_class = "result--more__btn" # Clase del botón para cargar más resultados.
        
        def get_article_data(index): # Método anidado para buscar noticias dentro de la página.
            try:
                title_element = self.driver.find_element(By.XPATH, f"//*[@id='vertical_wrapper']/div/div[3]/div/div[1]/div[3]/div[{index}]/div/h2/a[1]") # Extrae el elemento del título.
                
                return { # Se retornan los datos de arriba ya formateados.
                    "Title": title_element.text,
                    "Date": None, # DuckDuckGo no muestra fecha de las noticias.
                    "URL": title_element.get_attribute("href"), # El URL está en el mismo elemento que el título, se extrae el atributo href. 
                    "Website": "DuckDuckGo"
                }
            except Exception:
                return None

        def click_load_more(current_index): # Método anidado para presionar el botón de cargar más resultados. 
            try: # Busca y presiona el botón de cargar más resultados.
                load_more_button = self.driver.find_element(By.CLASS_NAME, load_button_class)
                self.driver.execute_script("arguments[0].click();", load_more_button)
                time.sleep(2)
                return current_index + 1
            except Exception:
                return current_index
        
        index = 1 # Índice encargado de pasar noticia por noticia
        try:
            while count < MAX_NEWS_PER_SITE: # Loop para extraer noticias solo hasta el límite establecido.
                article_data = get_article_data(index) # Extrae los datos ya formateados de una noticia por iteración.
                if article_data:
                    self.data.append(article_data) # Se agregan los datos de arriba a la lista de datos extraídos.
                    
                    if len(self.data) % (MAX_NEWS_PER_SITE/4) == 0: # Visualizador arbitrario de cuántas noticias lleva, solamente para saber si sigue funcionando.
                        print(f"{len(self.data)} noticias extraídas...")
                    
                    count += 1 # Aumenta el contador de noticias extraídas.
                    index += 1 # Aumenta el índice para buscar la próxima noticia
                else:
                    new_index = click_load_more(index) # El botón de cargar más resultados ocupa un índice de noticia por lo que debe sumar 1 más para buscar la siguiente noticia. 
                    if new_index == index: # Si no logra cargar más resultados el índice no avanza por lo que termina.
                        print("Búsqueda por DuckDuckGo finalizada.")
                        break
                    index = new_index
        except Exception as e:
            print(f"Se produjo un error al extraer datos de DuckDuckGo: {e}")

    def save_to_csv(self, filename): # Método para guardar los datos extraídos a través de un DataFrame de pandas a un .csv
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False)
        print(f"{len(self.data)} noticias guardadas en {filename}")

    def close(self): # Método para cerrar el controlador
        self.driver.quit()

if __name__ == "__main__":
    DRIVER_PATH = "C:/Users/Equipo/Drivers/chromedriver.exe" # Ruta de acceso al controlador del browser (cambiar la ruta a una propia)
    
    while True: # Loop para limitar la cantidad de caracteres máximos a ingresar
        QUERY = input("Término a buscar: ")
        if len(QUERY) <= MAX_QUERY_INPUT:
            break
        print(f"Término muy largo, máximo {MAX_QUERY_INPUT} caracteres.")

    scraper = WebScraper(DRIVER_PATH) # Inicializador del Web Scraper

    try:
        scraper.scrape_adnradio(QUERY) # Inicia la búsqueda en ADNRadio
        scraper.scrape_biobiochile(QUERY) # Inicia la búsqueda en BioBioChile
        scraper.scrape_cooperativa(QUERY) # Inicia la búsqueda en Cooperativa
        scraper.scrape_duckduckgo(QUERY) # Inicia la búsqueda en DuckDuckGo
    finally:
        scraper.save_to_csv(f"noticias_{QUERY.strip().replace(r' ','_')}.csv") # Guarda los datos extraídos en un archivo .csv (se puede visualizar desde un DataFrame o por SQL)
        scraper.close() # Cierra el controlador y termina el proceso completo
