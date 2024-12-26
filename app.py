import requests
from flask import Flask, request, jsonify
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

app = Flask(__name__)

# Настройка кэширования
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 3600})

# Настройка лимитера
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

# API ключ от OpenWeatherMap
API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# Функция для получения погоды из OpenWeatherMap
def get_weather_from_api(city):
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric',  # Для получения температуры в Цельсиях
        'lang': 'ru'  # Для получения ответов на русском языке
    }
    
    # Запрос к OpenWeatherMap
    response = requests.get(BASE_URL, params=params, timeout=10)
    
    if response.status_code != 200:
        return None
    
    # 
    data = response.json()
    
    # Извлекаем нужную информацию
    weather_info = {
        'город': data['name'],
        'температура': f"{data['main']['temp']}°C",
        'влажность': f"{data['main']['humidity']}%",
        'погода': data['weather'][0]['description'].capitalize(),
        'скорость_ветра': f"{data['wind']['speed']} м/с"
    }
    
    return weather_info

@app.route('/weather/', methods=['GET'])
@limiter.limit("10 per hour")  # Лимитируем 10 запросов на IP-адрес в час
def get_weather():
    city = request.args.get('city', '').strip()
    
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400
    
    # Проверка наличия кэшированных данных
    cached_weather = cache.get(city)
    if cached_weather:
        print(f"Данные для города {city} взяты из кэша")
        return jsonify(cached_weather)
    
    # Запрос к внешнему API
    weather_info = get_weather_from_api(city)
    
    if not weather_info:
        return jsonify({'error': 'City not found'}), 404
    
    # Сохраняем данные в кэш
    cache.set(city, weather_info)
    print(f"Данные для города {city} получены с внешнего API и кэшированы")

    return jsonify(weather_info)

if __name__ == "__main__":
    app.run()
