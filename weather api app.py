import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QDialog
from PyQt5.QtCore import Qt, QUrl
import folium
from PyQt5.QtWebEngineWidgets import QWebEngineView
from requests import HTTPError, RequestException
import os 
from decouple import config
class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.cityLabel = QLabel("Enter city name", self)
        self.cityInput = QLineEdit(self)
        self.getWeatherButton = QPushButton("Get Weather", self)
        self.tempLabel = QLabel(self)
        self.emojiLabel = QLabel(self)
        self.descriptionLabel = QLabel(self)
        self.mapButton = QPushButton("Show Map", self)
        self.mapButton.hide()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Weather App")

        vbox = QVBoxLayout()
        vbox.addWidget(self.cityLabel)
        vbox.addWidget(self.cityInput)
        vbox.addWidget(self.getWeatherButton)
        vbox.addWidget(self.tempLabel)
        vbox.addWidget(self.emojiLabel)
        vbox.addWidget(self.descriptionLabel)
        vbox.addWidget(self.mapButton)
        self.setLayout(vbox)

        self.cityLabel.setAlignment(Qt.AlignCenter)
        self.cityInput.setAlignment(Qt.AlignCenter)
        self.tempLabel.setAlignment(Qt.AlignCenter)
        self.emojiLabel.setAlignment(Qt.AlignCenter)
        self.descriptionLabel.setAlignment(Qt.AlignCenter)

        self.cityLabel.setObjectName("cityLabel")
        self.cityInput.setObjectName("cityInput")
        self.getWeatherButton.setObjectName("getWeatherButton")
        self.tempLabel.setObjectName("tempLabel")
        self.emojiLabel.setObjectName("emojiLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.mapButton.setObjectName("mapButton")

        self.setStyleSheet("""
            QLabel, QPushButton { font-family: Calibri; }
            QLabel#cityLabel { font-size: 40px; font-style: italic; }
            QLineEdit#cityInput { font-size: 40px; }
            QPushButton#getWeatherButton, QPushButton#mapButton { font-size: 30px; font-weight: bold; }
            QLabel#tempLabel { font-size: 75px; }
            QLabel#emojiLabel { font-size: 100px; font-family: Segoe UI emoji; }
            QLabel#descriptionLabel { font-size: 40px; }
        """)

        self.getWeatherButton.clicked.connect(self.getWeather)
        self.mapButton.clicked.connect(self.showMap)

    def getWeather(self):
        apikey = config("YOUR_OPENWEATHERMAP_API_KEY")
        city = self.cityInput.text()
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={apikey}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            print(data)

            if data["cod"] == 200:
                self.displayWeather(data)

                self.latitude = data["coord"]["lat"]
                self.longitude = data["coord"]["lon"]
                self.city_name_for_map = data["name"]
                self.mapButton.show()
            else:
                self.displayError("Unexpected API response code.")
                self.mapButton.hide() 

        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                match e.response.status_code:
                    case 400:
                        self.displayError("Bad request \n Please check your city name.")
                    case 401:
                        self.displayError("Unauthorized \n Please check your API key.")
                    case 403:
                        self.displayError("Forbidden \n Access denied.")
                    case 404:
                        self.displayError("Not Found \n City not found.")
                    case 500:
                        self.displayError("Internal server error \n Please try again later.")
                    case 502:
                        self.displayError("Bad Gateway \n Invalid response from the server.")
                    case 503:
                        self.displayError("Service Unavailable \n Server is down.")
                    case 504:
                        self.displayError("Gateway Timeout \n No response from the server.")
                    case _:
                        self.displayError(f"HTTP error occurred: {e.response.status_code}")
            else:
                self.displayError(f"HTTP error occurred without a response: {e}")
            self.mapButton.hide()

        except requests.exceptions.ConnectionError:
            self.displayError("Connection Error\nCheck your internet connection.")
            self.mapButton.hide()
        except requests.exceptions.Timeout:
            self.displayError("Timeout Error\nThe request timed out.")
            self.mapButton.hide()
        except requests.exceptions.TooManyRedirects:
            self.displayError("Too Many Redirects Error\nCheck the URL.")
            self.mapButton.hide()
        except requests.exceptions.RequestException as e:
            self.displayError(f"Request Error: {e}")
            self.mapButton.hide()
        except Exception as e: 
            self.displayError(f"An unexpected error occurred: {e}")
            self.mapButton.hide()


    def displayError(self, message):
        self.tempLabel.setStyleSheet("font-size:30px")
        self.tempLabel.setText(message)
        self.emojiLabel.clear()
        self.descriptionLabel.clear()
        self.mapButton.hide()

    def displayWeather(self, data):
        self.tempLabel.setStyleSheet("font-size:75px")
        temperatureK = data["main"]["temp"]
        temperatureC = temperatureK - 273.15
        # temperatureF = (temperatureK * 9 / 5) - 459.67 # Not used, can remove if not displaying Fahrenheit

        weatherDescription = data["weather"][0]["description"]
        self.descriptionLabel.setText(weatherDescription.capitalize()) 
        self.emojiLabel.setText(self.getWeatherEmoji(data["weather"][0]["id"]))
        self.tempLabel.setText(f"{temperatureC:.1f}°C")

    @staticmethod
    def getWeatherEmoji(weatherID):
        if 200 <= weatherID <= 232:
            return "⛈️"
        elif 300 <= weatherID <= 321:
            return "🌦️"
        elif 500 <= weatherID <= 531:
            return "🌧️"
        elif 600 <= weatherID <= 622:
            return "🌨️"
        elif 701 <= weatherID <= 741:
            return "🌫️"
        elif weatherID == 762:
            return "🌋"
        elif weatherID == 771:
            return "🌬️"
        elif weatherID == 781:
            return "🌪️"
        elif weatherID == 800:
            return "🌞"
        elif 801 <= weatherID <= 804:
            return "☁️"
        else:
            return "❓"
    def showMap(self):

        if not hasattr(self, 'latitude') or not hasattr(self, 'longitude'):
            self.displayError("No coordinates available to show map. Get weather first.")
            return

        map_dialog = QDialog(self)
        map_dialog.setWindowTitle(f"Map of {self.city_name_for_map}")
        map_dialog.setGeometry(100, 100, 800, 600)


        m = folium.Map(location=[self.latitude, self.longitude], zoom_start=10)
        folium.Marker([self.latitude, self.longitude], popup=self.city_name_for_map).add_to(m)

        map_file = "temp_map.html"
        m.save(map_file)


        webView = QWebEngineView()
        webView.setUrl(QUrl.fromLocalFile(os.path.abspath(map_file)))


        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(webView)
        map_dialog.setLayout(dialog_layout)

        map_dialog.exec_()

        if os.path.exists(map_file):
            os.remove(map_file)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    weather_app.show()
    sys.exit(app.exec_())