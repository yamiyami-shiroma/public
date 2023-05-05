# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import datetime
import requests
import json
import html
import xml.etree.ElementTree as ET
import random

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name, get_slot_value

from ask_sdk_model import Response
from ask_sdk_model.interfaces.audioplayer import (
    PlayDirective, PlayBehavior, AudioItem, Stream, AudioItemMetadata,
    StopDirective, ClearQueueDirective, ClearBehavior)
from utils import create_presigned_url

from plugins import mediawiki

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def PlayAudio(url, response_builder):
    speak_audio_item = AudioItem(
            stream=Stream(
                token=url,
                url=url,
                offset_in_milliseconds=0,
                expected_previous_token=None),
            metadata = None
        )

    return response_builder.add_directive(
        PlayDirective(
            play_behavior=PlayBehavior.REPLACE_ALL,
            audio_item=speak_audio_item
            )
        ).set_should_end_session(True)

class LaunchRequestHandler(AbstractRequestHandler):
    """起動時"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        audio_url = create_presigned_url("Media/boot.mp3")
        speak_output = '<audio src="' + html.escape(audio_url) + '"/>'

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ReadEventsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return(
            ask_utils.is_intent_name("ReadEventsIntent")(handler_input)
          )

    def handle(self, handler_input):
        date_value = get_slot_value(handler_input=handler_input, slot_name="dateTime")
        ask_speak = " not date"
        
        if date_value is None:
            dt = datetime.date.today()
        else:
            speak_output = date_value
            dt = datetime.datetime.strptime(date_value, '%Y-%m-%d')
        
        strdt = f'{str(dt.month)}月{str(dt.day)}日'
        event = mediawiki.GetDayEvents(strdt)
        
        name = event.split("[D]")[0]
        description = event.split("[D]")[1]
        speak_output = f'{strdt}は{name}なのだ。{description}なのだ'
        
        response = requests.get("https://api.tts.quest/v1/voicevox/?text="+speak_output+"&speaker=3")
        response_dict = json.loads(response.text)
        speak_url = response_dict["mp3DownloadUrl"]
        
        #共通文言「それでは天気を読み上げるのだ」
        audio_url = create_presigned_url("Media/wait.mp3")
        speak_output = '<audio src="' + html.escape(audio_url) + '"/>'

        response_builder = PlayAudio(speak_url,handler_input.response_builder)
        return(
            response_builder
                .speak(speak_output)
                #.ask(speak_url)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )

#天気予報
class WeatherEventsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return(
            ask_utils.is_intent_name("WeatherIntent")(handler_input)
          )

    def handle(self, handler_input):
        city_value = get_slot_value(handler_input=handler_input, slot_name="city")
        #デフォルト東京のコード
        city_code = "130010"
        if city_value is None:
            city_value = "東京都"
        else:
            # XMLからcityCode取得
            root = ET.fromstring(requests.get("https://weather.tsukumijima.net/primary_area.xml").text)
            weather_req = "https://weather.tsukumijima.net/api/forecast?city=471010"
            for city in root.iter('pref'):
                if city_value in city.attrib['title']:
                    city_value = city.attrib['title']
                    for town in city.iter('city'):
                        city_code = town.attrib['id']
                        break
                    break

        # 天気取得API
        weather_req = "https://weather.tsukumijima.net/api/forecast?city="+city_code
        weater_response = requests.get(weather_req)
        weather_response_dict = json.loads(weater_response.text)
        
        #読み上げ文言作成
        telops = [weather_response_dict["forecasts"][0]["telop"],weather_response_dict["forecasts"][1]["telop"],weather_response_dict["forecasts"][2]["telop"]]
        date_str = weather_response_dict["forecasts"][0]["date"]
        date = date_str.split('-')
        date_str = date[0]+"年"+date[1]+"月"+date[2]+"日"
        weather_output = date_str+"、"+city_value+"の本日の天気は"+telops[0]+"、明日は"+telops[1]+"で、明後日は"+telops[2]+"となるのだ"
        #雨をうと読むのでひらがなに置き換え
        weather_output = weather_output.replace("雨","あめ")
        
        #voicevox API
        response = requests.get("https://api.tts.quest/v1/voicevox/?text="+weather_output+"&speaker=3")
        response_dict = json.loads(response.text)
        speak_url = response_dict["mp3DownloadUrl"]
        
        #共通文言「それでは天気を読み上げるのだ」
        audio_url = create_presigned_url("Media/weather.mp3")
        speak_output = '<audio src="' + html.escape(audio_url) + '"/>'

        response_builder = PlayAudio(speak_url,handler_input.response_builder)
        return(
            response_builder
                .speak(speak_output)
                #.ask(speak_url)
                .response
        )

class HelloWorldIntentHandler(AbstractRequestHandler):
    """hello こんにちは、こんばんは、ハロー"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        num = random.randint(1,3)
        audio_url = create_presigned_url(f"Media/hello{num}.mp3")
        speak_output = '<audio src="' + html.escape(audio_url) + '"/>'

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        audio_url = create_presigned_url("Media/help.mp3")
        speak_output = '<audio src="' + html.escape(audio_url) + '"/>'

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )



class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        reprompt = "I didn't catch that. What can I help you with?"
        audio_url = create_presigned_url("Media/error.mp3")
        speech = '<audio src="' + html.escape(audio_url) + '"/>'

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        audio_url = create_presigned_url("Media/exception.mp3")
        speak_output = '<audio src="' + html.escape(audio_url) + '"/>'

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(ReadEventsIntentHandler())
sb.add_request_handler(WeatherEventsIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
