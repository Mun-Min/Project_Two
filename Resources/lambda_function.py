### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")

### Functionality Helper Functions ###
def parse_float(n):
    """
    Securely converts a non-numeric value to float.
    """
    try:
        return float(n)
    except ValueError:
        return float("nan")

def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }

def validate_data(age, buying_power, portfolio_type, intent_request):
    """
    Validates the data provided by the user.
    """

    # Validate that the user is over 21 years old
    if age is not None:
        if age < 18:
            return build_validation_result(
                False,
                "age",
                "You should be at least 18 years old to use this service, "
                "please provide a different date of birth.",
            )

    # Validate the investment amount, it should be > 0
    if buying_power is not None:
        buying_power = parse_float(
            buying_power
        )  # Since parameters are strings it's important to cast values
        if buying_power <= 0:
            return build_validation_result(
                False,
                "buying_power",
                "The amount to convert should be greater than zero, "
                "please provide a correct amount in USD to convert.",
            )

    # A True results is returned if age or amount are valid
    return build_validation_result(True, None, None)


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]



def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """
    risk_level = get_slots(intent_request)["portfolio_type"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["buying_power"]
    
    source = intent_request["invocationSource"]
    
    if source == "DialogCodeHook":
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt
        # for the first violation detected.

        ### YOUR DATA VALIDATION CODE STARTS HERE ###
        slots = get_slots(intent_request)
        validation_result = validate_data(age, investment_amount, risk_level, intent_request)
    if not validation_result['isValid']:
        slots[validation_result["violatedSlot"]] = None
        return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
        )
        ### YOUR DATA VALIDATION CODE ENDS HERE ###

        # Fetch current session attibutes
        output_session_attributes = intent_request["sessionAttributes"]

        return delegate(output_session_attributes, get_slots(intent_request))

    # Get the initial investment recommendation
    
    portfolio_list = []
    weights_list = []
    user_buying_power_allocation = []
    
    # create a function that will determine user weights 
    def determine_weights(): 
        user_stock_weights = 110 - age
        user_bonds_crypto_weights = (100 - user_stock_weights) / 2

        user_bonds_crypto_weights = user_bonds_crypto_weights / 100
        user_stock_weights = user_stock_weights / 100
    
        weights_list.append(user_stock_weights)
        weights_list.append(user_bonds_crypto_weights)
        weights_list.append(user_bonds_crypto_weights)
    
    initial_recommendation = []
    # create a function that will determine the allocation of users buying power based on calculated weights 
    def allocate_portfolio():
        
        for weight in weights_list: 
            investments_per_asset = investment_amount * weight
            user_buying_power_allocation.append('$' + str(investments_per_asset))

    ### YOUR FINAL INVESTMENT RECOMMENDATION CODE STARTS HERE ###
    if risk_level == 'high risk portfolio': 

        portfolio_list = ['TSLA', 'NVDA', '10yr Treasury Yield', 'ETH']
  
        # calculate weights for portfolio
        determine_weights()

        # allocate users buying power towards each asset class based off of calculated weights
        allocate_portfolio()
        
        recommendation = user_buying_power_allocation
    
    ### YOUR FINAL INVESTMENT RECOMMENDATION CODE ENDS HERE ###

    # Return a message with the initial recommendation based on the risk level.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """Thank you for your information based on the risk level you defined, my recommendation is to allocate your buying power based on the following (Stocks/Bonds/Crypto) = {}
            """.format(
                recommendation
            ),
        },
    )

### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "PortfolioGeneratorIntent":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    
    return dispatch(event)