# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
import json
import logging
import random
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

import fasttext

from rasa.shared.core.trackers import DialogueStateTracker

logger = logging.getLogger(__name__)


class LanguageIdentification(object):
    def __init__(self):
        pretrained_lang_model = "lid.176.ftz"
        self.model = fasttext.load_model(pretrained_lang_model)

    def predict_lang(self, text):
        predictions = self.model.predict(text)  # returns top 2 matching languages
        return predictions[0][0].split('__')[-1]


class MultilingualResponse(object):
    def __init__(self):
        # with open("multilingual_response.json") as fp:
        with open("account_mling.json") as fp:
            self.multilingual_response = json.load(fp)

    @staticmethod
    def random_response(responses):
        num_response = len(responses) - 1
        return responses[random.randint(0, num_response)]

    def predict_response(self, intent, lang):
        default_lang = 'en'
        try:
            mling_response = self.multilingual_response[intent]
            try:
                responses = mling_response[lang]
                final_response = self.random_response(responses)
            except:
                # if language detection fails (ie detects other than languages listed in the response)
                # fallback to English
                responses = mling_response[default_lang]
                final_response = self.random_response(responses)
        except:
            final_response = None
        return final_response


multilingual_response = MultilingualResponse()
language_detection = LanguageIdentification()


class ActionLanguageSelect(Action):

    def name(self) -> Text:
        return "action_utter_language_select"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # print(tracker.latest_message)
        # print(tracker.events)
        intent = tracker.latest_message['intent'].get('name')
        input_text = tracker.latest_message['text']
        lang = language_detection.predict_lang(input_text)
        response = multilingual_response.predict_response(intent=intent, lang=lang)
        if response:
            logger.info('Multilingual Response for the intent {1}, '
                        'in language {2}: {0}'.format(response, intent, lang))
            dispatcher.utter_message(text=response)
        else:
            logger.info('There is no multilingual response for intent:{0}, '
                        'in language:{1}'.format(intent, lang))
        return []
