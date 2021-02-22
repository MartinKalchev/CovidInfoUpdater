import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import time
import threading


API_KEY = "ta6aQ0siTKUV"
PROJECT_TOKEN = "tZU9e68k1H_g"
RUN_TOKEN = "tJKyRjLVWZio"


class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            "api_key" : self.api_key
        }
        self.data = self.get_data()

    def get_data(self):
        response = requests.get(f'https://parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data',
                                params=self.params)
        data = json.loads(response.text)
        return data

    def get_total_cases(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Coronavirus Cases:":
                return content['value']

    def get_total_deaths(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Deaths:":
                return content['value']

        return "0"

    def get_country_data(self, country):
        data = self.data["country"]

        for content in data:
            if content['name'].lower() == country.lower():
                return content

        return "0"

    def get_list_of_countries(self):
        countries = []
        for country in self.data['country']:
            countries.append(country['name'].lower())

        return countries

    def update_data(self):
        # initialize a new run on the parsehub servers
        response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run',
                                 params=self.params)

        # when a thread is not doing something it releases itself
        # and let the main thread start working(the voice assistant thread)
        def poll():
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    self.data = new_data
                    print("Data Updated")
                    break
                time.sleep(5)

        tr = threading.Thread(target=poll)
        tr.start()


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
        except Exception as e:
            print("Exception:", str(e))

    return said.lower()


def main():
    print("Program Started...")
    data = Data(API_KEY, PROJECT_TOKEN)
    END_PHRASE = "stop"
    country_list = data.get_list_of_countries()

    TOTAL_VOICE_PATTERNS = {
                    re.compile("[\w\s]+ total [\w\s]+ cases"): data.get_total_cases,
                    re.compile("[\w\s]+ total cases"): data.get_total_cases,
                    re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
                    re.compile("[\w\s]+ total deaths"): data.get_total_deaths
                    }

    COUNTRY_VOICE_PATTERNS = {
        re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths'],
    }

    UPDATE_INFO_COMMAND = "update"

    while True:
        print("Listening for request...")
        text = get_audio()
        print(text)
        result = None

        for pattern, func in COUNTRY_VOICE_PATTERNS.items():
            if pattern.match(text):
                country_words = set(text.split(" "))
                for country in country_list:
                    if country in country_words:
                        result = func(country)
                        break

        for pattern, func in TOTAL_VOICE_PATTERNS.items():
            if pattern.match(text):
                result = func()
                break

        if text == UPDATE_INFO_COMMAND:
            result = "Covid info is being updated... This may take a moment."
            data.update_data()

        if result:
            speak(result)

        if text.find(END_PHRASE) != -1:  # stop loop
            print("Program Exited")
            break


main()

