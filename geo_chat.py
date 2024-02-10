import json
import openai
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored

# Import our spatial functions
from spatial_functions import *

# Just Hard coding our example data for this demo
DEMO_GEODATAFRAME = invalid_polygons_gdf

# GPT Variables
GPT_MODEL = "gpt-3.5-turbo-0613"
openai.api_key = "YOUR_API_KEY"

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + openai.api_key,
    }
    json_data = {"model": model, "messages": messages}
    if tools is not None:
        json_data.update({"tools": tools})
    if tool_choice is not None:
        json_data.update({"tool_choice": tool_choice})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

# We use this to pretty print the conversation with our assistant
def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "tool": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "tool":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))


# Define our Geospatial Tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "repair_geodataframe_geom",
            "description": "Repair invalid geometries in a GeoDataFrame",
            "parameters": {},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bounding_box_of_gdf",
            "description": "Get the geospatial bounding box of a GeoDataFrame",
            "parameters": {},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buffer_gdf",
            "description": "Buffer a GeoDataFrame by a specified distance",
            "parameters": {
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "string",
                        "description": "A specific distance as a number that will be used to buffer the GeoDataFrame",
                    },
                },
                "required": ["distance"],
            },
        }
    },
]

if __name__ == "__main__":

    messages = []
    messages.append({"role": "system", "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."})

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        messages.append({"role": "user", "content": user_input})

        chat_response = chat_completion_request(messages, tools=tools)

        if chat_response.status_code == 200:
            response_data = chat_response.json()
            assistant_message_content = response_data["choices"][0].get("message", {}).get("content")

            # Ensure assistant_message_content is not None before appending
            if assistant_message_content:
                messages.append({"role": "assistant", "content": assistant_message_content})
            else:
                messages.append({"role": "assistant", "content": "Of course I can!"})

            tool_calls = response_data["choices"][0]["message"].get("tool_calls", [])
            
            for tool_call in tool_calls:
                function_call = tool_call["function"]
                tool_name = function_call["name"]

                if tool_name == "repair_geodataframe_geom":
                    repair_result = repair_geodataframe_geom(DEMO_GEODATAFRAME)
                    tool_message = "GeoDataFrame repair completed."

                elif tool_name == "bounding_box_of_gdf":
                    response = bounding_box_of_gdf(DEMO_GEODATAFRAME)
                    message = response["message"]
                    bbox = response["bbox"]
                    tool_message = f"{message} {bbox}"

                elif tool_name == "buffer_gdf":
                    function_arguments = json.loads(function_call["arguments"])
                    distance = function_arguments["distance"]
                    response = buffer_gdf(DEMO_GEODATAFRAME, int(distance))
                    DEMO_GEODATAFRAME = response["gdf"]
                    tool_message = f"The GeoDataFrame has been buffered by {distance}."
                
                else:
                    tool_message = f"Tool {tool_name} not recognized or not implemented."
                messages.append({"role": "assistant", "content": tool_message})

            # Print the conversation with the assistant
            pretty_print_conversation(messages)

        else:
            print(f"Failed to get a response from the chat service. Status Code: {chat_response.status_code}")
            try:
                error_details = chat_response.json()
                print("Response error details:", error_details.get("error", {}).get("message"))
            except Exception as e:
                print(f"Error parsing the error response: {e}")

    print("\nConversation ended.")

