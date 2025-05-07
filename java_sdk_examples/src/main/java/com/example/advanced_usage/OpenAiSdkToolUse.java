package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyDescription;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.completion.chat.*;
import com.theokanning.openai.service.FunctionExecutor;
import com.theokanning.openai.service.OpenAiService;

import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import static com.theokanning.openai.service.OpenAiService.*;

// Example Tool: Get Current Weather
class Weather {
    @JsonPropertyDescription("City and state, e.g., San Francisco, CA")
    public String location;

    @JsonPropertyDescription("The temperature unit, can be celsius or fahrenheit")
    @JsonProperty(required = true)
    public WeatherUnit unit;
}

enum WeatherUnit { CELSIUS, FAHRENHEIT }

class WeatherResponse {
    public String location;
    public WeatherUnit unit;
    public int temperature;
    public String description;

    public WeatherResponse(String location, WeatherUnit unit, int temperature, String description) {
        this.location = location;
        this.unit = unit;
        this.temperature = temperature;
        this.description = description;
    }    // getters for jackson serialization if needed, or public fields are fine for this simple example
}

public class OpenAiSdkToolUse {
    private static final ObjectMapper JSON_MAPPER = new ObjectMapper();

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName(); // Model that supports function calling

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Tool Use (Function Calling) --- ");

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(30)).newBuilder().build();
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                com.theokanning.openai.client.OpenAiApi openAiApi = retrofit.create(com.theokanning.openai.client.OpenAiApi.class);
                service = new OpenAiService(openAiApi);
                System.out.println("Using custom API base URL: " + apiBaseUrl);
            } else {
                service = new OpenAiService(apiKey, Duration.ofSeconds(30));
                System.out.println("Using default OpenAI API base URL.");
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        // 1. Define the tool (function)
        ChatFunction getWeatherFunction = ChatFunction.builder()
                .name("get_current_weather")
                .description("Get the current weather in a given location")
                .executor(Weather.class, w -> {
                    // Simulated tool execution
                    System.out.println("Simulating call to get_current_weather with location: " + w.location + ", unit: " + w.unit);
                    Random random = new Random();
                    return new WeatherResponse(w.location, w.unit, random.nextInt(15) + 10, "Sunny with a chance of clouds");
                })
                .build();
        
        FunctionExecutor functionExecutor = new FunctionExecutor(Collections.singletonList(getWeatherFunction));

        // 2. Initial User Message
        List<ChatMessage> messages = new ArrayList<>();
        messages.add(new ChatMessage(ChatMessageRole.USER.value(), "What is the weather like in London?"));

        System.out.println("Initial messages: " + messages);
        System.out.println("Tools (Functions) available: " + getWeatherFunction.getName());

        ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                .messages(messages)
                .functions(functionExecutor.getFunctions()) // Pass the list of available functions
                .functionCall(ChatCompletionRequest.ChatCompletionRequestFunctionCall.AUTO) // Let model decide, or force: new ChatCompletionRequestFunctionCall("get_current_weather")
                .temperature(0.7);
        
        if (modelName != null && !modelName.isEmpty()) {
            requestBuilder.model(modelName); // Ensure this model supports function calling
        } else {
            System.out.println("No model for function calling specified, using 'gpt-3.5-turbo-0613' or newer compatible model.");
            requestBuilder.model("gpt-3.5-turbo-0613"); // Or a newer model that supports functions
        }
        ChatCompletionRequest chatCompletionRequest = requestBuilder.build();

        try {
            System.out.println("\n--- Sending initial request to model ---");
            ChatMessage responseMessage = service.createChatCompletion(chatCompletionRequest).getChoices().get(0).getMessage();
            messages.add(responseMessage); // Add assistant's response (potential function call)

            if (responseMessage.getFunctionCall() != null) {
                ChatFunctionCall functionCall = responseMessage.getFunctionCall();
                System.out.println("--- Model requested a function call --- ");
                System.out.println("Function Name: " + functionCall.getName());
                System.out.println("Arguments: " + functionCall.getArguments()); // Arguments are JsonNode

                // 3. Execute the function
                // The FunctionExecutor can simplify this, or you can do it manually.
                // For manual execution:
                // if ("get_current_weather".equals(functionCall.getName())) {
                //     Weather weatherArgs = JSON_MAPPER.treeToValue(functionCall.getArguments(), Weather.class);
                //     WeatherResponse weatherResponse = (WeatherResponse) getWeatherFunction.getExecutor().apply(weatherArgs);
                //     String functionResponseContent = JSON_MAPPER.writeValueAsString(weatherResponse);
                //     ChatMessage functionResponseMessage = new ChatMessage(ChatMessageRole.FUNCTION.value(), functionResponseContent, functionCall.getName());
                //     messages.add(functionResponseMessage);
                // }

                // Using FunctionExecutor:
                ChatMessage functionResponseMessage = functionExecutor.executeAndConvertToMessageHandlingExceptions(functionCall);
                if (functionResponseMessage == null) {
                     System.err.println("Error executing function or function not found by executor.");
                     // Potentially add an error message back to the model
                     ChatMessage errorMsg = new ChatMessage(ChatMessageRole.FUNCTION.value(), 
                                                        "{\"error\": \"Function " + functionCall.getName() + " execution failed or not found.\"}", 
                                                        functionCall.getName());
                     messages.add(errorMsg);
                } else {
                    messages.add(functionResponseMessage);
                }
                System.out.println("--- (Simulated) Tool Execution Result added to messages ---");
                System.out.println(messages.get(messages.size()-1).getContent());

                // 4. Send results back to the model
                System.out.println("\n--- Sending tool results back to model ---");
                ChatCompletionRequest followupRequest = ChatCompletionRequest.builder()
                        .model(chatCompletionRequest.getModel()) // Use the same model
                        .messages(messages)
                        // No functions needed for this follow-up usually, model should generate text
                        .build();

                ChatMessage finalMessage = service.createChatCompletion(followupRequest).getChoices().get(0).getMessage();
                System.out.println("--- Final API Response --- ");
                System.out.println("Final Assistant Message: " + finalMessage.getContent());

            } else {
                System.out.println("--- Model generated text response directly --- ");
                System.out.println("Assistant Message: " + responseMessage.getContent());
            }

        } catch (retrofit2.HttpException e) {
            System.err.println("API HTTP Error: " + e.code() + " " + e.message());
            try {
                System.err.println("Error Body: " + (e.response() != null && e.response().errorBody() != null ? e.response().errorBody().string() : "N/A"));
            } catch (IOException ioe) { System.err.println("Error reading error body: " + ioe); }
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
            e.printStackTrace();
        }

        service.shutdownExecutor();
        System.out.println("\nSDK Tool Use (Function Calling) example complete.");
    }
} 