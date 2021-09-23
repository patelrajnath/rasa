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
from deep_translator import GoogleTranslator, MyMemoryTranslator, MicrosoftTranslator

import json
import random
from typing import Any, Text, Dict, List
import fasttext

import logging
logger = logging.getLogger(__name__)

microsoft_api_key = '6eb25dc1e0824f358ee564e81d6e0752'


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
        with open("multilingual_responses.json") as fp:
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
                response_english = self.random_response(responses)
                # final_response = GoogleTranslator(source='en', target=lang).translate(response_english)
                # response_translated = MyMemoryTranslator(source='en', target=lang).translate(response_english)
                final_response = MicrosoftTranslator(api_key=microsoft_api_key, source='en', target=lang).translate(
                    response_english)
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
        logger.info(f'The intent:{intent}')
        input_text = tracker.latest_message['text']
        logger.info(f'The user text:{input_text}')

        eqa_response = tracker.latest_message['eqa_response']
        logger.info(f'The Dummy EQA Response:{eqa_response}')

        lang = language_detection.predict_lang(input_text)
        logger.info('Predicted language is:{}'.format(lang))
        response = multilingual_response.predict_response(intent=intent, lang=lang)

        if response:
            logger.info('Multilingual Response:{0}'.format(response))
            dispatcher.utter_message(text=response)
        else:
            utter_intent = "utter_{}".format(intent)
            logger.info(f'utter_intent:{utter_intent}')
            try:
                response_default = domain.get('responses').get(utter_intent)[0].get('text')
            except:
                # This will be set if there is no response set for this utter_intent
                logger.info(f'Setting the response with utter_intent handle:{utter_intent}')
                response_default = utter_intent

            if response_default:
                if lang == 'en':
                    logger.info('Setting default response for the intent:{0}, '
                                'in language:{1}.'.format(intent, lang))
                    dispatcher.utter_message(text=response_default)
                else:
                    logger.info('There is no multilingual response for intent:{0}, '
                                'in language:{1}. Running online translation.'.format(intent, lang))
                    if microsoft_api_key and lang == 'zh':
                        # Change the language from 'zh' to 'Chinese Simplified',
                        # as Microsoft translate is not supported with zh
                        lang = "Chinese Simplified"
                    elif lang == 'zh':
                        # Change the language from 'zh' to 'zh-cn',
                        # as google translate is not supported with zh
                        lang = "{}-cn".format(lang)

                    # response_translated = GoogleTranslator(source='en', target=lang).translate(response_default)
                    # response_translated = MyMemoryTranslator(source='en', target=lang).translate(response_default)
                    response_translated = MicrosoftTranslator(api_key=microsoft_api_key, source='en', target=lang).translate(response_default)

                    logger.info('Translated response is:{0} in language:{1}, '
                                'for the english response:{2}'.format(response_translated, lang, response_default))
                    dispatcher.utter_message(text=response_translated)
        return []
