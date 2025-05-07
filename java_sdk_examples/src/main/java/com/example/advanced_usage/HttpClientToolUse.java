package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

public class HttpClientToolUse {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    // Simulated Tool: Get Current Weather
    private static String getCurrentWeather(String location, String unit) {
        System.out.println("Executing HTTP tool: getCurrentWeather for " + location + " in " + unit);
        Random random = new Random();
        Map<String, Object> weatherData = new HashMap<>();
        weatherData.put("location", location);
        weatherData.put("temperature", random.nextInt(15) + 10); // e.g., 10-24
        weatherData.put("unit", unit);
        weatherData.put("description", "Mostly sunny with occasional clouds.");
        try {
            return objectMapper.writeValueAsString(weatherData);
        } catch (JsonProcessingException e) {
            return "{\"error\": \"Failed to serialize weather data\"}";
        }
    }

    @SuppressWarnings("unchecked") // For casting generic Maps
    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName(); // Model that supports tool use

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- Java HTTP Client Tool Use --- ");

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        // 1. Define the tool(s) in the format the API expects
        Map<String, Object> weatherTool = new HashMap<>();
        weatherTool.put("type", "function");
        Map<String, Object> functionDetails = new HashMap<>();
        functionDetails.put("name", "get_current_weather");
        functionDetails.put("description", "Get the current weather in a given location");
        Map<String, Object> parameters = new HashMap<>();
        parameters.put("type", "object");
        Map<String, Object> properties = new HashMap<>();
        properties.put("location", Map.of("type", "string", "description", "The city and state, e.g. San Francisco, CA"));
        properties.put("unit", Map.of("type", "string", "enum", List.of("celsius", "fahrenheit")));
        parameters.put("properties", properties);
        parameters.put("required", List.of("location"));
        functionDetails.put("parameters", parameters);
        weatherTool.put("function", functionDetails);
        List<Map<String, Object>> tools = List.of(weatherTool);

        // Initial User Message
        List<Map<String, Object>> messages = new ArrayList<>();
        Map<String, Object> userMessage = new HashMap<>();
        userMessage.put("role", "user");
        userMessage.put("content", "What is the weather like in Boston?");
        messages.add(userMessage);

        // Prepare request body for the first call
        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", messages);
        requestBodyMap.put("tools", tools);
        requestBodyMap.put("tool_choice", "auto"); // or {"type": "function", "function": {"name": "get_current_weather"}}
        requestBodyMap.put("temperature", 0.7);
        if (modelName != null && !modelName.isEmpty()) {
            requestBodyMap.put("model", modelName);
        } else {
             System.out.println("No model specified, using a default. Ensure it supports tool use.");
             requestBodyMap.put("model", "gpt-3.5-turbo-1106"); // Or newer
        }

        try {
            String requestBodyJson = objectMapper.writeValueAsString(requestBodyMap);
            System.out.println("\n--- Sending initial request to model ---");
            System.out.println("Request Body: " + requestBodyJson);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(apiBaseUrl + "/chat/completions"))
                    .header("Content-Type", "application/json")
                    .header("Authorization", "Bearer " + apiKey)
                    .POST(HttpRequest.BodyPublishers.ofString(requestBodyJson))
                    .timeout(Duration.ofSeconds(30))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            System.out.println("--- Initial API Response --- ");
            System.out.println("Status: " + response.statusCode());
            System.out.println("Body: " + response.body());

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                Map<String, Object> responseMap = objectMapper.readValue(response.body(), Map.class);
                List<Map<String, Object>> choices = (List<Map<String, Object>>) responseMap.get("choices");
                Map<String, Object> firstChoice = choices.get(0);
                Map<String, Object> messageFromAssistant = (Map<String, Object>) firstChoice.get("message");

                messages.add(messageFromAssistant); // Add assistant's message to history

                if (messageFromAssistant.containsKey("tool_calls")) {
                    System.out.println("--- Model requested tool call(s) --- ");
                    List<Map<String, Object>> toolCalls = (List<Map<String, Object>>) messageFromAssistant.get("tool_calls");
                    
                    for (Map<String, Object> toolCall : toolCalls) {
                        String toolCallId = (String) toolCall.get("id");
                        Map<String, Object> functionCall = (Map<String, Object>) toolCall.get("function");
                        String functionName = (String) functionCall.get("name");
                        String functionArgsJson = (String) functionCall.get("arguments");

                        System.out.println("Tool Call ID: " + toolCallId);
                        System.out.println("Function Name: " + functionName);
                        System.out.println("Arguments: " + functionArgsJson);

                        String functionResponseContent = "";
                        if ("get_current_weather".equals(functionName)) {
                            Map<String, String> argsMap = objectMapper.readValue(functionArgsJson, Map.class);
                            functionResponseContent = getCurrentWeather(argsMap.get("location"), argsMap.getOrDefault("unit", "celsius"));
                        } else {
                            System.err.println("Unknown function requested: " + functionName);
                            functionResponseContent = "{\"error\": \"Unknown function: " + functionName + "\"}";
                        }
                        System.out.println("--- (Simulated) Tool Execution Result --- ");
                        System.out.println(functionResponseContent);

                        // Add tool result to messages
                        Map<String, Object> toolResponseMessage = new HashMap<>();
                        toolResponseMessage.put("tool_call_id", toolCallId);
                        toolResponseMessage.put("role", "tool");
                        toolResponseMessage.put("name", functionName);
                        toolResponseMessage.put("content", functionResponseContent); // Content must be a string
                        messages.add(toolResponseMessage);
                    }

                    // Send tool results back to the model
                    Map<String, Object> followupRequestBodyMap = new HashMap<>();
                    followupRequestBodyMap.put("messages", messages);
                    followupRequestBodyMap.put("model", requestBodyMap.get("model")); 
                    // No tools or tool_choice usually needed for this follow-up

                    String followupRequestBodyJson = objectMapper.writeValueAsString(followupRequestBodyMap);
                    System.out.println("\n--- Sending tool results back to model ---");
                    System.out.println("Follow-up Request Body: " + followupRequestBodyJson);

                    HttpRequest followupRequest = HttpRequest.newBuilder()
                            .uri(URI.create(apiBaseUrl + "/chat/completions"))
                            .header("Content-Type", "application/json")
                            .header("Authorization", "Bearer " + apiKey)
                            .POST(HttpRequest.BodyPublishers.ofString(followupRequestBodyJson))
                            .timeout(Duration.ofSeconds(30))
                            .build();

                    HttpResponse<String> followupResponse = httpClient.send(followupRequest, HttpResponse.BodyHandlers.ofString());
                    System.out.println("--- Final API Response --- ");
                    System.out.println("Status: " + followupResponse.statusCode());
                    System.out.println("Body: " + followupResponse.body());

                    if (followupResponse.statusCode() >= 200 && followupResponse.statusCode() < 300) {
                        Map<String, Object> followupResponseMap = objectMapper.readValue(followupResponse.body(), Map.class);
                        List<Map<String, Object>> followupChoices = (List<Map<String, Object>>) followupResponseMap.get("choices");
                        System.out.println("Final Assistant Message: " + ((Map<String,Object>)followupChoices.get(0).get("message")).get("content"));
                    }

                } else {
                    System.out.println("--- Model generated text response directly --- ");
                    System.out.println("Assistant Message: " + messageFromAssistant.get("content"));
                }
            } else {
                 System.err.println("Request failed or error in response structure. Status: " + response.statusCode());
            }

        } catch (IOException | InterruptedException e) {
            System.err.println("Error during HTTP request/response: " + e.getMessage());
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
            e.printStackTrace();
        }
        System.out.println("\nHTTP Client Tool Use example complete.");
    }
} 