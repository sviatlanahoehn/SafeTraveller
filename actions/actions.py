from typing import Text, Dict, Any, List, Union, Optional

#import rasa_core
from rasa_sdk.events import UserUtteranceReverted, ActionReverted
from rasa_sdk.events import SlotSet
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.knowledge_base.storage import InMemoryKnowledgeBase
from rasa_sdk.events import EventType
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.forms import FormAction
from rasa_sdk.events import AllSlotsReset
from rasa_sdk.events import FollowupAction

class ActionCheckBorders(Action):
    def name(self):
        return 'action_go_back'
    def run(self, dispatcher, tracker, domain):
        return [UserUtteranceReverted(), ActionReverted(), UserUtteranceReverted(), ActionReverted()]

class ActionCheckBorders(Action):
    def name(self):
        return 'action_check_borders'
    def run(self, dispatcher, tracker, domain):
        slots = []
        country_to = tracker.get_slot("country_to")
        country_from = tracker.get_slot("country_from")
        common_border=False
        if country_to=="Germany" or country_from=="Germany":
            common_border=True
        slots.append(SlotSet("common_border", common_border))
        return slots

class ActionResetEntityType(Action):
    def name(self):
        return 'action_reset_regulations_type'
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("regulations_type", None)]

class ActionSetLocal(Action):
    def name(self):
        return 'action_set_local'
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("regulations_type", "local_regulations")]
class ActionSetOpen(Action):
    def name(self):
        return 'action_set_open'
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("want_open_places", True)]

class ActionRepeatLast(Action):
    def name(self):
        return 'action_repeat_last'
    def run(self, dispatcher, tracker, domain):
        return [UserUtteranceReverted(), ActionReverted()]

class ActionValidateTransit(Action):
    def name(self):
        return 'action_validate_transit'
    def run(self, dispatcher, tracker, domain):
        slots = []
        return slots



class ActionValidateCountries(Action):
    def name(self):
        return 'action_validate_countries'
    def run(self, dispatcher, tracker, domain):
        countries = ["germany","luxembourg","netherlands"]
        country_main_lettrs = ["germ","lux","nether"]
        slots = [SlotSet("regulations_type", "entry_regulations")]
        common_border=False

        num_country_from = len(list(tracker.get_latest_entity_values(regulations_type="country", entity_role="from")))
        num_country_to = len(list(tracker.get_latest_entity_values(regulations_type="country", entity_role="to")))
        if num_country_to==1 and num_country_from==1:
            country_from = next(tracker.get_latest_entity_values(regulations_type="country", entity_role="from"), None)
            country_to = next(tracker.get_latest_entity_values(regulations_type="country", entity_role="to"), None)
            distinct_countries = country_from.lower()!=country_to.lower()

            if country_to.lower() in countries:
                slots.append(SlotSet("country_to", country_to))
            else:
                dispatcher.utter_message(response="utter_wrong_country_to")
                slots.append(SlotSet("country_to", None))

            if country_from.lower() in countries and distinct_countries:
                slots.append(SlotSet("country_from", country_from))
            else:
                dispatcher.utter_message(response="utter_wrong_country_from")
                slots.append(SlotSet("country_from", None))

            if country_to=="Germany" or country_from=="Germany":
                common_border=True
            slots.append(SlotSet("common_border", common_border))
        else:
            slots.append(SlotSet("country_to", None))
            slots.append(SlotSet("country_from", None))
            dispatcher.utter_message(response="utter_not_understood")
        return slots




class ActionResetTransportSlot(Action):
    def name(self):
        return 'action_reset_transport_slot'
    def run(self, dispatcher, tracker, domain):
        transit = tracker.get_slot("transit_DE")
        if transit==False:
            transport_type = "plane"
        else:
            transport_type = None
        return [SlotSet("transport_type", transport_type)]



class ActionUtterDisclaimer(Action):
    def name(self):
        return 'action_utter_disclaimer'
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(f"| Important: I'm based in Luxembourg and was designed only for people travelling to and from Luxembourg, Germany or the Netherlands. |\n")
        return []

class ActionAskConfirmCollectedInfo(Action):
    def name(self):
        return 'action_ask_confirm_collected_info'

    def run(self, dispatcher, tracker, domain):
        country_to = tracker.get_slot("country_to")
        dispatcher.utter_message(f"Here is the trip details that I have collected:\n")
        if country_to=="Luxembourg":
            transport_type = tracker.get_slot("transport_type")
            dispatcher.utter_message(f"You are going by {transport_type}\n")
            visit_purpose = tracker.get_slot("visit_purpose")
            if visit_purpose=="work":
                dispatcher.utter_message(f"You are going for {visit_purpose}-related purposes\n")
        elif country_to=="Germany":
            one_day = tracker.get_slot("<24h")
            if one_day==True:
                dispatcher.utter_message(f"You are going for one day\n")
            visit_purpose = tracker.get_slot("visit_purpose")
            if visit_purpose!=None:
                dispatcher.utter_message(f"You are going for {visit_purpose}-related purposes\n")
            tsw = tracker.get_slot("transport_sector_worker")
            if tsw==True:
                dispatcher.utter_message(f"You are a transport sector worker\n")
        elif country_to=="Netherlands":
            transport_type = tracker.get_slot("transport_type")
            if transport_type!=None:
                dispatcher.utter_message(f"You are going by {transport_type}\n")
            visit_purpose = tracker.get_slot("visit_purpose")
            dispatcher.utter_message(f"You are going for {visit_purpose}-related purposes\n")
            tsw = tracker.get_slot("transport_sector_worker")
            if tsw==True:
                dispatcher.utter_message(f"You are a transport sector worker\n")
        return []


class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback_custom"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_custom_fallback")

        current_slots = []
        country_from = tracker.get_slot("country_from")
        current_slots.append(country_from)
        country_to = tracker.get_slot("country_to")
        current_slots.append(country_to)
        regulations_type = tracker.get_slot("regulations_type")
        current_slots.append(regulations_type)
        transport_type = tracker.get_slot("transport_type")
        current_slots.append(transport_type)
        visit_purpose = tracker.get_slot("visit_purpose")
        current_slots.append(visit_purpose)
        one_day = tracker.get_slot("<24h")
        current_slots.append(one_day)

        dispatcher.utter_message(f"I could not undersatnd that, sorry.")
        dispatcher.utter_message(f"Please rephrase, so that we can continue.")

        return [UserUtteranceReverted()]


class ActionClearCountries(Action):
    def name(self) -> Text:
        return "action_clear_countries"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "DomainDict",
    ) -> List[Dict[Text, Any]]:
        slots = []
        correct_countries = tracker.get_slot("correct_countries")
        if correct_countries==False:
            slots.append(SlotSet("country_to", None))
            slots.append(SlotSet("country_from", None))
        return slots


class ValidateWantLocalInfoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_want_local_info_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> Optional[List[Text]]:
        required_slots = slots_mapped_in_domain + ["regulations_type"]
        return required_slots

    async def extract_regulations_type(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:

        last_intent = tracker.get_intent_of_latest_message()
        regulations_type = "entry_regulations"
        if last_intent == "affirm":
            regulations_type = "local_regulations"

        return {"regulations_type": regulations_type}


class ActionAskCorrectCountries(Action):
    def name(self):
        return "action_ask_correct_countries"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "DomainDict",
    ) -> List[Dict[Text, Any]]:
        country_to = tracker.get_slot("country_to")
        country_from = tracker.get_slot("country_from")
        dispatcher.utter_message(f"I am going to look for regulations on travel from {country_from} to {country_to}. Is that what you are looking for?")
        return []


# =========== Adaptation of ActionQueryAttribute class from tutorial-knowledge-base.actions
class CustomActionQueryKB(Action):

    def name(self):
        return "action_query_knowledgebase_cases"

    def __init__(self):
        self.knowledge_base = InMemoryKnowledgeBase("knowledge_base_data.json")

    def custom_get_attribute_of(
        self, regulations_type: Text, key_attribute: Text, entity: Text, attribute: Text
    ) -> List[Any]:
        if regulations_type not in self.knowledge_base.data:
            return []
        entities = self.knowledge_base.data[regulations_type]
        entity_of_interest = list(
            filter(lambda e: e[key_attribute] == entity, entities)
        )
       # if not entity_of_interest or len(entity_of_interest) > 1:
        if not entity_of_interest:
            return []
        return [entity_of_interest[0][attribute]]


# ------  UNNECESSARY ATTRIBUTE "location" ------ !!!
    def run(self, dispatcher, tracker, domain):
        regulations_type = tracker.get_slot("regulations_type")
        country_to = tracker.get_slot("country_to")
        attribute = "conditions"
        key_attribute = "id"
        case_id_transit= None
        case_id_children = None
        case_id_open_places = None
        children_travel = tracker.get_slot("travelling_with_children")
        case_id_details = None
        case_id_indoors = None
        case_id_outdoors = None
        case_id = None

        if regulations_type == "entry_regulations":
            visit_purpose = tracker.get_slot("visit_purpose")
            transport_type = tracker.get_slot("transport_type")
            transport_sector_worker = tracker.get_slot("transport_sector_worker")
            NL_worker = tracker.get_slot("NL_worker")
            less_than_24h = tracker.get_slot("<24h")
            transit_DE = tracker.get_slot("transit_DE")
            if transport_type!=None:
                transport_type = transport_type.lower()
            if visit_purpose != None:
                visit_purpose = visit_purpose.lower()

            if country_to=="Germany":
                case_id_children = 0
                if less_than_24h==True or transport_sector_worker==True: #or transit==True
                    case_id = 0
                elif visit_purpose=="work" and less_than_24h==False:
                    case_id = 1
                elif (visit_purpose=="leisure" or visit_purpose=="family") and less_than_24h==False:
                    case_id = 2
                else:
                    dispatcher.utter_message(response="utter_query_failed")
                    dispatcher.utter_message(response="utter_restart_please")

            elif country_to=="Luxembourg":
                if transport_type=="plane":
                    case_id_children = 2
                if transport_type=="car" or transport_type=="car" or transport_sector_worker==True:
                    case_id = 3
                elif transport_type=="plane" and transport_sector_worker==False:
                    case_id = 4
                else:
                    dispatcher.utter_message(response="utter_query_failed")
                    dispatcher.utter_message(response="utter_restart_please")

            elif country_to=="Netherlands":
                case_id_children = 4
                if (visit_purpose=="work" and NL_worker==True) or (visit_purpose=="leisure" and transport_type=="car"):
                    case_id = 5
                elif (visit_purpose=="work" and NL_worker==False) or (visit_purpose=="family" and transport_type=="car"):
                    case_id = 6
                elif visit_purpose=="family" and transport_type=="coach":
                    case_id = 7
                elif visit_purpose=="leisure" and transport_type=="coach":
                    case_id = 8
                elif visit_purpose=="leisure" and transport_type=="plane":
                    case_id = 9
                elif visit_purpose=="family" and transport_type=="plane": #!or changing planes in NL!
                    case_id = 10
                else:
                    dispatcher.utter_message(response="utter_query_failed")
                    dispatcher.utter_message(response="utter_restart_please")
            else:
                dispatcher.utter_message(response="utter_did_not_find_the_country")

            if transit_DE == True:
                case_id_transit = 0
                country_to_transit = "Germany"

        elif regulations_type == "local_regulations":
            place = tracker.get_slot("indoors/outdoors")
            location = tracker.get_slot("country_to")
            going_from = tracker.get_slot("visit_purpose")
            one_household = tracker.get_slot("one_household")
            open_places = tracker.get_slot("want_open_places")


            if location=="Germany":
                case_id_children = 1
                if open_places == True:
                    case_id_open_places = 13
                if place=="indoors":
                    case_id_indoors = 1
                elif place=="outdoors":
                    case_id_outdoors = 0
                elif place=="both":
                    case_id_indoors = 1
                    case_id_outdoors = 0
                else:
                    dispatcher.utter_message(response="utter_query_failed")
                    dispatcher.utter_message(response="utter_restart_please")
            elif location=="Luxembourg":
                case_id_children = 3
                if open_places == True:
                    case_id_open_places = 14
                if place=="indoors":
                    case_id_indoors = 7
                elif place=="outdoors":
                    if going_from=="work" and one_household==True:
                        case_id_outdoors = 3
                    elif going_from=="work":
                        case_id_outdoors = 4
                    elif one_household==True:
                        case_id_outdoors = 5
                    elif one_household==False:
                        case_id_outdoors = 6
                elif place=="both":
                    case_id_indoors = 7
                    if going_from=="work" and one_household==True:
                        case_id_outdoors = 3
                    elif going_from=="work":
                        case_id_outdoors = 4
                    elif one_household==True:
                        case_id_outdoors = 5
                    elif one_household==False:
                        case_id_outdoors = 6
            elif location=="Netherlands":
                if open_places == True:
                    case_id_open_places = 15
                if place=="indoors":
                    case_id_indoors = 12
                elif place=="outdoors":
                    if going_from=="work" and one_household==True:
                        case_id_outdoors = 8
                    elif going_from=="work":
                        case_id_outdoors = 9
                    elif one_household==True:
                        case_id_outdoors = 10
                    elif one_household==False:
                        case_id_outdoors = 11

        elif regulations_type == "details":
            country = tracker.get_slot("country_to")
            if country=="Germany":
                case_id = 20
            elif country=="Luxembourg":
                case_id = 21
            elif country=="Netherlands":
                case_id = 22
        else:
            dispatcher.utter_message(response="utter_query_failed")
            dispatcher.utter_message(response="utter_restart_please")

            return []

        rule_transit = ""
        if case_id_transit != None:
            rule_transit = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_transit, attribute)[0]
        rule_child = ""
        if children_travel == True and case_id_children != None:
            rule_child = self.custom_get_attribute_of("children_exceptions", key_attribute, case_id_children, attribute)[0]
        rule_open_pl = ""
        if case_id_open_places != None:
            rule_open_pl = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_open_places, attribute)[0]

        if regulations_type=="local_regulations":
            rule_indoors = ""
            if case_id_indoors!=None:
                rule_indoors = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_indoors, attribute)[0]
            rule_outdoors = ""
            if case_id_outdoors!=None:
                rule_outdoors = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_outdoors, attribute)[0]
            dispatcher.utter_message(f"The following regulations apply in {location} : \n {rule_indoors} \n {rule_outdoors} \n {rule_open_pl} \n ")
            rule_open_pl = ""
        else:
            rule_entry = self.custom_get_attribute_of(regulations_type, key_attribute, case_id, attribute)[0]
            if case_id!=None and case_id<20:
                dispatcher.utter_message(f"The following regulations apply in {country_to} : \n {rule_entry}")
                #dispatcher.utter_message(f"rule_transit: {rule_transit}")
                if rule_transit:
                    dispatcher.utter_message(f"The following regulations apply for transitting through {country_to_transit}: \n {rule_transit}\n")
                if rule_child:
                    dispatcher.utter_message(f"The following exceptions for children apply in {country_to} : \n {rule_child}\n")
            else:
                dispatcher.utter_message(f"The following requirements apply: \n {rule_entry} \n ")

        slots = [SlotSet("indoors/outdoors", None), SlotSet("one_household", None)]
        # SlotSet("transit_DE", None), SlotSet("transport_type", None)]
                # SlotSet("transit", None)
        if regulations_type=="local_regulations":
            slots.append(SlotSet("want_open_places", False))


        counter = tracker.get_slot("query_counter")
#===== counting queries
        if counter==None:
            counter = 1
        elif counter==1:
            counter = 2
        else:
            pass
        slots.append(SlotSet("query_counter", counter))

        return slots
