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

# risk_rec() is the function that defines the different risk levels, and is called ultimatly in the recommend_portfolio().
def risk_rec(risk_level):
    risk_rate= {
        "none" : "100% bonds (AGG), 0% equities (SPY)",
        "low" : "60% bonds (AGG), 40% equities (SPY)",
        "medium" : "40% bonds (AGG), 60% equities (SPY)",
        "high" : "20% bonds (AGG), 80% equities (SPY)"
    }
    return risk_rate[risk_level.lower()]

# input_data() function takes three parameters, the age, investment_amount and intent_request. We have set the age as above 0 years and below 65 years.
def input_data(age, investment_amount, intent_request):
    if age is not None:
        # age = parse_int(age)
        if int(age) < 0 or int(age) >= 65:
            return build_validation_result(
                False,
                "age",
                "I'm sorry, at this time we cannot offer investment advice because of age restrictions."
                )
# We have set the investment_amount to greater than 5000$.
    if investment_amount is not None:
        investment_amount = parse_int(investment_amount)
        if investment_amount < 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "I'm sorry, We ask that investments are over $5000"
                )
    
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


"""
Step 3: Enhance the Robo Advisor with an Amazon Lambda Function

In this section, you will create an Amazon Lambda function that will validate the data provided by the user on the Robo Advisor.

1. Start by creating a new Lambda function from scratch and name it `recommendPortfolio`. Select Python 3.7 as runtime.

2. In the Lambda function code editor, continue by deleting the AWS generated default lines of code, then paste in the starter code provided in `lambda_function.py`.

3. Complete the `recommend_portfolio()` function by adding these validation rules:

    * The `age` should be greater than zero and less than 65.
    * The `investment_amount` should be equal to or greater than 5000.

4. Once the intent is fulfilled, the bot should respond with an investment recommendation based on the selected risk level as follows:

    * **none:** "100% bonds (AGG), 0% equities (SPY)"
    * **low:** "60% bonds (AGG), 40% equities (SPY)"
    * **medium:** "40% bonds (AGG), 60% equities (SPY)"
    * **high:** "20% bonds (AGG), 80% equities (SPY)"

> **Hint:** Be creative while coding your solution, you can have all the code on the `recommend_portfolio()` function, or you can split the functionality across different functions, put your Python coding skills in action!

5. Once you finish coding your Lambda function, test it using the sample test events provided for this Challenge.

6. After successfully testing your code, open the Amazon Lex Console and navigate to the `recommendPortfolio` bot configuration, integrate your new Lambda function by selecting it in the “Lambda initialization and validation” and “Fulfillment” sections.

7. Build your bot, and test it with valid and invalid data for the slots.

"""


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]

    # Here we are grabbing the data from the Lex-Bot dialog. "DialogCodeHook" does the initialization and validation for user input.
    origin = intent_request["invocationSource"]

    if origin == "DialogCodeHook":
        # The "DialogCodeHook" does basic validation of the input slots.
        # This grabs the slots.
        slots = get_slots(intent_request)

        # Validates user's input using the input_data function
        # The input_data is passed to valid_result.
        valid_result = input_data(age, investment_amount, intent_request)
        
        # If the user inputs invalid data, the elicitSlot action is called and the user is prompted to re-enter.
        if not valid_result["isValid"]:
            slots[valid_result["violatedSlot"]] = None  
            # The above command emptys out the invalid slot.

            # And the elicitSlot is called to ask user to re-enter the data.
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                valid_result["violatedSlot"],
                valid_result["message"],
            )

        # Here we are grabbing the session attributes
        output_session_attributes = intent_request["sessionAttributes"]
        
        # If all the slots have valid inputs, delegate tells Lex to continue.
        return delegate(output_session_attributes, get_slots(intent_request))
        
    recommended_risk_level = risk_rec(risk_level)

    # This is a command to respond with some dialog text.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """Thank you {}.
            ${} USD has been invested into your account at the recommended risk: {}.
            """.format(
                first_name, investment_amount, recommended_risk_level
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
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)
