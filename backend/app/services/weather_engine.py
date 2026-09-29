from typing import Dict, Any

class WeatherEngine:
    def __init__(self):
        self._current_weather = "CLEAR"  # CLEAR, RAIN, NIGHT, FOG, LOW_VISIBILITY
        self._weather_profiles = {
            "CLEAR": {
                "visibility_factor": 1.0,
                "ocr_confidence_penalty": 0.0,
                "color_confidence_penalty": 0.0,
                "description": "Clear daylight conditions with optimal visibility."
            },
            "RAIN": {
                "visibility_factor": 0.78,
                "ocr_confidence_penalty": 0.15,
                "color_confidence_penalty": 0.12,
                "description": "Precipitation with road reflections and reduced optical clarity."
            },
            "NIGHT": {
                "visibility_factor": 0.65,
                "ocr_confidence_penalty": 0.20,
                "color_confidence_penalty": 0.25,
                "description": "Low-light environment dependent on street lamps and vehicle headlamps."
            },
            "FOG": {
                "visibility_factor": 0.55,
                "ocr_confidence_penalty": 0.30,
                "color_confidence_penalty": 0.35,
                "description": "Dense atmospheric moisture causing significant contrast degradation."
            },
            "LOW_VISIBILITY": {
                "visibility_factor": 0.50,
                "ocr_confidence_penalty": 0.35,
                "color_confidence_penalty": 0.40,
                "description": "Severe weather or camera lens obstruction."
            }
        }

    @property
    def current_weather(self) -> str:
        return self._current_weather

    def set_weather(self, weather: str) -> Dict[str, Any]:
        weather_upper = weather.upper()
        if weather_upper in self._weather_profiles:
            self._current_weather = weather_upper
        else:
            self._current_weather = "CLEAR"
        return self.get_context()

    def get_context(self) -> Dict[str, Any]:
        profile = self._weather_profiles.get(self._current_weather, self._weather_profiles["CLEAR"])
        return {
            "condition": self._current_weather,
            "visibility_factor": profile["visibility_factor"],
            "ocr_confidence_penalty": profile["ocr_confidence_penalty"],
            "color_confidence_penalty": profile["color_confidence_penalty"],
            "description": profile["description"],
            "requires_cautious_ocr": self._current_weather in ["RAIN", "NIGHT", "FOG", "LOW_VISIBILITY"]
        }

    def adjust_confidence(self, base_ocr_conf: float, base_color_conf: float) -> tuple[float, float, str]:
        profile = self._weather_profiles.get(self._current_weather, self._weather_profiles["CLEAR"])
        adj_ocr = max(0.1, min(0.99, base_ocr_conf * (1.0 - profile["ocr_confidence_penalty"])))
        adj_color = max(0.1, min(0.99, base_color_conf * (1.0 - profile["color_confidence_penalty"])))
        
        status = "OPTIMAL"
        if profile["visibility_factor"] < 0.70:
            status = "ENVIRONMENTAL_DEGRADATION"
        return round(adj_ocr, 2), round(adj_color, 2), status

weather_service = WeatherEngine()
